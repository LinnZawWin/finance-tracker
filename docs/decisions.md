# Finance Tracker: decisions and pending items

Why things were built the way they were, and what is still open. Read this with [schema.md](schema.md)
and the rules in [../CLAUDE.md](../CLAUDE.md).

## Pending items

| # | Item | Who | Notes |
|---|---|---|---|
| 1 | Create the five calculated columns in the maker editor | Owner | See "Calculated columns" below for names and formulas |
| 2 | Put the calculated columns back on forms and views, verify, regenerate `schema.md` | Claude | Run `build_ui.py`, then `verify.py --write-docs`, after item 1 |
| 3 | Change the base currency from NZD to AUD, then add CNY and other currencies | Owner | Claude must not touch Currency |
| 4 | Create the Google Sheet (worksheet `Inbox`, headers A to L) and set `lzw_KeepInboxSheetId` | Owner | Layout is in `CLAUDE.md` |
| 5 | Create the Google Sheets connection, bind both connection references, turn the flow on | Owner | The flow has never run; the first run is its real test |
| 6 | Agree the confidence threshold for auto-confirming AI matches | Owner | Not set yet; reconciliation rules depend on it |
| 7 | Test `recalc.py` and `statement_compare.py --apply` with real rows | Claude | Both have only run against empty tables |

## Decisions and reasoning

### Build method
- **Web API scripts instead of the model-apps `app-builder` skill.** The skill's engine generates its own
  names and does not cover rollup columns, so it could not guarantee the exact logical names required.
  Its reference material was used for the app module and site map payloads.
- **Flow created through the Dataverse `workflows` table instead of the power-automate FlowAgent tooling.**
  FlowAgent builds flows on existing embedded connections. No Google Sheets connection existed and the
  requirement was connection references, so the flow was created as a solution-aware record, left off.
- **The Dataverse MCP server and the `dataverse` npm CLI were not used**, by rule (MCP is billed).
- **All writes are idempotent and re-check before retrying.** The session's network proxy drops requests
  that are silent for about 10 seconds while Dataverse still completes them. A blind retry would create
  duplicates, so `dv.py` re-checks existence after a dropped write.

### Naming
- Lookup columns follow the convention (`lzw_bankaccount`, `lzw_paidfrom`, `lzw_category`), except Bank
  Account.Bank, which is `lzw_bankid` as specified.
- Every primary column is `lzw_name`, including those displayed as "Description".
- Relationship schema names are `<child table>_<Lookup>` (for example `lzw_reconciliationmatch_FinanceTransaction`).
- Option values start at 859130000 (the publisher's option prefix).

### Rollup columns
- Created through the API by copying the exact structure of an existing rollup in the environment.
- Each has one filter: Match Status = Confirmed (amounts), Role = Sale or not Sale (asset totals).
- **Line Count counts active lines only.** A rollup without a filter had no known-good template, so the
  proven "active rows" filter was used.
- Money rollups aggregate through the base currency, so totals can carry exchange-rate rounding until the
  base currency is AUD.

### Calculated columns
- Dataverse rejected every calculated formula sent through the API (error 0x80060424). Microsoft states
  that formulas are only supported through the maker editor.
- They were first created as plain currency columns "maintained by script". The owner then chose real
  calculated columns, so those five plain columns were deleted (all were empty) and are to be recreated
  by hand. A plain column cannot be converted to calculated, which is why they had to be deleted.
- Create them in this order, type Currency, behaviour Calculated, precision 2:

| # | Table | Display name | Formula |
|---|---|---|---|
| 1 | Bank Statement Line | Unallocated Amount | `lzw_amount - lzw_allocatedamount` |
| 2 | Finance Transaction | Actual Cost | IF Type = Expense: `lzw_actualamount * -1`. ELSE: `lzw_actualamount` |
| 3 | Finance Transaction | Partner Share | IF Share Type = Shared with Partner (A): `lzw_actualcost * 0.5`. ELSE IF All for Partner (AA): `lzw_actualcost`. ELSE: `0` |
| 4 | Finance Transaction | My Cost | `lzw_actualcost - lzw_partnershare` |
| 5 | Finance Asset | Net Cost | `lzw_totalcost - lzw_saleproceeds` |

- A calculated column is blank while any column it uses is blank, so these stay empty until the rollup
  they depend on has a value.
- Never run `build_formulas.py --fallback`: it recreates them as plain columns.

### Views, forms and app
- Each table's default "Active" view was given useful columns and is the view used by form subgrids.
- **Editable grid is set per table, not per view**, so inline editing applies to every Reconciliation
  Match view, not only Proposed Matches.
- "Banks" in the site map is a URL sub-area that opens Account with the Banks view, because a table
  sub-area cannot pin a view.
- Opening and Closing Balance allow negative values, because credit card balances can be negative.

### Flow
- Sheet headers with spaces are read with the connector's encoding (`Row_x0020_ID`, `AUD_x0020_Amount`).
- Rows are updated through the connector's own `__PowerAppsId__` column.
- "Get rows" defaults to 256 rows, so the flow asks for 5,000. Archive processed rows before that limit.
- The worksheet is set by name (`Inbox`). If the connector needs it picked from its list, re-select it
  in the designer.
- A row whose Row ID already exists is skipped and its Processed cell stays empty, as specified, so it
  is re-checked every hour.
- Each row runs inside a scope. A failure leaves the row unprocessed and the loop continues.
- The flow sets the row currency to AUD explicitly, because new rows otherwise take the base currency.

### Currency
- The environment's base currency was NZD at build time and Currency was deliberately not touched.
  AUD existed as an additional currency. The platform added `transactioncurrency` and `account` to the
  solution as references only.

### Repository
- No solution export is committed, because it contains the publisher's display name.
- The publisher unique name and environment URL are read from environment variables, never stored here.
- Statement files and parsed lines stay outside the repo (see `.gitignore`).
