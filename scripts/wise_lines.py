"""python scripts/wise_lines.py "<Wise csv>" <out lines json>

Convert the Wise CSV export into statement lines (AUD), following the owner's rules:
- skip REFUNDED rows and currency conversions (NEUTRAL)
- AUD-funded rows: Amount = AUD incl. fee, Original = target amount/currency
- foreign-balance rows: AUD = foreign / rate of the last AUD->currency conversion before the row
  (effective rate incl. fee); fallback: nearest AUD-funded card payment in that currency
- split payments (same ID, two balances) become one line
"""
import csv, json, sys, collections
from datetime import date

SRC, OUT = sys.argv[1], sys.argv[2]
R = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
R.sort(key=lambda r: r["Created on"])
f = lambda x: float(x) if x not in ("", None) else 0.0

# rates: foreign units per 1 AUD, effective (fee included)
conv = collections.defaultdict(list)   # ccy -> [(datetime, rate, desc)]
card = collections.defaultdict(list)
for r in R:
    if r["Status"] != "COMPLETED" or r["Source currency"] != "AUD" or r["Target currency"] == "AUD":
        continue
    aud = f(r["Source amount (after fees)"]) + f(r["Source fee amount"])
    rate = f(r["Target amount (after fees)"]) / aud if aud else None
    if not rate:
        continue
    tgt = conv if r["Direction"] in ("NEUTRAL", "IN") else card
    tgt[r["Target currency"]].append((r["Created on"], rate, f"{r['Created on'][:10]} {r['ID']}"))


def rate_for(ccy, when):
    before = [c for c in conv[ccy] if c[0] <= when]
    if before:
        return before[-1][1], f"last AUD->{ccy} conversion on {before[-1][2][:10]}"
    if conv[ccy]:
        c = conv[ccy][0]
        return c[1], f"first AUD->{ccy} conversion on {c[2][:10]} (none before this row)"
    if card[ccy]:
        c = min(card[ccy], key=lambda c: abs(date.fromisoformat(c[0][:10]) - date.fromisoformat(when[:10])))
        return c[1], f"no AUD->{ccy} conversion in file; rate of AUD-funded card payment on {c[2][:10]}"
    for r in R:  # cross rate: a ccy->X conversion chained with X's AUD rate
        if r["Direction"] == "NEUTRAL" and r["Source currency"] == ccy and r["Target currency"] != ccy:
            x = r["Target currency"]
            xr, xwhy = rate_for(x, r["Created on"])
            if xr:
                per_x = (f(r["Source amount (after fees)"]) + f(r["Source fee amount"])) / f(r["Target amount (after fees)"])
                return xr * per_x, (f"no AUD->{ccy} rate in file; cross rate from {ccy}->{x} conversion on "
                                    f"{r['Created on'][:10]} and {xwhy}")
    return None, f"no AUD->{ccy} rate in file"


groups = collections.OrderedDict()
skipped = collections.Counter()
for r in R:
    if r["Status"] == "REFUNDED":
        skipped["refunded"] += 1
        continue
    if r["Direction"] == "NEUTRAL":
        skipped["conversion"] += 1
        continue
    groups.setdefault(r["ID"], []).append(r)

lines, problems = [], []
for rid, rows in groups.items():
    first = rows[0]
    sign = 1 if first["Direction"] == "IN" else -1
    aud = fee = 0.0
    tgt_ccy = first["Target currency"]
    tgt_amt = 0.0
    notes, est, rates = [], False, []
    for r in rows:
        src_ccy, src = r["Source currency"], f(r["Source amount (after fees)"])
        sfee = f(r["Source fee amount"])
        tgt_amt += f(r["Target amount (after fees)"]) if r["Target currency"] == tgt_ccy else 0
        if r["Target currency"] != tgt_ccy:
            problems.append(f"{rid}: mixed target currencies")
        if src_ccy == "AUD":
            aud += src + sfee
            fee += sfee
            if tgt_ccy != "AUD":
                rates.append(f(r["Exchange rate"]))
        else:
            rate, why = rate_for(src_ccy, r["Created on"])
            if rate is None:
                problems.append(f"{rid}: {why}")
                continue
            a = round((src + sfee) / rate, 2)
            aud += a
            est = True
            fee += round(sfee / rate, 2)
            rates.append(round(rate, 6))
            notes.append(f"Paid from {src_ccy} balance: {src + sfee:.2f} {src_ccy}. AUD estimated at "
                         f"{rate:.6f} {src_ccy}/AUD ({why}).")
    if len(rows) > 1:
        notes.append(f"Split payment from {len(rows)} balances: " +
                     ", ".join(f"{f(r['Source amount (after fees)']):.2f} {r['Source currency']}" for r in rows) + ".")
    line = {"date": first["Created on"][:10], "amount": round(sign * aud, 2),
            "description": f"{first['Target name'] if sign < 0 else 'Money added from ' + first['Source name']}",
            "merchant": first["Target name"] if sign < 0 else first["Source name"],
            "bank_reference": rid, "bank_category": first["Category"], "fee": round(fee, 2) or None,
            "posted_date": first["Finished on"][:10]}
    if tgt_ccy != "AUD":
        line["original_amount"] = round(sign * tgt_amt, 2)
        line["original_currency"] = tgt_ccy
        line["exchange_rate"] = round(aud and tgt_amt / aud, 6)
    if first["Note"]:
        notes.append("Wise note: " + first["Note"])
    line["notes"] = " ".join(notes) or None
    line["estimated"] = est
    lines.append(line)

json.dump(lines, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"rows {len(R)}, skipped {dict(skipped)}, lines {len(lines)} ({sum(l['estimated'] for l in lines)} estimated), "
      f"split merged {sum(1 for v in groups.values() if len(v) > 1)}")
print("range", lines[0]["date"], "..", lines[-1]["date"], " net AUD", round(sum(l["amount"] for l in lines), 2))
print("money in", round(sum(l["amount"] for l in lines if l["amount"] > 0), 2),
      " out", round(sum(l["amount"] for l in lines if l["amount"] < 0), 2))
for l in lines:
    if l["estimated"]:
        print("  EST", l["date"], f"{l['amount']:>9.2f}", l["description"][:28], "|", l["notes"][:150])
print("PROBLEMS:", problems or "none")
