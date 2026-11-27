"""Convert the contract invoices (the "Salary" sheet of the owner's Fiscal Planner) into a lines folder for
statement_import.py (no writes). See "Contract invoices" in docs/statement-import.md.

    python scripts/contract_lines.py <out folder> <sheet csv> <payments json>

<sheet csv>: the sheet downloaded as CSV (header row kept). Columns read by name: Year, Month, Working Days,
Net Amount, GST, Total GST, Total Amount, Est. Tax, Paid On. Rows without a numeric Year and Month and a Paid On
date (totals, blanks, the rate table) are skipped.
<payments json> (written by hand, kept outside the repo):
    {"gst": {"<yyyy-mm of the quarter's last month>": "<paid yyyy-mm-dd>", ...},
     "tax": [{"fy": "FY2026", "from": "2025-07", "to": "2026-05", "paid": "2026-11-24", "amount": 82434.30}, ...]}

The employer account (Delta Insights) is a clearing account. One Bank Statement per invoice month,
`DeltaInsights_Invoice_<yyyy-mm>`, every line dated Paid On:
- `Invoice - <yyyy-mm> - <days> days, <net> + GST <gst>` + Total Amount (income incl GST), Bank Category "Gross income"
- `GST - <yyyy-mm>` - GST, Bank Category "GST" (also on the rounding lines)
- `Income Tax - <yyyy-mm>` - the month's share of the year's tax: the paid amount split by Net Amount (cents on
  the last month) when the year is in "tax", else the sheet's Est. Tax (owed, not paid yet); Bank Category "Income tax"
- `Paid to bank - <yyyy-mm>` - Total Amount (its Transfer Counterpart is the bank's salary line)
One Bank Statement per ATO payment, `DeltaInsights_ATO_<yyyy-mm-dd>`:
- `GST paid - <first>..<last month>` + the sheet's Total GST (whole dollars, as on the BAS) and, when the months'
  GST has cents, `GST rounding - <...>` + the cents; `Income tax paid - <fy>` + the amount.
So the account's balance is the GST and tax still owed. Checks: Total = Net + GST, each quarter's GST within a
dollar of its Total GST, every tax year's months present. A failed check stops.
"""
import calendar
import csv
import datetime as dt
import json
import os
import sys

NAME = "DeltaInsights"


def num(s):
    s = (s or "").replace(",", "").strip()
    return round(float(s), 2) if s else None


