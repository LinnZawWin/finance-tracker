"""Phase 2c: views, forms, editable grid, model-driven app and site map. Idempotent; never deletes."""
import uuid
from xml.sax.saxutils import escape, quoteattr

import dv
import spec

O = spec.OPT
CLASSID = {
    "String": "{4273EDBD-AC1D-40d3-9FB2-095C621B552D}", "Money": "{533B9108-5A8B-42cb-BD37-52D1B8E7C741}",
    "Picklist": "{3EF39988-22BB-4f0b-BBBE-64B5A3748AEE}", "Lookup": "{270BD3DB-D9AF-4782-9025-509E298DEC0A}",
    "Owner": "{270BD3DB-D9AF-4782-9025-509E298DEC0A}", "DateTime": "{5B773807-9FB2-42db-97C3-7A91EFF8ADFF}",
    "Integer": "{C6D124CA-7EDA-4a60-AEA9-7FB8D318B68F}", "Decimal": "{C3EFE0C3-0EC6-42be-8349-CBD9079C5A6F}",
    "Boolean": "{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}", "Memo": "{E0DECE4B-6FC8-4a8f-A065-082708572369}",
}
SUBGRID = "{E7A81278-8635-4d9e-8D4D-59480B391C5B}"

# Default ("Active ...") view columns per table: (column, width). Sort: (column, descending)
DEFAULT_COLS = {
    "lzw_bankaccount": ([("lzw_name", 200), ("lzw_shortname", 150), ("lzw_bankid", 120), ("lzw_accounttype", 120),
                         ("lzw_accountcurrency", 120), ("lzw_accountnumber", 150)], ("lzw_name", False)),
    "lzw_bankstatement": ([("lzw_name", 220), ("lzw_bankaccount", 160), ("lzw_periodstart", 110), ("lzw_periodend", 110),
                           ("lzw_sourcetype", 110), ("lzw_closingbalance", 130), ("lzw_linecount", 100)],
                          ("lzw_periodend", True)),
    "lzw_bankstatementline": ([("lzw_transactiondate", 110), ("lzw_name", 300), ("lzw_amount", 110),
                               ("lzw_bankaccount", 150), ("lzw_status", 120), ("lzw_merchant", 150),
                               ("lzw_runningbalance", 120), ("lzw_posteddate", 110), ("lzw_cardholder", 130),
                               ("lzw_ispending", 90)], ("lzw_transactiondate", True)),
    "lzw_financetransaction": ([("lzw_transactiondate", 110), ("lzw_name", 260), ("lzw_payee", 150),
                                ("lzw_amount", 120), ("lzw_mycost", 110), ("lzw_paidfrom", 150), ("lzw_category", 150),
                                ("lzw_sharetype", 150), ("lzw_reconciliationstatus", 140)], ("lzw_transactiondate", True)),
    "lzw_reconciliationmatch": ([("lzw_name", 110), ("lzw_bankstatementline", 260), ("lzw_financetransaction", 240),
                                 ("lzw_allocatedamount", 120), ("lzw_matchstatus", 120), ("lzw_matchmethod", 120),
                                 ("lzw_confidence", 100)], ("lzw_name", True)),
    "lzw_bankrule": ([("lzw_name", 200), ("lzw_matchtext", 180), ("lzw_matchtype", 110), ("lzw_bankaccount", 150),
                      ("lzw_defaultcategory", 150), ("lzw_priority", 90)], ("lzw_priority", False)),
    "lzw_financecategory": ([("lzw_name", 220), ("lzw_parentcategory", 180), ("lzw_categorytype", 120)], ("lzw_name", False)),
    "lzw_financeproject": ([("lzw_name", 220), ("lzw_projecttype", 120), ("lzw_startdate", 110), ("lzw_enddate", 110)], ("lzw_name", False)),
    "lzw_financeasset": ([("lzw_name", 220), ("lzw_assettype", 120), ("lzw_brand", 120), ("lzw_model", 120),
                          ("lzw_status", 100), ("lzw_totalcost", 120), ("lzw_netcost", 120)], ("lzw_name", False)),
    "lzw_financeassetlink": ([("lzw_name", 110), ("lzw_financeasset", 200), ("lzw_financetransaction", 240),
                              ("lzw_role", 140), ("lzw_allocatedamount", 120)], ("lzw_name", True)),
}


