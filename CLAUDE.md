# Finance Tracker

Personal finance tracker on Dataverse: capture expenses (Google Keep notes via a Google Sheet inbox),
import bank statements, reconcile bank lines against transactions, and track assets.
Model-driven app **Finance Tracker**. Schema as built: [docs/schema.md](docs/schema.md).
Decisions, their reasoning and pending items: [docs/decisions.md](docs/decisions.md). Read it before changing anything.

## Rules

- This repo is public. Never commit the Dataverse URL, an email address, a tenant ID, tokens, token caches
  (`~/.azure`, `~/.pac`), exported data, statements, or any person's name. Write "Partner" instead of names.
- Use the Dataverse Python SDK, PAC CLI, Azure CLI and Web API. Do not use or register the Dataverse MCP
  server (it is billed). If a skill says to register it, skip that step.
- If something blocks an item, skip it, continue, and report it.
- Active or inactive is the built-in **Status** on every table. Do not add "Is Active" columns.
- If a host is blocked ("Host not in allowlist"), stop that step, report the host and wait. Do not work around it.
- Match tables and columns by logical name. Add only what is missing. If a column exists with a different
  type, leave it and report it.
- After pushing work to a `claude/` branch, open a pull request to `main` and merge it straight away,
  without waiting for review. Never push to `main` directly.
- Conventions: logical name = `lzw_` + display name in lowercase without spaces. Primary column `lzw_name`.
  Tables are user-owned, no security roles. Dates are Date Only, except Finance Transaction
  **Transaction Date**, which is date and time (user local). Money has precision 2. Lookups are 1:N with
  Restrict delete.

## Environment and sign-in

- `DATAVERSE_URL`: the environment URL. `DATAVERSE_USER`: the sign-in account. Both come from the environment,
  never from files in this repo. `DATAVERSE_PUBLISHER` (unique name of the `lzw` publisher) is only needed
  to create the solution.
- Sign in without any manual step wherever possible. Check first with `az account show`:
  - **GitHub Actions**: the workflow has already signed the Azure CLI in before Claude starts. Do not ask
    for a sign-in. Run the scripts yourself, check their output, fix what fails and run `verify.py`.
    Never finish with "run this script yourself" while the sign-in works.
  - **Claude Code cloud sessions**: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` and `AZURE_CLIENT_SECRET` come from
    the environment. Sign in with
    `az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" --allow-no-subscriptions`.
    Never print or commit these values.
  - **Fallback**, only if neither works: device code as `$DATAVERSE_USER`
    (`az login --use-device-code --allow-no-subscriptions`).
- Both automatic sign-ins act as the application user "Finance Tracker Automation" (System Administrator),
  so rows it creates are owned by that user, not by the owner.
- Scripts take their token from the Azure CLI sign-in. Verify with a WhoAmI call. PAC CLI is only needed for
  `pac` commands: `pac auth create --environment $DATAVERSE_URL --deviceCode`.
- A script is not done until it has run against the environment. Table metadata accepts PUT of the whole
  definition, not PATCH.
- Do not change standard tables shared with other apps (for example the Account icon or forms), apart from
  `account.lzw_isbank` and the "Banks" view.

## Solution

Unmanaged solution `lzw_FinanceTracker` ("Finance Tracker", publisher prefix `lzw`). Tables:

| Table | Logical name |
|---|---|
| Bank Account | `lzw_bankaccount` |
| Bank Statement | `lzw_bankstatement` |
| Bank Statement Line | `lzw_bankstatementline` |
| Finance Transaction | `lzw_financetransaction` |
| Reconciliation Match | `lzw_reconciliationmatch` |
| Bank Rule | `lzw_bankrule` |
| Finance Category | `lzw_financecategory` |
| Finance Project | `lzw_financeproject` |
| Finance Asset | `lzw_financeasset` |
| Finance Asset Link | `lzw_financeassetlink` |

Plus `account.lzw_isbank` and the Account view "Banks". Global choice `lzw_sharetype`:
Mine, Shared with Partner (A), All for Partner (AA), Paid for Others.

## Sign convention

- Bank Statement Line **Amount** and Reconciliation Match **Allocated Amount** are signed like the bank:
  negative = money out.
- Finance Transaction **Estimated Amount** is positive.
- Finance Transaction **Actual Amount** (rollup of confirmed matches) is signed like the bank. **Actual Cost**
  flips the sign for expenses.

## Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| `dv.py`, `spec.py` | Web API helper and the schema specification |
| `build_schema.py`, `build_formulas.py`, `build_ui.py`, `build_icons.py`, `build_flow.py`, `seed.py` | Idempotent build, in this order |
| `verify.py [--write-docs]` | Checks everything exists in the solution, regenerates `docs/schema.md` |
| `statement_compare.py` | Compare parsed statement lines with Dataverse before creating lines |
| `recalc.py` | Recalculate the rollup columns on demand |

