"""Short console output for the reconciliation scripts: the detail goes to a report file.

detail(line): written to the report file; also printed with --verbose.
need(line):   something for the owner to decide; printed (the first MAX of each kind) and written to the file.
At exit the file's path is printed once, when anything was written to it.
The file is outside the repo: $FT_REPORT_DIR, or the system temp folder, under finance-tracker/.
"""
import atexit
import datetime as dt
import os
import sys
import tempfile
from collections import Counter

VERBOSE = "--verbose" in sys.argv
MAX = 15
_f, _shown = None, Counter()


def _file():
    global _f
    if _f is None:
        d = os.environ.get("FT_REPORT_DIR") or os.path.join(tempfile.gettempdir(), "finance-tracker")
        os.makedirs(d, exist_ok=True)
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        _f = open(os.path.join(d, f"{name}-{dt.datetime.now():%Y%m%d-%H%M%S}.txt"), "w", encoding="utf-8")
        atexit.register(lambda: (_f.close(), print(f"Details: {_f.name}")))
    return _f


def detail(line):
    _file().write(line + "\n")
    if VERBOSE:
        print(line)


def need(line, kind="item"):
    _file().write(line + "\n")
    _shown[kind] += 1
    if VERBOSE or _shown[kind] <= MAX:
        print(line)
    elif _shown[kind] == MAX + 1:
        print(f"   ... more {kind} lines in the details file")