def cond(attr, op, value=None):
    v = f' value="{value}"' if value is not None else ""
    return f'<condition attribute="{attr}" operator="{op}"{v} />'


ACTIVE = cond("statecode", "eq", 0)
FT, BSL, RM, FA = "lzw_financetransaction", "lzw_bankstatementline", "lzw_reconciliationmatch", "lzw_financeasset"

# Extra public views: table -> [(name, filter xml, optional column override, optional sort)]
VIEWS = {
    FT: [
        ("Needs Details", ACTIVE + cond("lzw_needsdetails", "eq", 1), None, None),
        ("Unreconciled", ACTIVE + cond("lzw_reconciliationstatus", "eq", O), None, None),
        ("Last 30 Days", ACTIVE + cond("lzw_transactiondate", "last-x-days", 30), None, None),
        # Split bills still waiting for someone's repayment: Partly Reconciled and paid more than my share
        # (Reconciliation Difference below 0 = still owed to me). Notes say who owes what.
        ("Owed to me", ACTIVE + cond("lzw_reconciliationstatus", "eq", O + 1) + cond("lzw_reconciliationdifference", "lt", 0),
         [("lzw_transactiondate", 110), ("lzw_name", 260), ("lzw_payee", 140), ("lzw_amount", 110),
          ("lzw_actualamount", 110), ("lzw_reconciliationdifference", 130), ("lzw_notes", 320)], ("lzw_transactiondate", False)),
        ("By Project", ACTIVE + cond("lzw_project", "not-null"),
         [("lzw_project", 170), ("lzw_transactiondate", 110), ("lzw_name", 260), ("lzw_payee", 150),
          ("lzw_amount", 120), ("lzw_mycost", 110), ("lzw_category", 150), ("lzw_sharetype", 150)], ("lzw_project", False)),
    ],
    BSL: [
        ("Unmatched Lines", ACTIVE + '<filter type="or">' + cond("lzw_status", "eq", O) + cond("lzw_status", "eq", O + 1)
         + "</filter>", None, None),
        ("Pending Lines", ACTIVE + cond("lzw_ispending", "eq", 1), None, None),
        ("Transfers", ACTIVE + cond("lzw_status", "eq", O + 3),
         [("lzw_transactiondate", 110), ("lzw_name", 280), ("lzw_amount", 110), ("lzw_bankaccount", 150),
          ("lzw_transfercounterpart", 240)], None),
    ],
    RM: [
        ("Proposed Matches", ACTIVE + cond("lzw_matchstatus", "eq", O),
         [("lzw_name", 110), ("lzw_matchstatus", 130), ("lzw_bankstatementline", 260), ("lzw_financetransaction", 240),
          ("lzw_allocatedamount", 120), ("lzw_confidence", 100), ("lzw_matchmethod", 120), ("lzw_aireasoning", 300)], None),
        ("Confirmed Matches", ACTIVE + cond("lzw_matchstatus", "eq", O + 1),
         [("lzw_name", 110), ("lzw_bankstatementline", 260), ("lzw_financetransaction", 240),
          ("lzw_allocatedamount", 120), ("lzw_matchmethod", 120), ("lzw_confirmedon", 140)], None),
    ],
    FA: [
        ("Owned Assets", ACTIVE + cond("lzw_status", "eq", O), None, None),
        ("Sold Assets", ACTIVE + cond("lzw_status", "eq", O + 1),
         [("lzw_name", 220), ("lzw_assettype", 120), ("lzw_disposaldate", 110), ("lzw_totalcost", 120),
          ("lzw_saleproceeds", 120), ("lzw_netcost", 120)], None),
    ],
    "account": [
        ("Banks", ACTIVE + cond("lzw_isbank", "eq", 1),
         [("name", 300), ("telephone1", 120), ("websiteurl", 200)], ("name", False)),
    ],
}

