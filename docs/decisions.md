# Finance Tracker: decisions and pending items

Why things were built the way they were, and what is still open. Read this with [schema.md](schema.md)
and the rules in [../CLAUDE.md](../CLAUDE.md).

## Pending items

| # | Item | Who | Notes |
|---|---|---|---|
| 6 | Delete `lzw_KeepInboxSheetId` and `lzw_FinanceTrackerGoogleSheets`? | Owner | Used only by the deleted Keep flow. Kept until the owner decides |
| 2 | Test Claude Code GitHub Actions | Owner | `.github/workflows/claude.yml` was added on 2026-11-15 and has never run. Comment `@claude` on an issue and check the run, including the Azure sign-in |
| 3 | Test `recalc.py`, `statement_compare.py --apply` and the formula columns with real rows | Claude | All have only run against empty tables |
| 5 | Add the Reconciliation Match editable grid setting to the solution | Claude | The setting is active, but `AddSolutionComponent` fails with 0x80048536. Only matters for a solution export |
| 7 | Web page: foreign cash entry (`CNY100`, a cash account's currency), Type Transfer and Transfer To | Owner to ask | Dataverse side done 2026-11-21. The owner enters trip notes through Claude Code for now |
| 8 | China Yunnan Trip, 30 Oct to 1 Nov 2026: 7 Wise pairs left for the owner (same amount on the same day, but the note's merchant equals the line's merchant); one note fragment "ipay 1.29 CNY 6" not entered (fits the Wise line Qrcode3460 on 29 Oct) | Owner | Entered 2026-11-21. "Beer for four" and "Beer cans and snacks" are dated 31 Oct in the notes but 28 Oct on Wise |

Done on 2026-11-15: the five formula columns were created and put on forms and views; base currency
verified as AUD; `lzw_KeepInboxSheetId` verified against the sheet URL; both connection references
verified as bound; confidence threshold agreed at 0.95. `verify.py`: 370 checks, 0 problems.

Done on 2026-11-20: the Planned Transactions flow was tested with a dummy one-off appointment and a dummy
one-occurrence series, run manually at 00:32 Brisbane. All values came out as specified, including Paid
From and Category taken from the series, and the real Broadband instance due that day was processed. A
second run ended Cancelled (nothing due), so nothing is created twice. The owner asked for the test data to
be removed: the two test Finance Transactions, the one-off appointment and the series (with its instance)
were deleted after a backup outside the repo. The Broadband transaction is real and was kept.

Also on 2026-11-20: **the web page replaces the Keep Inbox sheet and its flow** (owner's decision). At the
owner's request the flow "Finance Tracker - Import Keep Rows" (off, never run) was backed up outside the
repo and deleted, so turning it on is no longer pending. `build_flow.py` stays for the helpers that
`build_recurring_flow.py` imports, but its `main()` only runs with `--recreate`. `verify.py` now checks that
the Keep flow is gone and that the Planned Transactions flow is on. GitHub Pages was confirmed on.

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
- **Not audited.** Formula columns are computed when a row is read and never stored, so there is nothing to
  audit: setting `IsAuditEnabled` through the API returns success but the value stays false (tried
  2026-11-20). This is the one exception to "audit every column on a form".
- They are in the solution through their tables, which are included with all subcomponents (no separate
  column rows in `solutioncomponents`).
- Formulas (logical names):

| # | Table | Display name | Formula |
|---|---|---|---|
| 1 | Bank Statement Line | Unallocated Amount | `Decimal(lzw_amount) - Decimal(lzw_allocatedamount)` |
| 2 | Finance Transaction | Reconciliation Difference | `Decimal(lzw_amount) - If(Value(lzw_type) = 859130000, Decimal(lzw_actualamount) * -1, Decimal(lzw_actualamount))` |
| 3 | Finance Transaction | Partner Share | `If(Value(lzw_sharetype) = 859130001, Decimal(lzw_amount) * 0.5, Value(lzw_sharetype) = 859130002, Decimal(lzw_amount), 0)` |
| 4 | Finance Transaction | My Cost | `Decimal(lzw_amount) - lzw_partnershare` |
| 5 | Finance Asset | Net Cost | `Decimal(lzw_totalcost) - Decimal(lzw_saleproceeds)` |

### Amount instead of Estimated Amount (2026-11-20)
- Finance Transaction holds the **actual** income and expenses, and the owner wants real-time reporting. The
  costs were based on the Actual Amount rollup, which has a value only after a match is confirmed (weeks
  after the purchase) and then only after the rollup job or `recalc.py`.
- So the entered amount is the real amount: **Estimated Amount** (`lzw_estimatedamount`) was recreated as
  **Amount** (`lzw_amount`, Currency, positive, audited), and Partner Share and My Cost now use it. Recreated
  rather than renamed so the logical name matches the display name. Only one row existed (Broadband, copied).
- **Actual Cost** (`lzw_actualcost`) was replaced by **Reconciliation Difference**, which shows what the bank
  has not yet confirmed. The bank stays the check, not the source of the amount.
- Estimated transactions (Payment Type Estimated) get their Amount overwritten with the bank figure when
  they are reconciled.
- At the owner's request both old columns were deleted after backups outside the repo (definition, and the
  values of Estimated Amount). Nothing depended on them. The web page already used
  `lzw_amount` (merged in PR #14), so nothing broke.

### Reconciliation
- **Confidence threshold 0.95** (owner, 2026-11-15). AI matches at or above it are auto-confirmed, the
  rest are Proposed. Confidence is stored with 2 decimal places.
- **Reconcile on every inbox run** (owner, 2026-11-21). Processing the statement inbox always ends with
  reconciling the open bank lines against the Finance Transactions as far as the rules allow, so the owner
  does not have to ask for it separately.
- `scripts/reconcile.py` does it. Transfers need a transfer description on **both** lines, and a line that
  fits a Bank Rule is never a transfer (otherwise "PAYMENT TO ANZ ACCESS ADVANTAGE", an expense, paired
  with a Wise top-up of the same amount). Identical top-ups on the same day are paired either way. A pair
  with a rival is not written as a Proposed match: the web page would create a second match when the owner
  confirms it there, so it is listed in the session instead.
- Creating Finance Transactions from Bank Rules is left to the owner's go-ahead (pending): it would add
  hundreds of rows, including months where Keep notes (with their own category and project) were never
  entered.

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

### Planned Transactions (Appointment and Recurring Appointment)
- Appointments are repurposed as planned payments. The tables are renamed **Planned Transaction(s)**
  (Appointment) and **Recurring Transaction(s)** (Recurring Appointment), environment-wide, and sit under
  Capture in the Finance Tracker app. Amount and Payment Type came from an older solution.
- The old lookups (Financial Account, Transaction Category) pointed at the old tables, so **new lookups**
  were added: Paid From (Bank Account) and Finance Category (Finance Category). "Finance Category", not
  "Category", because Appointment has an OOTB Category column.
- **On 2026-11-19 the owner asked for these deletions** (an exception to the no-delete rule): the four old
  lookup columns (removed from forms and views first; their relationship maps are system maps and went
  with the relationships), and the 1,823 planned-transaction appointments dated before 2026-11-19. 20 past
  appointments without an Amount were kept. Deleting all instances of the ended "Car Loan" series also
  removed the series itself. Backups of the deleted values were kept outside the repo.
- **Processed** (Yes/No, default No) exists on both tables. The flow only reads and sets it on Appointment.
  Leave it No on the series: the platform copies series values to new instances.
- **Sign convention:** Amount on the series is positive = expense, negative = income (the reverse of the
  bank). The old data used negative = money out, so the open series were flipped on 2026-11-19 (the
  platform carried the change to their open instances). Appointments were not patched directly.
- **Updating a series rewrites all its open instances** (past and future), tested on Netflix: 21 open
  instances took the new amount, the 3 completed ones kept the old one. Completed and cancelled
  appointments are read-only. A series edit may also reset Processed on its open instances, which is why
  the flow checks for an existing transaction before creating one.
- The flow runs daily at 6 AM Brisbane and takes open or scheduled appointments with Processed = No and
  Start before tomorrow (Brisbane). Each gets a Finance Transaction: Description and Payee = Subject, Date =
  Start (Brisbane), Type = Income if Amount < 0 else Expense, Amount = abs(Amount), Share Type =
  Mine, Source = Recurring (new option 859130003), Source Row ID = appointment ID, currency = the
  appointment's currency (AUD if it has none). The flow then sets Processed = Yes. A failed appointment
  stays No, is retried next run, and the run ends Failed.

### Bills with a varying amount or date (2026-11-19)
- A planned amount is only a plan: the actual comes from the matched bank line (Actual Amount rollup).
  So varying bills get an estimate, flagged with Payment Type = Estimated, and the flow sets Needs Details =
  Yes on those so open estimates are visible.
- Regular bills use a series at the average amount on the typical debit day. Irregular bills (water: periods
  of 1 and 3 months) use one-off appointments from each invoice, which arrives about a month before it is due.
- "Utility (Electricity/Gas)" was every 4 weeks on Thursday at $117.49, which matched neither the dates
  (debits on the 23rd to 26th) nor the amounts. It is now monthly on the 24th from 24 Dec 2026 at $140.55,
  Estimated. Its open instance on 19 Nov was removed when the pattern changed, and the Oct bill ($122.22,
  due 24 Nov) is a one-off appointment. The series' previous values were backed up outside the repo.
- Exact-match reconciliation can never match an estimate, so estimated transactions match on payee,
  account and a 7-day window, at any amount (rule in `CLAUDE.md`).

### Owner's recurring list (2026-11-19)
- The owner's list is the source of truth for series. Six existing series were updated (the old salary
  series was renamed "Salary"), six were created. Pattern changes start from 19 Nov 2026, so each series'
  open instances were regenerated from that date. The list gave no day for Salary, so its 5th was kept.
- Bank Account "Manual" in the list is not an account: those series have no Paid From, so their
  transactions get Needs Details = Yes.
- Of the 27 old open series not on the list, the owner kept three car series, reshaped as Car Servicing,
  Car Insurance and Roadside Assist (Car Roadside Assistance merged into it) and Car Registration, and
  asked to delete the other 24 and the 59 cancelled series with an Amount. All were backed up outside the
  repo first. Deleting a series also deletes its instances.
- The list's description column went into the appointment Description, and the flow appends it to the
  transaction Notes. Descriptions are kept out of this repo because some name people.

### Lookups on series instances (2026-11-19)
- Earlier notes said custom columns are copied from a series to its instances. That holds for Amount,
  Payment Type, Description and currency, but not for the new lookups Paid From and Finance Category: after
  setting them on all 15 series, every open instance stayed empty, including instances generated afterwards.
- Patching the instances would not last (the platform keeps generating new ones), so the flow reads both
  lookups from the series when the instance has none. A one-off appointment keeps its own values.
- Categories chosen for the 15 series are in `CLAUDE.md`. Debatable choices: Mobile as Utilities, Super
  Duolingo as Subscriptions (not Education), Car Registration as Transport.

### Currency
- The base currency was NZD at build time. The owner has since changed it to AUD (verified 2026-11-15).
- On 2026-11-15, at the owner's request, CNY and CAD were added and every exchange rate was set from the
  Reserve Bank of Australia table for 13 Nov 2026 (units of foreign currency per 1 AUD):
  USD 0.6804, CNY 4.5380, EUR 0.6153, GBP 0.5142, NZD 1.2273, CAD 0.9701.
  Source: https://www.rba.gov.au/statistics/frequency/exchange-rates.html
- Rates are not updated automatically. A row keeps the rate it was saved with.
- The platform added `transactioncurrency` and `account` to the solution as references only.
- The GitHub secrets and Claude Code GitHub Actions are set up (owner, 2026-11-19).

### Foreign cash (2026-11-21)
- **One cash Bank Account per currency** (first: "CNY Cash", short name `CNYCash`, Account Type Other,
  Account Currency CNY, Statements Imported = No), reused on every trip so the cash left over carries on.
- **Last Rate on the Bank Account** (owner's choice over a rate history in statement lines): Last Rate
  (`lzw_lastrate`, 6 places, units of the account currency per 1 AUD, as the platform's currency rates) and
  Last Rate Date. A cash spend's AUD Amount = foreign amount / Last Rate. Update both whenever that currency
  is bought or received. The CNY rate 4.666043 (= 249.26 / 53.42) came from the Wise payment "Beer for two"
  on 30 Oct 2026, because the cash itself came from a friend paying their share of that bill.
- **Original Amount and Original Currency on Finance Transaction** (positive, as Amount). Amount stays AUD,
  so totals, shares and reconciliation are unchanged. Wise lines already carry the same pair.
- **Type = Transfer** (859130002) with **Transfer To** (Bank Account): my own money moving between accounts,
  out of Paid From and into Transfer To. Used when a friend pays back their share in foreign cash: the
  shared bill keeps only my share, and the friend's share becomes a Transfer from the paying account to
  the cash account. One bank line then matches both (split match, Method Manual).
  Reconciliation Difference treats Transfer like Expense (money out of Paid From); My Cost is 0 for a
  Transfer. Both formulas were updated in place (`build_formulas.py` now PUTs a changed formula).
- Cash accounts have no statements, so cash spends stay Unreconciled, like the AUD Cash account.
- The web page does not know Transfer or foreign amounts yet (the owner enters trip notes through Claude
  Code for now). Its View list counts a Transfer as money out.

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
- **Wise** stays one account. (Superseded on 2026-11-20, see "First statement import": lines are in AUD,
  refunded rows and conversions are not imported, and a split purchase is one line.)
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

### First statement import (2026-11-20)
- Imported from `Statements/Inbox`: ANZ Plus Everyday, Flex Saver and Growth Saver (Apr to Oct 2026, PDF),
  AMEX (14 Mar to 13 Nov 2026, xlsx), Kogan Money Black Card (to 19 Oct 2026, PDF) and Wise (CSV, 9 Jan to
  1 Nov 2026). 34 Bank Statements, 1,729 lines, all Unmatched. Dataverse had no lines before.
- **Checks before writing:** every ANZ running balance, each statement's opening against the previous
  closing, the Kogan account summary, the AMEX "Transaction Summary" sheet, filename against period, and
  no gaps between statements. All passed. All 102 transfers between the three ANZ accounts pair up by
  receipt number (useful for reconciliation).
- **Kogan** keeps the period printed on the statement, even the first one (20 Sep 2025 to 19 Jul 2026):
  Kogan does not issue a statement for a period without transactions (owner).
- **AMEX supplementary card:** the owner wanted a column to mark these lines. The existing **Card Holder**
  already holds the card member on every AMEX line, so no new column was added (3 lines in this import).
- **Wise** (owner's rules, replacing the 2026-11-15 design): amounts in AUD so the account reads like the
  others; refunded rows (14) and conversions (11) are not imported; a split purchase (8) is one line.
  Rows paid from a foreign balance (33) get an estimated AUD amount from the last AUD conversion into that
  currency. CAD had no AUD conversion in the file, so the rate of an AUD-funded CAD card payment was used;
  SGD had no AUD rate at all, so a cross rate (SGD to USD conversion, then USD per AUD) of 0.907 SGD per
  AUD was used (the Reserve Bank rate in Dataverse is 0.8753). The rate and its source are in each line's
  Notes. The statement "Wise 2026" covers the whole year and is topped up from a newer export each month.
- **Dates:** ANZ Transaction Date is the Effective Date when the statement shows one (345 of 668 lines),
  Posted Date the listed date. Wise dates are as exported (the export is probably UTC).
- **No Exchange Rate column.** Original Amount / Amount gives it; the Wise estimate rate is in Notes.
- Parsing, checks and the import are in `statement_parse.py`, `wise_lines.py` and `statement_import.py`
  so the monthly imports repeat the same rules. `statement_compare.py` now fills the new line columns and
  the Original Currency, and uses Bank Reference to keep identical lines apart.

### Web page for transactions (2026-11-15)
- **Why.** The owner wanted to enter and reorder transactions directly instead of through Keep, the sheet
  and the hourly flow.
- **Transaction Date became date and time.** A Date Only column cannot be changed, so the column on Finance
  Transaction was deleted and recreated as date and time (user local) while the table was empty. Bank
  Statement Line keeps Date Only, so matching compares the date part in Brisbane time.
- **Static page on GitHub Pages**, calling the Dataverse Web API from the browser. Dataverse allows this
  for single-page apps that sign in with Microsoft Entra ID.
- **No library.** The sign-in (authorization code with PKCE) is about 40 lines in the page itself, so there
  is nothing to build or update.
- **Nothing private in the page.** The Dataverse URL, tenant ID and app ID are typed in once and kept in
  the browser's local storage, together with the sign-in tokens.
- **App registration "Finance Tracker Web"**: single tenant, single-page redirect to the Pages address,
  delegated Dataverse permission, consent granted for the tenant. No secret.
- **Tested** in a browser against the environment with the automation identity's token: load, add,
  reorder, edit, clear a lookup and bulk entry. The Microsoft sign-in itself could not be tested from a
  cloud session and waits for the owner's first use.
- The project "Yunnan Trip" was renamed "China Yunnan Trip".

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
