"""Phase 2f: scheduled flow that turns due Planned Transactions (appointments) into Finance Transactions.

Created OFF, like the Keep flow. Reuses the lzw_FinanceTrackerDataverse connection reference.
Appointment Amount convention (after the sign flip of the series): positive = expense, negative = income.
Finance Transaction gets Amount = abs(Amount) and Type from the sign, or Transfer (with Transfer To) when the
appointment or its series has Transfer To (2026-11-27).
A transaction is created once per appointment (Source = Recurring, Source Row ID = appointment ID), so a
series edit cannot create duplicates. A processed appointment is set to Completed (status reason Completed).
"""
import json
import sys

import build_flow as bf
import dv
import spec

FLOW_NAME = "Scheduled: Create Finance Transactions from Planned Transactions"
O = spec.OPT
RECURRING = O + 3
ESTIMATED = O + 2  # Payment Type (global choice lzw_paymenttype): Auto, Manual, Estimated
TZ = bf.TZ
DV = bf.DV_API

T_LIST = "List_rows:_Appointment_(Due_and_Open)"
T_LOOP = "Apply_to_each:_Appointment"
T_TRY = "Scope:_Try"
T_EXIST = "List_rows:_Finance_Transaction_(Existing)"
T_SERIES = "List_rows:_Recurring_Transaction_(Series)"
T_AUD = "List_rows:_Currency_(AUD)"
T_END = "Compose:_compEndOfTodayUtc"
VAR = "varFailedCount"


def a(act, *args):
    return bf.action(DV, act, *args)


def item(field):
    return f"items('{T_LOOP}')?['{field}']"


def lookup(field):
    """The instance's value, else its series' value: the platform does not copy custom lookups to instances."""
    return f"coalesce({item(field)}, first(outputs('{T_SERIES}')?['body/value'])?['{field}'])"


def bind(field, entity_set):
    return f"@if(empty({lookup(field)}), null, concat('{entity_set}(', {lookup(field)}, ')'))"