# Forms: table -> list of tabs; tab = (label, [sections]); section = (label, [fields]) or
# ("subgrid", label, target table, relationship schema name)
FORMS = {
    "lzw_bankaccount": [("General", [
        ("Account", ["lzw_name", "lzw_shortname", "lzw_bankid", "lzw_accounttype", "lzw_accountcurrency",
                     "lzw_accountnumber"]),
        ("Settings", ["lzw_statementsimported", "lzw_lastrate", "lzw_lastratedate", "statecode", "ownerid"]),
    ])],
    "lzw_bankstatement": [("General", [
        ("Statement", ["lzw_name", "lzw_bankaccount", "lzw_periodstart", "lzw_periodend", "lzw_sourcetype"]),
        ("Balances", ["lzw_openingbalance", "lzw_closingbalance", "lzw_linecount", "lzw_importedon",
                      "transactioncurrencyid", "ownerid"]),
        ("Notes", ["lzw_notes"]),
    ]), ("Lines", [("subgrid", "Bank Statement Lines", BSL, "lzw_bankstatementline_BankStatement")])],
    BSL: [("General", [
        ("Line", ["lzw_name", "lzw_transactiondate", "lzw_posteddate", "lzw_amount", "lzw_bankaccount",
                  "lzw_bankstatement", "lzw_merchant", "lzw_runningbalance", "lzw_feeamount", "lzw_cardholder",
                  "lzw_ispending"]),
        ("Matching", ["lzw_status", "lzw_allocatedamount", "lzw_unallocatedamount", "lzw_transfercounterpart",
                      "lzw_originalamount", "lzw_originalcurrency", "lzw_source", "lzw_bankcategory",
                      "lzw_bankreference", "lzw_linenumber", "lzw_duplicatekey",
                      "transactioncurrencyid", "ownerid"]),
        ("Notes", ["lzw_notes"]),
    ]), ("Matches", [("subgrid", "Reconciliation Matches", RM, "lzw_reconciliationmatch_BankStatementLine")])],
    FT: [("General", [
        ("Transaction", ["lzw_name", "lzw_transactiondate", "lzw_type", "lzw_payee", "lzw_amount",
                         "lzw_originalamount", "lzw_originalcurrency", "lzw_paidfrom", "lzw_transferto", "lzw_category", "lzw_project", "lzw_sharetype", "lzw_partnershare",
                         "lzw_mycost", "lzw_needsdetails"]),
        ("Reconciliation", ["lzw_actualamount", "lzw_reconciliationdifference", "lzw_reconciliationstatus",
                            "lzw_source", "lzw_sourcerowid", "transactioncurrencyid", "ownerid"]),
        ("Notes", ["lzw_notes"]),
    ]), ("Matches and Assets", [
        ("subgrid", "Reconciliation Matches", RM, "lzw_reconciliationmatch_FinanceTransaction"),
        ("subgrid", "Finance Asset Links", "lzw_financeassetlink", "lzw_financeassetlink_FinanceTransaction"),
    ])],
    RM: [("General", [
        ("Match", ["lzw_name", "lzw_bankstatementline", "lzw_financetransaction", "lzw_allocatedamount",
                   "lzw_matchstatus"]),
        ("How it was matched", ["lzw_matchmethod", "lzw_confidence", "lzw_confirmedon", "transactioncurrencyid",
                                "ownerid"]),
        ("AI Reasoning", ["lzw_aireasoning"]),
    ])],
    "lzw_bankrule": [("General", [
        ("Rule", ["lzw_name", "lzw_matchtext", "lzw_matchtype", "lzw_bankaccount", "lzw_priority", "statecode"]),
        ("Defaults", ["lzw_defaultpayee", "lzw_defaultdescription", "lzw_defaultcategory", "lzw_defaultsharetype",
                      "ownerid"]),
    ])],
    "lzw_financecategory": [("General", [
        ("Category", ["lzw_name", "lzw_parentcategory", "lzw_categorytype", "statecode", "ownerid"]),
    ])],
    "lzw_financeproject": [("General", [
        ("Project", ["lzw_name", "lzw_projecttype", "lzw_startdate", "lzw_enddate", "statecode", "ownerid"]),
    ]), ("Transactions", [("subgrid", "Finance Transactions", FT, "lzw_financetransaction_Project")])],
    FA: [("General", [
        ("Asset", ["lzw_name", "lzw_assettype", "lzw_brand", "lzw_model", "lzw_serialnumber", "lzw_status",
                   "lzw_disposaldate", "lzw_warrantyexpiry"]),
        ("Cost", ["lzw_totalcost", "lzw_saleproceeds", "lzw_netcost", "transactioncurrencyid", "ownerid"]),
        ("Notes", ["lzw_notes"]),
    ]), ("Links", [("subgrid", "Finance Asset Links", "lzw_financeassetlink", "lzw_financeassetlink_FinanceAsset")])],
    "lzw_financeassetlink": [("General", [
        ("Link", ["lzw_name", "lzw_financeasset", "lzw_financetransaction", "lzw_role", "lzw_allocatedamount",
                  "transactioncurrencyid", "ownerid"]),
        ("Notes", ["lzw_notes"]),
    ])],
}

