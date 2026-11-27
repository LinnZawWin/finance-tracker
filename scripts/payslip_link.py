"""Link the imported payslips to their Finance Transactions and transfer pairs (see "AustralianSuper and payslips" in
docs/statement-import.md). Dry run by default; --apply writes, under the reconciliation lock.

    python scripts/payslip_link.py [--apply]

For every payslip statement on an Employer account (lines from payslip_lines.py; not the contract statements
`<Employer>_Invoice_*` and `<Employer>_ATO_*`, which contract_link.py links) that is not linked yet:
1. The Salary FT (net only, owner 2026-11-27): the existing Income "Salary" FT on the same day as the payment with the
   net or gross amount (entered from the bank line) is reused: its match to the bank line is deleted, Amount becomes
   the net (gross less tax), Paid From the employer. Without one, a new Salary FT is created.
2. No FTs for the tax withheld or the employer super: the Tax lines are matched to the Salary FT, so its Actual Amount
   is the net; the Superannuation line (the employer's contribution, locked in the fund) is set Ignored.
3. Matches (Manual, Confirmed): earnings lines (+) and Tax lines (-) -> Salary.
4. Transfer pairs: Net pay <-> the bank line with the opposite amount within 3 days that is not already a Transfer
   (the Everyday salary line; the same amount moved on to a saver the same day is a Transfer already),
   Superannuation paid <-> the super account's employer contribution with the opposite amount within 14 days.
A part that has no single candidate is reported and left.
"""
import datetime as dt
import sys

import dv
import lock
import spec
from recalc import rollup, rollup_op

APPLY = "--apply" in sys.argv
O = spec.OPT
INCOME, EXPENSE, IMPORT = O + 1, O, O + 2
MANUAL, CONFIRMED = O + 3, O + 1
L_MATCHED, L_TRANSFER, L_UNMATCHED, L_IGNORED = O + 2, O + 3, O, O + 4
RECONCILED = O + 2
EMPLOYER, SUPER = O + 6, O + 5


def q(s):
    return s.replace("'", "''")


def one(path):
    v = dv.get(path)["value"]
    return v[0] if len(v) == 1 else None


def cat(name):
    return one(f"lzw_financecategories?$select=lzw_financecategoryid&$filter=lzw_name eq '{q(name)}'")["lzw_financecategoryid"]


def main():
    accts = dv.get_all("lzw_bankaccounts?$select=lzw_bankaccountid,lzw_name,lzw_accounttype")
    employers = [a for a in accts if a.get("lzw_accounttype") == EMPLOYER]
    supers = [a["lzw_bankaccountid"] for a in accts if a.get("lzw_accounttype") == SUPER]
    c_salary, c_tax = cat("Salary and Contract Income"), cat("Tax")
    plan = []
    for emp in employers:
        eid = emp["lzw_bankaccountid"]
        for st in dv.get_all(f"lzw_bankstatements?$select=lzw_bankstatementid,lzw_name&$filter=_lzw_bankaccount_value eq {eid}"):
            if "_Invoice_" in st["lzw_name"] or "_ATO_" in st["lzw_name"]:
                continue  # contract invoices and ATO payments: contract_link.py
            lines = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_amount,lzw_transactiondate,"
                               "lzw_status,_lzw_transfercounterpart_value&$filter=_lzw_bankstatement_value eq "
                               f"{st['lzw_bankstatementid']} and statecode eq 0&$orderby=lzw_linenumber")
            plan.append((emp, st, lines))
    if not APPLY:
        for emp, st, lines in plan:
            link(emp, st, lines, supers, c_salary, c_tax)
        return
    with lock.held("payslip_link.py"):
        for emp, st, lines in plan:
            link(emp, st, lines, supers, c_salary, c_tax)


