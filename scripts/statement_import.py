"""Create the Bank Statements and their lines from the files written by statement_parse.py and wise_lines.py.

    python scripts/statement_import.py <lines folder>            # dry run: summary per statement
    python scripts/statement_import.py <lines folder> --apply    # write
    add --include-possible to also create the lines flagged as possible duplicates (after checking them)

Each statement is compared with the lines already in Dataverse (statement_compare.compare), so a re-run or
a newer Wise export creates only the shortfall. A statement is matched by name and Bank Account.
Wise: every "Wise*.json" in the folder goes to the Bank Statement "Wise <year>" (1 Jan to 31 Dec).
Mid-cycle exports (statement_parse.py marks them interim) create a placeholder Bank Statement whose Notes start
with "Interim". The next export or the final statement whose period overlaps it updates that same record:
name, period, balances, source type and notes. Its lines stay and only the missing ones are added.
"""
import glob
import sys, json, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dv
import statement_compare as sc

LINES, APPLY, POSSIBLE = sys.argv[1], "--apply" in sys.argv, "--include-possible" in sys.argv
ACCOUNTS = {"x3029": "ANZ Plus Everyday", "x5149": "ANZ Plus Flex Saver", "x3037": "ANZ Plus Growth Saver",
            "AMEX": "AMEX Credit Card", "Kogan": "Kogan Money Black Card", "Wise": "Wise",
            "NZGo": "ANZ NZ Go"}
CURRENCY = {"NZGo": "NZD"}  # statement and line currency when not AUD
SRC = {"PDF": 2, "CSV": 1}
INTERIM = ("Interim: placeholder from a mid-cycle export ({file}), covering {start} to {end}. Updated when the "
           "next export or the statement arrives; balances are those of the export.")
sp = os.path.join(LINES, "_statements.json")
stmts = json.load(open(sp)) if os.path.exists(sp) else []
for w in sorted(glob.glob(os.path.join(LINES, "Wise*.json"))):
    year = min(l["date"] for l in json.load(open(w, encoding="utf-8")))[:4]
    stmts.append(dict(file=os.path.basename(w)[:-5], account="Wise", kind="CSV", start=f"{year}-01-01",
                      end=f"{year}-12-31", opening=None, closing=None, wise_year=year))
acc_id = {a["lzw_name"]: a["lzw_bankaccountid"] for a in dv.get_all("lzw_bankaccounts?$select=lzw_name")}
tot = {"new": 0, "existing": 0, "update": 0, "possible": 0}
for s in stmts:
    acc = ACCOUNTS[s["account"]]
    aid = acc_id[acc]
    cur = sc.currency_id(CURRENCY.get(s["account"], "AUD"))
    lines = json.load(open(os.path.join(LINES, s["file"] + ".json"), encoding="utf-8"))
    for l in lines:
        if s["account"] == "AMEX":
            l.pop("bank_category", None)
    name = f"Wise {s['wise_year']}" if s["account"] == "Wise" else os.path.splitext(s["file"])[0]
    dates = sorted(l["date"] for l in lines)
    existing = sc.load_existing(aid, min(dates[0], s["start"]), max(dates[-1], s["end"])) if lines else []
    res = sc.compare(lines, existing, s["kind"] == "PDF")
    for k in tot:
        tot[k] += len(res[k])
    print(f"{acc:24} {name[:52]:52} in={len(lines):3} new={len(res['new']):3} existing={len(res['existing']):3} "
          f"update={len(res['update'])} possible={len(res['possible'])}")
    for line, row in res["possible"]:
        print(f"    CHECK {line['date']} {line['amount']:.2f} {line['description']} vs {row['amount']} {row['description']}")
    if POSSIBLE:
        res["new"] += [line for line, _ in res["possible"]]
    found = dv.get(f"lzw_bankstatements?$select=lzw_bankstatementid&$filter=lzw_name eq '{name.replace(chr(39), chr(39) * 2)}'"
                   f" and _lzw_bankaccount_value eq {aid}")["value"]
    placeholder = False
    if not found:  # an interim placeholder for an overlapping period becomes this statement
        found = dv.get(f"lzw_bankstatements?$select=lzw_bankstatementid,lzw_name&$filter=_lzw_bankaccount_value eq {aid}"
                       f" and startswith(lzw_notes,'Interim') and lzw_periodstart le {s['end']} and lzw_periodend ge {s['start']}")["value"]
        if len(found) > 1:
            print(f"    SKIPPED: {len(found)} interim placeholders overlap this period: {[x['lzw_name'] for x in found]}")
            continue
        placeholder = bool(found)
        if found:
            print(f"    updates the placeholder \"{found[0]['lzw_name']}\"")
    if not APPLY or not (res["new"] or res["update"] or placeholder):
        continue
    body = {"lzw_name": name, "lzw_periodstart": s["start"], "lzw_periodend": s["end"],
            "lzw_sourcetype": sc.O + SRC[s["kind"]], "lzw_BankAccount@odata.bind": f"/lzw_bankaccounts({aid})",
            "lzw_importedon": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({cur})"}
    if s["opening"] is not None:
        body["lzw_openingbalance"], body["lzw_closingbalance"] = s["opening"], s["closing"]
    body["lzw_notes"] = INTERIM.format(file=s["file"], start=s["start"], end=s["end"]) if s.get("interim") else None
    if s["account"] == "Wise":
        body["lzw_notes"] = ("Wise transaction export (CSV). Refunded rows and conversions between balances are "
                             "not imported. Amounts are AUD; lines paid from a foreign balance have an estimated AUD "
                             "amount, explained in the line Notes. Period set to the full year; the file is replaced "
                             "by a newer export each month.")
    if found:
        sid = found[0]["lzw_bankstatementid"]
        if placeholder or s.get("interim"):
            dv.patch(f"lzw_bankstatements({sid})", body)
    else:
        _, h = dv.call("POST", "lzw_bankstatements", body)
        sid = h.get("OData-EntityId", h.get("odata-entityid")).rsplit("(", 1)[1].rstrip(")")
    for line, row in res["update"]:
        dv.patch(f"lzw_bankstatementlines({row['id']})", {"lzw_name": line["description"][:500], "lzw_source": sc.O + 2})
    src = "PDF" if s["kind"] == "PDF" else "CSV"
    for line in res["new"]:
        b = sc.line_body(line, aid, sid, src, cur)
        key = b["lzw_duplicatekey"].replace("'", "''")
        done = lambda: bool(dv.get(f"lzw_bankstatementlines?$select=lzw_bankstatementlineid&$filter="
                                   f"_lzw_bankstatement_value eq {sid} and lzw_duplicatekey eq '{key}'")["value"])
        dv.post("lzw_bankstatementlines", b, done=done)
    print(f"    written: statement {sid}, {len(res['new'])} lines")
print("TOTAL", tot, "(written)" if APPLY else "(dry run)")