SITEMAP = [
    ("Capture", [FT, "appointment", "recurringappointmentmaster"]),  # Planned / Recurring Transactions
    ("Reconcile", [BSL, RM]),
    ("Statements", ["lzw_bankstatement", "lzw_bankaccount"]),
    ("Assets", [FA, "lzw_financeassetlink"]),
    ("Setup", ["lzw_financecategory", "lzw_financeproject", "lzw_bankrule", "BANKS"]),
]

_meta = {}


def meta(table):
    if table not in _meta:
        e = dv.get(f"EntityDefinitions(LogicalName='{table}')?$select=ObjectTypeCode,PrimaryIdAttribute,"
                   "PrimaryNameAttribute,MetadataId,EntitySetName")
        attrs = dv.get_all(f"EntityDefinitions(LogicalName='{table}')/Attributes?$select=LogicalName,AttributeType,SchemaName")
        e["attrs"] = {a["LogicalName"]: a for a in attrs}
        _meta[table] = e
    return _meta[table]


def gid():
    return "{" + str(uuid.uuid4()).upper() + "}"


# ------------------------------------------------------------------ views

def view_xml(table, flt, cols, sort):
    m = meta(table)
    dcols, dsort = DEFAULT_COLS.get(table, (None, None))
    cols = [c for c in (cols or dcols) if c[0] in m["attrs"]]
    sort = sort or dsort
    attrs = "".join(f'<attribute name="{c}" />' for c, _ in cols)
    fetch = (f'<fetch version="1.0" mapping="logical"><entity name="{table}"><attribute name="{m["PrimaryIdAttribute"]}" />'
             f'{attrs}<order attribute="{sort[0]}" descending="{"true" if sort[1] else "false"}" />'
             f'<filter type="and">{flt}</filter></entity></fetch>')
    cells = "".join(f'<cell name="{c}" width="{w}" />' for c, w in cols)
    layout = (f'<grid name="resultset" object="{m["ObjectTypeCode"]}" jump="{m["PrimaryNameAttribute"]}" select="1" icon="1" '
              f'preview="1"><row name="result" id="{m["PrimaryIdAttribute"]}">{cells}</row></grid>')
    return fetch, layout


def default_view(table):
    r = dv.get(f"savedqueries?$select=savedqueryid,name&$filter=returnedtypecode eq '{table}' and querytype eq 0 "
               "and isdefault eq true")["value"]
    return r[0]["savedqueryid"]


def build_views():
    ids = {}
    for table in DEFAULT_COLS:
        vid = default_view(table)
        fetch, layout = view_xml(table, ACTIVE, None, None)
        dv.patch(f"savedqueries({vid})", {"fetchxml": fetch, "layoutxml": layout})
        ids[(table, "default")] = vid
    for table, views in VIEWS.items():
        for name, flt, cols, sort in views:
            ex = dv.get(f"savedqueries?$select=savedqueryid&$filter=returnedtypecode eq '{table}' and name eq '{name}' "
                        "and querytype eq 0")["value"]
            fetch, layout = view_xml(table, flt, cols, sort)
            if ex:
                vid = ex[0]["savedqueryid"]
                dv.patch(f"savedqueries({vid})", {"fetchxml": fetch, "layoutxml": layout})
            else:
                check = lambda: bool(dv.get(f"savedqueries?$select=savedqueryid&$filter=returnedtypecode eq '{table}' "
                                            f"and name eq '{name}' and querytype eq 0")["value"])
                dv.post("savedqueries", {"name": name, "returnedtypecode": table, "querytype": 0, "fetchxml": fetch,
                                         "layoutxml": layout, "isdefault": False}, solution=True, done=check)
                vid = dv.get(f"savedqueries?$select=savedqueryid&$filter=returnedtypecode eq '{table}' and "
                             f"name eq '{name}' and querytype eq 0")["value"][0]["savedqueryid"]
                print(f"  + view {table}: {name}", flush=True)
            dv.add_to_solution(vid, 26)
            ids[(table, name)] = vid
    return ids