def definition(sets):
    amount = f"float({item('lzw_amount')})"
    aud = f"first(outputs('{T_AUD}')?['body/value'])?['transactioncurrencyid']"
    currency = (f"@if(empty({item('_transactioncurrencyid_value')}), "
                f"if(empty(outputs('{T_AUD}')?['body/value']), null, concat('transactioncurrencies(', {aud}, ')')), "
                f"concat('transactioncurrencies(', {item('_transactioncurrencyid_value')}, ')'))")
    create = a("CreateRecord", {
        "entityName": sets["lzw_financetransaction"],
        "item/lzw_name": f"@{item('subject')}",
        "item/lzw_transactiondate": f"@formatDateTime(convertFromUtc({item('scheduledstart')}, '{TZ}'), 'yyyy-MM-dd')",
        "item/lzw_payee": f"@{item('subject')}",
        # Transfer when Transfer To is set, else Income when negative, else Expense
        "item/lzw_type": f"@if(not(empty({lookup('_lzw_transferto_value')})), {O + 2}, if(less({amount}, 0), {O + 1}, {O}))",
        "item/lzw_amount": f"@if(less({amount}, 0), mul({amount}, -1), {amount})",
        "item/lzw_sharetype": O,  # Mine
        "item/lzw_source": RECURRING,
        "item/lzw_sourcerowid": f"@{item('activityid')}",
        # Needs Details while Paid From is missing or the amount is only an estimate (Payment Type = Estimated).
        "item/lzw_needsdetails": f"@or(empty({lookup('_lzw_paidfrom_value')}), "
                                 f"equals({item('lzw_paymenttype')}, {ESTIMATED}))",
        # The appointment's Description holds payee or how-to-pay details ("Manual - Buy Amazon Gift Card ...").
        "item/lzw_notes": f"@concat('Created from Planned Transaction. Payment Type: ', "
                          f"coalesce({item('lzw_paymenttype@OData.Community.Display.V1.FormattedValue')}, '-'), "
                          f"if(empty({item('description')}), '', concat(decodeUriComponent('%0A'), {item('description')})))",
        "item/lzw_PaidFrom@odata.bind": bind("_lzw_paidfrom_value", sets["lzw_bankaccount"]),
        "item/lzw_Category@odata.bind": bind("_lzw_financecategory_value", sets["lzw_financecategory"]),
        "item/lzw_TransferTo@odata.bind": bind("_lzw_transferto_value", sets["lzw_bankaccount"]),
        "item/transactioncurrencyid@odata.bind": currency,
    })
    try_scope = {
        "runAfter": {}, "type": "Scope",
        "actions": {
            T_EXIST: a("ListRecords", {
                "entityName": sets["lzw_financetransaction"], "$select": "lzw_financetransactionid", "$top": 1,
                "$filter": f"lzw_source eq {RECURRING} and lzw_sourcerowid eq '@{{{item('activityid')}}}'",
            }),
            # A single appointment has no series: the filter then matches nothing.
            T_SERIES: a("ListRecords", {
                "entityName": "recurringappointmentmasters", "$top": 1,
                "$select": "activityid,_lzw_paidfrom_value,_lzw_financecategory_value,_lzw_transferto_value",
                "$filter": f"@{{if(empty({item('seriesid')}), 'activityid eq null', "
                           f"concat('activityid eq ', {item('seriesid')}))}}",
            }),
            "Condition:_Transaction_Not_Created": {
                "runAfter": {T_EXIST: ["Succeeded"], T_SERIES: ["Succeeded"]}, "type": "If",
                "expression": {"equals": [f"@length(outputs('{T_EXIST}')?['body/value'])", 0]},
                "actions": {"Add_a_new_row:_Finance_Transaction": create},
                "else": {"actions": {}},
            },
            "Update_a_row:_Appointment_(Completed)": a("UpdateRecord", {
                "entityName": "appointments", "recordId": f"@{item('activityid')}",
                "item/statecode": 1, "item/statuscode": 3,  # Completed
            }, {"Condition:_Transaction_Not_Created": ["Succeeded"]}),
        },
    }
    loop = {
        "runAfter": {"Condition:_Appointments_Found": ["Succeeded"]},
        "type": "Foreach",
        "foreach": f"@outputs('{T_LIST}')?['body/value']",
        "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
        "actions": {
            T_TRY: try_scope,
            # A failed appointment stays Open and is retried on the next run.
            f"Increment_variable:_{VAR}": {
                "runAfter": {T_TRY: ["Failed", "TimedOut"]}, "type": "IncrementVariable",
                "inputs": {"name": VAR, "value": 1},
            },
        },
    }
    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": {
            "Recurrence:_Daily": {"type": "Recurrence", "recurrence": {
                "frequency": "Day", "interval": 1, "timeZone": TZ, "schedule": {"hours": ["6"], "minutes": [0]}}},
        },
        "actions": {
            f"Initialize_variable:_{VAR}": {"runAfter": {}, "type": "InitializeVariable",
                                            "inputs": {"variables": [{"name": VAR, "type": "integer", "value": 0}]}},
            # Start of tomorrow in Brisbane, as UTC: appointments before it are due (today or earlier).
            T_END: {"runAfter": {f"Initialize_variable:_{VAR}": ["Succeeded"]}, "type": "Compose",
                    "inputs": f"@convertToUtc(concat(formatDateTime(addDays(convertFromUtc(utcNow(), '{TZ}'), 1), "
                              f"'yyyy-MM-dd'), 'T00:00:00'), '{TZ}')"},
            T_AUD: a("ListRecords", {"entityName": "transactioncurrencies", "$select": "transactioncurrencyid",
                                     "$top": 1, "$filter": "isocurrencycode eq 'AUD'"},
                     {f"Initialize_variable:_{VAR}": ["Succeeded"]}),
            T_LIST: a("ListRecords", {
                "entityName": "appointments", "$top": 5000, "$orderby": "scheduledstart asc",
                "$select": "activityid,seriesid,subject,description,scheduledstart,lzw_amount,lzw_paymenttype,_lzw_paidfrom_value,"
                           "_lzw_financecategory_value,_lzw_transferto_value,_transactioncurrencyid_value",
                # Open (0) or Scheduled (3) only: completed (done) and cancelled appointments are read-only.
                "$filter": f"lzw_amount ne null and (statecode eq 0 or statecode eq 3) "
                           f"and scheduledstart lt @{{outputs('{T_END}')}}",
            }, {T_END: ["Succeeded"], T_AUD: ["Succeeded"]}),
            "Condition:_Appointments_Found": {
                "runAfter": {T_LIST: ["Succeeded"]}, "type": "If",
                "expression": {"equals": [f"@length(outputs('{T_LIST}')?['body/value'])", 0]},
                "actions": {"Terminate:_Cancelled_-_No_Appointments_Due": {
                    "runAfter": {}, "type": "Terminate", "inputs": {"runStatus": "Cancelled"}}},
                "else": {"actions": {}},
            },
            T_LOOP: loop,
            "Condition:_IsErrorRaised": {
                "runAfter": {T_LOOP: ["Succeeded", "Failed"]}, "type": "If",
                "expression": {"greater": [f"@variables('{VAR}')", 0]},
                "actions": {"Terminate:_Failed": {"runAfter": {}, "type": "Terminate", "inputs": {
                    "runStatus": "Failed", "runError": {
                        "code": "AppointmentsFailed",
                        "message": f"@concat('Failed to Add new row: Finance Transaction for ', "
                                   f"string(variables('{VAR}')), ' appointment(s). They stay open.')"}}}},
                "else": {"actions": {"Terminate:_Succeeded": {
                    "runAfter": {}, "type": "Terminate", "inputs": {"runStatus": "Succeeded"}}}},
            },
        },
    }


