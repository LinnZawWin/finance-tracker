"""Shared helpers for the cloud flow scripts (used by build_recurring_flow.py).

The Keep import flow, its environment variable lzw_KeepInboxSheetId and the Google Sheets connection reference
lzw_FinanceTrackerGoogleSheets were removed (flow 2026-11-20, the other two 2026-11-28): the web page replaced them.
"""
import dv

CR_DV = "lzw_FinanceTrackerDataverse"
DV_API = "shared_commondataserviceforapps"
TZ = "E. Australia Standard Time"  # Windows name for Australia/Brisbane


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
