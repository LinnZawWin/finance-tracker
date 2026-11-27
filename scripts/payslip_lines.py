"""Convert payslip PDFs into a lines folder for statement_import.py (no writes).

    python scripts/payslip_lines.py <out folder> <pdf> [<pdf> ...]

The employer is a Bank Account (Account Type Employer) that works as a clearing account: each payslip is one Bank
Statement, opening and closing balance 0, named after the file (`<Employer>_<yyyy-mm>`, for example
`DeltaInsights_2026-10`). Every line is dated the Payment Date. Lines, signed like a bank:
- one line per earnings item with an amount (`Salary & Wages - Ordinary Hours 136.0000 x $104.1667`), +,
  Bank Category "Gross income"
- `Tax - PAYG`, -, Bank Category "Income tax"
- `Superannuation - <fund line>` + (the employer's contribution earned, Bank Category "Employer super") and `Superannuation paid - <fund line>` -
  (paid to the fund; its Transfer Counterpart is the contribution line on the super account)
- `Net pay - <bank account> <reference>`, - (its Transfer Counterpart is the salary line on the bank account)
Check: earnings - tax - net pay = 0, and each section total equals the sum of its items. A file that fails stops.
Layout read: the Delta Insights payslip (pdfplumber text). Another employer's layout needs its own patterns.
"""
import json
import os
import re
import sys

import pdfplumber

ACCOUNT = {"DeltaInsights": "DeltaInsights"}  # file prefix -> statement_import.py account key
MONEY = r"-?\$[\d,]+\.\d{2}"


def money(s):
    return round(float(s.replace("$", "").replace(",", "")), 2)


def iso(d):
    dd, mm, yy = d.split("/")
    return f"{yy}-{mm}-{dd}"


def parse(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    m = re.search(r"Pay Period: (\d\d/\d\d/\d{4}) - (\d\d/\d\d/\d{4}) Payment Date: (\d\d/\d\d/\d{4}) "
                  rf"Total Earnings: ({MONEY}) Net Pay: ({MONEY})", text)
    if not m:
        raise SystemExit(f"{path}: pay period line not found")
    start, end, paid = iso(m.group(1)), iso(m.group(2)), iso(m.group(3))
    gross, net = money(m.group(4)), money(m.group(5))
    sections, cur = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        head = re.match(r"(SALARY & WAGES|TAX|SUPERANNUATION|LEAVE|PAYMENT DETAILS)\b", line)
        if head:
            cur = head.group(1)
            sections.setdefault(cur, {"items": [], "total": None})
            continue
        if cur is None:
            continue
        t = re.match(rf"TOTAL ({MONEY})", line)
        if t:
            sections[cur]["total"] = money(t.group(1))
            cur = None
            continue
        amounts = re.findall(MONEY, line)
        if cur == "SALARY & WAGES":
            q = re.match(rf"(.+?) ([\d.]+) (\$[\d,]+\.\d+) ({MONEY})", line)
            if q:  # hours, rate, this pay[, ytd]
                sections[cur]["items"].append((f"{q.group(1)} {q.group(2)} x {q.group(3)}", money(q.group(4))))
        elif cur in ("TAX", "SUPERANNUATION") and amounts:
            sections[cur]["items"].append((re.sub(rf"\s*{MONEY}.*$", "", line), money(amounts[0])))
        elif cur == "PAYMENT DETAILS" and amounts:
            sections[cur]["items"].append((re.sub(rf"\s*{MONEY}.*$", "", line), money(amounts[-1])))
    for k in ("SALARY & WAGES", "TAX", "SUPERANNUATION"):
        s = sections.get(k, {"items": [], "total": 0.0})
        if s["total"] is not None and round(sum(a for _, a in s["items"]), 2) != s["total"]:
            raise SystemExit(f"{path}: {k} items {s['items']} do not add up to {s['total']}")
    earn = [(d, a) for d, a in sections["SALARY & WAGES"]["items"] if a]
    tax = sections.get("TAX", {"items": []})["items"]
    sup = sections.get("SUPERANNUATION", {"items": []})["items"]
    pay = sections["PAYMENT DETAILS"]["items"]
    if round(sum(a for _, a in earn), 2) != gross or round(sum(a for _, a in pay), 2) != net:
        raise SystemExit(f"{path}: earnings {earn} or payments {pay} do not match {gross} / {net}")
    if round(gross - sum(a for _, a in tax) - net, 2) != 0:
        raise SystemExit(f"{path}: gross {gross} - tax {tax} != net {net}")
    lines = [{"description": f"Salary & Wages - {d}", "amount": a, "bank_category": "Gross income"} for d, a in earn]
    lines += [{"description": f"Tax - {d}", "amount": -a, "bank_category": "Income tax"} for d, a in tax if a]
    for d, a in sup:
        if a:
            lines += [{"description": f"Superannuation - {d}", "amount": a, "bank_category": "Employer super"},
                      {"description": f"Superannuation paid - {d}", "amount": -a}]
    lines += [{"description": f"Net pay - {d}", "amount": -a} for d, a in pay if a]
    for n, l in enumerate(lines, 1):
        l.update(date=paid, line_number=n, notes=f"Pay period {start} to {end}")
    return start, end, lines


out, files = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
sp = os.path.join(out, "_statements.json")
stmts = json.load(open(sp)) if os.path.exists(sp) else []
for p in files:
    name = os.path.splitext(os.path.basename(p))[0]
    acct = ACCOUNT[name.split("_")[0]]
    start, end, lines = parse(p)
    stmts = [s for s in stmts if s["file"] != name]
    stmts.append({"file": name, "account": acct, "kind": "PDF", "start": start, "end": end,
                  "opening": 0.0, "closing": 0.0})
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=1)
    print(f"{name}: {len(lines)} lines, paid {lines[0]['date']}, balance {round(sum(l['amount'] for l in lines), 2)}")
    for l in lines:
        print(f"    {l['amount']:10.2f}  {l['description']}")
with open(sp, "w", encoding="utf-8") as f:
    json.dump(stmts, f, indent=1)
