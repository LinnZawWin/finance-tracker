"""Reconcile the open Bank Statement Lines against the Finance Transactions, by the rules in docs/reconciliation.md.

    python scripts/reconcile.py            dry run: what would be paired, confirmed and left
    python scripts/reconcile.py --apply    write the transfers and the confirmed matches

Run once at the end of a session, after the imports and note entry (statement import rule 10). Steps:
1. Transfers: two open lines on two of my accounts with opposite amounts within 3 days, both with a transfer
   description (TRANSFER TO/FROM, PAYMENT TO, BPAY, PayID Payment Received, Money added from, ...). The same
   Bank Reference or the other account's number in the description wins a tie. A line with two equally good
   counterparts is left and reported. Written as Status = Transfer and Transfer Counterpart on both lines.
2. Transaction to line, the same candidates as the web page's Reconcile tab: same remaining amount (or the
   same original amount; for an estimated transaction the same account and a shared payee word), the same
   account when the transaction has Paid From, within 4 days, best first, each row used once. A pair is
   confirmed only when neither side has another candidate of the same kind (rule 4) and the transaction's
   Payee, when it has one, shares a word with the line (spaces in the line ignored). A transaction whose
   Payee equals the line's merchant ("Qrcode7684 - Alipay") ranks first, and only another same-merchant
   pair counts as a rival for it. The others are listed
   for the owner and nothing is written for them. Confirmed: a Reconciliation Match (Method Rule, Confirmed),
   the line Matched or Partly Matched, the transaction Reconciled or Partly Reconciled; an estimated
   transaction that is reconciled gets Amount = the bank figure and Needs Details = No.
3. Bank Rules (dry run only): how many of the lines left unmatched a rule would turn into new Finance
   Transactions. Creating them needs the owner's go-ahead.
Step 0 generates the cash lines (scripts/cash_lines.py: cash transactions, withdrawals and deposits).
With --apply it holds the Dataverse lock lzw_ReconcileLock (scripts/lock.py) from the first read to the last
write, so two sessions cannot reconcile at the same time; a second run stops with exit code 2. It then
recalculates the rollups of the rows it matched, so recalc.py is not needed afterwards.
statement_import.py --apply --reconcile runs this script with --apply after writing lines.
Output: counts and the pairs for the owner; every pair is in the details file it names (--verbose prints them all).
"""
import datetime as dt
import re
import sys
from collections import defaultdict

import dv
import lock
import report
from recalc import rollup

APPLY = "--apply" in sys.argv
if APPLY:
    import atexit
    try:
        _lock = lock.acquire("reconcile")
    except lock.Busy as e:
        print(f"NOT RUN: {e}. Wait for that run to finish (or run scripts/lock.py --release if it crashed).")
        sys.exit(2)
    atexit.register(lock.release, *_lock)

# 0. Cash has no statement: generate its lines first (cash_lines.py), so they are not left open below
import cash_lines
cash_lines.run(APPLY)
UNMATCHED, PARTLY, MATCHED, TRANSFER = 859130000, 859130001, 859130002, 859130003
UNREC, PARTREC, RECONCILED = 859130000, 859130001, 859130002
RULE, CONFIRMED = 859130000, 859130001
INCOME = 859130001
CONTAINS, STARTS, EXACT = 859130000, 859130001, 859130002
TRANSFER_RE = re.compile(r"TRANSFER (TO|FROM)|INTERNET BANKING TRANSFER|PAYMENT TO|BPAY|PAYID PAYMENT RECEIVED|"
                         r"MONEY ADDED FROM|PAYMENT - THANK YOU|PAYMENT RECEIVED", re.I)


def cents(v):
    return round(float(v or 0) * 100)


def day(s):
    return dt.date.fromisoformat(s[:10])


def local_day(s):
    """Finance Transaction dates are stored in UTC; the day is the Brisbane day (UTC+10, no DST)."""
    return (dt.datetime.fromisoformat(s.replace("Z", "+00:00")) + dt.timedelta(hours=10)).date()


def words(s):
    return {w for w in re.split(r"[^a-z0-9]+", (s or "").lower()) if len(w) > 2}


accounts = {a["lzw_bankaccountid"]: a for a in dv.get_all(
    "lzw_bankaccounts?$select=lzw_name,lzw_accountnumber")}
