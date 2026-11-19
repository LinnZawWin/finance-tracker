"""Compare parsed statement lines with the Bank Statement Lines already in Dataverse.

Always run this before creating Bank Statement Lines. It prints a summary (new, existing,
updates, possible duplicates) and writes nothing unless --apply is given.

    python scripts/statement_compare.py --account "ANZ Plus Everyday" --source PDF --file lines.json
    python scripts/statement_compare.py ... --statement <bank statement GUID> --apply

lines.json (keep it outside the repo): a list of objects
    {"date": "2026-01-31", "amount": -12.50, "description": "...", "balance": 100.00,
     "merchant": "...", "pending": false, "original_amount": -60.0}
Amounts are signed like the bank (negative = money out). "balance" and the last three are optional.

Rules
- Lines are compared by count per (date, amount, description): two identical purchases on one
  day are real, so only the shortfall is created.
- Running Balance separates identical lines when both sides have it.
- A PDF statement is final: an existing non-PDF row with the same date and amount is updated
  (description, balance, source) instead of creating a new line; only leftovers are created.
- A leftover that shares date + amount (different description) or date + description (different
  amount) with an unused existing row is flagged as a possible duplicate and is not written
  unless --include-possible is given.
"""
import argparse
import json
import re

import dv
import spec

O = spec.OPT
SOURCES = ["Screenshot", "CSV", "PDF"]


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip().upper())


def cents(x):
    return None if x is None else int(round(float(x) * 100))


def duplicate_key(line):
    bal = "" if line.get("balance") is None else f"{float(line['balance']):.2f}"
    ref = line.get("bank_reference") or ""
    return f"{line['date']}|{float(line['amount']):.2f}|{norm(line['description'])}|{bal}|{ref}"[:600]


# Optional line fields -> Bank Statement Line columns
OPTIONAL = {"posted_date": ("lzw_posteddate", None), "bank_reference": ("lzw_bankreference", 100),
            "card_holder": ("lzw_cardholder", 100), "fee": ("lzw_feeamount", None),
            "bank_category": ("lzw_bankcategory", 100), "line_number": ("lzw_linenumber", None),
            "notes": ("lzw_notes", None)}
STATUS = ["Unmatched", "Partly Matched", "Matched", "Transfer", "Ignored"]
_currency = {}


def currency_id(iso):
    if iso not in _currency:
        cur = dv.get(f"transactioncurrencies?$select=transactioncurrencyid&$filter=isocurrencycode eq '{iso}'")["value"]
        if not cur:
            raise SystemExit(f"Currency not in Dataverse: {iso}")
        _currency[iso] = cur[0]["transactioncurrencyid"]
    return _currency[iso]


def load_existing(account_id, start, end):
    rows = dv.get_all(
        "lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_transactiondate,lzw_amount,"
        "lzw_runningbalance,lzw_source,lzw_ispending,lzw_bankreference"
        f"&$filter=_lzw_bankaccount_value eq {account_id} and statecode eq 0 and "
        f"lzw_transactiondate ge {start} and lzw_transactiondate le {end}")
    return [{"id": r["lzw_bankstatementlineid"], "date": r["lzw_transactiondate"][:10], "amount": r["lzw_amount"],
             "description": r["lzw_name"], "balance": r.get("lzw_runningbalance"), "source": r.get("lzw_source"),
             "ref": r.get("lzw_bankreference"), "used": False} for r in rows]


def compare(incoming, existing, is_pdf):
    """Returns dict of lists: existing, update [(line, row)], new, possible [(line, row)]."""
    out = {"existing": [], "update": [], "new": [], "possible": []}

    def take(pred):
        for row in existing:
            if not row["used"] and pred(row):
                row["used"] = True
                return row
        return None

    def same_balance(line, row):
        a, b = cents(line.get("balance")), cents(row["balance"])
        r1, r2 = line.get("bank_reference"), row.get("ref")
        return (a is None or b is None or a == b) and (not r1 or not r2 or r1 == r2)

    rest = []
    for line in incoming:  # 1. exact matches, counted one for one
        row = take(lambda r: r["date"] == line["date"] and cents(r["amount"]) == cents(line["amount"])
                   and norm(r["description"]) == norm(line["description"]) and same_balance(line, r))
        (out["existing"] if row else rest).append(line)
    if is_pdf:  # 2. a PDF finalises earlier screenshot / CSV rows
        left = []
        for line in rest:
            match = lambda r, strict: (r["date"] == line["date"] and cents(r["amount"]) == cents(line["amount"])
                                       and r["source"] != O + SOURCES.index("PDF")
                                       and (not strict or cents(r["balance"]) == cents(line.get("balance"))))
            row = take(lambda r: match(r, True)) or take(lambda r: match(r, False) and same_balance(line, r))
            if row:
                out["update"].append((line, row))
            else:
                left.append(line)
        rest = left
    for line in rest:  # 3. leftovers: new, or flagged
        row = next((r for r in existing if not r["used"] and r["date"] == line["date"] and (
            cents(r["amount"]) == cents(line["amount"]) or norm(r["description"]) == norm(line["description"]))), None)
        if row:
            out["possible"].append((line, row))
        else:
            out["new"].append(line)
    return out


