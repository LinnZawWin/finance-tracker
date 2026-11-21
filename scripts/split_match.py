"""Link one Finance Transaction to several bank lines: a split bill (the card charge plus each friend's
repayment) or a charge and its refund. See "Split bills" in CLAUDE.md.

    python scripts/split_match.py <finance transaction id> <line id>[=<amount>] ... [--apply]

Each line is allocated its remaining amount, or <amount> (signed like the bank) when only part of it belongs
to this bill (one repayment covering two bills). Matches are Method Manual, Confirmed. The line becomes
Matched when nothing is left, else Partly Matched; the transaction Reconciled when its Reconciliation
Difference is 0, else Partly Reconciled. Holds the reconciliation lock. Dry run without --apply.
"""
import datetime as dt
import sys

import dv
import lock
from recalc import rollup

MANUAL, CONFIRMED = 859130003, 859130001
MATCHED, PARTLY = 859130002, 859130001
PARTREC, RECONCILED = 859130001, 859130002
INCOME = 859130001

args = [a for a in sys.argv[1:] if not a.startswith("--")]
APPLY = "--apply" in sys.argv
ft_id, parts = args[0], args[1:]
cents = lambda v: round(float(v or 0) * 100)

rollup("lzw_financetransactions", ft_id, "lzw_actualamount")  # matches written earlier count
t = dv.get(f"lzw_financetransactions({ft_id})?$select=lzw_name,lzw_amount,lzw_type,lzw_actualamount")
plan = []
for p in parts:
    lid, _, amt = p.partition("=")
    l = dv.get(f"lzw_bankstatementlines({lid})?$select=lzw_name,lzw_transactiondate,lzw_amount,lzw_allocatedamount,"
               "_transactioncurrencyid_value")
    rem = cents(l["lzw_amount"]) - cents(l["lzw_allocatedamount"])
    alloc = cents(amt) if amt else rem
    if alloc == 0 or abs(alloc) > abs(rem) or (alloc > 0) != (rem > 0):
        sys.exit(f"line {l['lzw_name']} {l['lzw_amount']}: {alloc / 100} does not fit its remaining {rem / 100}")
    plan.append((lid, l, alloc, rem))
actual = cents(t["lzw_actualamount"]) + sum(a for _, _, a, _ in plan)
sign = 1 if t["lzw_type"] == INCOME else -1
diff = cents(t["lzw_amount"]) - sign * actual
print(f"{t['lzw_name']} {t['lzw_amount']}: actual {actual / 100:.2f}, difference {diff / 100:.2f}")
for lid, l, alloc, rem in plan:
    print(f"   {l['lzw_transactiondate']} {l['lzw_name'][:45]:45} {l['lzw_amount']:>9.2f} allocate {alloc / 100:>8.2f}")
if not APPLY:
    sys.exit("(dry run)")

with lock.held("split_match"):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for lid, l, alloc, rem in plan:
        body = {"lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({lid})",
                "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({ft_id})",
                "lzw_allocatedamount": alloc / 100, "lzw_matchmethod": MANUAL, "lzw_matchstatus": CONFIRMED,
                "lzw_confirmedon": now, "lzw_confidence": 1,
                "lzw_aireasoning": "split_match.py: split bill or refund, from the transaction Notes"}
        if l["_transactioncurrencyid_value"]:
            body["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({l['_transactioncurrencyid_value']})"
        dv.post("lzw_reconciliationmatchs", body, done=lambda: bool(dv.get(  # the proxy may cut a write that lands
            f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter=_lzw_bankstatementline_value eq {lid}"
            f" and _lzw_financetransaction_value eq {ft_id}")["value"]))
        dv.patch(f"lzw_bankstatementlines({lid})", {"lzw_status": MATCHED if alloc == rem else PARTLY})
        rollup("lzw_bankstatementlines", lid, "lzw_allocatedamount")
    rollup("lzw_financetransactions", ft_id, "lzw_actualamount")
    dv.patch(f"lzw_financetransactions({ft_id})", {"lzw_reconciliationstatus": RECONCILED if diff == 0 else PARTREC})
print("written")
