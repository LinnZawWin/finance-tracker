"""Phase 2a: solution, global choice, tables, plain columns and lookups. Idempotent; never deletes."""
import os
import sys
import time

import dv
import spec
from dv import label

# Unique name of the existing publisher with prefix lzw. Passed in so no name is stored in this repo.
PUBLISHER = os.environ.get("DATAVERSE_PUBLISHER", "")
REPORT = []


def note(msg):
    print(msg, flush=True)
    REPORT.append(msg)


def ensure_solution():
    r = dv.get(f"solutions?$select=solutionid&$filter=uniquename eq '{dv.SOLUTION}'")["value"]
    if r:
        return
    if not PUBLISHER:
        sys.exit("Set DATAVERSE_PUBLISHER to the unique name of the lzw publisher before the first run.")
    pub = dv.get(f"publishers?$select=publisherid&$filter=uniquename eq '{PUBLISHER}'")["value"][0]["publisherid"]
    dv.post("solutions", {
        "uniquename": dv.SOLUTION, "friendlyname": "Finance Tracker", "version": "1.0.0.0",
        "publisherid@odata.bind": f"/publishers({pub})",
    })
    note("created solution " + dv.SOLUTION)


def ensure_global_choice():
    if dv.exists("GlobalOptionSetDefinitions(Name='lzw_sharetype')"):
        gid = dv.get("GlobalOptionSetDefinitions(Name='lzw_sharetype')")["MetadataId"]
        dv.add_to_solution(gid, 9)
        return gid
    _, h = dv.post("GlobalOptionSetDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
        "Name": "lzw_sharetype", "DisplayName": label("Share Type"), "IsGlobal": True,
        "OptionSetType": "Picklist",
        "Options": [{"Value": spec.OPT + i, "Label": label(o)} for i, o in enumerate(spec.SHARE_TYPE)],
    }, solution=True)
    note("created global choice lzw_sharetype")
    return dv.new_id(h)


def base(col, typ):
    b = {
        "@odata.type": f"Microsoft.Dynamics.CRM.{typ}",
        "SchemaName": spec.schema_name(col["name"], col.get("schema")),
        "DisplayName": label(col["name"]),
        "RequiredLevel": {"Value": "ApplicationRequired" if col.get("required") else "None"},
    }
    if col.get("description"):
        b["Description"] = label(col["description"])
    return b


def bool_options():
    return {"TrueOption": {"Value": 1, "Label": label("Yes")}, "FalseOption": {"Value": 0, "Label": label("No")},
            "OptionSetType": "Boolean"}


def column_body(col, share_type_id):
    k = col["kind"]
    if k == "string":
        return {**base(col, "StringAttributeMetadata"), "MaxLength": col["length"], "FormatName": {"Value": "Text"}}
    if k == "memo":
        return {**base(col, "MemoAttributeMetadata"), "MaxLength": 10000, "Format": "TextArea"}
    if k == "bool":
        return {**base(col, "BooleanAttributeMetadata"), "DefaultValue": bool(col["default"]), "OptionSet": bool_options()}
    if k == "choice":
        b = {**base(col, "PicklistAttributeMetadata"), "OptionSet": {
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata", "IsGlobal": False, "OptionSetType": "Picklist",
            "Options": [{"Value": spec.OPT + i, "Label": label(o)} for i, o in enumerate(col["options"])]}}
        if col["default"]:
            b["DefaultFormValue"] = spec.option_value(col["options"], col["default"])
        return b
    if k == "gchoice":
        b = {**base(col, "PicklistAttributeMetadata"),
             "GlobalOptionSet@odata.bind": f"/GlobalOptionSetDefinitions({share_type_id})"}
        if col["default"]:
            b["DefaultFormValue"] = spec.option_value(spec.SHARE_TYPE, col["default"])
        return b
    if k == "date":
        return {**base(col, "DateTimeAttributeMetadata"), "Format": "DateOnly", "DateTimeBehavior": {"Value": "DateOnly"}}
    if k == "datetime":
        return {**base(col, "DateTimeAttributeMetadata"), "Format": "DateAndTime", "DateTimeBehavior": {"Value": "UserLocal"}}
    if k == "money":
        return {**base(col, "MoneyAttributeMetadata"), "Precision": 2, "PrecisionSource": 0,
                "MinValue": -spec.BIG if col["signed"] else 0, "MaxValue": spec.BIG}
    if k == "decimal":
        return {**base(col, "DecimalAttributeMetadata"), "Precision": 2, "MinValue": col["lo"], "MaxValue": col["hi"]}
    if k == "int":
        return {**base(col, "IntegerAttributeMetadata"), "Format": "None", "MinValue": -2147483648, "MaxValue": 2147483647}
    if k == "file":
        return {**base(col, "FileAttributeMetadata"), "MaxSizeInKB": 32768}
    if k == "image":
        return {**base(col, "ImageAttributeMetadata"), "IsPrimaryImage": True, "CanStoreFullImage": True, "MaxSizeInKB": 10240}
    raise ValueError(k)


EXPECTED_TYPE = {"string": "String", "memo": "Memo", "bool": "Boolean", "choice": "Picklist", "gchoice": "Picklist",
                 "date": "DateTime", "datetime": "DateTime", "money": "Money", "decimal": "Decimal", "int": "Integer",
                 "file": "Virtual", "image": "Virtual", "lookup": "Lookup"}


