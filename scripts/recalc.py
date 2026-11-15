"""Recalculate the rollup columns now instead of waiting for the hourly system job.

Run after writing Reconciliation Matches or Finance Asset Links:
    python scripts/recalc.py            all active rows
    python scripts/recalc.py --days 60  only rows modified in the last 60 days

The formula columns (Unallocated Amount, Actual Cost, Partner Share, My Cost, Net Cost) are Power Fx
formula columns; they are worked out when a row is read, so they need no recalculation.
"""
import datetime
import sys

import dv


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


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else None
    targets = [("lzw_bankstatements", "lzw_bankstatementid", ["lzw_linecount"]),
               ("lzw_bankstatementlines", "lzw_bankstatementlineid", ["lzw_allocatedamount"]),
               ("lzw_financetransactions", "lzw_financetransactionid", ["lzw_actualamount"]),
               ("lzw_financeassets", "lzw_financeassetid", ["lzw_totalcost", "lzw_saleproceeds"])]
    n = 0
    for entity_set, id_col, fields in targets:
        for r in rows(entity_set, id_col, days):
            for f in fields:
                rollup(entity_set, r[id_col], f)
            n += 1
    print(f"recalculated rollups on {n} rows")


if __name__ == "__main__":
    main()