# ------------------------------------------------------------------ forms

def field_cell(table, field, banks_view):
    a = meta(table)["attrs"].get(field)
    if not a or a["AttributeType"] not in CLASSID:
        return None
    params = ""
    if table == "lzw_bankaccount" and field == "lzw_bankid":
        v = "{" + banks_view.upper() + "}"
        params = (f"<parameters><DefaultViewId>{v}</DefaultViewId><AvailableViewIds>{v}</AvailableViewIds>"
                  "<DisableViewPicker>true</DisableViewPicker><DisableMru>true</DisableMru></parameters>")
    rowspan = ' rowspan="4"' if a["AttributeType"] == "Memo" else ""
    cell = (f'<cell id="{gid()}"{rowspan}><labels><label description="" languagecode="1033" /></labels>'
            f'<control id="{field}" classid="{CLASSID[a["AttributeType"]]}" datafieldname="{field}">{params}</control></cell>')
    extra = "<row />" * 3 if rowspan else ""
    return f"<row>{cell}</row>{extra}"


def subgrid_section(label, target, relationship, view_id):
    v = "{" + view_id.upper() + "}"
    ctl = (f'<control id="Subgrid_{relationship[4:]}" classid="{SUBGRID}" indicationOfSubgrid="true"><parameters>'
           f"<ViewId>{v}</ViewId><IsUserView>false</IsUserView><RelationshipName>{relationship}</RelationshipName>"
           f"<TargetEntityType>{target}</TargetEntityType><AutoExpand>Fixed</AutoExpand><EnableQuickFind>false</EnableQuickFind>"
           f"<EnableViewPicker>false</EnableViewPicker><ViewIds>{v}</ViewIds><EnableJumpBar>false</EnableJumpBar>"
           "<ChartGridMode>Grid</ChartGridMode><VisualizationId /><IsUserChart>false</IsUserChart>"
           "<EnableChartPicker>false</EnableChartPicker><RecordsPerPage>10</RecordsPerPage></parameters></control>")
    return (f'<section showlabel="true" showbar="false" IsUserDefined="0" id="{gid()}" columns="1">'
            f'<labels><label description={quoteattr(label)} languagecode="1033" /></labels><rows>'
            f'<row><cell id="{gid()}" rowspan="8" colspan="1" auto="false"><labels><label description={quoteattr(label)} '
            f'languagecode="1033" /></labels>{ctl}</cell></row>' + "<row />" * 7 + "</rows></section>")


def form_xml(table, tabs, view_ids):
    out = ""
    for tab_label, sections in tabs:
        cols = []
        for sec in sections:
            if sec[0] == "subgrid":
                _, label, target, rel = sec
                cols.append((True, subgrid_section(label, target, rel, view_ids[(target, "default")])))
                continue
            label, fields = sec
            rows = "".join(filter(None, (field_cell(table, f, view_ids.get(("account", "Banks"), "")) for f in fields)))
            wide = fields == ["lzw_notes"] or fields == ["lzw_aireasoning"]
            cols.append((wide, f'<section showlabel="true" showbar="false" IsUserDefined="0" id="{gid()}" columns="1">'
                               f'<labels><label description={quoteattr(label)} languagecode="1033" /></labels>'
                               f"<rows>{rows}</rows></section>"))
        narrow = [x for w, x in cols if not w]
        wide = [x for w, x in cols if w]
        if len(narrow) >= 2 and not wide:
            half = (len(narrow) + 1) // 2
            columns = (f'<column width="50%"><sections>{"".join(narrow[:half])}</sections></column>'
                       f'<column width="50%"><sections>{"".join(narrow[half:])}</sections></column>')
            out += (f'<tab verticallayout="true" id="{gid()}" IsUserDefined="1"><labels><label description='
                    f'{quoteattr(tab_label)} languagecode="1033" /></labels><columns>{columns}</columns></tab>')
        elif len(narrow) >= 2:
            # two columns of fields, then the wide sections in their own tab body below
            half = (len(narrow) + 1) // 2
            columns = (f'<column width="50%"><sections>{"".join(narrow[:half])}</sections></column>'
                       f'<column width="50%"><sections>{"".join(narrow[half:])}</sections></column>')
            out += (f'<tab verticallayout="true" id="{gid()}" IsUserDefined="1"><labels><label description='
                    f'{quoteattr(tab_label)} languagecode="1033" /></labels><columns>{columns}</columns></tab>')
            out += (f'<tab verticallayout="true" id="{gid()}" IsUserDefined="1" showlabel="false"><labels><label '
                    f'description="Notes" languagecode="1033" /></labels><columns><column width="100%"><sections>'
                    f'{"".join(wide)}</sections></column></columns></tab>')
        else:
            out += (f'<tab verticallayout="true" id="{gid()}" IsUserDefined="1"><labels><label description='
                    f'{quoteattr(tab_label)} languagecode="1033" /></labels><columns><column width="100%"><sections>'
                    f'{"".join(narrow + wide)}</sections></column></columns></tab>')
    return f"<form><tabs>{out}</tabs></form>"


