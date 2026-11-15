# Finance Tracker: decisions and pending items

Why things were built the way they were, and what is still open. Read this with [schema.md](schema.md)
and the rules in [../CLAUDE.md](../CLAUDE.md).

## Pending items

| # | Item | Who | Notes |
|---|---|---|---|
| 1 | Turn on the flow "Finance Tracker - Import Keep Rows" | Owner | Still off on 2026-11-15. It has never run; the first run is its real test |
| 2 | Test Claude Code GitHub Actions | Owner | `.github/workflows/claude.yml` was added on 2026-11-15 and has never run. Comment `@claude` on an issue and check the run, including the Azure sign-in |
| 3 | Import the statements in `Statements/Inbox` | Claude | 33 PDFs, AMEX xlsx and csv, Wise csv, read and reviewed on 2026-11-15. Nothing imported. Waits for the owner |
| 4 | Extend `statement_compare.py` for the new line columns and per-line currency | Claude | Needed before the first import |
| 5 | Test `recalc.py`, `statement_compare.py --apply` and the formula columns with real rows | Claude | All have only run against empty tables |
| 6 | Add the Reconciliation Match editable grid setting to the solution | Claude | The setting is active, but `AddSolutionComponent` fails with 0x80048536. Only matters for a solution export |

Done on 2026-11-15: the five formula columns were created and put on forms and views; base currency
verified as AUD; `lzw_KeepInboxSheetId` verified against the sheet URL; both connection references
verified as bound; confidence threshold agreed at 0.95. `verify.py`: 370 checks, 0 problems.

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
- Money rollups aggregate through the base currency, which is now AUD.

### Formula columns
- History: Dataverse rejected calculated formulas sent through the API (error 0x80060424), so the five
  columns were first plain columns, then deleted to be recreated by hand as Calculated columns. Before
  that happened the owner chose **Formula** columns instead, because the Calculated behaviour is being
  discontinued.
- They are created by `build_formulas.py` as `DecimalAttributeMetadata` with `SourceType` 3 and the
  Power Fx text in `FormulaDefinition`. The API accepted this. Microsoft's developer documentation says
  that defining formulas with code is not supported, so if a later change is rejected, edit the formula in
  the maker editor and keep `spec.py` in step.
- **Decimal, not Currency.** A formula column cannot produce Currency. Currency inputs are wrapped in
  `Decimal()`. The columns show no currency symbol and do not follow the convention "Money has precision 2".
- Choices are compared by value (`Value(lzw_type) = 859130000`), which avoids display names in formulas.
- An empty input counts as 0, so these columns show 0 where a Calculated column would be blank.
- Formulas (logical names):

| # | Table | Display name | Formula |
|---|---|---|---|
| 1 | Bank Statement Line | Unallocated Amount | `Decimal(lzw_amount) - Decimal(lzw_allocatedamount)` |
| 2 | Finance Transaction | Actual Cost | `If(Value(lzw_type) = 859130000, Decimal(lzw_actualamount) * -1, Decimal(lzw_actualamount))` |
| 3 | Finance Transaction | Partner Share | `If(Value(lzw_sharetype) = 859130001, lzw_actualcost * 0.5, Value(lzw_sharetype) = 859130002, lzw_actualcost, 0)` |
| 4 | Finance Transaction | My Cost | `lzw_actualcost - lzw_partnershare` |
| 5 | Finance Asset | Net Cost | `Decimal(lzw_totalcost) - Decimal(lzw_saleproceeds)` |

### Reconciliation
- **Confidence threshold 0.95** (owner, 2026-11-15). AI matches at or above it are auto-confirmed, the
  rest are Proposed. Confidence is stored with 2 decimal places.

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
- The base currency was NZD at build time. The owner has since changed it to AUD (verified 2026-11-15).
- On 2026-11-15, at the owner's request, CNY and CAD were added and every exchange rate was set from the
  Reserve Bank of Australia table for 13 Nov 2026 (units of foreign currency per 1 AUD):
  USD 0.6804, CNY 4.5380, EUR 0.6153, GBP 0.5142, NZD 1.2273, CAD 0.9701.
  Source: https://www.rba.gov.au/statistics/frequency/exchange-rates.html
- Rates are not updated automatically. A row keeps the rate it was saved with.
- The platform added `transactioncurrency` and `account` to the solution as references only.

### Automation identity
- App registration **Finance Tracker Automation** (single tenant) with a service principal, added to the
  environment as an application user with the **System Administrator** role (the owner's choice, so that
  automation can change schema as well as data).
