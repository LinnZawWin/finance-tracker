"""Phase 2e: Appointment and Recurring Appointment as Planned / Recurring Transactions. Idempotent; never deletes.

Amount and Payment Type on these tables come from an older solution. Its lookups to the old account and
category tables were removed on 2026-11-19 (one-off, not part of this script). This script adds:
- Paid From (-> Bank Account), Transfer To (-> Bank Account, 2026-11-27: the flow then creates a Transfer) and
  Finance Category (-> Finance Category) on both tables.
- Payee (text 200) on both tables (2026-11-28): the flow takes the Finance Transaction's Payee from it. The series
  column is linked to the instance column (LinkedAttributeId), so the platform copies it to the instances.
  "Finance Category" rather than "Category" because Appointment already has an OOTB Category column.
- The 'Recurring' option on Finance Transaction Source.
- Those columns, Amount, Payment Type (and its global choice), the Planned / Recurring Transaction forms
  and views to the solution. Both tables go in as shells, without their other components.
- The new columns on the two forms and views.
- Table display names Planned Transaction(s) and Recurring Transaction(s), and both tables in the
  Finance Tracker app (site map group Capture).
Custom columns on Recurring Appointment are copied by the platform to the instances it generates.
"""
import re
import uuid

import build_schema as bs
import dv
from dv import label

TABLES = ("appointment", "recurringappointmentmaster")
FORMS = {"appointment": "Planned Transaction", "recurringappointmentmaster": "Recurring Transaction"}
VIEWS = {"appointment": "Planned Transactions", "recurringappointmentmaster": "Recurring Transactions"}
LEGACY = ("lzw_amount", "lzw_paymenttype")  # existing columns that belong in this solution
LOOKUPS = (("Paid From", "lzw_bankaccount"), ("Finance Category", "lzw_financecategory"),
           ("Transfer To", "lzw_bankaccount"))
NEW = ("lzw_paidfrom", "lzw_financecategory", "lzw_transferto")
SOURCE_RECURRING = 859130003
LOOKUP_CLASS = "{270BD3DB-D9AF-4782-9025-509E298DEC0A}"
TEXT_CLASS = "{4273EDBD-AC1D-40d3-9FB2-095C621B552D}"
AUDIT = {"Value": True, "CanBeChanged": True, "ManagedPropertyLogicalName": "canmodifyauditsettings"}


def ensure_lookup(tl, display, target):
    schema = "lzw_" + display.replace(" ", "")
    cl = schema.lower()
    if bs.existing_attr(tl, cl):
        return
    dv.post("RelationshipDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
        "SchemaName": f"lzw_{tl}_{schema[4:]}", "ReferencedEntity": target, "ReferencingEntity": tl,
        "CascadeConfiguration": {"Assign": "NoCascade", "Delete": "Restrict", "Merge": "NoCascade",
                                 "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade",
                                 "RollupView": "NoCascade"},
        "AssociatedMenuConfiguration": {"Behavior": "UseCollectionName", "Group": "Details", "Order": 10000},
        "Lookup": {"@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata", "SchemaName": schema,
                   "DisplayName": label(display), "RequiredLevel": {"Value": "None"}, "IsAuditEnabled": AUDIT},
    }, solution=True, done=lambda: bs.existing_attr(tl, cl) is not None)
    print(f"  + lookup {tl}.{cl} -> {target}")


def ensure_payee(tl):
    if bs.existing_attr(tl, "lzw_payee"):
        return
    dv.post(f"EntityDefinitions(LogicalName='{tl}')/Attributes", {
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata", "SchemaName": "lzw_Payee",
        "DisplayName": label("Payee"), "RequiredLevel": {"Value": "None"}, "MaxLength": 200,
        "FormatName": {"Value": "Text"}, "IsAuditEnabled": AUDIT,
        "Description": label("Payee of the Finance Transaction the flow creates (the Subject when empty)."),
    }, solution=True, done=lambda: bs.existing_attr(tl, "lzw_payee") is not None)
    print(f"  + text {tl}.lzw_payee")


