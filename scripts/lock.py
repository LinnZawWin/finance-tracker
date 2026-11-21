"""A lock in Dataverse, so only one session at a time writes reconciliation (reconcile.py --apply).

The lock is the value of the environment variable lzw_ReconcileLock: "<holder> <UTC time>" while held,
empty when free. It is taken with an If-Match update (optimistic concurrency), so two sessions in different
containers cannot both get it. A lock older than STALE minutes is treated as abandoned (a crashed run).

    with lock.held("reconcile"):
        ...writes...

    python scripts/lock.py            show the lock
    python scripts/lock.py --release  clear it by hand (only when no run is in progress)
"""
import contextlib
import datetime as dt
import os
import socket
import sys
import uuid

import dv

SCHEMA = "lzw_ReconcileLock"
STALE = 60  # minutes


class Busy(Exception):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _definition():
    q = f"environmentvariabledefinitions?$select=environmentvariabledefinitionid&$filter=schemaname eq '{SCHEMA}'"
    r = dv.get(q)["value"]
    if not r:
        dv.post("environmentvariabledefinitions", {
            "schemaname": SCHEMA, "displayname": "Reconcile Lock", "type": 100000000,
            "description": "Held by reconcile.py --apply while it writes: '<holder> <UTC time>', empty when free. "
                           "Managed by scripts/lock.py; do not edit by hand while a run is in progress.",
        }, solution=True, done=lambda: bool(dv.get(q)["value"]))
        r = dv.get(q)["value"]
    return r[0]["environmentvariabledefinitionid"]


def _value(def_id):
    """(value row id, value, etag) or (None, '', None)."""
    r = dv.get("environmentvariablevalues?$select=environmentvariablevalueid,value,createdon"
               f"&$filter=_environmentvariabledefinitionid_value eq {def_id}&$orderby=createdon")["value"]
    if not r:
        return None, "", None
    return r[0]["environmentvariablevalueid"], r[0].get("value") or "", r[0]["@odata.etag"]


def _held_by_other(value, me):
    if not value.strip():
        return None
    holder, _, since = value.rpartition(" ")
    try:
        age = (_now() - dt.datetime.fromisoformat(since.replace("Z", "+00:00"))).total_seconds() / 60
    except ValueError:
        age = STALE + 1
    if holder == me or age > STALE:
        return None
    return f"{holder} since {since} ({age:.0f} min ago)"


def acquire(purpose):
    me = f"{purpose}@{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"
    token = f"{me} {_now().strftime('%Y-%m-%dT%H:%M:%SZ')}"
    def_id = _definition()
    vid, value, etag = _value(def_id)
    other = _held_by_other(value, me)
    if other:
        raise Busy(f"reconciliation lock is held by {other}")
    if vid is None:
        dv.post("environmentvariablevalues", {
            "schemaname": SCHEMA + "_value", "value": token,
            "EnvironmentVariableDefinitionId@odata.bind": f"/environmentvariabledefinitions({def_id})"},
            done=lambda: _value(def_id)[0] is not None)
    else:
        try:
            dv.patch(f"environmentvariablevalues({vid})", {"value": token}, headers={"If-Match": etag})
        except dv.DvError as e:
            if e.code != 412:
                raise
    # Re-read: the token must be ours (covers a lost race and a retried write that had already landed).
    if _value(def_id)[1] != token:
        raise Busy(f"reconciliation lock was taken by another run: {_value(def_id)[1]}")
    return def_id, token


def release(def_id, token):
    vid, value, etag = _value(def_id)
    if vid and value == token:
        dv.patch(f"environmentvariablevalues({vid})", {"value": ""}, headers={"If-Match": etag})


@contextlib.contextmanager
def held(purpose):
    def_id, token = acquire(purpose)
    try:
        yield
    finally:
        release(def_id, token)


if __name__ == "__main__":
    d = _definition()
    vid, value, _ = _value(d)
    if "--release" in sys.argv and vid:
        dv.patch(f"environmentvariablevalues({vid})", {"value": ""})
        print("released")
    else:
        print("lock:", value or "(free)")
