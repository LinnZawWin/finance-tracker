"""Shared Dataverse Web API helper for the Finance Tracker scripts.

Reads DATAVERSE_URL from the environment and takes a token from the Azure CLI
sign-in (az login --use-device-code). Nothing secret is stored in this repo.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from azure.identity import AzureCliCredential

SOLUTION = "lzw_FinanceTracker"
PREFIX = "lzw_"
BASE = os.environ["DATAVERSE_URL"].rstrip("/")
API = BASE + "/api/data/v9.2/"
# Unbound actions that are safe to send twice.
IDEMPOTENT_ACTIONS = ("AddSolutionComponent", "AddAppComponents", "PublishXml", "PublishAllXml")
_cred = AzureCliCredential()
_tok = {"v": None, "exp": 0}


def token():
    if _tok["exp"] - time.time() < 300:
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
