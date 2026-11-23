"""Link Finance Transactions to bank lines: a split bill (the card charge plus each friend's repayment), a charge
and its refund, or one transaction per line in bulk. See "Split bills" in CLAUDE.md.

    python scripts/split_match.py <finance transaction id> <line id>[=<amount>] ... [--apply]
    python scripts/split_match.py --batch <file> [--apply]

A batch file has one transaction per line, in the same form: `<ft id> <line id>[=<amount>] ...`. Blank lines and
text after `#` are ignored. The whole batch is checked first and nothing is written if any part does not fit; then
it is written under one lock, which is much faster than one run per transaction (each Web API call takes about a
second through the proxy, see docs/decisions.md).

Each line is allocated its remaining amount, or <amount> (signed like the bank) when only part of it belongs
to this bill (one repayment covering two bills). A line used by several transactions in one batch is shared out in
order. Matches are Method Manual, Confirmed. The line becomes Matched when nothing is left, else Partly Matched;
the transaction Reconciled when its Reconciliation Difference is 0, else Partly Reconciled. Holds the
reconciliation lock. Dry run without --apply.
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
CHUNK = 40  # ids per In() filter, to keep the URL short


def cents(v):
    return round(float(v or 0) * 100)


def parse_args(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--batch" in argv:
        path = argv[argv.index("--batch") + 1]
        groups = []
        with open(path, encoding="utf-8") as f:
            for raw in f:
                toks = raw.split("#", 1)[0].split()
                if toks:
                    groups.append((toks[0], toks[1:]))
        return groups
    return [(args[0], args[1:])]


def by_ids(entity_set, id_col, ids, select):
    """Rows of entity_set whose primary key id_col is in ids, a few In() filters instead of one GET per row."""
    ids, out = sorted(set(ids)), {}
    for i in range(0, len(ids), CHUNK):
        vals = ",".join(f"'{x}'" for x in ids[i:i + CHUNK])
        for r in dv.get_all(f"{entity_set}?$select={select}&$filter=Microsoft.Dynamics.CRM.In("
                            f"PropertyName='{id_col}',PropertyValues=[{vals}])"):
            out[r[id_col]] = r
    return out


def plan_batch(groups):
    """Check every group against the current data. Returns (plans, problems); writes nothing."""
    fts = by_ids("lzw_financetransactions", "lzw_financetransactionid", [g[0] for g in groups],
                 "lzw_name,lzw_amount,lzw_type,lzw_actualamount")
    lines = by_ids("lzw_bankstatementlines", "lzw_bankstatementlineid",
                   [p.partition("=")[0] for _, ps in groups for p in ps],
                   "lzw_name,lzw_transactiondate,lzw_amount,lzw_allocatedamount,_transactioncurrencyid_value")
    # A transaction that already has matches: recalculate its rollup first so earlier matches count.
    had = set()
    ids = sorted(fts)
    for i in range(0, len(ids), CHUNK):
        flt = " or ".join(f"_lzw_financetransaction_value eq {x}" for x in ids[i:i + CHUNK])
        had |= {r["_lzw_financetransaction_value"] for r in dv.get_all(
            f"lzw_reconciliationmatchs?$select=_lzw_financetransaction_value&$filter={flt}")}
    for ft_id in had:
        fts[ft_id]["lzw_actualamount"] = rollup("lzw_financetransactions", ft_id, "lzw_actualamount")
    rem = {lid: cents(l["lzw_amount"]) - cents(l["lzw_allocatedamount"]) for lid, l in lines.items()}
    plans, problems, seen = [], [], set()
    for ft_id, parts in groups:
        t = fts.get(ft_id)
        if not t:
            problems.append(f"{ft_id}: no such Finance Transaction")
            continue
        if ft_id in seen:
            problems.append(f"{t['lzw_name']}: listed twice in the batch")
            continue
        seen.add(ft_id)
        if not parts:
            problems.append(f"{t['lzw_name']}: no lines given")
            continue
        alloc_list = []
        for p in parts:
            lid, _, amt = p.partition("=")
            l = lines.get(lid)
            if not l:
                problems.append(f"{t['lzw_name']}: no such bank line {lid}")
                continue
            r = rem[lid]
            alloc = cents(amt) if amt else r
            if alloc == 0 or abs(alloc) > abs(r) or (alloc > 0) != (r > 0):
                problems.append(f"{t['lzw_name']}: line {l['lzw_name']} {l['lzw_amount']}: {alloc / 100} does not fit "
                                f"its remaining {r / 100}")
                continue
            if any(x[0] == lid for x in alloc_list):
                problems.append(f"{t['lzw_name']}: line {l['lzw_name']} listed twice for it")
                continue
            rem[lid] = r - alloc
            alloc_list.append((lid, l, alloc))
        actual = cents(t["lzw_actualamount"]) + sum(a for _, _, a in alloc_list)
        sign = 1 if t["lzw_type"] == INCOME else -1
        plans.append(dict(ft_id=ft_id, t=t, allocs=alloc_list, actual=actual,
                          diff=cents(t["lzw_amount"]) - sign * actual))
    return plans, problems


def write(plans):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    amount = {lid: cents(l["lzw_amount"]) for p in plans for lid, l, _ in p["allocs"]}
    touched = []  # lines with a match written, finished even if a later write fails
    try:
        for p in plans:
            ft_id = p["ft_id"]
            for lid, l, alloc in p["allocs"]:
                body = {"lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({lid})",
                        "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({ft_id})",
                        "lzw_allocatedamount": alloc / 100, "lzw_matchmethod": MANUAL, "lzw_matchstatus": CONFIRMED,
                        "lzw_confirmedon": now, "lzw_confidence": 1,
                        "lzw_aireasoning": "split_match.py: split bill or refund, from the transaction Notes"}
                if l["_transactioncurrencyid_value"]:
                    body["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({l['_transactioncurrencyid_value']})"
                q = (f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter=_lzw_bankstatementline_value"
                     f" eq {lid} and _lzw_financetransaction_value eq {ft_id}")
                # The proxy may cut a write that lands: done() checks before a retry.
                dv.post("lzw_reconciliationmatchs", body, done=lambda q=q: bool(dv.get(q)["value"]))
                if lid not in touched:
                    touched.append(lid)
            rollup("lzw_financetransactions", ft_id, "lzw_actualamount")
            dv.patch(f"lzw_financetransactions({ft_id})",
                     {"lzw_reconciliationstatus": RECONCILED if p["diff"] == 0 else PARTREC})
            print(f"written: {p['t']['lzw_name']}")
    finally:
        # Each line once, after all its matches (a shared line is not done twice). Runs after a failure too, so the
        # line's Allocated Amount counts what was written and a rerun cannot allocate it again.
        for lid in touched:
            done = rollup("lzw_bankstatementlines", lid, "lzw_allocatedamount")
            dv.patch(f"lzw_bankstatementlines({lid})",
                     {"lzw_status": MATCHED if cents(done) == amount[lid] else PARTLY})


def main():
    apply = "--apply" in sys.argv
    plans, problems = plan_batch(parse_args(sys.argv[1:]))
    for p in plans:
        t = p["t"]
        print(f"{t['lzw_name']} {t['lzw_amount']}: actual {p['actual'] / 100:.2f}, difference {p['diff'] / 100:.2f}")
        for lid, l, alloc in p["allocs"]:
            print(f"   {l['lzw_transactiondate']} {l['lzw_name'][:45]:45} {l['lzw_amount']:>9.2f} allocate {alloc / 100:>8.2f}")
    if problems:
        print("NOT WRITTEN (nothing in the batch is written until every part fits):")
        for x in problems:
            print("   " + x)
        sys.exit(1)
    if not apply:
        sys.exit("(dry run)")
    with lock.held("split_match"):
        write(plans)
    print(f"written {len(plans)} transactions, {sum(len(p['allocs']) for p in plans)} matches")


if __name__ == "__main__":
    main()