def existing_attr(tl, cl):
    try:
        return dv.get(f"EntityDefinitions(LogicalName='{tl}')/Attributes(LogicalName='{cl}')?$select=AttributeType")
    except dv.DvError as e:
        if e.code == 404:
            return None
        raise


def ensure_table(t):
    tl = spec.table_logical(t)
    if dv.exists(f"EntityDefinitions(LogicalName='{tl}')?$select=LogicalName"):
        mid = dv.get(f"EntityDefinitions(LogicalName='{tl}')?$select=MetadataId")["MetadataId"]
        dv.add_to_solution(mid, 1)
        note(f"table {tl}: exists, added to solution")
        return
    primary = {
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata", "SchemaName": "lzw_Name",
        "IsPrimaryName": True, "MaxLength": t.get("primary_len", 200), "FormatName": {"Value": "Text"},
        "DisplayName": label(t["primary"]),
        "RequiredLevel": {"Value": "None" if t.get("autonumber") else "ApplicationRequired"},
    }
    if t.get("autonumber"):
        primary["AutoNumberFormat"] = t["autonumber"]
    dv.post("EntityDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
        "SchemaName": t["schema"], "DisplayName": label(t["display"]), "DisplayCollectionName": label(t["plural"]),
        "Description": label(f"Finance Tracker: {t['display']}"),
        "OwnershipType": "UserOwned", "HasNotes": False, "HasActivities": False, "IsActivity": False,
        "PrimaryNameAttribute": "lzw_name", "Attributes": [primary],
    }, solution=True, done=lambda: dv.exists(f"EntityDefinitions(LogicalName='{tl}')?$select=LogicalName"))
    note(f"table {tl}: created")


def ensure_column(tl, col, share_type_id):
    cl = spec.logical(col["name"], col.get("schema"))
    ex = existing_attr(tl, cl)
    if ex:
        if ex["AttributeType"] != EXPECTED_TYPE[col["kind"]]:
            note(f"TYPE MISMATCH {tl}.{cl}: exists as {ex['AttributeType']}, expected {EXPECTED_TYPE[col['kind']]} (left as is)")
        return
    try:
        dv.post(f"EntityDefinitions(LogicalName='{tl}')/Attributes", column_body(col, share_type_id), solution=True,
                done=lambda: existing_attr(tl, cl) is not None)
        print(f"  + {tl}.{cl}", flush=True)
    except dv.DvError as e:
        note(f"SKIPPED {tl}.{cl}: {e}")


def ensure_lookup(t, col):
    tl = spec.table_logical(t)
    cl = spec.logical(col["name"], col.get("schema"))
    ex = existing_attr(tl, cl)
    if ex:
        if ex["AttributeType"] != "Lookup":
            note(f"TYPE MISMATCH {tl}.{cl}: exists as {ex['AttributeType']}, expected Lookup (left as is)")
        return
    target = col["target"]
    body = {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
        "SchemaName": spec.rel_name(t, col),
        "ReferencedEntity": target, "ReferencingEntity": tl,
        "CascadeConfiguration": {"Assign": "NoCascade", "Delete": "Restrict", "Merge": "NoCascade",
                                 "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade",
                                 "RollupView": "NoCascade"},
        "AssociatedMenuConfiguration": {"Behavior": "UseCollectionName", "Group": "Details", "Order": 10000},
        "Lookup": {
            "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
            "SchemaName": spec.schema_name(col["name"], col.get("schema")),
            "DisplayName": label(col["name"]),
            "RequiredLevel": {"Value": "ApplicationRequired" if col["required"] else "None"},
        },
    }
    try:
        dv.post("RelationshipDefinitions", body, solution=True, done=lambda: existing_attr(tl, cl) is not None)
        print(f"  + lookup {tl}.{cl} -> {target}", flush=True)
    except dv.DvError as e:
        note(f"SKIPPED lookup {tl}.{cl}: {e}")


def ensure_account_isbank():
    if existing_attr("account", "lzw_isbank"):
        return
    dv.post("EntityDefinitions(LogicalName='account')/Attributes", {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata", "SchemaName": "lzw_IsBank",
        "DisplayName": label("Is Bank"), "RequiredLevel": {"Value": "None"}, "DefaultValue": False,
        "OptionSet": bool_options(),
    }, solution=True)
    note("account.lzw_isbank: created")


def main():
    ensure_solution()
    gid = ensure_global_choice()
    # Account goes into the solution without its existing components (shell only).
    acc = dv.get("EntityDefinitions(LogicalName='account')?$select=MetadataId")["MetadataId"]
    dv.post("AddSolutionComponent", {"ComponentId": acc, "ComponentType": 1, "SolutionUniqueName": dv.SOLUTION,
                                     "AddRequiredComponents": False, "DoNotIncludeSubcomponents": True})
    ensure_account_isbank()
    for t in spec.TABLES:
        ensure_table(t)
    time.sleep(20)
    for t in spec.TABLES:
        for col in t["columns"]:
            if col["kind"] not in ("lookup", "rollup", "calc"):
                ensure_column(spec.table_logical(t), col, gid)
    time.sleep(20)
    for t in spec.TABLES:
        for col in t["columns"]:
            if col["kind"] == "lookup":
                ensure_lookup(t, col)
    print("\n== report ==")
    print("\n".join(REPORT))


if __name__ == "__main__":
    sys.exit(main())
