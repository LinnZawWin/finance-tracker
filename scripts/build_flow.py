"""Phase 2d: environment variable, connection references and the Keep import cloud flow (created OFF)."""
import json

import dv
import spec

FLOW_NAME = "Finance Tracker - Import Keep Rows"
ENV_VAR = "lzw_KeepInboxSheetId"
ENV_PARAM = f"Keep Inbox Sheet Id ({ENV_VAR})"
CR_DV = "lzw_FinanceTrackerDataverse"
CR_GS = "lzw_FinanceTrackerGoogleSheets"
DV_API = "shared_commondataserviceforapps"
GS_API = "shared_googlesheet"
TZ = "E. Australia Standard Time"  # Windows name for Australia/Brisbane
O = spec.OPT


def ensure_env_var():
    if dv.get(f"environmentvariabledefinitions?$select=schemaname&$filter=schemaname eq '{ENV_VAR}'")["value"]:
        return
    dv.post("environmentvariabledefinitions", {
        "schemaname": ENV_VAR, "displayname": "Keep Inbox Sheet Id", "type": 100000000,
        "description": "Google Sheet ID of the Keep Inbox spreadsheet (the value between /d/ and /edit in its URL).",
    }, solution=True, done=lambda: bool(
        dv.get(f"environmentvariabledefinitions?$select=schemaname&$filter=schemaname eq '{ENV_VAR}'")["value"]))
    print("  + environment variable", ENV_VAR)


def ensure_conn_ref(name, display, api):
    q = f"connectionreferences?$select=connectionreferenceid&$filter=connectionreferencelogicalname eq '{name}'"
    if dv.get(q)["value"]:
        return
    dv.post("connectionreferences", {
        "connectionreferencelogicalname": name, "connectionreferencedisplayname": display,
        "connectorid": f"/providers/Microsoft.PowerApps/apis/{api}",
    }, solution=True, done=lambda: bool(dv.get(q)["value"]))
    print("  + connection reference", name)


def action(api, op, params, run_after=None):
    return {
        "runAfter": run_after or {},
        "type": "OpenApiConnection",
        "inputs": {
            "host": {"connectionName": api, "operationId": op, "apiId": f"/providers/Microsoft.PowerApps/apis/{api}"},
            "parameters": params,
            "authentication": "@parameters('$authentication')",
        },
    }


def col(name):
    """Sheet cell of the current row as a trimmed string. Spaces in headers are encoded by the connector."""
    key = name.replace(" ", "_x0020_")
    return f"trim(string(coalesce(items('For_each_row')?['{key}'], '')))"