lines = dv.get_all(
    "lzw_bankstatementlines?$select=lzw_name,lzw_transactiondate,lzw_amount,lzw_allocatedamount,lzw_originalamount,"
    "lzw_merchant,lzw_bankreference,_lzw_bankaccount_value,_transactioncurrencyid_value,lzw_ispending"
    f"&$filter=statecode eq 0 and (lzw_status eq {UNMATCHED} or lzw_status eq {PARTLY})")
fts = dv.get_all(
    "lzw_financetransactions?$select=lzw_name,lzw_transactiondate,lzw_type,lzw_payee,lzw_amount,lzw_actualamount,"
    "lzw_notes,_lzw_paidfrom_value"
    f"&$filter=statecode eq 0 and (lzw_reconciliationstatus eq null or lzw_reconciliationstatus ne {RECONCILED})")
for l in lines:
    l["day"] = day(l["lzw_transactiondate"])
    l["rem"] = cents(l["lzw_amount"]) - cents(l["lzw_allocatedamount"])
for t in fts:
    t["day"] = local_day(t["lzw_transactiondate"])
    t["est"] = bool(re.search(r"Payment Type: Estimated", t["lzw_notes"] or "", re.I))
    t["want"] = (1 if t["lzw_type"] == INCOME else -1) * cents(t["lzw_amount"]) - cents(t["lzw_actualamount"])
acct = lambda i: accounts.get(i, {}).get("lzw_name", "?")
show_l = lambda l: f"{l['day']} {acct(l['_lzw_bankaccount_value'])[:22]:22} {l['rem'] / 100:>10.2f}  {l['lzw_name'][:60]}"
show_t = lambda t: f"{t['day']} {acct(t['_lzw_paidfrom_value'])[:22]:22} {t['want'] / 100:>10.2f}  {t['lzw_name']} ({t['lzw_payee']})"

# Bank Rules: a line that fits one is an expense or income, never a transfer (for example ANZ Access Advantage)
rules = dv.get_all("lzw_bankrules?$select=lzw_matchtext,lzw_matchtype,lzw_priority,_lzw_bankaccount_value"
                   "&$filter=statecode eq 0&$orderby=lzw_priority")


def rule_for(l):
    d = (l["lzw_name"] or "").upper()
    for r in rules:
        m = (r["lzw_matchtext"] or "").upper()
        if r["_lzw_bankaccount_value"] and r["_lzw_bankaccount_value"] != l["_lzw_bankaccount_value"]:
            continue
        if (r["lzw_matchtype"] == EXACT and d == m.strip()) or (r["lzw_matchtype"] == STARTS and d.startswith(m)) \
                or (r["lzw_matchtype"] not in (EXACT, STARTS) and m in d):
            return r
    return None



# 1. Transfers
def acct_digits(i):
    return re.sub(r"\D", "", accounts.get(i, {}).get("lzw_accountnumber") or "")


ALIASES = {"AMEX": ["AMERICAN EXPRESS", "AMEX"], "KOGAN": ["KOGAN"], "WISE": ["WISE"]}


def names_account(desc, account_id):
    """The description names the other account's bank, for example PAYMENT TO AMERICAN EXPRESS."""
    name, d = accounts.get(account_id, {}).get("lzw_name", "").upper(), (desc or "").upper()
    return any(k in name and any(w in d for w in ws) for k, ws in ALIASES.items())


tl = [l for l in lines if l["rem"] == cents(l["lzw_amount"]) and TRANSFER_RE.search(l["lzw_name"] or "")
      and not rule_for(l)]
by_amt = defaultdict(list)
for l in tl:
    by_amt[l["rem"]].append(l)
cands = []
for a in tl:
    if a["rem"] >= 0:
        continue
    for b in by_amt[-a["rem"]]:
        if b["_lzw_bankaccount_value"] == a["_lzw_bankaccount_value"] or abs((a["day"] - b["day"]).days) > 3:
            continue
        ref = bool(a["lzw_bankreference"]) and a["lzw_bankreference"] == b["lzw_bankreference"]
        num = any(len(d) >= 6 and d[-9:] in re.sub(r"\D", "", x["lzw_name"])
                  for x, d in ((a, acct_digits(b["_lzw_bankaccount_value"])), (b, acct_digits(a["_lzw_bankaccount_value"]))))
        named = any(names_account(x["lzw_name"], y["_lzw_bankaccount_value"]) for x, y in ((a, b), (b, a)))
        cands.append(((ref, num, named, -abs((a["day"] - b["day"]).days)), a, b))
