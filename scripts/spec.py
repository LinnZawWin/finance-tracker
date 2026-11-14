"""Finance Tracker schema specification (single source of truth for the build scripts)."""

OPT = 859130000  # option value prefix of the lzw publisher

SHARE_TYPE = ["Mine", "Shared with Partner (A)", "All for Partner (AA)", "Paid for Others"]

BIG = 922337203685477


def s(name, length=200, **kw):
    return dict(kind="string", name=name, length=length, **kw)


def memo(name):
    return dict(kind="memo", name=name)


def yn(name, default=False):
    return dict(kind="bool", name=name, default=default)


def choice(name, options, default=None, **kw):
    return dict(kind="choice", name=name, options=options, default=default, **kw)


def gchoice(name, default=None):
    return dict(kind="gchoice", name=name, default=default)


def date(name, **kw):
    return dict(kind="date", name=name, **kw)


def dt(name):
    return dict(kind="datetime", name=name)


def money(name, signed=False, **kw):
    return dict(kind="money", name=name, signed=signed, **kw)


def dec(name, lo=-100000000000, hi=100000000000):
    return dict(kind="decimal", name=name, lo=lo, hi=hi)


def integer(name):
    return dict(kind="int", name=name)


def lookup(name, target, required=False, schema=None):
    return dict(kind="lookup", name=name, target=target, required=required, schema=schema)


def rollup(name, kind, child, rel_lookup, agg, source=None, flt=None):
    """flt = (attribute, operator, option label) on the child table, or ('statecode','Equal',0)."""
    return dict(kind="rollup", name=name, type=kind, child=child, rel_lookup=rel_lookup,
                agg=agg, source=source, flt=flt)


def calc(name, formula):
    return dict(kind="calc", name=name, formula=formula)


