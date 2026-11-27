"""Convert AustralianSuper "MemberTransactions" CSV exports into a lines folder for statement_import.py (no writes).

    python scripts/super_lines.py <out folder> <csv> [<csv> ...] [--opening 0.00]

Each CSV is one Bank Statement on the Bank Account "AustralianSuper" (account key "Super"):
- `AustralianSuper.MemberTransactions.<yyyy-mm-dd>__<yyyy-mm-dd>.<member>.csv`: a financial year, final.
  Named "AustralianSuper <period end>".
- `AustralianSuper.MemberTransactions.Current-statement.<member>.csv`: the current financial year so far, an
  interim placeholder from 1 Jul to the last date in the file. Named "AustralianSuper <start> to <end>"; the next
  export (or the year's final CSV) updates it and adds only the missing lines.
Files are chained oldest first: opening = the previous closing (the first one takes --opening, default 0),
closing = opening + the sum of its lines. The CSV has no balances, so check each closing balance against the
annual statement or the app before importing.
Line: date = Date, amount = Total Amount (signed like a bank: negative = out of the super account),
description = "<Title> - <Description>" (Title alone when Description is empty), notes = the payment period of a
contribution, line number = the order in the file.
"""
import csv
import datetime as dt
import json
import os
import re
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opening = float(sys.argv[sys.argv.index("--opening") + 1]) if "--opening" in sys.argv else 0.0
if "--opening" in sys.argv:
    args.remove(sys.argv[sys.argv.index("--opening") + 1])
out, files = args[0], args[1:]
os.makedirs(out, exist_ok=True)


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    lines = []
    for n, r in enumerate(rows, 1):
        if not r.get("Date"):
            continue
        desc = r["Title"].strip() + (f" - {r['Description'].strip()}" if r.get("Description", "").strip() else "")
        line = {"date": r["Date"], "amount": round(float(r["Total Amount"] or 0), 2), "description": desc,
                "line_number": n, "bank_category": r["Category"].strip()}
        if r.get("Payment period", "").strip():
            line["notes"] = f"Payment period {r['Payment period'].strip()}"
        lines.append(line)
    return lines


def period(path, lines):
    m = re.search(r"(\d{4}-\d{2}-\d{2})__(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    if m:
        return m.group(1), m.group(2), False
    last = max(l["date"] for l in lines)
    d = dt.date.fromisoformat(last)
    fy = d.year if d.month >= 7 else d.year - 1
    return f"{fy}-07-01", last, True


parsed = []
for p in files:
    lines = read(p)
    start, end, interim = period(p, lines)
    parsed.append((start, end, interim, p, lines))
parsed.sort()
sp = os.path.join(out, "_statements.json")
stmts = [s for s in (json.load(open(sp)) if os.path.exists(sp) else []) if s["account"] != "Super"]
bal = opening
for start, end, interim, p, lines in parsed:
    total = round(sum(l["amount"] for l in lines), 2)
    name = f"AustralianSuper {start} to {end}" if interim else f"AustralianSuper {end}"
    s = {"file": name, "account": "Super", "kind": "CSV", "start": start, "end": end,
         "opening": round(bal, 2), "closing": round(bal + total, 2)}
    if interim:
        s["interim"] = True
    bal = s["closing"]
    stmts.append(s)
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=1)
    cats = {}
    for l in lines:
        cats[l["bank_category"]] = round(cats.get(l["bank_category"], 0) + l["amount"], 2)
    print(f"{name:44} lines={len(lines):3} opening={s['opening']:10.2f} closing={s['closing']:10.2f}"
          f"{' interim' if interim else ''}\n    {cats}")
with open(sp, "w", encoding="utf-8") as f:
    json.dump(stmts, f, indent=1)
