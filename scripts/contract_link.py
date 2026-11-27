"""Link the contract invoice statements (contract_lines.py) to their Finance Transactions and transfer pairs, and
create the Planned Transactions for what is still owed. See "Contract invoices" in docs/statement-import.md.
Dry run by default; --apply writes, under the reconciliation lock.

    python scripts/contract_link.py <payments json> [--apply]

<payments json> is the file given to contract_lines.py, plus the due dates of what is owed:
    "owed": {"gst": "2027-02-28", "tax": "2027-11-24"}

1. Salary: per invoice, the Income "Salary" FT of Delta Insights on Paid On (+-1 day) with the Total Amount is reused:
   its match to the bank line is deleted, that bank line becomes the Transfer Counterpart of "Paid to bank", Paid From
   becomes the employer. Without one, a new Salary FT (Source Import); "Paid to bank" pairs with an unmatched bank
   line of the same amount within 3 days if there is exactly one, else it stays Unmatched (before the bank history).
2. GST: per "GST paid" line, the Expense FT of Payee ATO with that amount on that day (+-1) is reused the same way
   (its Flex Saver BPAY line becomes the Transfer Counterpart); without one, a new "GST Payment (for <months> income)"
   FT, Paid From Flex Saver, no bank line. Matched: the quarter's "GST - <month>" lines and the rounding line.
3. Income tax: per "Income tax paid - <fy>" line, the Expense "Income Tax" FT with that amount on that day is reused
   (its AMEX line becomes the counterpart); without one, a new one (Payee Australian Taxation Office, no Paid From,
   Needs Details). Matched: the "Income Tax - <month>" lines whose Notes name that year.
4. Owed: the GST lines no payment covers and the tax lines from Est. Tax get one Planned Transaction each
   (GST: Manual, Flex Saver; tax: Estimated), Category Tax, due on the "owed" dates. Link them by hand
   (split_match.py) once the flow has created their Finance Transactions.
"""
import datetime as dt
import json
import sys

import dv
import lock
import spec
from recalc import rollup

O = spec.OPT
APPLY = "--apply" in sys.argv
INCOME, EXPENSE, IMPORT = O + 1, O, O + 2
MANUAL, CONFIRMED = O + 3, O + 1
L_UNMATCHED, L_MATCHED, L_TRANSFER = O, O + 2, O + 3
RECONCILED = O + 2
PT_MANUAL, PT_ESTIMATED = O + 1, O + 2
NOW = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def q(s):
    return s.replace("'", "''")


def day(d, n):
    return (dt.date.fromisoformat(d[:10]) + dt.timedelta(days=n)).isoformat()


class Ctx:
    def __init__(self):
        accts = {a["lzw_name"]: a["lzw_bankaccountid"] for a in dv.get_all("lzw_bankaccounts?$select=lzw_name")}
        self.emp, self.flex = accts["Delta Insights"], accts["ANZ Plus Flex Saver"]
        cats = {c["lzw_name"]: c["lzw_financecategoryid"] for c in dv.get_all("lzw_financecategories?$select=lzw_name")}
        self.c_salary, self.c_tax = cats["Salary and Contract Income"], cats["Tax"]
        self.aud = dv.get("transactioncurrencies?$select=transactioncurrencyid&$filter=isocurrencycode eq 'AUD'")[
            "value"][0]["transactioncurrencyid"]
        sts = dv.get_all("lzw_bankstatements?$select=lzw_bankstatementid,lzw_name&$filter=_lzw_bankaccount_value eq "
                         f"{self.emp} and (startswith(lzw_name,'DeltaInsights_Invoice_') or "
                         "startswith(lzw_name,'DeltaInsights_ATO_'))")
        self.lines = []
        for st in sorted(sts, key=lambda s: s["lzw_name"]):
            for l in dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_amount,"
                                "lzw_transactiondate,lzw_status,lzw_notes&$filter=_lzw_bankstatement_value eq "
                                f"{st['lzw_bankstatementid']} and statecode eq 0&$orderby=lzw_linenumber"):
                l["kind"], _, l["rest"] = l["lzw_name"].partition(" - ")
                self.lines.append(l)
        self.matches, self.pairs, self.fts = [], [], []  # (line, ft key), (line, bank line id), FTs to finish

    def of(self, kind):
        return [l for l in self.lines if l["kind"] == kind]