def read_sheet(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    head = rows[0]
    col = {k: head.index(k) for k in ("Year", "Month", "Working Days", "Net Amount", "GST", "Total GST",
                                      "Total Amount", "Est. Tax", "Paid On")}
    out = []
    for r in rows[1:]:
        g = lambda k: r[col[k]].strip() if col[k] < len(r) else ""
        if not (g("Year").isdigit() and g("Month").isdigit() and g("Paid On")):
            continue
        m = f"{int(g('Year')):04d}-{int(g('Month')):02d}"
        paid = dt.datetime.strptime(g("Paid On"), "%d-%b-%Y").date().isoformat()
        row = dict(month=m, days=g("Working Days"), net=num(g("Net Amount")), gst=num(g("GST")),
                   qgst=num(g("Total GST")), total=num(g("Total Amount")), est=num(g("Est. Tax")), paid=paid)
        if round(row["net"] + row["gst"], 2) != row["total"]:
            raise SystemExit(f"{m}: Net {row['net']} + GST {row['gst']} != Total {row['total']}")
        out.append(row)
    return out


def main():
    out, sheet, pay = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = read_sheet(sheet)
    pay = json.load(open(pay, encoding="utf-8"))
    tax = {}
    for t in pay["tax"]:
        months = [r for r in rows if t["from"] <= r["month"] <= t["to"]]
        base = round(sum(r["net"] for r in months), 2)
        left = round(t["amount"], 2)
        for i, r in enumerate(months):
            share = left if i == len(months) - 1 else round(t["amount"] * r["net"] / base, 2)
            left = round(left - share, 2)
            tax[r["month"]] = (share, t["fy"])
        print(f"{t['fy']}: {len(months)} months, Net {base:,.2f}, tax {t['amount']:,.2f} "
              f"({t['amount'] / base:.4%} of Net), paid {t['paid']}")
    stmts, files = [], {}
    note = ("Contract invoice (contract_lines.py, from the Fiscal Planner sheet). The employer account is a clearing "
            "account: the invoice incl GST in, the payment to the bank, the month's GST and income tax out; the ATO "
            "payments come back in, so the balance is what is still owed.")
    for r in rows:
        m = r["month"]
        y, mo = map(int, m.split("-"))
        t, fy = tax.get(m, (r["est"], None))
        tax_note = (f"{fy} income tax, paid amount split by Net Amount" if fy else
                    "Est. Tax from the sheet: owed, not paid yet. The Salary FT's net uses this estimate; replace it "
                    "with the year's assessment (split by Net Amount) when it arrives")
        lines = [
            dict(description=f"Invoice - {m} - {r['days']} days, {r['net']:,.2f} + GST {r['gst']:,.2f}", amount=r["total"],
                 bank_category="Gross income"),
            dict(description=f"GST - {m}", amount=-r["gst"], bank_category="GST"),
            dict(description=f"Income Tax - {m}", amount=-t, notes=tax_note, bank_category="Income tax"),
            dict(description=f"Paid to bank - {m}", amount=-r["total"]),
        ]
        name = f"{NAME}_Invoice_{m}"
        for n, l in enumerate(lines, 1):
            l.update(date=r["paid"], line_number=n)
            l.setdefault("notes", f"Invoice for {m}, paid {r['paid']}")
        files[name] = lines
        stmts.append(dict(file=name, account=NAME, kind="Sheet", start=f"{m}-01",
                          end=f"{m}-{calendar.monthrange(y, mo)[1]:02d}", opening=None, closing=None, notes=note))
    # ATO payments
    ato = {}
    first = rows[0]["month"]
    for r in rows:
        if r["qgst"] is None:
            continue
        months = [x for x in rows if first <= x["month"] <= r["month"]]
        first = next((x["month"] for x in rows if x["month"] > r["month"]), "9999-99")
        gst = round(sum(x["gst"] for x in months), 2)
        if abs(gst - r["qgst"]) >= 1:
            raise SystemExit(f"GST {months[0]['month']}..{r['month']}: months {gst} vs Total GST {r['qgst']}")
        paid = pay["gst"].get(r["month"])
        if not paid:
            print(f"GST {months[0]['month']}..{r['month']} {r['qgst']:,.2f}: no payment date, left owed")
            continue
        per = f"{months[0]['month']}..{r['month']}"
        ls = ato.setdefault(paid, [])
        ls.append(dict(description=f"GST paid - {per}", amount=r["qgst"], notes=f"GST for {per}, paid {paid}"))
        if round(gst - r["qgst"], 2):
            ls.append(dict(description=f"GST rounding - {per}", amount=round(gst - r["qgst"], 2),
                           notes="The BAS is in whole dollars", bank_category="GST"))
    for t in pay["tax"]:
        ato.setdefault(t["paid"], []).append(dict(description=f"Income tax paid - {t['fy']}", amount=t["amount"],
                                                  notes=f"{t['fy']} income tax, paid {t['paid']}"))
    for paid, ls in sorted(ato.items()):
        name = f"{NAME}_ATO_{paid}"
        for n, l in enumerate(ls, 1):
            l.update(date=paid, line_number=n)
        files[name] = ls
        stmts.append(dict(file=name, account=NAME, kind="Sheet", start=paid, end=paid, opening=None, closing=None,
                          notes="ATO payment (contract_lines.py): the GST or income tax paid from the bank comes back "
                                "into the clearing account."))
    os.makedirs(out, exist_ok=True)
    for name, ls in files.items():
        with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(ls, f, indent=1)
    with open(os.path.join(out, "_statements.json"), "w", encoding="utf-8") as f:
        json.dump(stmts, f, indent=1)
    bal = 0.0
    for s in stmts:
        ls = files[s["file"]]
        bal = round(bal + sum(l["amount"] for l in ls), 2)
        print(f"{s['file']:32} {len(ls)} lines  " + "  ".join(f"{l['amount']:>10,.2f}" for l in ls))
    print(f"{len(stmts)} statements; balance after all = {bal:,.2f} (negative = still owed to the ATO)")


if __name__ == "__main__":
    main()