def build_forms(view_ids):
    ids = {}
    for table, tabs in FORMS.items():
        f = dv.get(f"systemforms?$select=formid,name&$filter=objecttypecode eq '{table}' and type eq 2")["value"][0]
        try:
            dv.patch(f"systemforms({f['formid']})", {"formxml": form_xml(table, tabs, view_ids)})
            print(f"  form {table}: updated", flush=True)
        except dv.DvError as e:
            print(f"  FORM FAILED {table}: {e}", flush=True)
        dv.add_to_solution(f["formid"], 60)
        ids[table] = f["formid"]
    return ids


# ------------------------------------------------------------------ editable grid

def grid_params(editing):
    p = [("EnableEditing", "Enum", editing), ("EnableFiltering", "Enum", "yes"), ("EnableSorting", "Enum", "yes"),
         ("EnableGrouping", "Enum", "no"), ("EnableAggregation", "Enum", "no"), ("EnableMultipleSelection", "Enum", "yes"),
         ("EnableRangeSelection", "Enum", "yes"), ("EnableJumpBar", "Enum", "no"), ("EnablePagination", "Enum", "yes"),
         ("EnableDropdownColor", "Enum", "no"), ("EnableStatusIcons", "Enum", "yes"), ("EnableTypeIcons", "Enum", "no"),
         ("NavigationTypesAllowed", "Enum", "all"), ("ReflowBehavior", "Enum", "Reflow"), ("ShowAvatar", "Enum", "yes"),
         ("ShowFooter", "Enum", "yes"), ("ShowColumnHeaders", "Enum", "yes"), ("EnableStatusColumn", "Enum", "yes")]
    return ('<parameters><data-set name="Items"><columnsDefaultView /></data-set>'
            + "".join(f'<{n} static="true" type="{t}">{v}</{n}>' for n, t, v in p) + "</parameters>")


def build_editable_grid():
    """Power Apps grid control with editing on, as the default grid for Reconciliation Match."""
    xml = ('<controlDescriptions><controlDescription>'
           f'<customControl id="{SUBGRID}"><parameters /></customControl>'
           + "".join(f'<customControl name="Microsoft.PowerApps.PowerAppsOneGrid" formFactor="{ff}">{grid_params("yes")}'
                     "</customControl>" for ff in (0, 1, 2))
           + "</controlDescription></controlDescriptions>")
    ex = dv.get(f"customcontroldefaultconfigs?$select=customcontroldefaultconfigid&$filter=primaryentitytypecode eq '{RM}'")["value"]
    try:
        if ex:
            cid = ex[0]["customcontroldefaultconfigid"]
            dv.patch(f"customcontroldefaultconfigs({cid})", {"controldescriptionxml": xml})
        else:
            dv.post("customcontroldefaultconfigs", {"primaryentitytypecode": RM, "controldescriptionxml": xml},
                    solution=True, done=lambda: bool(dv.get(
                        "customcontroldefaultconfigs?$select=customcontroldefaultconfigid&$filter="
                        f"primaryentitytypecode eq '{RM}'")["value"]))
            cid = dv.get("customcontroldefaultconfigs?$select=customcontroldefaultconfigid&$filter="
                         f"primaryentitytypecode eq '{RM}'")["value"][0]["customcontroldefaultconfigid"]
        dv.add_to_solution(cid, 68)
        print("  editable grid configured for " + RM, flush=True)
        return True
    except dv.DvError as e:
        print(f"  EDITABLE GRID FAILED: {e}", flush=True)
        return False


# ------------------------------------------------------------------ app