def find_ft(filt, date):
    return dv.get_all("lzw_financetransactions?$select=lzw_financetransactionid,lzw_name,lzw_amount,"
                      f"lzw_transactiondate&$filter={filt} and lzw_transactiondate ge {day(date, -1)} and "
                      f"lzw_transactiondate lt {day(date, 2)}")


def bank_matches(ftid, emp):
    ms = dv.get_all("lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid,_lzw_bankstatementline_value&$filter="
                    f"_lzw_financetransaction_value eq {ftid}")
    out = []
    for m in ms:
        l = dv.get(f"lzw_bankstatementlines({m['_lzw_bankstatementline_value']})?$select=lzw_name,lzw_amount,"
                   "_lzw_bankaccount_value")
        if l["_lzw_bankaccount_value"] != emp:
            out.append((m["lzw_reconciliationmatchid"], m["_lzw_bankstatementline_value"], l))
    return out


def plan_ft(ctx, label, filt, date, amount, new_body, line):
    """Reuse the FT that filt finds (moving its bank match to a transfer pair with line) or plan a new one."""
    c = find_ft(filt, date)
    if len(c) > 1:
        print(f"    SKIPPED {label}: {len(c)} transactions fit")
        return None
    ft = {"label": label, "id": c[0]["lzw_financetransactionid"] if c else None, "body": new_body, "old": [],
          "amount": amount}
    if c:
        ft["old"] = bank_matches(ft["id"], ctx.emp)
        for _, lid, bl in ft["old"]:
            if line is not None:
                ctx.pairs.append((line, lid))
        print(f"    {label}: reuse FT {c[0]['lzw_name']} {c[0]['lzw_amount']:,.2f} ({c[0]['lzw_transactiondate'][:10]}); "
              + (", ".join(f"bank line {bl['lzw_name'][:45]} {bl['lzw_amount']:,.2f} -> transfer" for _, _, bl in ft["old"])
                 or "no bank match"))
    else:
        print(f"    {label}: new FT {new_body['lzw_name']} {amount:,.2f} on {date[:10]}")
    ctx.fts.append(ft)
    return ft