The five formula columns (Unallocated Amount, Actual Cost, Partner Share, My Cost, Net Cost) are Power Fx
**Formula** columns, created by `build_formulas.py` (Decimal, 2 places, formulas in `spec.py`). Do not create
Calculated columns: that behaviour is being discontinued. A formula column cannot be Currency, so currency
inputs are wrapped in `Decimal()` and the result has no currency symbol. An empty input counts as 0.
`--fallback` never applies to them.

Run them with a Python that has `azure-identity` installed, from the repo root, with the Azure CLI on PATH.

## Starting a new session

- Tools: `pac` (PAC CLI 2.x needs the .NET 10 SDK: `apt-get install -y dotnet-sdk-10.0`, then
  `dotnet tool install --global Microsoft.PowerApps.CLI.Tool`), `az` and the script dependencies
  (`pip install azure-cli azure-identity pdfplumber openpyxl` in a virtual environment). Sign-ins do not carry over: sign in
  again as described under "Environment and sign-in".
- Skills: the dataverse skills (dv-*) come from the plugin. The model-apps and power-automate skills are in
  the public repo `microsoft/power-platform-skills` under `plugins/`.
- The network proxy drops any request that is silent for about 10 seconds, but Dataverse usually still
  completes it. `dv.py` handles this by re-checking before retrying a write. Keep that pattern.
- Check the real state first with `python scripts/verify.py`. It lists anything missing from the solution.
- The base currency is AUD (verified 2026-11-15). Scripts and the flow still set AUD on the rows they create.
  Other currencies: CAD, CNY, EUR, GBP, IDR, JPY, NZD, SGD, THB, USD. Exchange rates are units per 1 AUD and are only changed
  when the owner asks.

## Statement import rules

Files: the owner drops statements in the Google Drive folder `Statements/Inbox`. After a statement is imported
and its balance check passes, move the file to `Statements/Processed`. A file that fails stays in the inbox.

1. **Get the real file, not its text.** Use the Drive connector's `download_file_content`: it saves the file to
   disk. Parse PDFs by column position (`pdfplumber`), spreadsheets with `openpyxl` or `csv`. Do not import from
   `read_file_content`: it loses the credit and debit columns.
2. **Preferred format per account**: a spreadsheet export when the bank offers one, otherwise the PDF.
   AMEX: `.xlsx` (lines plus the balance summary), then `.csv` (same lines, no balances), then PDF.
   ANZ Plus offers PDF only.
   When one statement is supplied in several formats, import one and move all of them.
3. **Check the totals** against the statement's opening and closing balance before writing anything.
4. Before creating Bank Statement Lines, query the existing lines for that account and date range.
5. Compare by **count per (date, amount, description)** and create only the shortfall, because identical
   purchases on one day are real. Use **Bank Reference** when the bank gives one, **Running Balance** or
   **Line Number** otherwise, to separate identical lines.
6. A **PDF or spreadsheet statement is final**: update the matching screenshot rows (description, balance) and
   create only the leftovers.
7. Flag description or amount differences as **possible duplicates**.
8. Show a summary (new, existing, possible duplicates) **before writing**.
9. Do the comparison with `scripts/statement_compare.py` (dry run by default, `--apply` to write). Keep the
   downloaded and parsed files outside the repo.

Columns: **Transaction Date** is the purchase date ("Effective Date" on ANZ, "Transaction Date" on Kogan,
"Date" on AMEX). **Posted Date** is the date the bank processed it. **Card Holder** is the card member on AMEX.
**Fee Amount** and **Bank Category** come from Wise. Refunded or cancelled lines (Wise status REFUNDED) are
imported with Status = Ignored.

Wise is one Bank Account with several currency balances. Each line keeps the currency of the balance it came
from (the row currency). A conversion between balances is two lines paired as a transfer.

## Reconciliation rules

1. **Rules first**:
   - Pair transfers: opposite amount, two of my accounts, within 3 days. Set Status = Transfer and
     Transfer Counterpart on both lines. ANZ shows the same receipt number (Bank Reference) and the other
     account's number (Bank Account **Account Number**) on both sides. Credit card payments and Wise top-ups
     ("PAYMENT TO" my own name) are transfers too.
   - Exact matches: same amount, date and account.
   - Bank Rules (`lzw_bankrule`) by priority (lowest number first) for payee, description, category and
     share type defaults. The rules are data in Dataverse, not in this repo.