def link(emp, st, lines, supers, c_salary, c_tax):
    eid, name = emp["lzw_bankaccountid"], st["lzw_name"]
    payee = emp["lzw_name"]
    kind = lambda l: l["lzw_name"].split(" - ", 1)[0]
    earn = [l for l in lines if kind(l) == "Salary & Wages"]
    tax = [l for l in lines if kind(l) == "Tax"]
    sup = [l for l in lines if kind(l) == "Superannuation"]
    sup_paid = [l for l in lines if kind(l) == "Superannuation paid"]
    net = [l for l in lines if kind(l) == "Net pay"]
    day = lines[0]["lzw_transactiondate"][:10]
    if all(l["lzw_status"] in (L_MATCHED, L_TRANSFER, L_IGNORED) for l in lines):
        print(f"{name}: already linked")
        return
    gross = round(sum(l["lzw_amount"] for l in earn), 2)
    netamt = round(-sum(l["lzw_amount"] for l in net), 2)
    taxamt = round(-sum(l["lzw_amount"] for l in tax), 2)
    if round(gross - taxamt, 2) != netamt:
        print(f"    SKIPPED {name}: gross {gross:.2f} - tax {taxamt:.2f} != net pay {netamt:.2f}")
        return
    print(f"{name}: paid {day}, gross {gross:.2f}, tax {taxamt:.2f}, net {netamt:.2f}")
    # 1. Salary FT
    d0 = dt.date.fromisoformat(day)
    lo, hi = d0 - dt.timedelta(days=1), d0 + dt.timedelta(days=2)
    cands = dv.get_all("lzw_financetransactions?$select=lzw_financetransactionid,lzw_amount,lzw_transactiondate&$filter="
                       f"lzw_type eq {INCOME} and lzw_name eq 'Salary' and lzw_transactiondate ge {lo} and "
                       f"lzw_transactiondate lt {hi} and (lzw_amount eq {netamt} or lzw_amount eq {gross})")
    if len(cands) > 1:
        print(f"    SKIPPED: {len(cands)} Salary transactions fit")
        return
    sal = cands[0] if cands else None
    when = sal["lzw_transactiondate"] if sal else f"{day}T02:00:00Z"
    old = []
    if sal:
        old = dv.get_all("lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid,_lzw_bankstatementline_value,"
                         f"lzw_allocatedamount&$filter=_lzw_financetransaction_value eq {sal['lzw_financetransactionid']}")
        old = [m for m in old if m["_lzw_bankstatementline_value"] not in {l["lzw_bankstatementlineid"] for l in lines}]
        print(f"    Salary FT {sal['lzw_financetransactionid']} {sal['lzw_amount']:.2f} -> {netamt:.2f}, "
              f"remove {len(old)} match(es) to the bank line")
    else:
        print(f"    new Salary FT {netamt:.2f}")
    # 4. counterparts
    pairs = []
    for l in net:
        bank = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_transactiondate&$filter="
                          f"lzw_amount eq {-l['lzw_amount']} and _lzw_bankaccount_value ne {eid} and statecode eq 0 and "
                          f"lzw_status ne {L_TRANSFER} and "
                          f"lzw_transactiondate ge {d0 - dt.timedelta(days=3)} and lzw_transactiondate le {d0 + dt.timedelta(days=3)}")
        pairs.append((l, bank))
    for l in sup_paid:
        acc = " or ".join(f"_lzw_bankaccount_value eq {s}" for s in supers)
        cont = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_transactiondate&$filter="
                          f"lzw_amount eq {-l['lzw_amount']} and ({acc}) and statecode eq 0 and "
                          f"startswith(lzw_name,'Contribution - Employer') and "
                          f"lzw_transactiondate ge {d0} and lzw_transactiondate le {d0 + dt.timedelta(days=14)}")
        pairs.append((l, cont))
    for l, c in pairs:
        if len(c) == 1:
            print(f"    transfer {l['lzw_amount']:10.2f} {l['lzw_name'][:40]:40} <-> {c[0]['lzw_transactiondate']} {c[0]['lzw_name'][:60]}")
        else:
            print(f"    NO PAIR ({len(c)} candidates) for {l['lzw_name']}")
    if not APPLY:
        return
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    note = f"From payslip {name}."
    base = {"lzw_payee": payee, "lzw_PaidFrom@odata.bind": f"/lzw_bankaccounts({eid})",
            "lzw_transactiondate": when, "lzw_source": IMPORT}
    for m in old:
        dv.call("DELETE", f"lzw_reconciliationmatchs({m['lzw_reconciliationmatchid']})")
        lid = m["_lzw_bankstatementline_value"]
        dv.patch(f"lzw_bankstatementlines({lid})", {"lzw_status": L_UNMATCHED})
    notes = (f"{note} Net pay: gross {gross:,.2f} less PAYG {taxamt:,.2f}, matched to the earnings and tax lines on "
             f"the {payee} account; the net was paid to the bank (Transfer from the {payee} account).")
    if sal:
        sid = sal["lzw_financetransactionid"]
        dv.patch(f"lzw_financetransactions({sid})", dict(base, lzw_amount=netamt, lzw_notes=notes))
    else:
        sid = create(dict(base, lzw_name="Salary", lzw_type=INCOME, lzw_amount=netamt, lzw_notes=notes), c_salary)
    fts = [(sid, earn + tax)]
    # Matches, statuses, transfer pairs and rollups in dv.batch requests instead of one request per write.
    ops = []
    for fid, ls in fts:
        for l in ls:
            lid = l["lzw_bankstatementlineid"]
            if not dv.get(f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter=_lzw_bankstatementline_value eq {lid}")["value"]:
                ops.append(("POST", "lzw_reconciliationmatchs", {
                    "lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({lid})",
                    "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({fid})",
                    "lzw_allocatedamount": l["lzw_amount"], "lzw_matchmethod": MANUAL, "lzw_matchstatus": CONFIRMED,
                    "lzw_confirmedon": now, "lzw_aireasoning": f"payslip_link.py: {name}"}))
            ops.append(("PATCH", f"lzw_bankstatementlines({lid})", {"lzw_status": L_MATCHED}))
        ops.append(("PATCH", f"lzw_financetransactions({fid})", {"lzw_reconciliationstatus": RECONCILED}))
    for l in sup:  # the employer's contribution: locked in the fund, no FT
        ops.append(("PATCH", f"lzw_bankstatementlines({l['lzw_bankstatementlineid']})", {"lzw_status": L_IGNORED}))
    for l, c in pairs:
        if len(c) != 1:
            continue
        a, b = l["lzw_bankstatementlineid"], c[0]["lzw_bankstatementlineid"]
        for x, y in ((a, b), (b, a)):
            ops.append(("PATCH", f"lzw_bankstatementlines({x})", {"lzw_status": L_TRANSFER,
                        "lzw_TransferCounterpart@odata.bind": f"/lzw_bankstatementlines({y})"}))

    def landed(chunk):
        post = next((b for m, _, b in chunk if m == "POST"), None)
        if post is None:  # only PATCHes: sending them again is harmless
            return False
        lid = post["lzw_BankStatementLine@odata.bind"].split("(")[1].rstrip(")")
        return bool(dv.get(f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter="
                           f"_lzw_bankstatementline_value eq {lid}")["value"])
    dv.batch(ops, done=landed)
    dv.batch([rollup_op("lzw_bankstatementlines", l["lzw_bankstatementlineid"], "lzw_allocatedamount")
              for _, ls in fts for l in ls]
             + [rollup_op("lzw_bankstatementlines", c[0]["lzw_bankstatementlineid"], "lzw_allocatedamount")
                for _, c in pairs if len(c) == 1]
             + [rollup_op("lzw_financetransactions", fid, "lzw_actualamount") for fid, _ in fts])
    print("    written")


def existing_ft(name, when, amt, eid):
    r = dv.get(f"lzw_financetransactions?$select=lzw_financetransactionid&$filter=lzw_name eq '{q(name)}' and "
               f"lzw_transactiondate eq {when} and lzw_amount eq {amt} and _lzw_paidfrom_value eq {eid}")["value"]
    return r[0]["lzw_financetransactionid"] if r else None


def create(body, category):
    body = dict(body, **{"lzw_Category@odata.bind": f"/lzw_financecategories({category})"})
    eid = body["lzw_PaidFrom@odata.bind"].split("(")[1].rstrip(")")
    done = lambda: bool(existing_ft(body["lzw_name"], body["lzw_transactiondate"], body["lzw_amount"], eid))
    _, h = dv.post("lzw_financetransactions", body, done=done)
    return dv.new_id(h) or existing_ft(body["lzw_name"], body["lzw_transactiondate"], body["lzw_amount"], eid)


if __name__ == "__main__":
    main()
