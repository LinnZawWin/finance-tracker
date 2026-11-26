"""Phase 2d: SVG icons for the model-driven app and every table. Idempotent; never deletes.
The standard Account table is left alone: its icon is shared with every other app in the environment.

Creates one SVG web resource per icon (type 11, in the solution), sets IconVectorName on each lzw_ table and
the web resource on the app module. Table icons use currentColor so they take the theme colour. Run after build_ui.py, then publish.
"""
import base64

import dv

NAVY = "#001A4D"

# 32x32 glyphs drawn with strokes (inner markup only). Colour is applied by the wrapper.
GLYPHS = {
    "lzw_bankaccount": '<path d="M3 12 16 4l13 8z"/><path d="M6 14v10M12 14v10M20 14v10M26 14v10M3 28h26"/>',
    "lzw_bankstatement": '<path d="M7 3h14l5 5v21H7z"/><path d="M21 3v5h5M11 14h11M11 19h11M11 24h7"/>',
    "lzw_bankstatementline": '<path d="M4 9h24M4 16h24M4 23h24"/><circle cx="8" cy="9" r="1"/><circle cx="8" cy="16" r="1"/><circle cx="8" cy="23" r="1"/>',
    "lzw_financetransaction": '<path d="M4 11h21l-5-5M28 21H7l5 5"/>',
    "lzw_reconciliationmatch": '<circle cx="11" cy="16" r="7"/><circle cx="21" cy="16" r="7"/>',
    "lzw_bankrule": '<path d="M4 8h24l-9 10v9l-6-3v-6z"/>',
    "lzw_financecategory": '<path d="M4 4h12l12 12-12 12L4 16z"/><circle cx="10" cy="10" r="1.5"/>',
    "lzw_financeproject": '<path d="M3 9h10l3 3h13v15H3z"/>',
    "lzw_financeasset": '<path d="M16 3 28 9.5v13L16 29 4 22.5v-13z"/><path d="M4 9.5 16 16l12-6.5M16 16v13"/>',
    "lzw_financeassetlink": '<path d="M13 19a5 5 0 0 0 7 0l5-5a5 5 0 0 0-7-7l-2 2"/><path d="M19 13a5 5 0 0 0-7 0l-5 5a5 5 0 0 0 7 7l2-2"/>',
}
APP_NAME = "lzw_/icons/financetracker_app.svg"


def svg(inner, background=None):
    """Table icons match the built-in Fluent icons: 20 px, a 1 px line and currentColor, so the app colours them
    like the standard tables (no hard-coded colour, as Microsoft recommends for IconVectorName)."""
    if background:  # the app icon keeps its own tile
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
                f'<rect width="32" height="32" rx="4" fill="{background}"/>'
                f'<g fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'{inner}</g></svg>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="20" height="20">'
            '<g style="fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round">'
            f'{inner}</g></svg>')


def ensure_webresource(name, display, content):
    b64 = base64.b64encode(content.encode()).decode()
    q = f"webresourceset?$select=webresourceid&$filter=name eq '{name}'"
    rows = dv.get(q)["value"]
    if rows:
        wid = rows[0]["webresourceid"]
        dv.patch(f"webresourceset({wid})", {"content": b64})
        print(f"  ~ {name}", flush=True)
    else:
        dv.post("webresourceset", {"name": name, "displayname": display, "webresourcetype": 11, "content": b64},
                solution=True, done=lambda: bool(dv.get(q)["value"]))
        wid = dv.get(q)["value"][0]["webresourceid"]
        print(f"  + {name}", flush=True)
    dv.add_to_solution(wid, 61)
    return wid


def main():
    for table, inner in GLYPHS.items():
        name = f"lzw_/icons/{table}.svg"
        ensure_webresource(name, f"Icon {table}", svg(inner))
        path = f"EntityDefinitions(LogicalName='{table}')"
        m = dv.get(path)  # the whole definition: table metadata only accepts PUT, not PATCH
        if m.get("IconVectorName") != name:
            m["IconVectorName"] = name
            try:
                dv.call("PUT", path, m, solution=True, headers={"MSCRM.MergeLabels": "true"},
                        done=lambda: dv.get(path + "?$select=IconVectorName").get("IconVectorName") == name)
                print(f"  icon set on {table}", flush=True)
            except dv.DvError as e:
                print(f"  ICON FAILED {table}: {e}", flush=True)
    wid = ensure_webresource(APP_NAME, "Icon Finance Tracker app",
                             svg('<path d="M4 9h18v13H4z"/><path d="M10 9V5h18v13h-6"/>', background=NAVY))
    rows = dv.get("appmodules/Microsoft.Dynamics.CRM.RetrieveUnpublishedMultiple()?$select=appmoduleid,uniquename")["value"]
    app = next((a["appmoduleid"] for a in rows if a["uniquename"] == "lzw_FinanceTracker"), None)
    if app:
        dv.patch(f"appmodules({app})", {"webresourceid": wid})
        print("  app icon set", flush=True)
    print("publishing...", flush=True)
    try:
        dv.publish_all()
    except Exception as e:  # the proxy may drop the call; it still completes server side
        print("  publish call interrupted:", type(e).__name__, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