def line_body(line, account_id, statement_id, source, aud):
    body = {
        "lzw_name": line["description"][:500], "lzw_transactiondate": line["date"], "lzw_amount": line["amount"],
        "lzw_source": O + SOURCES.index(source), "lzw_ispending": bool(line.get("pending")),
        "lzw_duplicatekey": duplicate_key(line),
        "lzw_BankAccount@odata.bind": f"/lzw_bankaccounts({account_id})",
        "lzw_BankStatement@odata.bind": f"/lzw_bankstatements({statement_id})",
    }
    if line.get("balance") is not None:
        body["lzw_runningbalance"] = line["balance"]
    if line.get("merchant"):
        body["lzw_merchant"] = line["merchant"][:200]
    if line.get("original_amount") is not None:
        body["lzw_originalamount"] = line["original_amount"]
    if line.get("original_currency"):
        body["lzw_OriginalCurrency@odata.bind"] = f"/transactioncurrencies({currency_id(line['original_currency'])})"
    for key, (col, length) in OPTIONAL.items():
        val = line.get(key)
        if val is not None and val != "":
            body[col] = val[:length] if length else val
    if line.get("status"):
        body["lzw_status"] = O + STATUS.index(line["status"])
    if aud:
        body["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({aud})"
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--account", required=True, help="Bank Account name")
    ap.add_argument("--source", required=True, choices=SOURCES)
    ap.add_argument("--file", required=True, help="JSON file with the parsed lines")
    ap.add_argument("--statement", help="Bank Statement GUID (required with --apply)")
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--include-possible", action="store_true", help="also create possible duplicates")
    a = ap.parse_args()

    incoming = json.load(open(a.file))
    if not incoming:
        print("no lines in file")
        return
    name = a.account.replace("'", "''")
    acc = dv.get(f"lzw_bankaccounts?$select=lzw_bankaccountid&$filter=lzw_name eq '{name}'")["value"]
    if not acc:
        raise SystemExit(f"Bank Account not found: {a.account}")
    account_id = acc[0]["lzw_bankaccountid"]
    dates = sorted(line["date"] for line in incoming)
    existing = load_existing(account_id, dates[0], dates[-1])
    res = compare(incoming, existing, a.source == "PDF")

    print(f"Account: {a.account}   Period: {dates[0]} to {dates[-1]}   Incoming: {len(incoming)}   "
          f"In Dataverse: {len(existing)}")
    print(f"  existing (no change): {len(res['existing'])}")
    print(f"  to update from PDF:   {len(res['update'])}")
    print(f"  new:                  {len(res['new'])}")
    print(f"  possible duplicates:  {len(res['possible'])}")
    for line, row in res["update"]:
        print(f"    UPDATE {line['date']} {line['amount']:>10.2f}  '{row['description']}' -> '{line['description']}'")
    for line in res["new"]:
        print(f"    NEW    {line['date']} {line['amount']:>10.2f}  {line['description']}")
    for line, row in res["possible"]:
        print(f"    CHECK  {line['date']} {line['amount']:>10.2f}  {line['description']}   vs existing "
              f"{row['amount']:.2f} '{row['description']}'")
    if not a.apply:
        print("Nothing written. Re-run with --statement <id> --apply after confirming the summary.")
        return
    if not a.statement:
        raise SystemExit("--statement is required with --apply")
    cur = dv.get("transactioncurrencies?$select=transactioncurrencyid&$filter=isocurrencycode eq 'AUD'")["value"]
    aud = cur[0]["transactioncurrencyid"] if cur else None
    for line, row in res["update"]:
        body = {"lzw_name": line["description"][:500], "lzw_source": O + SOURCES.index("PDF"), "lzw_ispending": False,
                "lzw_duplicatekey": duplicate_key(line)}
        if line.get("balance") is not None:
            body["lzw_runningbalance"] = line["balance"]
        dv.patch(f"lzw_bankstatementlines({row['id']})", body)
    to_create = res["new"] + ([line for line, _ in res["possible"]] if a.include_possible else [])
    for line in to_create:
        # A dropped connection is not retried blindly; re-run the comparison instead, it only creates the shortfall.
        dv.post("lzw_bankstatementlines", line_body(line, account_id, a.statement, a.source, aud))
    print(f"updated {len(res['update'])}, created {len(to_create)}. Now run: python scripts/recalc.py")


if __name__ == "__main__":
    main()
