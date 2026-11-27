"""Convert payslip PDFs into a lines folder for statement_import.py (no writes).

    python scripts/payslip_lines.py <out folder> <pdf> [<pdf> ...]

The employer is a Bank Account (Account Type Employer) that works as a clearing account: each payslip is one Bank
Statement, opening and closing balance 0, named after the file (`<Employer>_<yyyy-mm>`, for example
`DeltaInsights_2026-10`). Every line is dated the Payment Date. Lines, signed like a bank:
- one line per earnings item with an amount (`Salary & Wages - Ordinary Hours 136.0000 x $104.1667`), +
- `Tax - PAYG`, -
- `Superannuation - <fund line>` + (the employer's contribution earned) and `Superannuation paid - <fund line>` -
  (paid to the fund; its Transfer Counterpart is the contribution line on the super account)
- `Net pay - <bank account> <reference>`, - (its Transfer Counterpart is the salary line on the bank account)
Check: earnings - tax - net pay = 0, and each section total equals the sum of its items. A file that fails stops.
Layouts read (pdfplumber text), chosen by the file prefix:
- `DeltaInsights_<yyyy-mm>`: the Delta Insights payslip, as above.
- `Paxus_<payment date yyyy-mm-dd>`: the weekly Paxus pay advice (contractor placed with a client). Lines:
  `Salary & Wages - <client> <item> <qty> x <rate>` +, `Tax - PAYG` -, `Superannuation - <fund>` +,
  `Net pay - bank` -. Paxus pays super monthly (one AustralianSuper contribution for the payslips paid in a
  calendar month), so the payslips have no `Superannuation paid` line. Instead one statement per month,
  `Paxus_Super_<yyyy-mm>` (kind Sheet, dated the contribution), holds `Superannuation paid - <fund> <yyyy-mm>` -;
  the script reads the AustralianSuper contribution line from Dataverse (read only) and stops unless the month's
  payslip super adds up to it. Balances are chained in date order, so the account balance is the super earned and
  not yet paid. Checks: items add up to gross, gross - tax - deductions = net = the paid amount, no allowances.
"""
import datetime as dt
import json
import os
import re
import sys

import pdfplumber

ACCOUNT = {"DeltaInsights": "DeltaInsights", "Paxus": "Paxus"}  # file prefix -> statement_import.py account key
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
    lines = [{"description": f"Salary & Wages - {d}", "amount": a} for d, a in earn]
    lines += [{"description": f"Tax - {d}", "amount": -a} for d, a in tax if a]
    for d, a in sup:
        if a:
            lines += [{"description": f"Superannuation - {d}", "amount": a},
                      {"description": f"Superannuation paid - {d}", "amount": -a}]
    lines += [{"description": f"Net pay - {d}", "amount": -a} for d, a in pay if a]
    for n, l in enumerate(lines, 1):
        l.update(date=paid, line_number=n, notes=f"Pay period {start} to {end}")
    return start, end, lines


def num(s):
    return round(float(s.replace("$", "").replace(",", "")), 2)


def dmy(d):
    return dt.datetime.strptime(d, "%d/%m/%Y").date()


