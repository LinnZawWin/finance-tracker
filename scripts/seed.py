"""Seed data: created only if missing. Never deletes or overwrites existing values (except Is Bank on Accounts)."""
import dv
import spec

O = spec.OPT
BANKS = ["ANZ", "AMEX", "Wise"]
ACCOUNT_TYPES = ["Everyday", "Savings", "Credit Card", "Wise", "Other"]
BANK_ACCOUNTS = [  # name, short name, account type, bank
    ("ANZ Plus Everyday", "Everyday;ANZ", "Everyday", "ANZ"),
    ("ANZ Flex", "Flex", "Everyday", "ANZ"),
    ("ANZ Savings", "Savings", "Savings", "ANZ"),
    ("AMEX Credit Card", "AMEX", "Credit Card", "AMEX"),
    ("Wise", "Wise", "Wise", "Wise"),
]
EXPENSE = ["Groceries", "Dining and Drinks", "Transport", "Rent and Housing", "Utilities", "Insurance", "Health",
           "Subscriptions", "Entertainment", "Shopping", "Clothing", "Gifts", "Travel", "Education",
           "Fees and Charges", "Support Payments", "Other Expense"]
INCOME = ["Salary and Contract Income", "Interest", "Refund", "Asset Sale", "Other Income"]


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


def main():
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
    _, created = ensure("lzw_financeprojects", "lzw_financeprojectid", "lzw_name", "Yunnan Trip", {"lzw_projecttype": O})
    print("created" if created else "exists ", "project Yunnan Trip")


if __name__ == "__main__":
    main()