cands.sort(key=lambda c: c[0], reverse=True)
same = lambda x, y: x is y or (x["_lzw_bankaccount_value"], x["day"]) == (y["_lzw_bankaccount_value"], y["day"])
used, transfers, unsure = set(), [], []
for key, a, b in cands:
    ia, ib = a["lzw_bankstatementlineid"], b["lzw_bankstatementlineid"]
    if ia in used or ib in used:
        continue
    # A rival only counts when it would pair a line with a different account or day: two identical top-ups
    # on the same day can be paired either way.
    rivals = [c for c in cands if c[0] == key and c[1:] != (a, b) and
              {c[1]["lzw_bankstatementlineid"], c[2]["lzw_bankstatementlineid"]} & {ia, ib}
              and not {c[1]["lzw_bankstatementlineid"], c[2]["lzw_bankstatementlineid"]} & used
              and not (same(c[1], a) and same(c[2], b))]
    if rivals:
        unsure.append((a, b, len(rivals)))
        continue
    used |= {ia, ib}
    transfers.append((a, b))
print(f"1. Transfers: {len(transfers)} pairs, {len(unsure)} left (more than one counterpart)")
for a, b, n in unsure:
    report.need("   unsure: " + show_l(a) + " <-> " + show_l(b) + f" +{n} other", "unsure transfer")
for a, b in transfers:
    report.detail("   transfer: " + show_l(a) + " <-> " + show_l(b))

# 2. Transaction to line
open_lines = [l for l in lines if l["lzw_bankstatementlineid"] not in used]
pc = []
for t in fts:
    if not t["lzw_amount"] and not t["est"]:
        continue
    tw = words(f"{t['lzw_payee']} {t['lzw_name']}")
    for l in open_lines:
        if t["_lzw_paidfrom_value"] and t["_lzw_paidfrom_value"] != l["_lzw_bankaccount_value"]:
            continue
        days = abs((t["day"] - l["day"]).days)
        if days > 4:
            continue
        same_sign = (l["rem"] > 0) == (t["want"] > 0)
        if l["rem"] == t["want"]:
            reason, score = "same amount", 1.0
        elif l["lzw_originalamount"] is not None and abs(cents(l["lzw_originalamount"])) == abs(t["want"]) and same_sign:
            reason, score = "same original amount", 0.9
        elif t["est"] and same_sign and words(f"{l['lzw_merchant']} {l['lzw_name']}") & tw:
            reason, score = "estimated, same payee", 0.7
        else:
            continue
        # The note's Payee equal to the line's merchant (for example "Qrcode7684 - Alipay") singles the line out.
        merchant = bool(t["lzw_payee"]) and t["lzw_payee"].strip().lower() in {
            (l["lzw_merchant"] or "").strip().lower(), (l["lzw_name"] or "").strip().lower()}
        pc.append(dict(t=t, l=l, reason=reason, days=days, merchant=merchant,
                       score=score + (0.1 if t["_lzw_paidfrom_value"] else 0) + (0.2 if merchant else 0) - days * 0.03))
# A Payee none of whose words appears in the line (spaces ignored: "Didi" in "DIDIMOBILITY") is a doubt.
def payee_differs(t, l):
    flat = re.sub(r"[^a-z0-9]+", "", f"{l['lzw_merchant']} {l['lzw_name']}".lower())
    return bool(words(t["lzw_payee"])) and not any(w in flat for w in words(t["lzw_payee"]))


for c in pc:
    c["payee_differs"] = payee_differs(c["t"], c["l"])
pc.sort(key=lambda c: c["score"], reverse=True)
# Totally identical rows are interchangeable: transactions with the same account, amount, day, description and
# payee; lines with the same account, amount, day and description. A rival made only of such twins is no rival,
# so a group of identical transactions and identical lines is paired one each.
twin_t = lambda a, b: a is b or (a["_lzw_paidfrom_value"], a["want"], a["day"], a["lzw_name"], a["lzw_payee"]) == \
    (b["_lzw_paidfrom_value"], b["want"], b["day"], b["lzw_name"], b["lzw_payee"])
twin_l = lambda a, b: a is b or (a["_lzw_bankaccount_value"], a["rem"], a["day"], " ".join((a["lzw_name"] or "").split())) == \
    (b["_lzw_bankaccount_value"], b["rem"], b["day"], " ".join((b["lzw_name"] or "").split()))
