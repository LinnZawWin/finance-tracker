"""Weekly cash forecast (read only).

Weeks run Monday to Sunday (Brisbane). Prints the previous, current and next two weeks:
- the Planned Transactions of each week (income and planned expenses; Transfers to the ATO separately),
- a weekly spending allowance: the average weekly day-to-day spending of the last N complete weeks,
- for the previous and current week, the day-to-day Finance Transactions taken off that allowance,
- the latest balance of each bank account and what is due on AMEX.

Day-to-day spending = Expense Finance Transactions that are not planned bills (categories in PLANNED_CATEGORIES,
or Source Recurring), not part of a trip (Project set), not one-offs (ONE_OFF_CATEGORIES), counted at Amount
(the money that left the account, before any Partner share).

Usage: python scripts/forecast.py [--history-weeks 13] [--today YYYY-MM-DD]
"""
import argparse
import collections
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dv  # noqa: E402

TZ = dt.timedelta(hours=10)  # Brisbane, no daylight saving
EXPENSE, INCOME, TRANSFER = 859130000, 859130001, 859130002
SOURCE_RECURRING = 859130003
# Bills that the Planned Transactions already cover, so they are not part of the allowance.
PLANNED_CATEGORIES = {"Support Payments", "Rent", "Utilities", "Insurance", "Subscriptions", "Fees and Charges",
                      "Investment", "Car Maintenance", "Transport", "Tax", "Salary and Contract Income"}
# Rare, large costs that would distort a weekly average.
ONE_OFF_CATEGORIES = {"Fines", "Parking Fines", "Legal and Professional"}
OPEN = 0


def local(iso):
    return (dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) + TZ).date()


def utc(d):
    return (dt.datetime.combine(d, dt.time()) - TZ).strftime("%Y-%m-%dT%H:%M:%SZ")


