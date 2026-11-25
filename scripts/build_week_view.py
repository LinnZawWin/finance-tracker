"""Create the system view "Current Week Pending Transactions" on Planned Transaction (appointment). Idempotent."""
import dv

NAME = "Current Week Pending Transactions"
LAYOUT = ('<grid name="resultset" object="4201" jump="subject" select="1" icon="1" preview="1">'
          '<row name="result" id="activityid"><cell name="scheduledstart" width="100"/>'
          '<cell name="subject" width="300"/><cell name="lzw_amount" width="100"/>'
          '<cell name="transactioncurrencyid" width="100"/><cell name="lzw_paymenttype" width="100"/>'
          '<cell name="lzw_paidfrom" width="150"/><cell name="lzw_financecategory" width="150"/></row></grid>')
FETCH = ('<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true"><entity name="appointment">'
         '<attribute name="subject"/><attribute name="activityid"/><attribute name="scheduledstart"/>'
         '<attribute name="lzw_amount"/><attribute name="transactioncurrencyid"/><attribute name="lzw_paymenttype"/>'
         '<attribute name="lzw_paidfrom"/><attribute name="lzw_financecategory"/>'
         '<order attribute="scheduledstart" descending="false"/><order attribute="subject" descending="false"/>'
         '<filter type="and"><condition attribute="scheduledstart" operator="this-week"/>'
         '<condition attribute="statecode" operator="eq" value="0"/></filter></entity></fetch>')

rows = dv.get("savedqueries?$select=savedqueryid&$filter=returnedtypecode eq 'appointment' and name eq '%s'" % NAME)["value"]
body = {"name": NAME, "returnedtypecode": "appointment", "querytype": 0, "isdefault": False,
        "description": "Planned Transactions due this week that are still open.",
        "layoutxml": LAYOUT, "fetchxml": FETCH}
if rows:
    vid = rows[0]["savedqueryid"]; dv.patch(f"savedqueries({vid})", body); print("updated", vid)
else:
    r = dv.post("savedqueries", body); vid = dv.new_id(r.headers) if hasattr(r, "headers") else None
    vid = vid or dv.get("savedqueries?$select=savedqueryid&$filter=returnedtypecode eq 'appointment' and name eq '%s'" % NAME)["value"][0]["savedqueryid"]
    print("created", vid)
dv.add_to_solution(vid, 26)
rows = dv.get("appmodules/Microsoft.Dynamics.CRM.RetrieveUnpublishedMultiple()?$select=appmoduleid,uniquename")["value"]
app = next(a["appmoduleid"] for a in rows if a["uniquename"] == "lzw_FinanceTracker")
dv.post("AddAppComponents", {"AppId": app, "Components": [{"@odata.type": "Microsoft.Dynamics.CRM.savedquery", "savedqueryid": vid}]})
dv.publish_all()
print("added to solution and app, published")