TABLES = [
    dict(schema="lzw_BankAccount", display="Bank Account", plural="Bank Accounts", primary="Name", columns=[
        s("Short Name", 100, description="Aliases used in expense notes, separated by semicolons"),
        lookup("Bank", "account", schema="lzw_BankId"),
        choice("Account Type", ["Everyday", "Savings", "Credit Card", "Wise", "Other"]),
        lookup("Account Currency", "transactioncurrency"),
        yn("Statements Imported", True),
        yn("Is Active", True),
    ]),
    dict(schema="lzw_BankStatement", display="Bank Statement", plural="Bank Statements", primary="Name", columns=[
        lookup("Bank Account", "lzw_bankaccount", True),
        date("Period Start"), date("Period End"),
        choice("Source Type", ["Screenshot", "CSV", "PDF", "Other"]),
        dict(kind="file", name="Source File"),
        money("Opening Balance", True), money("Closing Balance", True),
        dt("Imported On"),
        rollup("Line Count", "int", "lzw_bankstatementline", "lzw_BankStatement", "Count",
               flt=("statecode", "Equal", 0)),
        memo("Notes"),
    ]),
    dict(schema="lzw_BankStatementLine", display="Bank Statement Line", plural="Bank Statement Lines",
         primary="Description", primary_len=500, columns=[
        lookup("Bank Statement", "lzw_bankstatement", True),
        lookup("Bank Account", "lzw_bankaccount", True),
        date("Transaction Date", required=True),
        money("Amount", True, description="Signed like the bank: negative = money out (AUD)"),
        dec("Original Amount"),
        lookup("Original Currency", "transactioncurrency"),
        money("Running Balance", True),
        s("Merchant", 200),
        choice("Source", ["Screenshot", "CSV", "PDF"]),
        yn("Is Pending"),
        choice("Status", ["Unmatched", "Partly Matched", "Matched", "Transfer", "Ignored"], "Unmatched"),
        lookup("Transfer Counterpart", "lzw_bankstatementline"),
        s("Duplicate Key", 600),
        rollup("Allocated Amount", "money", "lzw_reconciliationmatch", "lzw_BankStatementLine", "Sum",
               source="lzw_allocatedamount", flt=("lzw_matchstatus", "Equal", "Confirmed")),
        calc("Unallocated Amount", ("sub", "lzw_amount", "lzw_allocatedamount")),
        memo("Notes"),
    ]),
    dict(schema="lzw_FinanceTransaction", display="Finance Transaction", plural="Finance Transactions",
         primary="Description", columns=[
        date("Transaction Date", required=True),
        choice("Type", ["Expense", "Income"], "Expense"),
        s("Payee", 200),
        money("Estimated Amount", False, description="Positive amount (AUD)"),
        lookup("Paid From", "lzw_bankaccount"),
        lookup("Category", "lzw_financecategory"),
        lookup("Project", "lzw_financeproject"),
        gchoice("Share Type", "Mine"),
        yn("Needs Details", False),
        choice("Source", ["Keep", "Manual", "Import"]),
        s("Source Row ID", 100),
        rollup("Actual Amount", "money", "lzw_reconciliationmatch", "lzw_FinanceTransaction", "Sum",
               source="lzw_allocatedamount", flt=("lzw_matchstatus", "Equal", "Confirmed")),
        calc("Actual Cost", ("if", ("lzw_type", "Expense"), ("mul", "lzw_actualamount", "-1"),
                             ("field", "lzw_actualamount"))),
        calc("Partner Share", ("if", ("lzw_sharetype", "Shared with Partner (A)"), ("mul", "lzw_actualcost", "0.5"),
                               ("lzw_sharetype", "All for Partner (AA)"), ("field", "lzw_actualcost"),
                               ("const", "0"))),
        calc("My Cost", ("sub", "lzw_actualcost", "lzw_partnershare")),
        choice("Reconciliation Status", ["Unreconciled", "Partly Reconciled", "Reconciled"], "Unreconciled"),
        memo("Notes"),
    ]),
    dict(schema="lzw_ReconciliationMatch", display="Reconciliation Match", plural="Reconciliation Matches",
         primary="Name", autonumber="RM-{SEQNUM:6}", columns=[
        lookup("Bank Statement Line", "lzw_bankstatementline", True),
        lookup("Finance Transaction", "lzw_financetransaction", True),
        money("Allocated Amount", True, description="Signed like the bank line"),
        choice("Match Method", ["Rule", "AI Auto", "AI Proposed", "Manual"]),
        choice("Match Status", ["Proposed", "Confirmed", "Rejected"], "Proposed"),
        dec("Confidence", 0, 1),
        memo("AI Reasoning"),
        dt("Confirmed On"),
    ]),
    dict(schema="lzw_BankRule", display="Bank Rule", plural="Bank Rules", primary="Name", columns=[
        s("Match Text", 200),
        choice("Match Type", ["Contains", "Starts With", "Exact"], "Contains"),
        lookup("Bank Account", "lzw_bankaccount"),
        s("Default Payee", 200), s("Default Description", 200),
        lookup("Default Category", "lzw_financecategory"),
        gchoice("Default Share Type"),
        integer("Priority"),
        yn("Is Active", True),
    ]),
    dict(schema="lzw_FinanceCategory", display="Finance Category", plural="Finance Categories", primary="Name", columns=[
        lookup("Parent Category", "lzw_financecategory"),
        choice("Category Type", ["Expense", "Income", "Both"]),
        yn("Is Active", True),
    ]),
    dict(schema="lzw_FinanceProject", display="Finance Project", plural="Finance Projects", primary="Name", columns=[
        choice("Project Type", ["Trip", "Event", "Home", "Other"]),
        date("Start Date"), date("End Date"),
        yn("Is Active", True),
    ]),
    dict(schema="lzw_FinanceAsset", display="Finance Asset", plural="Finance Assets", primary="Name", columns=[
        choice("Asset Type", ["Clothing", "Gadget", "Furniture", "Appliance", "Equipment", "Other"]),
        s("Brand", 100), s("Model", 100), s("Serial Number", 100),
        choice("Status", ["Owned", "Sold", "Gifted", "Disposed", "Lost"], "Owned"),
        date("Disposal Date"), date("Warranty Expiry"),
        dict(kind="image", name="Photo"),
        rollup("Total Cost", "money", "lzw_financeassetlink", "lzw_FinanceAsset", "Sum",
               source="lzw_allocatedamount", flt=("lzw_role", "NotEqual", "Sale")),
        rollup("Sale Proceeds", "money", "lzw_financeassetlink", "lzw_FinanceAsset", "Sum",
               source="lzw_allocatedamount", flt=("lzw_role", "Equal", "Sale")),
        calc("Net Cost", ("sub", "lzw_totalcost", "lzw_saleproceeds")),
        memo("Notes"),
    ]),
    dict(schema="lzw_FinanceAssetLink", display="Finance Asset Link", plural="Finance Asset Links",
         primary="Name", autonumber="AL-{SEQNUM:6}", columns=[
        lookup("Finance Asset", "lzw_financeasset", True),
        lookup("Finance Transaction", "lzw_financetransaction", True),
        choice("Role", ["Purchase", "Accessory or Repair", "Refund", "Sale"]),
        money("Allocated Amount", True,
              description="Positive for purchase, accessory and sale; negative for refund"),
        memo("Notes"),
    ]),
]


def schema_name(display, override=None):
    return override or "lzw_" + display.replace(" ", "")


def logical(display, override=None):
    return schema_name(display, override).lower()


def table_logical(t):
    return t["schema"].lower()


def rel_name(table, col):
    return f"{table_logical(table)}_{schema_name(col['name'], col.get('schema'))[4:]}"


def option_value(options, label):
    return OPT + options.index(label)


def find_choice(table_logical_name, col_logical):
    """Return the option list for a choice column (local or the Share Type global)."""
    for t in TABLES:
        if table_logical(t) == table_logical_name:
            for c in t["columns"]:
                if logical(c["name"], c.get("schema")) == col_logical:
                    return SHARE_TYPE if c["kind"] == "gchoice" else c["options"]
    raise KeyError((table_logical_name, col_logical))