def parse_paxus(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    rows = text.splitlines()
    paid = dmy(re.search(r"Payment Date: (\d{1,2}/\d\d/\d{4})", text).group(1))
    items = []
    for r in rows:
        m = re.match(r"(.+?) (\d{1,2}/\d\d/\d{4}) ([\d.]+) ([\d.,]+) ([\d,]+\.\d\d)$", r)
        if m:
            items.append((m.group(1), dmy(m.group(2)), float(m.group(3)), m.group(4), num(m.group(5))))
    cur = re.search(r"^Current ([\d,.]+) ([\d,.]+) ([\d,.]+) ([\d,.]+) ([\d,.]+) \$([\d,.]+)$", text, re.M)
    if not items or not cur:
        raise SystemExit(f"{path}: items or the Current totals line not found")
    gross, sup, allow, tax, ded, net = (num(x) for x in cur.groups())
    fund = re.search(r"^(.+?) ([\d,]+\.\d\d) ([\d,]+\.\d\d)$", rows[rows.index("Name Period TD YTD") + 1])
    acct = re.search(r"([\d,]+\.\d\d)$", rows[rows.index("Account Name Amount") + 1])
    if round(sum(i[4] for i in items), 2) != gross or allow or ded or round(gross - tax - ded, 2) != net \
            or not acct or num(acct.group(1)) != net or not fund or num(fund.group(2)) < sup:
        raise SystemExit(f"{path}: totals do not add up (items {items}, current {cur.groups()})")
    end = max(i[1] for i in items)
    start = end - dt.timedelta(days=6)
    lines = [{"description": f"Salary & Wages - {c} {q:.2f} x {r}", "amount": a} for c, _, q, r, a in items]
    lines += [{"description": "Tax - PAYG", "amount": -tax}] if tax else []
    lines += [{"description": f"Superannuation - {fund.group(1)}", "amount": sup}] if sup else []
    lines.append({"description": "Net pay - bank", "amount": -net})
    for n, l in enumerate(lines, 1):
        l.update(date=paid.isoformat(), line_number=n, notes=f"Pay period {start} to {end}")
    return start.isoformat(), end.isoformat(), lines, fund.group(1), num(fund.group(2))


def paxus_ptd(slips):
    """Super per payslip = the rise in the fund's Period TD (month to date) since the month's previous payslip, so
    the month adds up to the contribution; the printed Super column is rounded and can differ by a cent."""
    last = {}
    for i, (name, lines, fund, ptd, start, end) in enumerate(slips):
        month = lines[0]["date"][:7]
        amt = round(ptd - last.get(month, 0.0), 2)
        last[month] = ptd
        sl = next(l for l in lines if l["description"].startswith("Superannuation - "))
        if amt != sl["amount"]:
            sl["notes"] += f"; super {amt:.2f} from the month-to-date {ptd:.2f} (printed {sl['amount']:.2f})"
            sl["amount"] = amt
        slips[i] = (name, lines, fund, amt, start, end)


def paxus_super(slips):
    """One Paxus_Super_<yyyy-mm> statement per payment month, dated the AustralianSuper contribution."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dv
    super_id = dv.get("lzw_bankaccounts?$select=lzw_bankaccountid&$filter=lzw_name eq 'AustralianSuper'")["value"][0]["lzw_bankaccountid"]
    conts = dv.get_all("lzw_bankstatementlines?$select=lzw_amount,lzw_transactiondate,lzw_notes&$filter="
                       f"_lzw_bankaccount_value eq {super_id} and statecode eq 0 and "
                       "startswith(lzw_name,'Contribution - Employer - PAXUS')")
    out = []
    for month in sorted({s[1][0]["date"][:7] for s in slips}):
        part = [s for s in slips if s[1][0]["date"][:7] == month]
        total = round(sum(s[3] for s in part), 2)
        c = [x for x in conts if (x.get("lzw_notes") or "").startswith(f"Payment period {month}-01/")]
        if len(c) != 1 or round(c[0]["lzw_amount"], 2) != total:
            raise SystemExit(f"Paxus super {month}: payslips {total} vs contribution {[x['lzw_amount'] for x in c]}")
        day = c[0]["lzw_transactiondate"][:10]
        out.append((f"Paxus_Super_{month}", day, [{
            "description": f"Superannuation paid - {part[0][2]} {month}", "amount": -total, "date": day,
            "line_number": 1, "notes": f"Super for the {len(part)} payslips paid in {month}: "
                                       + ", ".join(s[0] for s in part)}]))
    return out


out, files = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
sp = os.path.join(out, "_statements.json")
stmts = json.load(open(sp)) if os.path.exists(sp) else []
paxus = []
for p in files:
    name = os.path.splitext(os.path.basename(p))[0]
    acct = ACCOUNT[name.split("_")[0]]
    if acct == "Paxus":
        start, end, lines, fund, ptd = parse_paxus(p)
        paxus.append((name, lines, fund, ptd, start, end))
        continue
    start, end, lines = parse(p)
    stmts = [s for s in stmts if s["file"] != name]
    stmts.append({"file": name, "account": acct, "kind": "PDF", "start": start, "end": end,
                  "opening": 0.0, "closing": 0.0})
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=1)
    print(f"{name}: {len(lines)} lines, paid {lines[0]['date']}, balance {round(sum(l['amount'] for l in lines), 2)}")
    for l in lines:
        print(f"    {l['amount']:10.2f}  {l['description']}")
if paxus:
    paxus.sort(key=lambda s: s[1][0]["date"])
    paxus_ptd(paxus)
    events = [(s[1][0]["date"], s[0], s[4], s[5], s[1], "PDF") for s in paxus]
    events += [(day, name, day, day, lines, "Sheet") for name, day, lines in paxus_super(paxus)]
    bal = 0.0
    for day, name, start, end, lines, kind in sorted(events, key=lambda e: (e[0], e[5])):
        opening, bal = bal, round(bal + sum(l["amount"] for l in lines), 2)
        notes = ("Paxus pay advice (payslip_lines.py). The employer account is a clearing account: earnings and "
                 "employer super in, tax and net pay out; super is paid monthly (Paxus_Super_<yyyy-mm>), so the "
                 "balance is the super earned and not yet paid.") if kind == "PDF" else (
                 "Paxus super paid to AustralianSuper for the month's payslips (payslip_lines.py).")
        stmts = [s for s in stmts if s["file"] != name]
        stmts.append({"file": name, "account": "Paxus", "kind": kind, "start": start, "end": end,
                      "opening": opening, "closing": bal, "notes": notes})
        with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(lines, f, indent=1)
        print(f"{name}: {len(lines)} lines, dated {day}, balance {opening:.2f} -> {bal:.2f}")
        for l in lines:
            print(f"    {l['amount']:10.2f}  {l['description']}")
with open(sp, "w", encoding="utf-8") as f:
    json.dump(stmts, f, indent=1)
