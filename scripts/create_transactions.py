"""Create Finance Transactions from a notes file in a fixed format (see "Notes file" in docs/entering-notes.md).

    python scripts/create_transactions.py <notes file>            dry run: counts and problems only
    python scripts/create_transactions.py <notes file> --apply    create the rows that pass every check
    add --verbose to print every row

One row per line, fields separated by "|" (spaces around them ignored, empty trailing fields may be left out):

    date | description | payee | amount | share | account | project | category | notes | original | claim

- date: yyyy-mm-dd. amount: AUD, positive = Expense, negative = Income (saved positive).
- share: empty or Mine, A, AA, P (Paid for Others). account: the Bank Account name or one of its Short Name
  aliases. project: the Finance Project name. category: the Finance Category name (required). Matching ignores case.
- original: a foreign amount such as "CNY 100" (Original Amount and Original Currency; the AUD amount is still needed).
- claim: "Employer" or "Tax", optionally with the part to claim ("Employer 262.50"); sets Claim Type, Claim Status
  Pending and Claim Amount (the whole Amount when no part is given).
- "#" starts a comment line; blank lines are ignored.

Transfers, split bills, assets and anything else these fields cannot hold are not taken: create those by hand.
Nothing is written when any row has a problem, so fix the file and run again. A row whose date, description and
amount already exist (an active row) is skipped as a duplicate. Each row gets Source = Keep, currency AUD and
Source Row ID "notes:<file hash>:<line>", so a rerun of the same file after an interrupted --apply creates
only the rows that are missing. Rows of a day are 10 minutes apart in file order, after that day's last
existing row (12:00 Brisbane when the day has none), closer together if they would pass midnight.
"""
import datetime as dt
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dv
import statement_compare as sc

OPT = 859130000
EXPENSE, INCOME = OPT, OPT + 1
KEEP = OPT
SHARE = {"": 0, "mine": 0, "a": 1, "aa": 2, "p": 3}
TZ = dt.timezone(dt.timedelta(hours=10))  # Brisbane, no daylight saving
STEP = dt.timedelta(minutes=10)
FIELDS = ["date", "description", "payee", "amount", "share", "account", "project", "category", "notes", "original", "claim"]
CLAIM = {"employer": OPT, "tax": OPT + 1, "income tax": OPT + 1}  # Claim Type; Claim Status Pending = OPT