def plan(ctx, pay):
    open_ = lambda l: l["lzw_status"] not in (L_MATCHED, L_TRANSFER)
    # 1. Salary
    print("Salary")
    for inv in ctx.of("Invoice"):
        if not open_(inv):
            continue
        m = inv["rest"].split(" - ")[0]
        date, total = inv["lzw_transactiondate"][:10], inv["lzw_amount"]
        to_bank = next(l for l in ctx.of("Paid to bank") if l["rest"] == m)
        body = {"lzw_name": "Salary", "lzw_type": INCOME, "lzw_amount": total, "lzw_payee": "Delta Insights",
                "lzw_transactiondate": f"{date}T02:00:00Z", "lzw_source": IMPORT, "category": ctx.c_salary,
                "paidfrom": ctx.emp, "lzw_notes": f"Contract invoice {m} incl GST (Fiscal Planner sheet). GST and "
                "income tax are lines on the Delta Insights account; the payment is a Transfer to the bank."}
        ft = plan_ft(ctx, f"{m} Salary", f"lzw_type eq {INCOME} and lzw_name eq 'Salary' and lzw_payee eq "
                     f"'Delta Insights' and lzw_amount eq {total}", date, total, body, to_bank)
        if ft is None:
            continue
        ctx.matches.append((inv, ft))
        if not ft["old"] and open_(to_bank):
            c = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name&$filter=lzw_amount eq "
                           f"{total} and _lzw_bankaccount_value ne {ctx.emp} and statecode eq 0 and lzw_status eq "
                           f"{L_UNMATCHED} and lzw_transactiondate ge {day(date, -3)} and lzw_transactiondate le {day(date, 3)}")
            if len(c) == 1:
                ctx.pairs.append((to_bank, c[0]["lzw_bankstatementlineid"]))
                print(f"        Paid to bank <-> {c[0]['lzw_name'][:60]}")
            else:
                print(f"        Paid to bank: {len(c)} bank lines fit, left Unmatched")
    # 2. GST
    print("GST")
    gst_lines = {l["rest"]: l for l in ctx.of("GST")}
    covered = set()
    for paid in ctx.of("GST paid"):
        per = paid["rest"]
        a, b = per.split("..")
        months = [l for k, l in gst_lines.items() if a <= k <= b]
        covered.update(l["lzw_bankstatementlineid"] for l in months)
        rounding = [l for l in ctx.of("GST rounding") if l["rest"] == per]
        targets = [l for l in months + rounding if open_(l)]
        if not targets and not open_(paid):
            continue
        date, amt = paid["lzw_transactiondate"][:10], paid["lzw_amount"]
        body = {"lzw_name": f"GST Payment (for {a} to {b} income)", "lzw_type": EXPENSE, "lzw_amount": amt,
                "lzw_payee": "ATO", "lzw_transactiondate": f"{date}T02:00:00Z", "lzw_source": IMPORT,
                "category": ctx.c_tax, "paidfrom": ctx.flex,
                "lzw_notes": f"GST for {a} to {b} (Fiscal Planner sheet). No bank line (before the bank history); "
                             "the date is from the sheet's GST Account Transfer Out Total column."}
        ft = plan_ft(ctx, f"GST {per}", f"lzw_type eq {EXPENSE} and lzw_payee eq 'ATO' and lzw_amount eq {amt}",
                     date, amt, body, paid if open_(paid) else None)
        if ft:
            ctx.matches += [(l, ft) for l in targets]
    owed_gst = [l for l in gst_lines.values() if l["lzw_bankstatementlineid"] not in covered]
    # 3. Income tax
    print("Income tax")
    for paid in ctx.of("Income tax paid"):
        fy = paid["rest"]
        months = [l for l in ctx.of("Income Tax") if (l.get("lzw_notes") or "").startswith(f"{fy} ")]
        targets = [l for l in months if open_(l)]
        if not targets and not open_(paid):
            continue
        date, amt = paid["lzw_transactiondate"][:10], paid["lzw_amount"]
        body = {"lzw_name": "Income Tax", "lzw_type": EXPENSE, "lzw_amount": amt, "lzw_payee": "Australian Taxation Office",
                "lzw_transactiondate": f"{date}T02:00:00Z", "lzw_source": IMPORT, "category": ctx.c_tax,
                "lzw_needsdetails": True, "lzw_notes": f"{fy} income tax (owner). No bank line (before the bank "
                "history); account not known."}
        ft = plan_ft(ctx, f"Income tax {fy} ({len(months)} months)", f"lzw_type eq {EXPENSE} and lzw_name eq "
                     f"'Income Tax' and lzw_amount eq {amt}", date, amt, body, paid if open_(paid) else None)
        if ft:
            ctx.matches += [(l, ft) for l in targets]
    owed_tax = [l for l in ctx.of("Income Tax") if (l.get("lzw_notes") or "").startswith("Est. Tax")]
    # 4. Owed
    print("Owed (Planned Transactions)")
    appts = []
    for ls, key, subject, ptype, paidfrom in (
            (owed_gst, "gst", "GST Payment (for {} income)", PT_MANUAL, ctx.flex),
            (owed_tax, "tax", "Income Tax (for {} income)", PT_ESTIMATED, None)):
        if not ls:
            continue
        ms = sorted(l["rest"] for l in ls)
        per = ms[0] if len(ms) == 1 else f"{ms[0]} to {ms[-1]}"
        amt = round(-sum(l["lzw_amount"] for l in ls), 2)
        subj, due = subject.format(per), pay["owed"][key]
        exists = dv.get(f"appointments?$select=activityid&$filter=subject eq '{q(subj)}'")["value"]
        print(f"    {subj}: {amt:,.2f} due {due}" + (" (exists)" if exists else ""))
        if not exists:
            appts.append(dict(subject=subj, amount=amt, due=due, ptype=ptype, paidfrom=paidfrom,
                              desc=f"Owed on the Delta Insights account (lines {', '.join(ms)}). "
                                   + ("Est. Tax from the Fiscal Planner sheet; correct it when the assessment arrives."
                                      if key == "tax" else "From the Fiscal Planner sheet.")))
    print(f"Plan: {sum(1 for f in ctx.fts if not f['id'])} new FTs, {sum(1 for f in ctx.fts if f['id'])} reused, "
          f"{len(ctx.matches)} matches, {len(ctx.pairs)} transfer pairs, {len(appts)} Planned Transactions")
    return appts