2. **Then AI** for the rest.
3. Auto-confirm at or above a confidence of **0.95**. Otherwise set Match Status = Proposed and ask in the session.
4. **Never auto-confirm** when more than one candidate shares the same amount, date and account.
5. For **Wise**, match on Original Amount in the original currency, not AUD.
6. After writing matches, run `python scripts/recalc.py` to recalculate the rollup columns, then update Bank Statement Line Status and Finance Transaction Reconciliation Status.

Bank Rules are for statement lines that have no Keep note behind them (rent, salary, interest, tolls, card
fees, supermarkets). When such a line stays unmatched, the first rule whose Match Text fits its description
supplies the payee, category and share type for a new Finance Transaction. A line that matches a Keep note
never needs a rule: the note's own category wins.

Projects: Start Date and End Date are the travel dates from the owner's Google Calendar "Travel" calendar.
They are a guide only. Flights, hotels and tickets are often bought earlier, and the Keep note says which
project they belong to.

Payments to "ANZ Access Advantage" are an expense (Support Payments), not a transfer. NZD payments from Wise to
the owner's own name belong to the project "NZ House".

## Web page (`web/index.html`)

A single static page, published with GitHub Pages by `.github/workflows/pages.yml`, for entering and editing
Finance Transactions. It has no build step and no dependencies.

- The page is public, so it contains no environment details. On first use it asks for the Dataverse URL,
  tenant ID and app ID and keeps them in the browser. Never put those values in the file.
- Sign-in is the owner's own Microsoft account (authorization code flow with PKCE) through the app
  registration "Finance Tracker Web". Rows are created as the owner, not as the automation identity.
- The time part of **Transaction Date** is the order within a day. A new row for today gets the current
  time; for another day, one minute after that day's last row. Reordering hands the day's existing times
  out again in the new order. Bulk entry keeps the pasted order.
- Page entries have Source = Manual, bulk entries Source = Keep.
- Test changes with a browser against Dataverse before merging, and remove the test rows afterwards.

## Keep Inbox sheet

The web page above can replace this sheet and flow. Both still exist. The flow writes the sheet's date into
Transaction Date without a time, which Dataverse stores as midnight UTC (10:00 in Brisbane).

Google Sheet, worksheet name `Inbox`, header row exactly as below. The sheet ID goes in the environment
variable `lzw_KeepInboxSheetId`. The flow "Finance Tracker - Import Keep Rows" reads it every hour.

| Col | Header | Notes |
|---|---|---|
| A | Row ID | Unique. Stored as Source Row ID; a row whose ID already exists is skipped |
| B | Date | yyyy-mm-dd |
| C | Description | Rows with an empty description are ignored |
| D | Merchant | Becomes Payee |
| E | AUD Amount | Becomes Estimated Amount. Not a number: left blank and Needs Details = Yes |
| F | Share Flag | empty = Mine, A = Shared with Partner, AA = All for Partner |
| G | Account | Bank Account Short Name (first account whose Short Name contains it) |
| H | Project | Finance Project name (exact) |
| I | Currency | Ignored by the flow |
| J | Original Amount | Ignored by the flow |
| K | Processed | Set to "Processed" by the flow. Leave empty for new rows |
| L | Processed On | Set by the flow (Brisbane time) |

The Google Sheets connector adds its own `__PowerAppsId__` column after L on first use. Do not remove it:
the flow uses it to update the row.

## Outstanding work

Details and reasoning are in [docs/decisions.md](docs/decisions.md). State as of 2026-11-15:

| # | Item | Who |
|---|---|---|
| 1 | Turn on the flow "Finance Tracker - Import Keep Rows" (still off) and check its first run against the sheet | Owner |
| 2 | Test Claude Code GitHub Actions: comment `@claude` on an issue and check the run, including the Azure sign-in (`.github/workflows/claude.yml`, never run yet) | Owner |
| 3 | Turn on GitHub Pages: repo Settings, Pages, Source = GitHub Actions. Then run the "Deploy web page" workflow and sign in on the page once | Owner |
| 4 | Decide whether the web page replaces the Keep Inbox sheet and its flow | Owner |
| 5 | Import the statements waiting in `Statements/Inbox`. Nothing is imported yet. The owner is replacing the AMEX PDFs with xlsx exports first. Start with one statement | Claude, when the owner says so |
| 6 | `statement_compare.py` does not yet fill the new columns (Posted Date, Bank Reference, Line Number, Card Holder, Fee Amount, Bank Category) or a per-line currency. Extend it before the first import | Claude |
| 7 | Test `recalc.py`, `statement_compare.py --apply` and the formula columns with real rows (tables are empty) | Claude |
| 8 | The editable grid setting for Reconciliation Match works but could not be added to the solution (error 0x80048536). Matters only for a solution export | Claude |