def esc(s):
    return s.replace("'", "''")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    apply, verbose = "--apply" in sys.argv, "--verbose" in sys.argv
    path = args[0]
    raw = open(path, encoding="utf-8").read()
    tag = hashlib.sha1(raw.encode()).hexdigest()[:8]

    accounts = {}
    for a in dv.get_all("lzw_bankaccounts?$select=lzw_bankaccountid,lzw_name,lzw_shortname&$filter=statecode eq 0"):
        for k in [a["lzw_name"]] + (a["lzw_shortname"] or "").split(";"):
            if k.strip():
                accounts.setdefault(k.strip().lower(), set()).add((a["lzw_bankaccountid"], a["lzw_name"]))
    projects = {p["lzw_name"].strip().lower(): p["lzw_financeprojectid"]
                for p in dv.get_all("lzw_financeprojects?$select=lzw_financeprojectid,lzw_name&$filter=statecode eq 0")}
    cats = {c["lzw_name"].strip().lower(): c["lzw_financecategoryid"]
            for c in dv.get_all("lzw_financecategories?$select=lzw_financecategoryid,lzw_name&$filter=statecode eq 0")}
    aud = sc.currency_id("AUD")

    rows, problems = [], []
    for n, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > len(FIELDS):
            problems.append(f"line {n}: {len(parts)} fields, at most {len(FIELDS)}")
            continue
        f = dict(zip(FIELDS, parts + [""] * (len(FIELDS) - len(parts))))
        bad = []
        try:
            day = dt.date.fromisoformat(f["date"])
        except ValueError:
            bad.append(f"date '{f['date']}'")
            day = None
        if not f["description"]:
            bad.append("no description")
        try:
            amount = round(float(f["amount"].replace(",", "")), 2)
        except ValueError:
            bad.append(f"amount '{f['amount']}'")
            amount = None
        share = SHARE.get(f["share"].lower())
        if share is None:
            bad.append(f"share '{f['share']}'")
        acct = None
        if f["account"]:
            hit = accounts.get(f["account"].lower(), set())
            if len(hit) != 1:
                bad.append(f"account '{f['account']}' " + ("not found" if not hit else "fits " + ", ".join(sorted(h[1] for h in hit))))
            else:
                acct = next(iter(hit))
        proj = None
        if f["project"]:
            proj = projects.get(f["project"].lower())
            if not proj:
                bad.append(f"project '{f['project']}' not found")
        cat = cats.get(f["category"].lower()) if f["category"] else None
        if not cat:
            bad.append(f"category '{f['category']}' not found" if f["category"] else "no category")
        orig = None
        if f["original"]:
            m = re.fullmatch(r"([A-Za-z]{3})\s*([\d,]+(?:\.\d+)?)", f["original"])
            if not m:
                bad.append(f"original '{f['original']}' (write it like CNY 100)")
            else:
                try:
                    orig = (sc.currency_id(m.group(1).upper()), round(float(m.group(2).replace(",", "")), 2))
                except Exception:
                    bad.append(f"currency '{m.group(1)}' not found")
        claim = None
        if f["claim"]:
            m = re.fullmatch(r"(employer|income tax|tax)\s*([\d,]+(?:\.\d+)?)?", f["claim"].strip().lower())
            if not m:
                bad.append(f"claim '{f['claim']}' (write Employer or Tax, optionally with the amount)")
            else:
                part = round(float(m.group(2).replace(",", "")), 2) if m.group(2) else None
                if part is not None and amount is not None and part > abs(amount):
                    bad.append(f"claim {part} is more than the amount")
                claim = (CLAIM[m.group(1)], part)
        if bad:
            problems.append(f"line {n}: " + "; ".join(bad) + f"  [{line.strip()[:80]}]")
            continue
        rows.append(dict(n=n, day=day, f=f, amount=amount, share=share, acct=acct, proj=proj, cat=cat, orig=orig, claim=claim,
                         rid=f"notes:{tag}:{n}"))

    # Existing rows on those days: duplicates and the time of each day's last row
    existing = {}
    for day in sorted({r["day"] for r in rows}):
        start = dt.datetime.combine(day, dt.time(), TZ).astimezone(dt.timezone.utc)
        flt = (f"statecode eq 0 and lzw_transactiondate ge {start:%Y-%m-%dT%H:%M:%SZ} and "
               f"lzw_transactiondate lt {start + dt.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}")
        existing[day] = dv.get_all("lzw_financetransactions?$select=lzw_name,lzw_amount,lzw_transactiondate,lzw_sourcerowid"
                                   f"&$filter={flt}&$orderby=lzw_transactiondate asc")
    new, dups = [], []
    for r in rows:
        ex = existing[r["day"]]
        if any(e["lzw_sourcerowid"] == r["rid"] for e in ex) or any(
                (e["lzw_name"] or "").strip().lower() == r["f"]["description"].lower()
                and round(e["lzw_amount"] or 0, 2) == abs(r["amount"]) for e in ex):
            dups.append(r)
        else:
            new.append(r)

    # Times: 10 minutes apart after the day's last row, closer if they would pass midnight
    for day in {r["day"] for r in new}:
        todo = [r for r in new if r["day"] == day]
        ex = existing[day]
        base = (dt.datetime.fromisoformat(ex[-1]["lzw_transactiondate"].replace("Z", "+00:00")) + dt.timedelta(minutes=1)
                if ex else dt.datetime.combine(day, dt.time(12), TZ))
        room = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), TZ) - dt.timedelta(minutes=1) - base
        step = min(STEP, room / (len(todo) - 1)) if len(todo) > 1 else STEP
        step = max(step, dt.timedelta(0))
        for i, r in enumerate(todo):
            r["when"] = (base + i * step).replace(microsecond=0).astimezone(dt.timezone.utc)

    show = lambda r: (f"  {r['day']} {r['f']['description'][:40]:40} {r['amount']:>9.2f} "
                      f"{(r['acct'] or ('', ''))[1][:18]:18} {r['f']['category'][:24]}")
    print(f"{len(rows) + len(problems)} rows read: {len(new)} new, {len(dups)} duplicates, {len(problems)} with problems")
    for p in problems:
        print("  PROBLEM", p)
    for r in dups:
        print("  duplicate", show(r).strip())
    if verbose:
        for r in new:
            print("  new", show(r).strip())
    if problems:
        print("NOT WRITTEN: fix the problems and run again.")
        sys.exit(1)
    if not apply:
        print("(dry run)")
        return

    for r in new:
        f = r["f"]
        body = {"lzw_name": f["description"][:200], "lzw_payee": f["payee"] or None, "lzw_amount": abs(r["amount"]),
                "lzw_type": INCOME if r["amount"] < 0 else EXPENSE, "lzw_sharetype": OPT + r["share"],
                "lzw_notes": f["notes"] or None, "lzw_source": KEEP, "lzw_sourcerowid": r["rid"],
                "lzw_transactiondate": f"{r['when']:%Y-%m-%dT%H:%M:%SZ}", "lzw_needsdetails": False,
                "lzw_Category@odata.bind": f"/lzw_financecategories({r['cat']})",
                "transactioncurrencyid@odata.bind": f"/transactioncurrencies({aud})"}
        if r["acct"]:
            body["lzw_PaidFrom@odata.bind"] = f"/lzw_bankaccounts({r['acct'][0]})"
        if r["proj"]:
            body["lzw_Project@odata.bind"] = f"/lzw_financeprojects({r['proj']})"
        if r["orig"]:
            body["lzw_OriginalCurrency@odata.bind"] = f"/transactioncurrencies({r['orig'][0]})"
            body["lzw_originalamount"] = r["orig"][1]
        if r["claim"]:
            body.update(lzw_claimtype=r["claim"][0], lzw_claimstatus=OPT,
                        lzw_claimamount=r["claim"][1] if r["claim"][1] is not None else abs(r["amount"]))
        done = lambda rid=r["rid"]: bool(dv.get("lzw_financetransactions?$select=lzw_financetransactionid"
                                                f"&$filter=lzw_sourcerowid eq '{esc(rid)}'")["value"])
        dv.post("lzw_financetransactions", body, done=done)
    print(f"written: {len(new)} Finance Transactions")


if __name__ == "__main__":
    main()