def money(x):
    return f"{x:,.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history-weeks", type=int, default=13)
    ap.add_argument("--today")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else (dt.datetime.now(dt.timezone.utc) + TZ).date()
    monday = today - dt.timedelta(days=today.weekday())
    weeks = [monday + dt.timedelta(weeks=i) for i in (-1, 0, 1, 2)]
    hist_start = monday - dt.timedelta(weeks=a.history_weeks)

    cats = {c["lzw_financecategoryid"]: c["lzw_name"] for c in dv.get_all("lzw_financecategories?$select=lzw_name")}
    accounts = {x["lzw_bankaccountid"]: x for x in dv.get_all(
        "lzw_bankaccounts?$select=lzw_name,lzw_shortname,lzw_accounttype&$filter=statecode eq 0")}

    # Day-to-day spending from the start of the history to the end of the current week.
    fts = dv.get_all(
        "lzw_financetransactions?$select=lzw_name,lzw_transactiondate,lzw_amount,lzw_source,_lzw_category_value,"
        f"_lzw_project_value&$filter=statecode eq 0 and lzw_type eq {EXPENSE} and "
        f"lzw_transactiondate ge {utc(hist_start)} and lzw_transactiondate lt {utc(monday + dt.timedelta(weeks=1))}")
    spend = collections.defaultdict(list)
    for f in fts:
        cat = cats.get(f["_lzw_category_value"])
        if f["_lzw_project_value"] or f["lzw_source"] == SOURCE_RECURRING:
            continue
        if cat in PLANNED_CATEGORIES or cat in ONE_OFF_CATEGORIES:
            continue
        d = local(f["lzw_transactiondate"])
        spend[d - dt.timedelta(days=d.weekday())].append((d, f["lzw_name"], cat, f["lzw_amount"] or 0))
    hist = [sum(x[3] for x in spend.get(hist_start + dt.timedelta(weeks=i), [])) for i in range(a.history_weeks)]
    # A week with no day-to-day spending was spent on a trip (its costs carry a Project): leave it out.
    used = [h for h in hist if h > 0] or [0.0]
    allowance = round(sum(used) / len(used), 2)

    # Planned Transactions in the four weeks (open, and completed ones for the past days).
    end = weeks[-1] + dt.timedelta(weeks=1)
    appts = dv.get_all(
        "appointments?$select=subject,scheduledstart,lzw_amount,statecode,_lzw_transferto_value"
        f"&$filter=lzw_amount ne null and statecode ne 2 and scheduledstart ge {utc(weeks[0])} "
        f"and scheduledstart lt {utc(end)}&$orderby=scheduledstart")
    planned = collections.defaultdict(list)
    for p in appts:
        d = local(p["scheduledstart"])
        planned[d - dt.timedelta(days=d.weekday())].append(p)

    print(f"Today {today:%a %d %b %Y}. Weekly allowance {money(allowance)} = average day-to-day spending of the "
          f"{len(used)} of the {a.history_weeks} weeks {hist_start:%d %b} to {monday - dt.timedelta(days=1):%d %b %Y} "
          f"that had any (lowest {money(min(used))}, highest {money(max(used))}).")
    print("   weeks: " + ", ".join(f"{hist_start + dt.timedelta(weeks=i):%d %b} {money(h)}" for i, h in enumerate(hist)))
    for w in weeks:
        label = {-1: "Previous", 0: "Current", 1: "Next", 2: "Following"}[(w - monday).days // 7]
        print(f"\n== {label} week: {w:%a %d %b} to {w + dt.timedelta(days=6):%a %d %b %Y}")
        inc = exp = xfer = 0.0
        for p in planned[w]:
            amt = p["lzw_amount"]
            done = "" if p["statecode"] == OPEN else " (done)"
            kind = "transfer" if p["_lzw_transferto_value"] else ("income" if amt < 0 else "expense")
            if kind == "transfer":
                xfer += amt
            elif kind == "income":
                inc += -amt
            else:
                exp += amt
            print(f"   {local(p['scheduledstart']):%a %d %b}  {kind:8} {money(abs(amt)):>12}  {p['subject']}{done}")
        if not planned[w]:
            print("   no Planned Transactions")
        spent = sum(x[3] for x in spend.get(w, [])) if w <= monday else 0.0
        if w <= monday:
            print(f"   day-to-day spent {money(spent)} of {money(allowance)}: "
                  f"{money(abs(allowance - spent))} {'left' if spent <= allowance else 'over'}")
            for d, name, cat, amt in sorted(spend.get(w, []), key=lambda x: -x[3])[:5]:
                print(f"      largest: {d:%a %d %b} {money(amt):>9}  {name} ({cat})")
        left = max(allowance - spent, 0.0) if w == monday else (0.0 if w < monday else allowance)
        net = inc - exp - (spent if w <= monday else 0.0) - left
        print(f"   income {money(inc)}, planned expenses {money(exp)}, "
              f"day-to-day {money(spent if w <= monday else allowance)}{' + ' + money(left) + ' still allowed' if w == monday else ''}, "
              f"net {money(net)}" + (f"; to the ATO {money(xfer)}" if xfer else ""))

    # Balances: the closing balance of each account's latest statement that has one.
    print("\n== Balances (latest statement with a closing balance)")
    stmts = dv.get_all("lzw_bankstatements?$select=lzw_name,lzw_periodend,lzw_closingbalance,_lzw_bankaccount_value"
                       "&$filter=lzw_closingbalance ne null&$orderby=lzw_periodend desc")
    latest = {}
    for s in stmts:
        latest.setdefault(s["_lzw_bankaccount_value"], s)
    total = 0.0
    for aid, s in sorted(latest.items(), key=lambda x: accounts.get(x[0], {}).get("lzw_name", "")):
        acc = accounts.get(aid)
        if not acc or acc["lzw_accounttype"] in (859130006,) or s["lzw_closingbalance"] == 0:
            continue
        bal = s["lzw_closingbalance"]
        if acc["lzw_accounttype"] != 859130005:  # super is locked: not counted in the total
            total += bal
        print(f"   {acc['lzw_name']:32} {money(bal):>12}  as of {s['lzw_periodend']}"
              + ("  (not in total: locked)" if acc["lzw_accounttype"] == 859130005 else ""))
    print(f"   {'Total (AUD rows, ANZ NZ Go in NZD)':32} {money(total):>12}")

    # AMEX: the last closed statement (period ending on the 13th) less the payments since, and the current cycle.
    amex = next(k for k, v in accounts.items() if v["lzw_shortname"] == "AMEX")
    closed = [s for s in stmts if s["_lzw_bankaccount_value"] == amex and " to " not in s["lzw_name"]]
    if closed:
        last = closed[0]
        lines = dv.get_all(f"lzw_bankstatementlines?$select=lzw_name,lzw_amount,lzw_transactiondate&$filter="
                           f"_lzw_bankaccount_value eq {amex} and lzw_transactiondate gt {last['lzw_periodend']}")
        paid = sum(x["lzw_amount"] for x in lines if x["lzw_amount"] > 0)  # payments, refunds and credits
        due = -last["lzw_closingbalance"] - paid
        cur = latest.get(amex)
        print(f"\n== AMEX\n   statement to {last['lzw_periodend']}: {money(-last['lzw_closingbalance'])}, "
              f"payments and credits since {money(paid)}, still due {money(max(due, 0))}")
        if cur and cur is not last:
            print(f"   balance as of {cur['lzw_periodend']}: {money(-cur['lzw_closingbalance'])} "
                  f"(new charges go on the statement closing on the 13th)")


if __name__ == "__main__":
    main()
