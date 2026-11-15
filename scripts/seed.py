"""Seed data: created only if missing. Never deletes or overwrites existing values (except Is Bank on Accounts)."""
import dv
import spec

O = spec.OPT
BANKS = ["ANZ", "AMEX", "Wise", "Kogan Money"]
ACCOUNT_TYPES = ["Everyday", "Savings", "Credit Card", "Wise", "Other"]
# Old name -> new name. Applied first, so a rename is never re-created under its old name.
RENAMED_ACCOUNTS = {"ANZ Flex": "ANZ Plus Flex Saver", "ANZ Savings": "ANZ Plus Growth Saver"}
RENAMED_PROJECTS = {"Yunnan Trip": "China Yunnan Trip"}
RENAMED_CATEGORIES = {"Dining and Drinks": "Dining", "Tobacco and Vape": "Smoking"}
BANK_ACCOUNTS = [  # name, short name, account type, bank
    ("ANZ Plus Everyday", "Everyday;ANZ", "Everyday", "ANZ"),
    ("ANZ Plus Flex Saver", "Flex", "Savings", "ANZ"),
    ("ANZ Plus Growth Saver", "Savings", "Savings", "ANZ"),
    ("AMEX Credit Card", "AMEX", "Credit Card", "AMEX"),
    ("Wise", "Wise", "Wise", "Wise"),
    ("Kogan Money Black Card", "Kogan", "Credit Card", "Kogan Money"),
]
EXPENSE = ["Groceries", "Dining", "Drinks", "Smoking", "Transport", "Rent and Housing", "Utilities",
           "Insurance", "Health", "Personal Care", "Subscriptions", "Entertainment", "Sport and Fitness", "Shopping",
           "Home and Hardware", "Clothing", "Gifts", "Travel", "Education", "Pets", "Tax", "Fines",
           "Legal and Professional", "Cash Withdrawal", "Fees and Charges", "Support Payments", "Other Expense"]
INCOME = ["Salary and Contract Income", "Interest", "Refund", "Reimbursement", "Asset Sale", "Other Income"]
CHILDREN = {"Transport": ["Public Transport", "Rideshare and Taxi", "Fuel", "Tolls", "Parking", "Car Maintenance"]}


def find(entity_set, id_col, name_col, name):
    q = name.replace("'", "''")
    r = dv.get(f"{entity_set}?$select={id_col}&$filter={name_col} eq '{q}'")["value"]
    return r[0][id_col] if r else None


def ensure(entity_set, id_col, name_col, name, body):
    rid = find(entity_set, id_col, name_col, name)
    if rid:
        return rid, False
    dv.post(entity_set, {name_col: name, **body}, done=lambda: find(entity_set, id_col, name_col, name) is not None)
    return find(entity_set, id_col, name_col, name), True


def rename(entity_set, id_col, renames, extra=None):
    for old, new in renames.items():
        rid = find(entity_set, id_col, "lzw_name", old)
        if rid and not find(entity_set, id_col, "lzw_name", new):
            dv.patch(f"{entity_set}({rid})", {"lzw_name": new, **(extra or {}).get(new, {})})
            print("renamed", old, "->", new)


def main():
    rename("lzw_bankaccounts", "lzw_bankaccountid", RENAMED_ACCOUNTS,
           {"ANZ Plus Flex Saver": {"lzw_accounttype": O + ACCOUNT_TYPES.index("Savings")}})
    rename("lzw_financecategories", "lzw_financecategoryid", RENAMED_CATEGORIES)
    rename("lzw_financeprojects", "lzw_financeprojectid", RENAMED_PROJECTS)
    bank_ids = {}
    for b in BANKS:
        rid, created = ensure("accounts", "accountid", "name", b, {"lzw_isbank": True})
        if not created:
            dv.patch(f"accounts({rid})", {"lzw_isbank": True})
        bank_ids[b] = rid
        print(("created" if created else "updated Is Bank on"), "account", b)
    for name, short, typ, bank in BANK_ACCOUNTS:
        _, created = ensure("lzw_bankaccounts", "lzw_bankaccountid", "lzw_name", name, {
            "lzw_shortname": short, "lzw_accounttype": O + ACCOUNT_TYPES.index(typ),
            "lzw_BankId@odata.bind": f"/accounts({bank_ids[bank]})"})
        print("created" if created else "exists ", "bank account", name)
    for i, names in enumerate((EXPENSE, INCOME)):
        for name in names:
            _, created = ensure("lzw_financecategories", "lzw_financecategoryid", "lzw_name", name,
                                {"lzw_categorytype": O + i})
            print("created" if created else "exists ", "category", name)
    for parent, names in CHILDREN.items():
        pid = find("lzw_financecategories", "lzw_financecategoryid", "lzw_name", parent)
        for name in names:
            _, created = ensure("lzw_financecategories", "lzw_financecategoryid", "lzw_name", name, {
                "lzw_categorytype": O, "lzw_ParentCategory@odata.bind": f"/lzw_financecategories({pid})"})
            print("created" if created else "exists ", "category", parent, ">", name)
    _, created = ensure("lzw_financeprojects", "lzw_financeprojectid", "lzw_name", "China Yunnan Trip",
                        {"lzw_projecttype": O})
    print("created" if created else "exists ", "project China Yunnan Trip")


if __name__ == "__main__":
    main()
