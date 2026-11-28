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


def dt(name, **kw):
    return dict(kind="datetime", name=name, **kw)


def money(name, signed=False, **kw):
    return dict(kind="money", name=name, signed=signed, **kw)


def dec(name, lo=-100000000000, hi=100000000000, places=2, **kw):
    return dict(kind="decimal", name=name, lo=lo, hi=hi, places=places, **kw)


def integer(name):
    return dict(kind="int", name=name)


def lookup(name, target, required=False, schema=None):
    return dict(kind="lookup", name=name, target=target, required=required, schema=schema)


def rollup(name, kind, child, rel_lookup, agg, source=None, flt=None):
    """flt = (attribute, operator, option label) on the child table, or ('statecode','Equal',0)."""
    return dict(kind="rollup", name=name, type=kind, child=child, rel_lookup=rel_lookup,
                agg=agg, source=source, flt=flt)


def calc(name, formula):
    """Power Fx formula column (Decimal, precision 2). Formulas use logical names."""
    return dict(kind="calc", name=name, formula=formula)


TABLES = [
    dict(schema="lzw_BankAccount", display="Bank Account", plural="Bank Accounts", primary="Name", columns=[
        s("Short Name", 100, description="Aliases used in expense notes, separated by semicolons"),
        lookup("Bank", "account", schema="lzw_BankId"),
        choice("Account Type", ["Everyday", "Savings", "Credit Card", "Wise", "Other", "Super", "Employer"]),
        lookup("Account Currency", "transactioncurrency"),
        s("Account Number", 50, description="As written on statements and in transfer descriptions; cards: last digits only"),
        yn("Statements Imported", True),
        dec("Last Rate", 0, 1000000000, places=6,
            description="Foreign cash: units of the account currency per 1 AUD from the last time this currency "
                        "was bought or received. Converts cash spends to AUD"),
        date("Last Rate Date", description="Date of the conversion that gave Last Rate"),
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
        choice("Source", ["Screenshot", "CSV", "PDF", "Generated"]),
        yn("Is Pending"),
        choice("Status", ["Unmatched", "Partly Matched", "Matched", "Transfer", "Ignored"], "Unmatched"),
        lookup("Transfer Counterpart", "lzw_bankstatementline"),
        s("Duplicate Key", 600),
        date("Posted Date", description="Date the bank processed the line; Transaction Date is the purchase date"),
        s("Bank Reference", 100, description="The bank's own reference or ID for the line"),
        integer("Line Number"),
        s("Card Holder", 100),
        money("Fee Amount", False, description="Fee the bank charged on this line, already included in Amount"),
        s("Bank Category", 100, description="Category the bank or card assigned"),
        rollup("Allocated Amount", "money", "lzw_reconciliationmatch", "lzw_BankStatementLine", "Sum",
               source="lzw_allocatedamount", flt=("lzw_matchstatus", "Equal", "Confirmed")),
        calc("Unallocated Amount", "Decimal(lzw_amount) - Decimal(lzw_allocatedamount)"),
        memo("Notes"),
    ]),
    dict(schema="lzw_FinanceTransaction", display="Finance Transaction", plural="Finance Transactions",
         primary="Description", columns=[
        dt("Transaction Date", required=True,
           description="Date and time. The time orders the transactions within a day"),
        choice("Type", ["Expense", "Income", "Transfer"], "Expense"),
        s("Payee", 200),
        money("Amount", False, description="The real amount, positive for income and expenses. Type sets the "
                                           "direction. Estimates (Payment Type Estimated) are overwritten with the "
                                           "bank figure when reconciled"),
        lookup("Paid From", "lzw_bankaccount"),
        lookup("Transfer To", "lzw_bankaccount"),
        dec("Original Amount", 0, 100000000000,
            description="Amount in the original (foreign) currency, positive. Amount is the AUD value"),
        lookup("Original Currency", "transactioncurrency"),
        lookup("Category", "lzw_financecategory"),
        lookup("Project", "lzw_financeproject"),
        gchoice("Share Type", "Mine"),
        yn("Needs Details", False),
        choice("Source", ["Keep", "Manual", "Import"]),
        s("Source Row ID", 100),
        rollup("Actual Amount", "money", "lzw_reconciliationmatch", "lzw_FinanceTransaction", "Sum",
               source="lzw_allocatedamount", flt=("lzw_matchstatus", "Equal", "Confirmed")),
        # Amount minus the bank's confirmed amount with its sign turned into a cost: 0 once fully reconciled.
        # Expense and Transfer take money out of Paid From; Income brings it in.
        calc("Reconciliation Difference", "Decimal(lzw_amount) - If(Value(lzw_type) = 859130001, "
                                          "Decimal(lzw_actualamount), Decimal(lzw_actualamount) * -1)"),
        calc("Partner Share", "If(Value(lzw_sharetype) = 859130001, Decimal(lzw_amount) * 0.5, "
                              "Value(lzw_sharetype) = 859130002, Decimal(lzw_amount), 0)"),
        # A transfer moves my own money between accounts: no cost.
        calc("My Cost", "If(Value(lzw_type) = 859130002, 0, Decimal(lzw_amount) - lzw_partnershare)"),
        choice("Reconciliation Status", ["Unreconciled", "Partly Reconciled", "Reconciled"], "Unreconciled"),
        # Claims (owner, 2026-11-25): Employer = reimbursed by the employer (closed by the claim bank line),
        # Income Tax = a deduction in the tax return (closed when the return is lodged).
        choice("Claim Type", ["Employer", "Income Tax"],
               description="Employer: reimbursed by the employer into a bank account. Income Tax: claimed as a deduction"),
        choice("Claim Status", ["Pending", "Claimed"],
               description="Pending until the whole Claim Amount is reimbursed (Employer) or lodged in a tax return (Income Tax)"),
        money("Claim Amount", False, description="The part of Amount to claim, positive. Empty = the whole Amount"),
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
    ]),
    dict(schema="lzw_FinanceCategory", display="Finance Category", plural="Finance Categories", primary="Name", columns=[
        lookup("Parent Category", "lzw_financecategory"),
        choice("Category Type", ["Expense", "Income", "Both"]),
        # 60/20/20 plan (owner, 2026-11-28): which part of take-home pay an expense category belongs to.
        choice("Budget Group", ["Needs", "Wants", "Savings"]),
    ]),
    dict(schema="lzw_FinanceProject", display="Finance Project", plural="Finance Projects", primary="Name", columns=[
        choice("Project Type", ["Trip", "Event", "Home", "Other"]),
        date("Start Date"), date("End Date"),
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
        calc("Net Cost", "Decimal(lzw_totalcost) - Decimal(lzw_saleproceeds)"),
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
