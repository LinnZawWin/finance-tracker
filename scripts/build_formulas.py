"""Phase 2b: rollup and formula columns.

Rollups are sent as XAML. The five formula columns (spec kind "calc") are Power Fx formula columns:
Decimal, precision 2, SourceType 3, with the formula text from spec.py in FormulaDefinition.
A formula column cannot be Currency, so currency inputs are wrapped in Decimal().

Usage:
  python build_formulas.py              create every rollup/formula column that is missing; report failures
  python build_formulas.py --fallback   for rollups that still do not exist, create a plain column of the
                                        same type and name. Never applied to formula columns.
  python build_formulas.py --dump NAME  print the generated definition for one column logical name
"""
import sys

import dv
import spec
from dv import label

V9 = "Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35"
V4 = "Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089"
WF = f"Microsoft.Crm.Workflow, {V9}"
HEADER = (
    '<?xml version="1.0" encoding="utf-16"?><Activity x:Class="XrmWorkflow00000000000000000000000000000000" '
    'xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" '
    f'xmlns:mcwc="clr-namespace:Microsoft.Crm.Workflow.ClientActivities;assembly=Microsoft.Crm.Workflow, {V9}" '
    'xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities, Version=4.0.0.0, '
    'Culture=neutral, PublicKeyToken=31bf3856ad364e35" '
    f'xmlns:mxs="clr-namespace:Microsoft.Xrm.Sdk;assembly=Microsoft.Xrm.Sdk, {V9}" '
    f'xmlns:mxsq="clr-namespace:Microsoft.Xrm.Sdk.Query;assembly=Microsoft.Xrm.Sdk, {V9}" '
    f'xmlns:mxswa="clr-namespace:Microsoft.Xrm.Sdk.Workflow.Activities;assembly=Microsoft.Xrm.Sdk.Workflow, {V9}" '
    f'xmlns:s="clr-namespace:System;assembly=mscorlib, {V4}" '
    f'xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib, {V4}" '
    f'xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=mscorlib, {V4}" '
    'xmlns:srs="clr-namespace:System.Runtime.Serialization;assembly=System.Runtime.Serialization, '
    f'{V4}" xmlns:this="clr-namespace:" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'
    '<x:Members><x:Property Name="InputEntities" Type="InArgument(scg:IDictionary(x:String, mxs:Entity))" />'
    '<x:Property Name="CreatedEntities" Type="InArgument(scg:IDictionary(x:String, mxs:Entity))" /></x:Members>'
    '<this:XrmWorkflow00000000000000000000000000000000.InputEntities>'
    '<InArgument x:TypeArguments="scg:IDictionary(x:String, mxs:Entity)" />'
    '</this:XrmWorkflow00000000000000000000000000000000.InputEntities>'
    '<this:XrmWorkflow00000000000000000000000000000000.CreatedEntities>'
    '<InArgument x:TypeArguments="scg:IDictionary(x:String, mxs:Entity)" />'
    '</this:XrmWorkflow00000000000000000000000000000000.CreatedEntities>'
    '<mva:VisualBasic.Settings>Assembly references and imported namespaces for internal implementation'
    '</mva:VisualBasic.Settings>'
)
NULLTYPE = ('<InArgument x:TypeArguments="s:Type"><mxswa:ReferenceLiteral x:TypeArguments="s:Type">'
            '<x:Null /></mxswa:ReferenceLiteral></InArgument>')
PRIMARY = '[InputEntities(&quot;primaryEntity&quot;)]'
TEMP = '[CreatedEntities(&quot;primaryEntity#Temp&quot;)]'


def typeref(t):
    return f'<InArgument x:TypeArguments="s:Type"><mxswa:ReferenceLiteral x:TypeArguments="s:Type" Value="{t}" /></InArgument>'


def get_prop(attr, entity, var, target=None):
    tt = typeref(target) if target else NULLTYPE
    return (f'<mxswa:GetEntityProperty Attribute="{attr}" Entity="{PRIMARY}" EntityName="{entity}" Value="[{var}]">'
            f'<mxswa:GetEntityProperty.TargetType>{tt}</mxswa:GetEntityProperty.TargetType></mxswa:GetEntityProperty>')


def evaluate(op, params, target, result):
    tt = (typeref(target) if target else NULLTYPE).replace(
        '<InArgument x:TypeArguments="s:Type">', '<InArgument x:TypeArguments="s:Type" x:Key="TargetType">', 1)
    return (f'<mxswa:ActivityReference AssemblyQualifiedName="Microsoft.Crm.Workflow.Activities.EvaluateExpression, {WF}" '
            'DisplayName="EvaluateExpression"><mxswa:ActivityReference.Arguments>'
            f'<InArgument x:TypeArguments="x:String" x:Key="ExpressionOperator">{op}</InArgument>'
            f'<InArgument x:TypeArguments="s:Object[]" x:Key="Parameters">[New Object() {{ {params} }}]</InArgument>'
            + tt
            + f'<OutArgument x:TypeArguments="x:Object" x:Key="Result">[{result}]</OutArgument>'
            '</mxswa:ActivityReference.Arguments></mxswa:ActivityReference>')


def condition(op, value_var, operand_var, result):
    return (f'<mxswa:ActivityReference AssemblyQualifiedName="Microsoft.Crm.Workflow.Activities.EvaluateCondition, {WF}" '
            'DisplayName="EvaluateCondition"><mxswa:ActivityReference.Arguments>'
            f'<InArgument x:TypeArguments="mxsq:ConditionOperator" x:Key="ConditionOperator">{op}</InArgument>'
            f'<InArgument x:TypeArguments="s:Object[]" x:Key="Parameters">[New Object() {{ {value_var} }}]</InArgument>'
            f'<InArgument x:TypeArguments="x:Object" x:Key="Operand">[{operand_var}]</InArgument>'
            f'<OutArgument x:TypeArguments="x:Boolean" x:Key="Result">[{result}]</OutArgument>'
            '</mxswa:ActivityReference.Arguments></mxswa:ActivityReference>')