- **GitHub Actions uses no secret**: two GitHub federated credentials for this repository,
  `repo:<owner>/finance-tracker:ref:refs/heads/main` (issues and conversation comments) and
  `repo:<owner>/finance-tracker:pull_request` (pull request events, added 2026-11-15 so that reviews and
  review comments can reach Dataverse). GitHub does not give an identity token to pull requests from forks.
- **Claude Code cloud sessions use a client secret** (owner's choice, 2026-11-15, to avoid the device-code
  sign-in in every session). It is stored only as environment variables in the owner's personal cloud
  environment. It expires and must be renewed in the app registration; device code is the fallback.
- The client ID and tenant ID are not stored in this repo. They belong in GitHub secrets.
- The workflow `.github/workflows/claude.yml` signs in with `azure/login` (OIDC, `allow-no-subscriptions: true`,
  `permissions: id-token: write`), passes `DATAVERSE_URL` from the secret and installs `azure-identity`.
  The scripts then get their token from the Azure CLI as usual. Claude is allowed to run `python scripts/*`.
- The Azure step uses `continue-on-error`, so a failed sign-in leaves Claude running without Dataverse access.
- Claude signs in with the secret `CLAUDE_CODE_OAUTH_TOKEN`.

### Statement review (2026-11-15)
- Every file in `Statements/Inbox` was read before any import, and the schema and reference data were
  extended to fit. Added columns: Bank Account **Account Number**; Bank Statement Line **Posted Date**,
  **Bank Reference**, **Line Number**, **Card Holder**, **Fee Amount**, **Bank Category**.
- **Getting the real file.** The Drive connector's text view of a PDF drops the credit and debit columns.
  `download_file_content` saves the binary to disk instead. Parsed by column position with `pdfplumber`,
  an ANZ statement's credit and debit totals matched its opening and closing balance exactly.
- **AMEX format.** The `.xlsx` export has one row per line with purchase date, processed date, card member,
  foreign amount, a unique reference, and a balance summary. The `.csv` has the same rows without balances.
  The PDF has neither the reference nor the processed date. So: xlsx, then csv, then PDF.
- **Wise** stays one account. Lines keep the currency of the balance they came from. Refunded lines are
  imported as Ignored. The CSV repeats an ID when one purchase is split across two balances, so the
  duplicate key is ID plus source currency.
- **Categories.** "Dining and Drinks" was renamed "Dining" and "Drinks" split out (bars and liquor stores).
  New: Tobacco and Vape, Personal Care, Sport and Fitness, Home and Hardware, Pets, Tax, Fines, Legal and
  Professional, Cash Withdrawal, Reimbursement (income), and six children of Transport.
- **Accounts.** "ANZ Flex" and "ANZ Savings" were renamed to the statement names (ANZ Plus Flex Saver, ANZ
  Plus Growth Saver). Kogan Money Black Card was added. `seed.py` renames before it creates, so old names
  are not re-created.
- **Kept out of the repo** because they are personal: account numbers, projects other than the seeded one,
  and the Bank Rules (48 created). They live only in Dataverse.
- **Status instead of "Is Active".** The custom "Is Active" column was deleted from Bank Account, Bank
  Rule, Finance Category and Finance Project on the owner's instruction (every value was Yes). The built-in
  Status (Active / Inactive) is on the forms instead. Inactive rows drop out of lookups and default views.
- **The "never delete" rule was removed** by the owner on 2026-11-15.
- "Tobacco and Vape" was renamed "Smoking".
- **Project dates** come from the owner's Google Calendar "Travel" calendar (all-day events, end date
  inclusive). The seeded "Yunnan Trip" takes its dates from the calendar event for the same trip.
- **Bank Rules** only apply to statement lines with no Keep note. No script applies them yet: they are
  read during reconciliation.
- JPY, SGD, THB and IDR were added with the Reserve Bank of Australia rates for 13 Nov 2026
  (108.81, 0.8753, 23.02, 12385 per 1 AUD).

### Icons
- `build_icons.py` creates one SVG web resource per table (`lzw_/icons/<table>.svg`) plus the app icon and
  sets `IconVectorName`. Run against the environment on 2026-11-15.
- The Account table is not given an icon: it is a standard table shared with the owner's other apps.
- The first GitHub Actions run (issue 7) wrote the script but did not run it, although the workflow had
  signed in to Azure, because `CLAUDE.md` then described only the device-code sign-in. `CLAUDE.md` now
  tells Claude to run and verify scripts itself.

### Repository
- No solution export is committed, because it contains the publisher's display name.
- The publisher unique name and environment URL are read from environment variables, never stored here.
- Statement files and parsed lines stay outside the repo (see `.gitignore`).
