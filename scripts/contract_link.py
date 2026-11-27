"""Link the contract invoice statements (contract_lines.py) to their Finance Transactions and transfer pairs, and
create the Planned Transactions for what is still owed. See "Contract invoices" in docs/statement-import.md.
Dry run by default; --apply writes, under the reconciliation lock.

    python scripts/contract_link.py <payments json> [--apply]

<payments json> is the file given to contract_lines.py, plus the due dates of what is owed:
    "owed": {"gst": "2027-02-28", "tax": "2027-11-24"}

Net only (owner, 2026-11-27): the Salary FT is the net, like a split bill. GST and income tax have no FTs.
1. Salary: per invoice, the Income "Salary" FT of Delta Insights on Paid On (+-1 day) with the Total Amount or the
   net is reused: its match to the bank line is deleted, that bank line becomes the Transfer Counterpart of "Paid to
   bank", Paid From becomes the employer, Amount the net. Without one, a new Salary FT (Source Import); "Paid to bank"
   pairs with an unmatched bank line of the same amount within 3 days if there is exactly one, else it stays Unmatched
   (before the bank history). Matched: the month's Invoice (+), GST (-) and Income Tax (-) lines, so Actual Amount =
   Amount = Total - GST - income tax. A quarter's "GST rounding" line goes to the Salary FT of its last month.
2. ATO payments: each "GST paid" and "Income tax paid" line pairs as a Transfer with the bank line of the opposite
   amount within 3 days (Flex Saver BPAY, AMEX) when there is exactly one; an Expense FT matched only to that bank
   line (entered from a note) is deleted first. Without a bank line it stays Unmatched (before the bank history).
3. Owed: the GST lines no payment covers and the tax lines from Est. Tax get one Planned Transaction each
   (GST: Manual, Flex Saver; tax: Estimated), Transfer To Delta Insights, no Category, due on the "owed" dates.
   The flow makes them Transfer FTs; match each to its bank payment line and pair that line with a new
   `DeltaInsights_ATO_<date>` line (Status Transfer).
"""
import datetime as dt
import json
import sys

import dv
import lock
import spec
from recalc import rollup_op

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
        self.drops = []  # (match id, FT id, name): note FTs for an ATO payment, deleted

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


def bank_payment(ctx, line):
    """The one bank line paying this ATO line (opposite amount, another account, within 3 days, not a Transfer)."""
    d = line["lzw_transactiondate"][:10]
    c = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name,lzw_status&$filter=lzw_amount eq "
                   f"{-line['lzw_amount']} and _lzw_bankaccount_value ne {ctx.emp} and statecode eq 0 and lzw_status ne "
                   f"{L_TRANSFER} and lzw_transactiondate ge {day(d, -3)} and lzw_transactiondate le {day(d, 3)}")
    if len(c) != 1:
        return None, []
    ms = dv.get_all("lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid,_lzw_financetransaction_value&$filter="
                    f"_lzw_bankstatementline_value eq {c[0]['lzw_bankstatementlineid']}")
    drop = []
    for m in ms:  # an Expense FT entered from a note for the payment: deleted when this is its only match
        fid = m["_lzw_financetransaction_value"]
        others = dv.get(f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter="
                        f"_lzw_financetransaction_value eq {fid}")["value"]
        ft = dv.get(f"lzw_financetransactions({fid})?$select=lzw_name,lzw_type,lzw_amount")
        if len(others) != 1 or ft["lzw_type"] != EXPENSE:
            print(f"    SKIPPED {line['lzw_name']}: bank line is matched to {ft['lzw_name']} (check by hand)")
            return None, []
        drop.append((m["lzw_reconciliationmatchid"], fid, ft["lzw_name"]))
    return c[0], drop