def optionset_literal(value, kind, result):
    return evaluate("CreateCrmType",
                    f'Microsoft.Xrm.Sdk.Workflow.WorkflowPropertyType.OptionSetValue, "{value}", "{kind}"',
                    "mxs:OptionSetValue", result)


# ---------------------------------------------------------------- rollup

def rollup_xaml(parent, child, relationship, agg, source, flt_attr, flt_op, flt_value, flt_kind):
    p = "RollupRuleStep1"
    key = f"relatedlinked_{relationship}#{parent}#{child}#Temp"
    return (HEADER + '<mxswa:Workflow><Sequence DisplayName="RollupRuleStep1">'
            '<Sequence DisplayName="Source"><Sequence.Variables>'
            '<Variable x:TypeArguments="x:String" Default="[Nothing]" Name="HierarchicalRelationshipName" />'
            '</Sequence.Variables></Sequence>'
            '<Sequence DisplayName="Target"><Sequence.Variables>'
            f'<Variable x:TypeArguments="x:Boolean" Default="False" Name="{p}_1" />'
            f'<Variable x:TypeArguments="x:Object" Name="{p}_2" /><Variable x:TypeArguments="x:Object" Name="{p}_3" />'
            '</Sequence.Variables>'
            f'<mcwc:SetAttributeValue DisplayName="{child}.{parent}.{relationship}" '
            f'Entity="[CreatedEntities(&quot;{key}&quot;)]" EntityName="{child}" />'
            + get_prop(flt_attr, child, f"{p}_2")
            + optionset_literal(flt_value, flt_kind, f"{p}_3")
            + condition(flt_op, f"{p}_3", f"{p}_2", f"{p}_1")
            + '</Sequence><Sequence DisplayName="Aggregate"><Sequence.Variables>'
            f'<Variable x:TypeArguments="x:Object" Name="{p}_4" /><Variable x:TypeArguments="x:Object" Name="{p}_5" />'
            '</Sequence.Variables>'
            + get_prop(source, child, f"{p}_5")
            + evaluate(agg, f"{p}_5", None, f"{p}_4")
            + '</Sequence></Sequence></mxswa:Workflow></Activity>')


# ---------------------------------------------------------------- driver

def formula_for(t, col):
    tl = spec.table_logical(t)
    cl = spec.logical(col["name"])
    if col["kind"] == "calc":
        return 3, col["formula"]
    child = col["child"]
    relationship = f"{child}_{col['rel_lookup'][4:]}"
    attr, op, val = col["flt"]
    if attr == "statecode":
        value, kind = val, "State"
    else:
        value, kind = spec.option_value(spec.find_choice(child, attr), val), "Picklist"
    source = col["source"] or child + "id"
    return 2, rollup_xaml(tl, child, relationship, col["agg"], source, attr, op, value, kind)


def body_for(col, source_type=None, xaml=None):
    if col["kind"] == "calc":  # Power Fx formula column: Decimal, no MinValue / MaxValue
        return {"@odata.type": "Microsoft.Dynamics.CRM.DecimalAttributeMetadata",
                "SchemaName": spec.schema_name(col["name"]), "DisplayName": label(col["name"]),
                "RequiredLevel": {"Value": "None"}, "Precision": 2, "SourceType": 3, "FormulaDefinition": xaml}
    typ = "IntegerAttributeMetadata" if col.get("type") == "int" else "MoneyAttributeMetadata"
    b = {"@odata.type": f"Microsoft.Dynamics.CRM.{typ}", "SchemaName": spec.schema_name(col["name"]),
         "DisplayName": label(col["name"]), "RequiredLevel": {"Value": "None"}}
    if typ == "MoneyAttributeMetadata":
        b.update(Precision=2, PrecisionSource=0, MinValue=-spec.BIG, MaxValue=spec.BIG)
    else:
        b.update(Format="None", MinValue=-2147483648, MaxValue=2147483647)
    if source_type:
        b.update(SourceType=source_type, FormulaDefinition=xaml)
    return b


def main():
    fallback = "--fallback" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    for t in spec.TABLES:
        tl = spec.table_logical(t)
        for col in t["columns"]:
            if col["kind"] not in ("rollup", "calc"):
                continue
            cl = spec.logical(col["name"])
            if "--dump" in sys.argv:
                if cl in only:
                    print(formula_for(t, col)[1])
                continue
            if only and cl not in only and f"{tl}.{cl}" not in only:
                continue
            if dv.exists(f"EntityDefinitions(LogicalName='{tl}')/Attributes(LogicalName='{cl}')?$select=LogicalName"):
                print(f"exists {tl}.{cl}")
                continue
            if fallback and col["kind"] == "calc":
                print(f"skipped {tl}.{cl}: formula columns have no plain fallback")
                continue
            if fallback:
                dv.post(f"EntityDefinitions(LogicalName='{tl}')/Attributes", body_for(col), solution=True)
                print(f"PLAIN (maintained by script) {tl}.{cl}")
                continue
            st, xaml = formula_for(t, col)
            try:
                dv.post(f"EntityDefinitions(LogicalName='{tl}')/Attributes", body_for(col, st, xaml), solution=True,
                        done=lambda: dv.exists(f"EntityDefinitions(LogicalName='{tl}')/Attributes(LogicalName='{cl}')?$select=LogicalName"))
                print(f"created {col['kind']} {tl}.{cl}")
            except dv.DvError as e:
                print(f"FAILED {col['kind']} {tl}.{cl}: {e}")


if __name__ == "__main__":
    main()