def sitemap_xml(view_ids):
    groups = ""
    for title, items in SITEMAP:
        subs = ""
        for it in items:
            if it == "BANKS":
                v = view_ids[("account", "Banks")]
                url = escape(f"/main.aspx?pagetype=entitylist&etn=account&viewid={{{v}}}&viewtype=1039")
                subs += (f'<SubArea Id="lzw_ft_banks" Url="{url}" Icon="/_imgs/imagestrips/transparent_spacer.gif">'
                         '<Titles><Title LCID="1033" Title="Banks" /></Titles></SubArea>')
            else:
                subs += f'<SubArea Id="lzw_ft_{it.removeprefix("lzw_")}" Entity="{it}" />'
        groups += (f'<Group Id="lzw_ft_{title.lower()}"><Titles><Title LCID="1033" Title="{title}" /></Titles>{subs}</Group>')
    return ('<SiteMap IntroducedVersion="7.0.0.0"><Area Id="lzw_ft_area" ShowGroups="true">'
            f'<Titles><Title LCID="1033" Title="Finance Tracker" /></Titles>{groups}</Area></SiteMap>')


def build_app(view_ids, form_ids):
    xml = sitemap_xml(view_ids)
    sm = dv.get("sitemaps?$select=sitemapid&$filter=sitemapnameunique eq 'lzw_FinanceTracker'")["value"]
    if sm:
        smid = sm[0]["sitemapid"]
        dv.patch(f"sitemaps({smid})", {"sitemapxml": xml})
    else:
        dv.post("sitemaps", {"sitemapname": "Finance Tracker", "sitemapnameunique": "lzw_FinanceTracker", "sitemapxml": xml},
                solution=True, done=lambda: bool(dv.get(
                    "sitemaps?$select=sitemapid&$filter=sitemapnameunique eq 'lzw_FinanceTracker'")["value"]))
        smid = dv.get("sitemaps?$select=sitemapid&$filter=sitemapnameunique eq 'lzw_FinanceTracker'")["value"][0]["sitemapid"]
        print("  + site map", flush=True)
    app_filter = "appmodules/Microsoft.Dynamics.CRM.RetrieveUnpublishedMultiple()?$select=appmoduleid,uniquename"

    def find_app():
        rows = dv.get(app_filter)["value"]
        return next((a["appmoduleid"] for a in rows if a["uniquename"] == "lzw_FinanceTracker"), None)

    app = find_app()
    if not app:
        dv.post("appmodules", {"name": "Finance Tracker", "uniquename": "lzw_FinanceTracker",
                               "description": "Personal finance capture, bank statement reconciliation and assets",
                               "webresourceid": "953b9fac-1e5e-e611-80d6-00155ded156f", "clienttype": 4,
                               "navigationtype": 0, "formfactor": 1},
                solution=True, done=lambda: find_app() is not None)
        app = find_app()
        print("  + app module", flush=True)
    comps = [{"@odata.type": "Microsoft.Dynamics.CRM.sitemap", "sitemapid": smid}]
    for table in list(DEFAULT_COLS) + ["account"]:
        m = meta(table)
        comps.append({"@odata.id": f"{m['EntitySetName']}({m['MetadataId']})"})
    for (table, name), vid in view_ids.items():
        comps.append({"@odata.type": "Microsoft.Dynamics.CRM.savedquery", "savedqueryid": vid})
    for table, fid in form_ids.items():
        comps.append({"@odata.type": "Microsoft.Dynamics.CRM.systemform", "formid": fid})
    dv.post("AddAppComponents", {"AppId": app, "Components": comps})
    try:
        v = dv.get(f"ValidateApp(AppModuleId={app})")
        print("  ValidateApp:", v.get("AppValidationResponse", v), flush=True)
    except dv.DvError as e:
        print("  ValidateApp error:", e, flush=True)
    return app


def main():
    view_ids = build_views()
    form_ids = build_forms(view_ids)
    build_editable_grid()
    print("publishing customizations...", flush=True)
    try:
        dv.publish_all()
    except Exception as e:  # the proxy may drop the long publish call; it still completes server side
        print("  publish call interrupted:", type(e).__name__, flush=True)
    app = build_app(view_ids, form_ids)
    try:
        dv.post("PublishXml", {"ParameterXml": f"<importexportxml><appmodules><appmodule>{app}</appmodule></appmodules></importexportxml>"})
    except Exception as e:
        print("  app publish call interrupted:", type(e).__name__, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
