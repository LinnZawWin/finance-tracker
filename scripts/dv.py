"""Shared Dataverse Web API helper for the Finance Tracker scripts.

Reads DATAVERSE_URL from the environment and takes a token from the Azure CLI
sign-in. When the Azure CLI is not signed in and AZURE_CLIENT_ID, AZURE_TENANT_ID and
AZURE_CLIENT_SECRET are set (Claude Code cloud sessions), it signs in as that service
principal first. Nothing secret is stored in this repo.
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import AzureCliCredential

SOLUTION = "lzw_FinanceTracker"
PREFIX = "lzw_"
BASE = os.environ["DATAVERSE_URL"].rstrip("/")
API = BASE + "/api/data/v9.2/"
# Unbound actions that are safe to send twice.
IDEMPOTENT_ACTIONS = ("AddSolutionComponent", "AddAppComponents", "PublishXml", "PublishAllXml")
_cred = AzureCliCredential()
_tok = {"v": None, "exp": 0}


def _sp_login():
    """Sign the Azure CLI in as the service principal from the environment, if one is set."""
    ids = [os.environ.get(k) for k in ("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID")]
    if not all(ids):
        return False
    r = subprocess.run(["az", "login", "--service-principal", "-u", ids[0], "-p", ids[1], "--tenant", ids[2],
                        "--allow-no-subscriptions", "--output", "none"], capture_output=True, text=True)
    if r.returncode:
        # stderr from az does not contain the secret; keep only the last line.
        raise RuntimeError("Azure CLI service principal sign-in failed: "
                           + (r.stderr.strip().splitlines() or ["exit %d" % r.returncode])[-1])
    print("Signed the Azure CLI in as the service principal from the environment.")
    return True


def token():
    if _tok["exp"] - time.time() < 300:
        try:
            t = _cred.get_token(BASE + "/.default")
        except ClientAuthenticationError:
            # CredentialUnavailableError (not signed in) is a subclass.
            if not _sp_login():
                raise
            t = _cred.get_token(BASE + "/.default")
        _tok["v"], _tok["exp"] = t.token, t.expires_on
    return _tok["v"]


class DvError(Exception):
    def __init__(self, code, body):
        self.code, self.body = code, body
        super().__init__(f"HTTP {code}: {body[:600]}")


def call(method, path, body=None, solution=False, headers=None, retries=4, done=None):
    """Call the Web API. Returns (parsed json or None, response headers)."""
    url = path if path.startswith("http") else API + urllib.parse.quote(path, safe="/()?=&$',@*:;%-._~!")
    h = {
        "Authorization": "Bearer " + token(),
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
    }
    if solution:
        h["MSCRM.SolutionUniqueName"] = SOLUTION
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries + 1):
        h["Authorization"] = "Bearer " + token()
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
                return (json.loads(raw) if raw else None), dict(r.headers)
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            transient = e.code in (429, 502, 503, 504) or any(
                s in txt for s in ("0x80040216", "0x80060891", "0x80071151", "another customization", "0x80044363")
            )
            if transient and attempt < retries:
                time.sleep(10 * (attempt + 1))
                continue
            raise DvError(e.code, txt)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            # The proxy drops requests that stay silent for ~10s, but Dataverse usually still
            # completes them. Reads are retried; writes are retried only after `done()` says
            # the change did not land, so nothing is created twice.
            if attempt >= retries:
                raise
            time.sleep(15 * (attempt + 1))
            if method in ("GET", "PATCH") or path in IDEMPOTENT_ACTIONS:
                continue
            if done is None:
                raise
            for _ in range(6):
                try:
                    if done():
                        return None, {}
                except DvError:
                    pass
                time.sleep(10)
            continue


BATCH_SIZE = 25  # operations per $batch request: small enough to answer well within the proxy's ~10 s


def _url(path):
    return path if path.startswith("http") else API + urllib.parse.quote(path, safe="/()?=&$',@*:;%-._~!")


def _batch_body(ops, boundary):
    """multipart/mixed body: the writes in one change set (atomic), the reads after it."""
    crlf, parts, cs = "\r\n", [], "changeset_" + boundary
    writes = [o for o in ops if o[0] != "GET"]
    if writes:
        inner = []
        for n, (method, path, body) in enumerate(writes, 1):
            req = [f"--{cs}", "Content-Type: application/http", "Content-Transfer-Encoding: binary",
                   f"Content-ID: {n}", "", f"{method} {_url(path)} HTTP/1.1",
                   "Content-Type: application/json; charset=utf-8", ""]
            inner.append(crlf.join(req) + crlf + (json.dumps(body) if body is not None else ""))
        parts.append(f"--batch_{boundary}{crlf}Content-Type: multipart/mixed; boundary={cs}{crlf}{crlf}"
                     + crlf.join(inner) + f"{crlf}--{cs}--")
    for method, path, _ in ops:
        if method == "GET":
            parts.append(crlf.join([f"--batch_{boundary}", "Content-Type: application/http",
                                    "Content-Transfer-Encoding: binary", "", f"GET {_url(path)} HTTP/1.1",
                                    "Accept: application/json", "", ""]))
    return (crlf.join(parts) + f"{crlf}--batch_{boundary}--{crlf}").encode()


def _batch_parse(raw):
    """[(status, json or None, headers)] in the order of the responses (writes first, then reads)."""
    out = []
    for chunk in raw.split("HTTP/1.1 ")[1:]:
        head, _, rest = chunk.replace("\r\n", "\n").partition("\n\n")
        lines = head.split("\n")
        status = int(lines[0].split()[0])
        hdrs = dict(l.split(": ", 1) for l in lines[1:] if ": " in l)
        body = rest.split("\n--", 1)[0].strip()
        try:
            data = json.loads(body) if body else None
        except ValueError:
            data = None
        out.append((status, data, hdrs))
    return out


def batch(ops, done=None, size=BATCH_SIZE):
    """Send many operations in $batch requests of `size`, instead of one request each.

    ops: [(method, path, body)], method GET, POST, PATCH or DELETE. In each request the writes form one change set,
    which Dataverse applies all or nothing, and the reads (for example CalculateRollupField) follow it, so a read sees
    the writes of its own request. Returns [(status, json, headers)] in the order of ops; after a dropped request that
    had landed the entries of that request are (None, None, {}).
    done(chunk) -> bool: called when the proxy drops a request that contains POST or DELETE, with that request's ops;
    True = the change set landed (it is atomic, so checking one of its writes is enough). Without done such a drop
    raises, as call() does; requests of only GET and PATCH are simply resent. An error in a change set raises DvError
    and nothing of that request is written (requests sent before it stay written).
    A PATCH to an id that does not exist creates that row (upsert), as with call(): only PATCH ids you have read.
    """
    results = []
    for i in range(0, len(ops), size):
        chunk = ops[i:i + size]
        order = [n for n, o in enumerate(chunk) if o[0] != "GET"] + [n for n, o in enumerate(chunk) if o[0] == "GET"]
        boundary = f"{int(time.time() * 1000)}_{i}"
        data = _batch_body([chunk[n] for n in order], boundary)
        resend_ok = all(o[0] in ("GET", "PATCH") for o in chunk)
        for attempt in range(5):
            req = urllib.request.Request(API + "$batch", data=data, method="POST", headers={
                "Authorization": "Bearer " + token(), "Accept": "application/json", "OData-MaxVersion": "4.0",
                "OData-Version": "4.0", "Content-Type": f"multipart/mixed; boundary=batch_{boundary}"})
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    got = _batch_parse(r.read().decode("utf-8", "replace"))
                break
            except urllib.error.HTTPError as e:
                txt = e.read().decode("utf-8", "replace")
                if e.code in (429, 502, 503, 504) and attempt < 4:
                    time.sleep(10 * (attempt + 1))
                    continue
                bad = [g for g in _batch_parse(txt) if g[0] >= 400]  # a failed change set: show its error
                raise DvError(bad[0][0] if bad else e.code, json.dumps(bad[0][1]) if bad else txt)
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt >= 4:
                    raise
                time.sleep(15 * (attempt + 1))
                if resend_ok:
                    continue
                if done is None:
                    raise
                landed = False
                for _ in range(6):
                    try:
                        landed = done(chunk)
                        break
                    except DvError:
                        time.sleep(10)
                if landed:
                    got = None
                    break
        if got is None:
            results += [(None, None, {})] * len(chunk)
            continue
        errors = [g for g in got if g[0] >= 400]
        if errors or len(got) != len(chunk):
            raise DvError(errors[0][0] if errors else 0, json.dumps(errors[0][1] if errors else got)[:600])
        mapped = [None] * len(chunk)
        for n, g in zip(order, got):
            mapped[n] = g
        results += mapped
    return results


def get(path, **kw):
    return call("GET", path, **kw)[0]


def get_all(path):
    out, url = [], path
    while url:
        r = get(url)
        out += r["value"]
        url = r.get("@odata.nextLink")
    return out


def post(path, body, **kw):
    return call("POST", path, body, **kw)


def patch(path, body, **kw):
    return call("PATCH", path, body, **kw)


def exists(path):
    try:
        get(path)
        return True
    except DvError as e:
        if e.code == 404:
            return False
        raise


def new_id(resp_headers):
    """Extract the GUID from an OData-EntityId response header."""
    v = resp_headers.get("OData-EntityId") or resp_headers.get("odata-entityid") or ""
    return v[v.rfind("(") + 1:v.rfind(")")]


def label(text):
    return {"LocalizedLabels": [{"Label": text, "LanguageCode": 1033}]}


def publish_all():
    post("PublishAllXml", {})


def add_to_solution(component_id, component_type, required=False):
    post("AddSolutionComponent", {
        "ComponentId": component_id, "ComponentType": component_type,
        "SolutionUniqueName": SOLUTION, "AddRequiredComponents": required,
    })