def main():
    sets = {t: dv.get(f"EntityDefinitions(LogicalName='{t}')?$select=EntitySetName")["EntitySetName"]
            for t in ("lzw_financetransaction", "lzw_bankaccount", "lzw_financecategory")}
    data = json.dumps({"properties": {
        "connectionReferences": {DV: {"runtimeSource": "embedded", "api": {"name": DV},
                                      "connection": {"connectionReferenceLogicalName": bf.CR_DV}}},
        "definition": definition(sets)}, "schemaVersion": "1.0.0.0"})
    q = f"workflows?$select=workflowid,statecode&$filter=category eq 5 and name eq '{FLOW_NAME}'"
    ex = dv.get(q)["value"]
    if ex:
        wid, on = ex[0]["workflowid"], ex[0]["statecode"] == 1
        if on and "--update-on" not in sys.argv:
            print("  flow exists and is ON; left untouched (pass --update-on to update it)")
            return
        if on:
            dv.patch(f"workflows({wid})", {"statecode": 0, "statuscode": 1})
        dv.patch(f"workflows({wid})", {"clientdata": data})
        if on:
            dv.patch(f"workflows({wid})", {"statecode": 1, "statuscode": 2})
        print("  flow definition updated", "(turned off, updated, turned back on)" if on else "(still OFF)")
        return
    dv.post("workflows", {
        "category": 5, "name": FLOW_NAME, "type": 1, "primaryentity": "none",
        "description": "Daily 6 AM (Brisbane): creates a Finance Transaction for each open Planned Transaction "
                       "(appointment) dated today or earlier, then sets the appointment to Completed.",
        "clientdata": data,
    }, solution=True, done=lambda: bool(dv.get(q)["value"]))
    print("  + flow created (OFF):", FLOW_NAME)


if __name__ == "__main__":
    main()