def plan(ctx, pay):
    open_ = lambda l: l["lzw_status"] not in (L_MATCHED, L_TRANSFER)
    # 1. Salary (net)
    print("Salary")
    for inv in ctx.of("Invoice"):
        m = inv["rest"].split(" - ")[0]
        parts = [inv] + [l for l in ctx.of("GST") + ctx.of("Income Tax") if l["rest"] == m]
        parts += [l for l in ctx.of("GST rounding") if l["rest"].split("..")[1] == m]  # the quarter's last month
        todo = [l for l in parts if open_(l)]
        if not todo:
            continue
        date, total = inv["lzw_transactiondate"][:10], inv["lzw_amount"]
        net = round(sum(l["lzw_amount"] for l in parts), 2)
        est = any((l.get("lzw_notes") or "").startswith("Est. Tax") for l in parts)
        to_bank = next(l for l in ctx.of("Paid to bank") if l["rest"] == m)
        body = {"lzw_name": "Salary", "lzw_type": INCOME, "lzw_amount": net, "lzw_payee": "Delta Insights",
                "lzw_transactiondate": f"{date}T02:00:00Z", "lzw_source": IMPORT, "category": ctx.c_salary,
                "paidfrom": ctx.emp, "lzw_notes": net_note(m, total, parts, est)}
        ft = plan_ft(ctx, f"{m} Salary", f"lzw_type eq {INCOME} and lzw_name eq 'Salary' and lzw_payee eq "
                     f"'Delta Insights' and (lzw_amount eq {total} or lzw_amount eq {net})", date, net, body,
                     to_bank if open_(to_bank) else None)
        if ft is None:
            continue
        ctx.matches += [(l, ft) for l in todo]
        if not ft["old"] and open_(to_bank):
            c = dv.get_all("lzw_bankstatementlines?$select=lzw_bankstatementlineid,lzw_name&$filter=lzw_amount eq "
                           f"{total} and _lzw_bankaccount_value ne {ctx.emp} and statecode eq 0 and lzw_status eq "
                           f"{L_UNMATCHED} and lzw_transactiondate ge {day(date, -3)} and lzw_transactiondate le {day(date, 3)}")
            if len(c) == 1:
                ctx.pairs.append((to_bank, c[0]["lzw_bankstatementlineid"]))
                print(f"        Paid to bank <-> {c[0]['lzw_name'][:60]}")
            else:
                print(f"        Paid to bank: {len(c)} bank lines fit, left Unmatched")
    # 2. ATO payments: Transfers from the bank
    print("ATO payments")
    gst_lines = {l["rest"]: l for l in ctx.of("GST")}
    covered = set()
    for paid in ctx.of("GST paid") + ctx.of("Income tax paid"):
        if paid["kind"] == "GST paid":
            a, b = paid["rest"].split("..")
            covered.update(l["lzw_bankstatementlineid"] for k, l in gst_lines.items() if a <= k <= b)
        if not open_(paid):
            continue
        bl, drop = bank_payment(ctx, paid)
        if bl is None:
            print(f"    {paid['lzw_name']} {paid['lzw_amount']:,.2f}: no single bank line, left Unmatched")
            continue
        ctx.pairs.append((paid, bl["lzw_bankstatementlineid"]))
        ctx.drops += drop
        print(f"    {paid['lzw_name']} <-> {bl['lzw_name'][:50]}"
              + "".join(f"; delete FT {n}" for _, _, n in drop))
    owed_gst = [l for l in gst_lines.values() if l["lzw_bankstatementlineid"] not in covered]
    owed_tax = [l for l in ctx.of("Income Tax") if (l.get("lzw_notes") or "").startswith("Est. Tax")]
    # 3. Owed
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
                              desc=f"Transfer to the Delta Insights account: owed there (lines {', '.join(ms)}), "
                                   "already taken off the net Salary FTs. "
                                   + ("Est. Tax from the Fiscal Planner sheet; correct it when the assessment arrives."
                                      if key == "tax" else "From the Fiscal Planner sheet.")))
    print(f"Plan: {sum(1 for f in ctx.fts if not f['id'])} new FTs, {sum(1 for f in ctx.fts if f['id'])} reused, "
          f"{len(ctx.matches)} matches, {len(ctx.pairs)} transfer pairs, {len(ctx.drops)} FTs deleted, "
          f"{len(appts)} Planned Transactions")
    return appts