def definition(sets):
    sheet = f"@parameters('{ENV_PARAM}')"
    amount = col("AUD Amount")
    flag = f"toUpper({col('Share Flag')})"
    first_id = lambda act, idcol: f"first(outputs('{act}')?['body/value'])?['{idcol}']"
    quoted = lambda expr: f"replace({expr}, '''', '''''')"

    create = action(DV_API, "CreateRecord", {
        "entityName": sets["lzw_financetransaction"],
        "item/lzw_name": f"@{col('Description')}",
        "item/lzw_transactiondate": f"@{col('Date')}",
        "item/lzw_payee": f"@{col('Merchant')}",
        "item/lzw_estimatedamount": f"@if(isFloat({amount}), float({amount}), null)",
        "item/lzw_sharetype": f"@if(equals({flag}, 'AA'), {O + 2}, if(equals({flag}, 'A'), {O + 1}, {O}))",
        "item/lzw_type": O,            # Expense
        "item/lzw_source": O,          # Keep
        "item/lzw_sourcerowid": f"@{col('Row ID')}",
        "item/lzw_needsdetails": f"@not(isFloat({amount}))",
        "item/lzw_PaidFrom@odata.bind":
            f"@if(empty(outputs('Find_bank_account')?['body/value']), null, "
            f"concat('{sets['lzw_bankaccount']}(', {first_id('Find_bank_account', 'lzw_bankaccountid')}, ')'))",
        "item/lzw_Project@odata.bind":
            f"@if(empty(outputs('Find_project')?['body/value']), null, "
            f"concat('{sets['lzw_financeproject']}(', {first_id('Find_project', 'lzw_financeprojectid')}, ')'))",
        "item/transactioncurrencyid@odata.bind":
            "@if(empty(outputs('Get_AUD_currency')?['body/value']), null, "
            f"concat('transactioncurrencies(', {first_id('Get_AUD_currency', 'transactioncurrencyid')}, ')'))",
    }, {"Find_bank_account": ["Succeeded"], "Find_project": ["Succeeded"]})

    if_new = {
        "runAfter": {"Find_existing_transaction": ["Succeeded"]},
        "type": "If",
        "expression": {"equals": ["@length(outputs('Find_existing_transaction')?['body/value'])", 0]},
        "actions": {
            "Find_bank_account": action(DV_API, "ListRecords", {
                "entityName": sets["lzw_bankaccount"], "$select": "lzw_bankaccountid,lzw_shortname", "$top": 1,
                "$orderby": "lzw_name asc",
                # Paid From only when G is not empty: an empty G gets a filter that matches nothing.
                "$filter": f"@{{if(empty({col('Account')}), 'lzw_bankaccountid eq null', "
                           f"concat('statecode eq 0 and contains(lzw_shortname,''', {quoted(col('Account'))}, ''')'))}}",
            }),
            "Find_project": action(DV_API, "ListRecords", {
                "entityName": sets["lzw_financeproject"], "$select": "lzw_financeprojectid", "$top": 1,
                "$filter": f"@{{if(empty({col('Project')}), 'lzw_financeprojectid eq null', "
                           f"concat('lzw_name eq ''', {quoted(col('Project'))}, ''''))}}",
            }),
            "Create_Finance_Transaction": create,
            "Mark_row_processed": action(GS_API, "PatchItem", {
                "dataset": sheet, "table": "Inbox",
                "id": "@items('For_each_row')?['__PowerAppsId__']",
                "item/Processed": "Processed",
                "item/Processed_x0020_On": f"@convertFromUtc(utcNow(), '{TZ}', 'yyyy-MM-dd HH:mm:ss')",
            }, {"Create_Finance_Transaction": ["Succeeded"]}),
        },
        "else": {"actions": {}},
    }

    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "$connections": {"defaultValue": {}, "type": "Object"},
            "$authentication": {"defaultValue": {}, "type": "SecureObject"},
            ENV_PARAM: {"defaultValue": "", "type": "String", "metadata": {"schemaName": ENV_VAR}},
        },
        "triggers": {
            "Every_hour": {"type": "Recurrence",
                           "recurrence": {"frequency": "Hour", "interval": 1, "timeZone": TZ}},
        },
        "actions": {
            "Get_rows": action(GS_API, "GetItems", {"dataset": sheet, "table": "Inbox", "$top": 5000}),
            "Get_AUD_currency": action(DV_API, "ListRecords", {
                "entityName": "transactioncurrencies", "$select": "transactioncurrencyid", "$top": 1,
                "$filter": "isocurrencycode eq 'AUD'"}),
            "Filter_unprocessed_rows": {
                "runAfter": {"Get_rows": ["Succeeded"], "Get_AUD_currency": ["Succeeded"]},
                "type": "Query",
                "inputs": {
                    "from": "@outputs('Get_rows')?['body/value']",
                    "where": "@and(empty(item()?['Processed']), not(empty(item()?['Description'])))",
                },
            },
            "For_each_row": {
                "runAfter": {"Filter_unprocessed_rows": ["Succeeded"]},
                "type": "Foreach",
                "foreach": "@body('Filter_unprocessed_rows')",
                "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
                "actions": {
                    "Process_row": {
                        "runAfter": {}, "type": "Scope",
                        "actions": {
                            "Find_existing_transaction": action(DV_API, "ListRecords", {
                                "entityName": sets["lzw_financetransaction"],
                                "$select": "lzw_financetransactionid", "$top": 1,
                                "$filter": f"@{{concat('lzw_sourcerowid eq ''', {quoted(col('Row ID'))}, '''')}}",
                            }),
                            "If_not_imported_yet": if_new,
                        },
                    },
                    # A failed row is left unprocessed (K stays empty) and the loop carries on.
                    "Row_failed_-_leave_unprocessed": {
                        "runAfter": {"Process_row": ["Failed", "TimedOut"]},
                        "type": "Compose",
                        "inputs": "@concat('Row not imported: ', string(items('For_each_row')?['Row_x0020_ID']))",
                    },
                },
            },
        },
    }


def client_data(sets):
    def ref(name, api):
        return {"runtimeSource": "embedded", "connection": {"connectionReferenceLogicalName": name}, "api": {"name": api}}
    return {
        "properties": {
            "connectionReferences": {DV_API: ref(CR_DV, DV_API), GS_API: ref(CR_GS, GS_API)},
            "definition": definition(sets),
        },
        "schemaVersion": "1.0.0.0",
    }


def main():
    ensure_env_var()
    ensure_conn_ref(CR_DV, "Finance Tracker Dataverse", DV_API)
    ensure_conn_ref(CR_GS, "Finance Tracker Google Sheets", GS_API)
    sets = {t: dv.get(f"EntityDefinitions(LogicalName='{t}')?$select=EntitySetName")["EntitySetName"]
            for t in ("lzw_financetransaction", "lzw_bankaccount", "lzw_financeproject")}
    data = json.dumps(client_data(sets))
    q = f"workflows?$select=workflowid,statecode&$filter=category eq 5 and name eq '{FLOW_NAME}'"
    ex = dv.get(q)["value"]
    if ex:
        if ex[0]["statecode"] == 0:
            dv.patch(f"workflows({ex[0]['workflowid']})", {"clientdata": data})
            print("  flow definition updated (still OFF)")
        else:
            print("  flow exists and is ON; left untouched")
        return
    dv.post("workflows", {
        "category": 5, "name": FLOW_NAME, "type": 1, "primaryentity": "none",
        "description": "Hourly import of unprocessed Keep Inbox sheet rows into Finance Transactions.",
        "clientdata": data,
    }, solution=True, done=lambda: bool(dv.get(q)["value"]))
    print("  + flow created (OFF):", FLOW_NAME)


if __name__ == "__main__":
    main()