def link_payee():
    """Series Payee copies to its instances when it is linked (AttributeMetadata.LinkedAttributeId on the series
    column, as Amount and Payment Type already are). The platform copies it each time the series is expanded."""
    target = dv.get("EntityDefinitions(LogicalName='appointment')/Attributes(LogicalName='lzw_payee')?$select=MetadataId")
    path = ("EntityDefinitions(LogicalName='recurringappointmentmaster')/Attributes(LogicalName='lzw_payee')/"
            "Microsoft.Dynamics.CRM.StringAttributeMetadata")
    md = dv.get(path)
    if (md.get("LinkedAttributeId") or "").lower() == target["MetadataId"].lower():
        return
    md["LinkedAttributeId"] = target["MetadataId"]
    md = {k: v for k, v in md.items() if not k.startswith("@odata.") or k == "@odata.type"}
    md["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
    dv.call("PUT", "EntityDefinitions(LogicalName='recurringappointmentmaster')/Attributes(LogicalName='lzw_payee')", md,
            solution=True, headers={"MSCRM.MergeLabels": "true"})
    print("  recurringappointmentmaster.lzw_payee linked to appointment.lzw_payee")


def ensure_source_option():
    p = ("EntityDefinitions(LogicalName='lzw_financetransaction')/Attributes(LogicalName='lzw_source')/"
         "Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$select=LogicalName&$expand=OptionSet($select=Options)")
    has = lambda: any(o["Value"] == SOURCE_RECURRING for o in dv.get(p)["OptionSet"]["Options"])
    if has():
        return
    dv.post("InsertOptionValue", {
        "EntityLogicalName": "lzw_financetransaction", "AttributeLogicalName": "lzw_source",
        "Value": SOURCE_RECURRING, "Label": label("Recurring"), "SolutionUniqueName": dv.SOLUTION,
    }, done=has)
    print("  + Finance Transaction Source option 'Recurring'")


def add_components():
    for tl in TABLES:
        mid = dv.get(f"EntityDefinitions(LogicalName='{tl}')?$select=MetadataId")["MetadataId"]
        dv.post("AddSolutionComponent", {"ComponentId": mid, "ComponentType": 1, "SolutionUniqueName": dv.SOLUTION,
                                         "AddRequiredComponents": False, "DoNotIncludeSubcomponents": True})
        for cl in LEGACY + NEW + ("lzw_payee",):
            aid = dv.get(f"EntityDefinitions(LogicalName='{tl}')/Attributes(LogicalName='{cl}')?$select=MetadataId")
            dv.add_to_solution(aid["MetadataId"], 2)
        rels = dv.get(f"EntityDefinitions(LogicalName='{tl}')?$select=LogicalName&$expand=ManyToOneRelationships"
                      "($select=MetadataId,ReferencingAttribute)")["ManyToOneRelationships"]
        for r in rels:
            if r["ReferencingAttribute"] in NEW:
                dv.add_to_solution(r["MetadataId"], 10)
        dv.add_to_solution(form_id(tl), 60)
        dv.add_to_solution(view(tl)["savedqueryid"], 26)
    gid = dv.get("GlobalOptionSetDefinitions(Name='lzw_paymenttype')?$select=MetadataId")["MetadataId"]
    dv.add_to_solution(gid, 9)
    print("  solution components added")


def form_id(tl):
    return dv.get(f"systemforms?$select=formid&$filter=objecttypecode eq '{tl}' and type eq 2 "
                  f"and name eq '{FORMS[tl]}'")["value"][0]["formid"]


def view(tl):
    return dv.get(f"savedqueries?$select=savedqueryid,layoutxml,fetchxml&$filter=returnedtypecode eq '{tl}' "
                  f"and name eq '{VIEWS[tl]}'")["value"][0]


def cell(field, text, classid):
    return (f'<cell id="{{{uuid.uuid4()}}}" locklevel="0" colspan="1" rowspan="1" showlabel="true">'
            f'<labels><label description="{text}" languagecode="1033" /></labels>'
            f'<control id="{field}" classid="{classid}" datafieldname="{field}" disabled="false" /></cell>')


def update_form(tl):
    fid = form_id(tl)
    xml = dv.get(f"systemforms({fid})?$select=formxml")["formxml"]
    rows, added = "", []
    if 'datafieldname="lzw_paidfrom"' not in xml:
        # New rows go after the row that holds Amount.
        m = re.search(r'datafieldname="lzw_amount".*?</row>', xml, re.S)
        rows = (f"<row>{cell('lzw_paidfrom', 'Paid From', LOOKUP_CLASS)}"
                f"{cell('lzw_financecategory', 'Finance Category', LOOKUP_CLASS)}</row>")
        xml = xml[:m.end()] + rows + xml[m.end():]
        added += ["Paid From", "Finance Category"]
    if 'datafieldname="lzw_transferto"' not in xml:
        m = re.search(r'datafieldname="lzw_paidfrom".*?</row>', xml, re.S)
        xml = xml[:m.end()] + f"<row>{cell('lzw_transferto', 'Transfer To', LOOKUP_CLASS)}</row>" + xml[m.end():]
        added.append("Transfer To")
    if 'datafieldname="lzw_payee"' not in xml:
        m = re.search(r'datafieldname="lzw_amount".*?</row>', xml, re.S)
        xml = xml[:m.end()] + f"<row>{cell('lzw_payee', 'Payee', TEXT_CLASS)}</row>" + xml[m.end():]
        added.append("Payee")
    if not added:
        return
    dv.patch(f"systemforms({fid})", {"formxml": xml})
    print(f"  form {FORMS[tl]}: added {', '.join(added)}")


def update_view(tl):
    v = view(tl)
    lay, fx = v["layoutxml"], v["fetchxml"]
    cols = [c for c in ("lzw_payee",) + NEW if f'name="{c}"' not in lay]
    if not cols:
        return
    lay = lay.replace("</row>", "".join(f'<cell name="{c}" width="150"/>' for c in cols) + "</row>")
    fx = fx.replace("</entity>", "".join(f'<attribute name="{c}"/>' for c in cols) + "</entity>")
    dv.patch(f"savedqueries({v['savedqueryid']})", {"layoutxml": lay, "fetchxml": fx})
    print(f"  view {VIEWS[tl]}: added {', '.join(cols)}")


def rename_table(tl):
    """Display names follow the Finance Tracker names (the forms and views already use them)."""
    single, plural = FORMS[tl], VIEWS[tl]
    md = dv.get(f"EntityDefinitions(LogicalName='{tl}')")
    if (md["DisplayName"].get("UserLocalizedLabel") or {}).get("Label") == single:
        return
    md["DisplayName"], md["DisplayCollectionName"] = label(single), label(plural)
    dv.call("PUT", f"EntityDefinitions(LogicalName='{tl}')", md, solution=True,
            headers={"MSCRM.MergeLabels": "true"})
    print(f"  table {tl}: renamed to {single} / {plural}")


def add_to_app():
    """Sub-areas under Capture in the Finance Tracker site map, plus the tables, forms and views in the app."""
    sm = dv.get("sitemaps?$select=sitemapid,sitemapxml&$filter=sitemapnameunique eq 'lzw_FinanceTracker'")["value"][0]
    xml = sm["sitemapxml"]
    subs = "".join(f'<SubArea Id="lzw_ft_{tl}" Entity="{tl}" />' for tl in TABLES if f'Entity="{tl}"' not in xml)
    if subs:
        m = re.search(r'<Group Id="lzw_ft_capture">.*?(?=</Group>)', xml, re.S)
        xml = xml[:m.end()] + subs + xml[m.end():]
        dv.patch(f"sitemaps({sm['sitemapid']})", {"sitemapxml": xml})
        print("  site map: added Planned and Recurring Transactions under Capture")
    rows = dv.get("appmodules/Microsoft.Dynamics.CRM.RetrieveUnpublishedMultiple()?$select=appmoduleid,uniquename")
    app = next(a["appmoduleid"] for a in rows["value"] if a["uniquename"] == "lzw_FinanceTracker")
    comps = []
    for tl in TABLES:
        m = dv.get(f"EntityDefinitions(LogicalName='{tl}')?$select=MetadataId,EntitySetName")
        comps += [{"@odata.id": f"{m['EntitySetName']}({m['MetadataId']})"},  # same form as build_ui.py
                  {"@odata.type": "Microsoft.Dynamics.CRM.systemform", "formid": form_id(tl)},
                  {"@odata.type": "Microsoft.Dynamics.CRM.savedquery", "savedqueryid": view(tl)["savedqueryid"]}]
    dv.post("AddAppComponents", {"AppId": app, "Components": comps})
    print("  app: tables, forms and views added")
    return app


def main():
    for tl in TABLES:
        for display, target in LOOKUPS:
            ensure_lookup(tl, display, target)
        ensure_payee(tl)
    link_payee()
    ensure_source_option()
    add_components()
    for tl in TABLES:
        rename_table(tl)
        update_form(tl)
        update_view(tl)
    app = add_to_app()
    xml = "".join(f"<entity>{t}</entity>" for t in TABLES + ("lzw_financetransaction",))
    dv.post("PublishXml", {"ParameterXml": f"<importexportxml><entities>{xml}</entities>"
                                           f"<appmodules><appmodule>{app}</appmodule></appmodules></importexportxml>"})
    print("  published")


if __name__ == "__main__":
    main()