uT, uL, confirm, propose = set(), set(), [], []
for c in pc:
    tid, lid = c["t"]["lzw_financetransactionid"], c["l"]["lzw_bankstatementlineid"]
    if tid in uT or lid in uL:
        continue
    uT.add(tid)
    uL.add(lid)
    # A same-merchant pair only has a rival in another same-merchant pair.
    c["others"] = sum(1 for o in pc if o is not c and o["reason"] == c["reason"] and (o["t"] is c["t"] or o["l"] is c["l"])
                      and (o["merchant"] or not c["merchant"])
                      and not (twin_t(o["t"], c["t"]) and twin_l(o["l"], c["l"]))
                      and not o["payee_differs"])  # a pair rule 4 would never confirm is no rival
    (propose if c["others"] or c["payee_differs"] else confirm).append(c)
print(f"2. Transaction to line: {len(confirm)} to confirm, {len(propose)} for the owner "
      f"(another candidate), {len(fts) - len(confirm) - len(propose)} transactions with no candidate")
for c in confirm:
    report.detail("   confirm: " + show_t(c["t"]) + " <-> " + show_l(c["l"]) + f" [{c['reason']}{', same merchant' if c['merchant'] else ''}, {c['days']} d]")
for c in propose:
    report.need("   owner:   " + show_t(c["t"]) + " <-> " + show_l(c["l"]) + f" [{c['reason']}, {c['days']} d, " + (f"+{c['others']} other" if c["others"] else "payee differs") + "]", "owner")
for t in fts:
    if t["lzw_financetransactionid"] not in uT:
        report.detail("   none:    " + show_t(t))

# 3. Bank Rules (count only)
left = [l for l in open_lines if l["lzw_bankstatementlineid"] not in uL]
ruled = [l for l in left if rule_for(l)]
print(f"3. Bank Rules: {len(ruled)} of the {len(left)} lines left fit a rule (not created; needs the owner's go-ahead)")

if not APPLY:
    print("(dry run)")
    sys.exit()

now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for a, b in transfers:
    for x, y in ((a, b), (b, a)):
        dv.patch(f"lzw_bankstatementlines({x['lzw_bankstatementlineid']})", {
            "lzw_status": TRANSFER,
            "lzw_TransferCounterpart@odata.bind": f"/lzw_bankstatementlines({y['lzw_bankstatementlineid']})"})
for c in confirm:
    t, l = c["t"], c["l"]
    body = {"lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({l['lzw_bankstatementlineid']})",
            "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({t['lzw_financetransactionid']})",
            "lzw_allocatedamount": l["rem"] / 100, "lzw_matchmethod": RULE, "lzw_matchstatus": CONFIRMED,
            "lzw_confirmedon": now, "lzw_confidence": round(max(0.0, min(1.0, c["score"])), 2),
            "lzw_aireasoning": f"reconcile.py: {c['reason']}{', same merchant' if c['merchant'] else ''}, "
                               f"{c['days']} day(s) apart, no other candidate"}
    if l["_transactioncurrencyid_value"]:
        body["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({l['_transactioncurrencyid_value']})"
    q = (f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter=_lzw_bankstatementline_value"
         f" eq {l['lzw_bankstatementlineid']} and _lzw_financetransaction_value eq {t['lzw_financetransactionid']}")
    dv.post("lzw_reconciliationmatchs", body, done=lambda q=q: bool(dv.get(q)["value"]))
    dv.patch(f"lzw_bankstatementlines({l['lzw_bankstatementlineid']})", {"lzw_status": MATCHED})
    if t["est"]:
        fb = {"lzw_reconciliationstatus": RECONCILED, "lzw_needsdetails": False, "lzw_amount": abs(l["rem"]) / 100}
    else:
        fb = {"lzw_reconciliationstatus": RECONCILED}      # as the web page's Confirm: the pair is the whole match
    dv.patch(f"lzw_financetransactions({t['lzw_financetransactionid']})", fb)
for c in confirm:
    rollup("lzw_bankstatementlines", c["l"]["lzw_bankstatementlineid"], "lzw_allocatedamount")
    rollup("lzw_financetransactions", c["t"]["lzw_financetransactionid"], "lzw_actualamount")
print(f"written: {len(transfers)} transfer pairs, {len(confirm)} matches; rollups recalculated on the matched rows")
