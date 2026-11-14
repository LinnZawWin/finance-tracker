"""Recalculate rollup columns, then fill the plain columns that are "maintained by script".

Run after writing Reconciliation Matches or Finance Asset Links:
    python scripts/recalc.py            all active rows
    python scripts/recalc.py --days 60  only rows modified in the last 60 days

Maintained by script (plain money columns, see docs/schema.md):
    Bank Statement Line.Unallocated Amount = Amount - Allocated Amount
    Finance Transaction.Actual Cost        = -Actual Amount for Expense, else Actual Amount
    Finance Transaction.Partner Share      = Actual Cost x 0.5 (Shared with Partner), Actual Cost (All for Partner), else 0
    Finance Transaction.My Cost            = Actual Cost - Partner Share
    Finance Asset.Net Cost                 = Total Cost - Sale Proceeds
"""
import datetime
import sys

import dv
import spec

O = spec.OPT


def rollup(entity_set, rid, field):
    """Force a rollup column to recalculate and return its value."""
    r = dv.get(f"CalculateRollupField(Target=@t,FieldName=@f)?@t={{'@odata.id':'{entity_set}({rid})'}}&@f='{field}'")
    return r.get(field)


def rows(entity_set, select, days):
    flt = "statecode eq 0"
    if days:
        since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        flt += f" and modifiedon ge {since}"
    return dv.get_all(f"{entity_set}?$select={select}&$filter={flt}")


def r2(x):
    return None if x is None else round(x, 2)


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else None
    n = 0
    for r in rows("lzw_bankstatements", "lzw_bankstatementid", days):
        rollup("lzw_bankstatements", r["lzw_bankstatementid"], "lzw_linecount")
        n += 1
    for r in rows("lzw_bankstatementlines", "lzw_bankstatementlineid,lzw_amount,lzw_unallocatedamount", days):
        rid = r["lzw_bankstatementlineid"]
        allocated = rollup("lzw_bankstatementlines", rid, "lzw_allocatedamount") or 0
        value = r2((r.get("lzw_amount") or 0) - allocated) if r.get("lzw_amount") is not None else None
        if value != r.get("lzw_unallocatedamount"):
            dv.patch(f"lzw_bankstatementlines({rid})", {"lzw_unallocatedamount": value})
        n += 1
    for r in rows("lzw_financetransactions",
                  "lzw_financetransactionid,lzw_type,lzw_sharetype,lzw_actualcost,lzw_partnershare,lzw_mycost", days):
        rid = r["lzw_financetransactionid"]
        actual = rollup("lzw_financetransactions", rid, "lzw_actualamount")
        if actual is None:
            cost = share = mine = None
        else:
            cost = -actual if r.get("lzw_type") == O else actual
            share = cost * 0.5 if r.get("lzw_sharetype") == O + 1 else cost if r.get("lzw_sharetype") == O + 2 else 0
            mine = cost - share
        new = {"lzw_actualcost": r2(cost), "lzw_partnershare": r2(share), "lzw_mycost": r2(mine)}
        if any(new[k] != r.get(k) for k in new):
            dv.patch(f"lzw_financetransactions({rid})", new)
        n += 1
    for r in rows("lzw_financeassets", "lzw_financeassetid,lzw_netcost", days):
        rid = r["lzw_financeassetid"]
        total = rollup("lzw_financeassets", rid, "lzw_totalcost") or 0
        sale = rollup("lzw_financeassets", rid, "lzw_saleproceeds") or 0
        if r2(total - sale) != r.get("lzw_netcost"):
            dv.patch(f"lzw_financeassets({rid})", {"lzw_netcost": r2(total - sale)})
        n += 1
    print(f"recalculated {n} rows")


if __name__ == "__main__":
    main()