def net_note(m, total, parts, est):
    gst = -sum(l["lzw_amount"] for l in parts if l["kind"] in ("GST", "GST rounding"))
    tax = -sum(l["lzw_amount"] for l in parts if l["kind"] == "Income Tax")
    note = (f"Contract invoice {m}, net (Fiscal Planner sheet): {total:,.2f} incl GST less GST {gst:,.2f} and income "
            f"tax {tax:,.2f}, matched to those lines on the Delta Insights account. The payment is a Transfer to the "
            "bank; the GST and tax payments are Transfers into the Delta Insights account.")
    if est:
        note += (" The income tax is the sheet's estimate (Est. Tax) for now; replace it with the year's assessment "
                 "(split by Net Amount) when it arrives.")
    return note


def has_match(lid):
    return bool(dv.get(f"lzw_reconciliationmatchs?$select=lzw_reconciliationmatchid&$filter="
                       f"_lzw_bankstatementline_value eq {lid}")["value"])


def write(ctx, appts):
    """Every step in dv.batch requests (about 25 operations each) instead of one request per write."""
    # 1. Moved bank matches: delete the match, the bank line becomes Unmatched (then a Transfer in step 4).
    ops = []
    for ft in ctx.fts:
        for mid, lid, _ in ft["old"]:
            ops += [("DELETE", f"lzw_reconciliationmatchs({mid})", None),
                    ("PATCH", f"lzw_bankstatementlines({lid})", {"lzw_status": L_UNMATCHED})]
    for mid, fid, _ in ctx.drops:  # note FTs for an ATO payment: the bank line becomes a Transfer in step 4
        ops += [("DELETE", f"lzw_reconciliationmatchs({mid})", None), ("DELETE", f"lzw_financetransactions({fid})", None)]
    gone = lambda chunk: not dv.exists(next(p for m, p, _ in chunk if m == "DELETE"))
    dv.batch(ops, done=gone)
    for _, _, n in ctx.drops:
        print(f"    deleted FT {n}")
    # 2. Finance Transactions: reused Salary FTs move to the employer; new ones are created.
    ops, new = [], []
    for ft in ctx.fts:
        if ft["id"]:
            if ft["body"]["lzw_name"] == "Salary":
                ops.append(("PATCH", f"lzw_financetransactions({ft['id']})", {
                    "lzw_PaidFrom@odata.bind": f"/lzw_bankaccounts({ctx.emp})", "lzw_notes": ft["body"]["lzw_notes"],
                    "lzw_amount": ft["amount"]}))
            continue
        b = {k: v for k, v in ft["body"].items() if k not in ("category", "paidfrom")}
        b["lzw_Category@odata.bind"] = f"/lzw_financecategories({ft['body']['category']})"
        if ft["body"].get("paidfrom"):
            b["lzw_PaidFrom@odata.bind"] = f"/lzw_bankaccounts({ft['body']['paidfrom']})"
        b["transactioncurrencyid@odata.bind"] = f"/transactioncurrencies({ctx.aud})"
        ft["look"] = (f"lzw_financetransactions?$select=lzw_financetransactionid&$filter=lzw_name eq "
                      f"'{q(b['lzw_name'])}' and lzw_transactiondate eq {b['lzw_transactiondate']} and "
                      f"lzw_amount eq {b['lzw_amount']}")
        ops.append(("POST", "lzw_financetransactions", b))
        new.append((len(ops) - 1, ft))
    looks = {id(b): ft["look"] for (_, _, b), (_, ft) in zip([ops[n] for n, _ in new], new)}
    landed = lambda chunk: bool(dv.get(looks[id(next(b for m, _, b in chunk if m == "POST"))])["value"])
    res = dv.batch(ops, done=landed)
    for n, ft in new:
        ft["id"] = dv.new_id(res[n][2]) or dv.get(ft["look"])["value"][0]["lzw_financetransactionid"]
    for ft in ctx.fts:
        print(f"    FT {ft['label']}: {ft['id']}")
    # 3. Matches (a line that has one already is skipped) and the lines Matched.
    ops, ids, matched = [], sorted({l["lzw_bankstatementlineid"] for l, _ in ctx.matches}), set()
    for i in range(0, len(ids), 40):  # the lines that have a match already, 40 per query
        flt = " or ".join(f"_lzw_bankstatementline_value eq {x}" for x in ids[i:i + 40])
        matched |= {m["_lzw_bankstatementline_value"] for m in dv.get_all(
            f"lzw_reconciliationmatchs?$select=_lzw_bankstatementline_value&$filter={flt}")}
    for line, ft in ctx.matches:
        lid = line["lzw_bankstatementlineid"]
        if lid not in matched:
            ops.append(("POST", "lzw_reconciliationmatchs", {
                "lzw_BankStatementLine@odata.bind": f"/lzw_bankstatementlines({lid})",
                "lzw_FinanceTransaction@odata.bind": f"/lzw_financetransactions({ft['id']})",
                "lzw_allocatedamount": line["lzw_amount"], "lzw_matchmethod": MANUAL, "lzw_matchstatus": CONFIRMED,
                "lzw_confirmedon": NOW, "lzw_aireasoning": "contract_link.py"}))
        ops.append(("PATCH", f"lzw_bankstatementlines({lid})", {"lzw_status": L_MATCHED}))
    first_line = lambda chunk: next(b for m, _, b in chunk if m == "POST")[
        "lzw_BankStatementLine@odata.bind"].split("(")[1].rstrip(")")
    dv.batch(ops, done=lambda chunk: has_match(first_line(chunk)))
    print(f"    {len(ctx.matches)} matches")
    # 4. Reconciliation status, transfer pairs, then the rollups of every line and FT touched.
    ops = []
    for ft in ctx.fts:
        tot = round(sum(l["lzw_amount"] for l, f in ctx.matches if f is ft), 2)
        if not tot:  # nothing new for it in this run
            continue
        if abs(tot) == round(ft["amount"], 2):
            ops.append(("PATCH", f"lzw_financetransactions({ft['id']})", {"lzw_reconciliationstatus": RECONCILED}))
        else:
            print(f"    NOT RECONCILED {ft['label']}: lines {tot:,.2f} vs {ft['amount']:,.2f}")
    for line, other in ctx.pairs:
        a = line["lzw_bankstatementlineid"]
        for x, y in ((a, other), (other, a)):
            ops.append(("PATCH", f"lzw_bankstatementlines({x})", {
                "lzw_status": L_TRANSFER, "lzw_TransferCounterpart@odata.bind": f"/lzw_bankstatementlines({y})"}))
    dv.batch(ops)
    lines = {l["lzw_bankstatementlineid"] for l, _ in ctx.matches} | {o for _, o in ctx.pairs}
    lines |= {lid for ft in ctx.fts for _, lid, _ in ft["old"]}
    dv.batch([rollup_op("lzw_bankstatementlines", l, "lzw_allocatedamount") for l in sorted(lines)]
             + [rollup_op("lzw_financetransactions", ft["id"], "lzw_actualamount") for ft in ctx.fts])
    print(f"    {len(ctx.pairs)} transfer pairs")
    # 5. Planned Transactions for what is owed.
    ops = []
    for ap in appts:
        b = {"subject": ap["subject"], "scheduledstart": f"{ap['due']}T02:00:00Z",
             "scheduledend": f"{ap['due']}T02:30:00Z", "lzw_amount": ap["amount"], "lzw_paymenttype": ap["ptype"],
             "description": ap["desc"],
             "lzw_TransferTo_Appointment@odata.bind": f"/lzw_bankaccounts({ctx.emp})",
             "transactioncurrencyid@odata.bind": f"/transactioncurrencies({ctx.aud})"}
        if ap["paidfrom"]:
            b["lzw_PaidFrom_Appointment@odata.bind"] = f"/lzw_bankaccounts({ap['paidfrom']})"
        ops.append(("POST", "appointments", b))
    subj = lambda chunk: q(next(b for m, _, b in chunk if m == "POST")["subject"])
    dv.batch(ops, done=lambda chunk: bool(dv.get(f"appointments?$select=activityid&$filter=subject eq "
                                                 f"'{subj(chunk)}'")["value"]))
    for ap in appts:
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