def write(ctx, appts):
    for ft in ctx.fts:
        if ft["id"]:
            for mid, lid, _ in ft["old"]:
                dv.call("DELETE", f"lzw_reconciliationmatchs({mid})")
                dv.patch(f"lzw_bankstatementlines({lid})", {"lzw_status": L_UNMATCHED})
                rollup("lzw_bankstatementlines", lid, "lzw_allocatedamount")
            if ft["body"]["lzw_name"] == "Salary":
                dv.patch(f"lzw_financetransactions({ft['id']})", {
                    "lzw_PaidFrom@odata.bind": f"/lzw_bankaccounts({ctx.emp})", "lzw_notes": ft["body"]["lzw_notes"]})
        else:
            b = {k: v for k, v in ft["body"].items() if k not in ("category", "paidfrom")}
            b["lzw_Category@odata.bind"] = f"/lzw_financecategories({ft['body']['category']})"
            if ft["body"].get("paidfrom"):
                b["lzw_PaidFrom@odata.bind"] = f"/lzw_bankaccounts({ft['body']['paidfrom']})"
            b["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({ctx.aud})"
            filt = (f"lzw_name eq '{q(b['lzw_name'])}' and lzw_transactiondate eq {b['lzw_transactiondate']} "
                    f"and lzw_amount eq {b['lzw_amount']}")
            look = lambda: dv.get(f"lzw_financetransactions?$select=lzw_financetransactionid&$filter={filt}")["value"]
            _, h = dv.post("lzw_financetransactions", b, done=lambda: bool(look()))
            ft["id"] = dv.new_id(h) or look()[0]["lzw_financetransactionid"]
        print(f"    FT {ft['label']}: {ft['id']}", flush=True)
    for line, ft in ctx.matches:
        lid = line["lzw_bankstatementlineid"]
        has = lambda: bool(dv.get("lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter="
                                  f"_lzw_bankstatementline_value eq {lid}")["value"])
        if not has():
            dv.post("lzw_reconciliationmatchs", {
                "lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({lid})",
                "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({ft['id']})",
                "lzw_allocatedamount": line["lzw_amount"], "lzw_matchmethod": MANUAL, "lzw_matchstatus": CONFIRMED,
                "lzw_confirmedon": NOW, "lzw_aireasoning": "contract_link.py"}, done=has)
        dv.patch(f"lzw_bankstatementlines({lid})", {"lzw_status": L_MATCHED})
        rollup("lzw_bankstatementlines", lid, "lzw_allocatedamount")
    for ft in ctx.fts:
        rollup("lzw_financetransactions", ft["id"], "lzw_actualamount")
        tot = round(sum(l["lzw_amount"] for l, f in ctx.matches if f is ft), 2)
        if abs(tot) == round(ft["amount"], 2):
            dv.patch(f"lzw_financetransactions({ft['id']})", {"lzw_reconciliationstatus": RECONCILED})
        else:
            print(f"    NOT RECONCILED {ft['label']}: lines {tot:,.2f} vs {ft['amount']:,.2f}")
    for line, other in ctx.pairs:
        a = line["lzw_bankstatementlineid"]
        for x, y in ((a, other), (other, a)):
            dv.patch(f"lzw_bankstatementlines({x})", {"lzw_status": L_TRANSFER,
                     "lzw_TransferCounterpart@odata.bind": f"/lzw_bankstatementlines({y})"})
    for ap in appts:
        start = f"{ap['due']}T02:00:00Z"
        b = {"subject": ap["subject"], "scheduledstart": start,
             "scheduledend": f"{ap['due']}T02:30:00Z", "lzw_amount": ap["amount"], "lzw_paymenttype": ap["ptype"],
             "description": ap["desc"], "lzw_FinanceCategory_Appointment@odata.bind":
                 f"/lzw_financecategories({ctx.c_tax})",
             "transactioncurrencyid@odata.bind": f"/transactioncurrencies({ctx.aud})"}
        if ap["paidfrom"]:
            b["lzw_PaidFrom_Appointment@odata.bind"] = f"/lzw_bankaccounts({ap['paidfrom']})"
        dv.post("appointments", b, done=lambda: bool(dv.get(
            f"appointments?$select=activityid&$filter=subject eq '{q(ap['subject'])}'")["value"]))
        print(f"    Planned Transaction {ap['subject']} created")
    print("written")


def main():
    pay = json.load(open(sys.argv[1], encoding="utf-8"))
    ctx = Ctx()
    if not APPLY:
        plan(ctx, pay)
        print("(dry run)")
        return
    with lock.held("contract_link.py"):
        write(ctx, plan(ctx, pay))


if __name__ == "__main__":
    main()
