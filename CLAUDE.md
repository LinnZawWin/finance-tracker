# Finance Tracker

Personal finance tracker on Dataverse: capture expenses (Google Keep notes entered through the web page),
import bank statements, reconcile bank lines against transactions, and track assets.
Model-driven app **Finance Tracker**. Schema as built: [docs/schema.md](docs/schema.md).
Decisions, their reasoning and pending items: [docs/decisions.md](docs/decisions.md). Read it before changing anything.

## Rules

- **Keep this file current.** After every change to Dataverse, the flows, the scripts or the data, update
  this file in the same session so a new session can start from it without losing context: the current state
  (tables, columns, flows and whether they are on, sign conventions, rules learned), not a history.
  Put the reasoning and the pending items in `docs/decisions.md`. Do this before reporting the work as done.
- This repo is public. Never commit the Dataverse URL, an email address, a tenant ID, tokens, token caches
  (`~/.azure`, `~/.pac`), exported data, statements, or any person's name. Write "Partner" instead of names.
- Use the Dataverse Python SDK, PAC CLI, Azure CLI and Web API. Do not use or register the Dataverse MCP
  server (it is billed). If a skill says to register it, skip that step.
- If something blocks an item, skip it, continue, and report it.
- **Suggest a new session when it is cheaper.** Every turn re-sends the whole conversation, so a long session
  costs more per turn. When the context has grown long (many batches, large script or query output) and the next
  request does not depend on what is only in this session (scratchpad files, IDs looked up, a running task), say
  so at the end of the reply and suggest starting a new session. Make sure this file and `docs/decisions.md` are
  current first, so the new session loses nothing. Do not suggest it in the middle of a task.
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
    `scripts/dv.py` does this itself when the Azure CLI is not signed in and the three variables are set, so
    any script signs in on its first call; run the command by hand only for `az` calls before any script.
  - **Claude Code on the owner's Windows machine**: the git-ignored `.claude/settings.local.json` sets
    `DATAVERSE_URL`, `DATAVERSE_USER` and `AZURE_CONFIG_DIR` (`~/.azure-personal`, the owner's own sign-in,
    kept apart from other Azure CLI sign-ins on that machine). The refresh token there renews itself;
    if it expires, sign in again with device code with `AZURE_CONFIG_DIR` set to that folder.
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
| Planned Transaction (OOTB Appointment, renamed) | `appointment` |
| Recurring Transaction (OOTB Recurring Appointment, renamed) | `recurringappointmentmaster` |

Plus `account.lzw_isbank` and the Account view "Banks". Global choice `lzw_sharetype`:
Mine, Shared with Partner (A), All for Partner (AA), Paid for Others.
Finance Transaction **Source**: Keep (859130000), Manual, Import, Recurring (859130003).
Finance Transaction **Type**: Expense (859130000), Income, Transfer (859130002).

Planned and Recurring Transaction are in the solution as shells: only these components, not the whole table.
Columns (same on both): Amount `lzw_amount`, Payment Type `lzw_paymenttype` (global choice: Auto, Manual,
Estimated), Paid From `lzw_paidfrom` (Bank Account), Finance Category `lzw_financecategory`, Processed
`lzw_processed` (Yes/No, default No). Forms "Planned Transaction" / "Recurring Transaction", views
"Planned Transactions" / "Recurring Transactions". Both tables are under Capture in the app. The old lookups
Financial Account and Transaction Category (to the old MoneyManagement tables) were deleted.

## Flows

| Flow | Schedule | State | Script |
|---|---|---|---|
| Scheduled: Create Finance Transactions from Planned Transactions | Daily 6 AM Brisbane | **On** since 2026-11-19. Tested 2026-11-20 (manual runs: one Succeeded, one Cancelled with nothing due) | `build_recurring_flow.py` |

It uses the connection reference `lzw_FinanceTrackerDataverse` (bound). The build scripts update a flow's
definition only while it is off. `build_recurring_flow.py --update-on` turns the flow off, updates it and
turns it back on. Name new flows `<Table>: <Flow Name>`
(`Scheduled:` for recurrence).

To run a flow by hand, call the Power Automate API with an Azure CLI token for
`https://service.flow.microsoft.com/`: `POST .../environments/<env id>/flows/<workflowid>/triggers/<trigger>/run`
(api-version 2016-11-01). Take the environment ID from the `environments` list in that API, matching
`instanceUrl`: the PAC profile and FlowAgent on this machine are signed in to another account.

## Planned Transactions

- The scheduled flow takes open or scheduled appointments with Processed = No and Start before tomorrow
  (Brisbane) and creates a Finance Transaction for each: Description and Payee = Subject, Date = Start,
  Type = Income if Amount < 0 else Expense, Estimated Amount = abs(Amount), Share Type = Mine, Source =
  Recurring, Source Row ID = appointment ID, Paid From and Category from the appointment or else its
  series, Needs Details = Yes when Paid
  From is empty or Payment Type = Estimated, Notes = "Created from Planned Transaction. Payment Type: <x>"
  plus the appointment's Description on a new line, currency = the appointment's (AUD if none). Then it
  sets Processed = Yes. It skips an appointment that already has a Recurring transaction with that Source
  Row ID.
- The appointment **Description** holds the payee or how to pay ("Manual - ..." = paid by hand). Every
  series has a Paid From (the account the money leaves), including Manual ones.
- **Current series** (owner's list, applied 2026-11-19; all AUD; amounts positive = expense):

| Series | Amount | Pattern | Paid From | Payment Type | Finance Category |
|---|---|---|---|---|---|
| Salary | -18,333.33 | Monthly, 5th | Everyday | Auto | Salary and Contract Income |
| Rent | 560.00 | Weekly, Sunday | Flex | Auto | Rent and Housing |
| Health Insurance | 81.50 | Weekly, Monday | Flex | Auto | Insurance |
| Broadband | 71.95 | Monthly, 20th | AMEX | Auto | Utilities |
| Utility (Electricity/Gas) | 140.55 | Monthly, 24th (from 24 Dec 2026) | Flex | Estimated | Utilities |
| YouTube Premium | 6.60 | Monthly, 25th | Flex | Auto | Subscriptions |
| Claude Pro | 34.00 | Monthly, 4th | AMEX | Auto | Subscriptions |
| Crunchyroll | 3.33 | Monthly, 21st | Flex | Manual | Subscriptions |
| Water Use | 130.00 | Every 3 months, 1st (from 1 Jan 2027) | Flex | Estimated | Utilities |
| Spotify Premium | 34.23 | Every 6 months, 28th (Jan, Jul) | Flex | Manual | Subscriptions |
| Mobile | 154.00 | Yearly, 12 Aug | AMEX | Manual | Utilities |
| Super Duolingo | 28.54 | Yearly, 12 Oct | Flex | Manual | Subscriptions |
| Car Servicing | 400.00 | Yearly, 1 Dec | AMEX | Manual | Car Maintenance |
| Car Insurance and Roadside Assist | 602.42 | Yearly, 11 Mar | AMEX | Manual | Insurance |
| Car Registration | 1,049.72 | Yearly, 28 Feb | AMEX | Manual | Transport |

  These 15 are the only series with an Amount. All other old series (24 open, 59 cancelled) were deleted on
  2026-11-19 at the owner's request. 2 cancelled series without an Amount are calendar items: leave them.
- **Bills whose amount or date varies:**
  - Regular (monthly, for example electricity): a series on the typical debit day with Payment Type =
    Estimated and the average of recent bills. When a bill arrives, put its exact amount and due date in a
    one-off appointment and move the series start past it, or edit the Finance Transaction if it already
    exists. "Utility (Electricity/Gas)" is set up this way: monthly on the 24th from 24 Dec 2026, $140.55
    (average of May to Oct 2026), plus a one-off $122.22 on 24 Nov 2026 (Payment Type Auto).
  - Irregular (for example water, about quarterly): no series. Create a one-off appointment from each invoice
    (exact amount, due date, Payment Type Manual).
  - Changing a series' recurrence pattern deletes and regenerates its open instances (tested). Editing
    a single instance has not been tested: a later series edit may overwrite it.
- Platform behaviour, tested:
  - Updating a series rewrites the same columns on **all its open instances**, past and future. Completed
    and cancelled appointments are read-only and keep their values.
  - Amount, Payment Type, Description and currency are copied from a series to its instances (on create
    and on update). **Paid From and Finance Category are not** (tested 2026-11-19: empty on every instance),
    so the flow reads them from the series (`seriesid`) when the instance has none. Set them on the series.
  - Keep Processed = No on series.
  - Deleting every instance of a series deletes the series too.
- Past planned transactions (before 2026-11-19) were deleted. 20 past appointments without an Amount are
  real meetings: leave them.

## Foreign cash

- One cash Bank Account per currency, reused across trips: "CNY Cash" (short name `CNYCash`, Account Type
  Other, Account Currency CNY, no statements) and "JPY Cash" (`JPYCash`, added 2026-11-23). Add others the same way.
- Bank Account **Last Rate** (`lzw_lastrate`, units of the account currency per 1 AUD, 6 places) and
  **Last Rate Date**. A cash spend: Amount (AUD) = foreign amount / Last Rate, rounded to cents; Original
  Amount = the foreign amount, Original Currency = the account currency, Paid From = the cash account, Notes
  say which rate was used. When that currency is bought or received, update Last Rate and Last Rate Date.
  CNY Cash: 4.666043 from 30 Oct 2026. Cash a friend pays back is valued at Last Rate, not at the bill.
  Cash left over from an earlier trip: Income (Other Income) Paid From the cash account, valued at Last Rate
  (23 Oct 2026 "Leftover CNY from Previous China Trip", CNY 200 = AUD 42.86, project China Yunnan Trip, changed
  from a Transfer on 2026-11-23; 22 Aug "Leftover JPY from Previous Japan Trip"). Its cash line is matched and
  the transaction is Reconciled.
- Finance Transaction **Original Amount** (positive) and **Original Currency**: the foreign amount. Fill them
  for Wise rows too (the CSV / Keep columns Currency and Original Amount). Amount is always AUD and the row
  currency stays AUD.
- **Transfer** (Type = Transfer, Paid From = the account the money leaves, **Transfer To** = the account it
  goes into): my own money moving between accounts. My Cost is 0. A friend paying back their share of a
  bill in foreign cash: the bill keeps only my share (Amount and Original Amount less theirs) and their
  share is a Transfer from the paying account to the cash account; the one bank line is split between the
  two (Method Manual). When the cash (at Last Rate) is worth more than my share, the bill becomes Income
  of the difference: eSIM AUD 9.58 paid back as CNY 70 = AUD 15.00 gives a Transfer of 15.00 and Income
  5.42 on the bill; the AMEX line is split -15.00 / +5.42.
- Trip notes are entered through Claude Code, not the web page (it has no foreign or Transfer support yet).
  Note lines: `Description Amount [A|AA] [Account] [Project]` or `Description|Merchant|AUD|Share|Account|
  Project|Currency|Original Amount`; `CNY100` = a foreign amount; a date line may end with the project
  ("Yunnan Trip" = "China Yunnan Trip"). Fill Payee, Paid From and Original Amount from the matching Wise
  line when the note has none, then run `reconcile.py`.

## Categories

Every Finance Transaction Claude creates gets a Category from its description (the payee only when the
description says nothing). Transfers have none. The first rule that fits wins; when none fits, ask.

| Description says | Category |
|---|---|
| Concert, festival, gig, show or event tickets (also clubbing event tickets such as "ULTRA PRE-PARTY"; also a ticket bought for someone). Not sports tickets, club entry or attractions | Events (under Entertainment) |
| "for <someone>" (for example "for Mom"), gift, present, souvenir (also snacks or cosmetics bought for someone, and AA trip items such as a keychain or balloon) | Gifts |
| Hotel, accommodation | Accommodation (Travel) |
| Tour guide tips, other trip costs | Travel |
| W Support (Joint Main) | Support Payments |
| Rent | Rent and Housing |
| Insurance | Insurance |
| Utility, broadband, electricity, water, mobile | Utilities |
| YouTube, Claude Pro, Prime Video, Crunchyroll, Spotify, Duolingo, DiDi Pass | Subscriptions |
| Annual fee, bank fees | Fees and Charges |
| Interlock device | Fines |
| Fuel | Fuel (Transport) |
| Taxi, DiDi, Uber (not Uber Eats) | Rideshare and Taxi (Transport) |
| Train, metro, commute, Translink | Public Transport (Transport) |
| Pokies, casino, betting (win or loss) | Gambling (Category Type Both) |
| Sports tickets, attractions, club entry, cover charge, cat cafe entry, shisha bar | Entertainment |
| Ice skating, gym | Sport and Fitness |
| Clinic, vaccination, supplements, chemist | Health |
| Haircut, laser hair removal, cosmetics (own) | Personal Care |
| Grocery | Groceries |
| Dinner, lunch, breakfast, takeaway, KFC, noodles, sushi: a meal, even with drinks ("Dinner and drinks") | Food and Soft Drinks |
| Beer, wine, spirits; "drinks" at a bar, pub or club; bottle shop | Alcohol |
| Cold, isotonic or sports drinks, juice, matcha, coffee, café or dessert-bar drinks, snacks, ice cream, yoghurt, restaurant reservation | Food and Soft Drinks |
| Keychain, T-shirt for myself | Shopping |
| Income: refund | Refund |
| Income: interest, savings bonus | Interest |
| Income: a friend paying back more than my cost | Reimbursement |
| Income: salary | Salary and Contract Income |

A "Weekly Allowance" note, or any note marked Transfer between two of my bank accounts (for example a Wise top-up
from Flex), is my own money moving between my accounts (the bank lines are already paired as a transfer): do not
create a Finance Transaction for it. The one for 25 Oct (3,000.00 Growth Saver to Flex Saver)
was deleted on 2026-11-21 at the owner's request.

The owner writes drinking at a restaurant as its own line (for example "drinking at Korean restaurant") when
more of the bill went on alcohol than on the meal; that line is Alcohol. A plain "Drink" from a shop is
Food and Soft Drinks unless it names alcohol.

The categories are data in Dataverse (`lzw_financecategory`); add one only with the owner's agreement.

**Payee** is the real business name, not the bank descriptor ("WW METRO 2885 FORTITUDE VLY" = Woolworths
Metro, "DIDIMOBILITY AUSTRALIA" = DiDi). For a booking or ticket platform the owner decides: EatClub lines
take the venue, Fever lines stay "Fever". When the descriptor names no business (an LS / Pty Ltd name,
an Alipay QR code), ask. A friend's cash repayment takes the friend as Payee; a cash tip, the person's role
("Chinese Tour Guide"). As of 2026-11-22 every Finance Transaction linked to a bank line has a Payee.
**Whenever a bank line is linked to a Finance Transaction that has no Payee** (by `reconcile.py`, `split_match.py`,
the web page or by hand), suggest a Payee from the line by this rule in the session, as a table (transaction,
bank line, suggested Payee, basis), and write it once the owner agrees. Check unclear descriptors online and
give the source. Do this after every reconciliation run, including the one at the end of an inbox run.

## Sign convention

- Bank Statement Line **Amount** and Reconciliation Match **Allocated Amount** are signed like the bank:
  negative = money out. They are AUD except on "ANZ NZ Go", which is NZD (row currency NZD).
- Finance Transaction **Estimated Amount** is positive.
- Finance Transaction **Actual Amount** (rollup of confirmed matches) is signed like the bank. **Actual Cost**
  flips the sign for expenses.
- Finance Transaction Original Amount is positive, like Amount. Transfer: money out of Paid From.
- Planned and Recurring Transaction **Amount** is the opposite of the bank: positive = expense, negative =
  income. The open series were converted to this on 2026-11-19.

## Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| `dv.py`, `spec.py` | Web API helper and the schema specification |
| `build_schema.py`, `build_formulas.py`, `build_ui.py`, `build_icons.py`, `seed.py` | Idempotent build, in this order. `build_schema.py` adds missing choice options; `build_formulas.py` updates a formula that differs from `spec.py`; `build_ui.py` rewrites the forms and views. `build_flow.py` (the retired Keep flow) only provides helpers now |
| `build_appointments.py`, `build_recurring_flow.py` | Planned / Recurring Transactions: columns, rename, forms, views, app and the scheduled flow (created off; an existing flow that is on is left untouched) |
| `verify.py [--write-docs]` | Checks everything exists in the solution, regenerates `docs/schema.md` |
| `statement_parse.py <inbox> <out>` | Parse and check ANZ, ANZ New Zealand, Kogan and AMEX files into lines files (no writes) |
| `wise_lines.py <csv> <out json>` | Convert the Wise export into AUD lines by the Wise rules below |
| `statement_import.py <out> [--apply] [--include-possible] [--no-reconcile]` | Create the Bank Statements and only the missing lines (dry run by default). `--apply` then runs `reconcile.py --apply --verbose` itself (exit code 2 if another run holds the lock) |
| `statement_compare.py` | The comparison used by `statement_import.py`; also a single-statement CLI |
| `reconcile.py [--apply] [--verbose]` | Reconcile open bank lines: transfers, then transaction-to-line pairs (as the web page suggests them, confirmed only without a rival and when the transaction's Payee shares a word with the line), then a count of lines a Bank Rule fits (dry run by default). `--apply` holds the lock and recalculates the rollups of the rows it matched |
| `lock.py [--release]` | The reconciliation lock: environment variable `lzw_ReconcileLock` ("<holder> <UTC time>", empty = free), taken with If-Match so only one session reconciles at a time; older than 60 minutes = abandoned. `--release` clears it after a crashed run |
| `split_match.py <ft id> <line id>[=<amount>] ... [--apply]` | Link one Finance Transaction to several bank lines (split bill or refund, see "Split bills and refunds"): Method Manual, Confirmed; sets line and transaction status; holds the lock (dry run by default) |
| `cash_lines.py [--apply]` | Generate the cash lines (see "Cash lines"); `reconcile.py` runs it first, under the lock (dry run by default) |
| `recalc.py` | Recalculate the rollup columns on demand |

The five formula columns (Unallocated Amount, Actual Cost, Partner Share, My Cost, Net Cost) are Power Fx
**Formula** columns, created by `build_formulas.py` (Decimal, 2 places, formulas in `spec.py`). Do not create
Calculated columns: that behaviour is being discontinued. A formula column cannot be Currency, so currency
inputs are wrapped in `Decimal()` and the result has no currency symbol. An empty input counts as 0.
Formula columns cannot be audited (they are not stored); the API accepts the setting but ignores it.
`--fallback` never applies to them.

Run them with a Python that has `azure-identity` installed, from the repo root, with the Azure CLI on PATH.

## Starting a new session

- Tools: in a cloud session the Finance Tracker environment's setup script installs them when the container
  starts: the .NET 10 SDK and `pac` (PAC CLI 2.x needs .NET 10; `/opt/pac`, linked to `/usr/local/bin/pac`), and
  `pip install --break-system-packages --ignore-installed argcomplete azure-cli azure-identity pdfplumber openpyxl`
  (`--ignore-installed argcomplete` because pip cannot replace the Debian copy). Check with `which az pac`;
  if one is missing, run that command by hand. Elsewhere install them yourself (the Azure CLI and script
  dependencies in a virtual environment). Sign-ins do not carry over: sign in
  again as described under "Environment and sign-in".
- Skills: the dataverse skills (dv-*) come from the plugin. The model-apps and power-automate skills are in
  the public repo `microsoft/power-platform-skills` under `plugins/`.
- The network proxy drops any request that is silent for about 10 seconds, but Dataverse usually still
  completes it. `dv.py` handles this by re-checking before retrying a write. Keep that pattern.
- `.claude/settings.json` (committed) allows the Google Drive tools used for the statement inbox (search,
  metadata, download, move/rename, create folder) without a prompt. Other tools follow the session's mode.
- Check the real state first with `python scripts/verify.py`. It lists anything missing from the solution.
  It does not yet cover the Planned / Recurring Transaction components.
- The base currency is AUD (verified 2026-11-15). Scripts and the flow still set AUD on the rows they create.
  Other currencies: CAD, CNY, EUR, GBP, IDR, JPY, NZD, SGD, THB, USD. Exchange rates are units per 1 AUD and are only changed
  when the owner asks. The Planned Transactions flow uses the appointment's currency.

## Parallel sessions

Several sessions may create Finance Transactions at the same time. Creating them does not take the lock.
- Give each session its own notes (a date range or a trip), so no transaction is created twice and the times
  that order a day's rows do not interleave. Before creating, check for an existing row with the same date,
  description and amount.
- Only `reconcile.py --apply` (with `cash_lines.py`) and `split_match.py --apply` take `lzw_ReconcileLock`.
  When another session holds it, the run writes nothing: `reconcile.py` prints NOT RUN and exits with code 2,
  `split_match.py` stops with a `Busy` error. That is not a failure.
- **Reconcile once, at the end** (owner, 2026-11-23). When the owner says other sessions are running, a session
  only creates transactions and imports lines, with `statement_import.py --apply --no-reconcile`. It does not
  run `reconcile.py --apply`. Links that `reconcile.py` cannot find (split bills, refunds, one line split over
  several parts, ANZ NZ Go, claims) are run with `split_match.py --apply` together at the end of the session,
  not one by one. Report the lines and transactions left open.
- Once every session has finished creating, one session (the last one, or a new one the owner starts) runs
  `reconcile.py --apply --verbose`, then suggests Payees (Reconciliation rule 7). A single session on its own
  keeps the normal flow (the import reconciles itself).
- **When the lock is held, wait and retry without asking.** Check it with `python scripts/lock.py` every few
  minutes (in a cloud session use Monitor with an until-loop, not a foreground `sleep`) and rerun the step as
  soon as it shows "(free)". Do not run `lock.py --release` while the holder is under 60 minutes old: only a
  lock older than that is abandoned (the next run takes it over by itself). Report how long you waited.
- Each session updates this file and `docs/decisions.md`. Before pushing, merge the latest `main` and keep
  both sessions' changes.

## Statement import rules

Files: the owner drops statements in the Google Drive folder `Statements/Inbox`. After a statement is imported
and its balance check passes, move the file to `Statements/Processed` (mid-cycle exports to
`Statements/Processed/Mid-cycle`) and rename it there, so the files are easy to find for manual checks.
A file that fails stays in the inbox. Save the downloaded copy under the same new name before parsing: the
parser reads these names, and the Bank Statement is named after the file (without the extension).

| File | Name in Processed |
|---|---|
| ANZ Plus Everyday | `ANZ Plus <period end> - Everyday x3029 Statement.pdf` |
| ANZ Plus Flex Saver | `ANZ Plus Flex Saver <period end> - Flex Saver x5149 Statement.pdf` |
| ANZ Plus Growth Saver | `ANZ Save <period end> - Growth Saver x3037 Statement.pdf` |
| AMEX | `AMEX <period end>.xlsx` |
| Kogan | `KoganMoneyBlackCard_<yyyymmdd of period end>.pdf` |
| ANZ NZ Go | `ANZ NZ Go <period end> - Statement.pdf` |
| Wise | `Wise <year> (until <Mon>).csv` |
| Mid-cycle export (`Mid-cycle` folder) | the same pattern with `<start> to <end>` instead of the period end, for example `AMEX 2026-11-14 to 2026-11-21.xlsx`, `ANZ Plus Flex Saver 2026-10-31 to 2026-11-20 - Flex Saver x5149 Transaction List.pdf` |

Dates are `yyyy-mm-dd` and are the period printed on the statement, not the download date.

1. **Get the real file, not its text.** Use the Drive connector's `download_file_content`: it saves the file to
   disk. Parse PDFs by column position (`pdfplumber`), spreadsheets with `openpyxl` or `csv`. Do not import from
   `read_file_content`: it loses the credit and debit columns. On the owner's Windows machine the Drive folder
   is mounted locally (`G:\My Drive\Statements`), so read the files there. Its Python is ARM64, where
   `pdfplumber` does not install (no `cryptography` wheel): use `pypdf` with `extraction_mode="layout"` and
   take each ANZ line's sign from the running balance change, which checks every line as well.
2. **Preferred format per account**: a spreadsheet export when the bank offers one, otherwise the PDF.
   AMEX: `.xlsx` (lines plus the balance summary), then `.csv` (same lines, no balances), then PDF.
   ANZ Plus offers PDF only.
   **Mid-cycle exports** create a **placeholder** Bank Statement (Notes start with "Interim", balances are
   those of the export). The next export or the final statement whose period overlaps it updates that same
   record (name, period, balances, source type, notes) and adds only the lines it lacks, so the lines stay in
   one statement. Two exports are recognised: the ANZ Plus "Transaction List" PDF (period from "Commencing"
   to the day before "generated on") and the AMEX current-cycle `.xlsx` (its summary has "Total Balance"
   instead of "Statement Balance"; the period starts on the cycle start and ends on the last date in the
   file name). `statement_import.py --include-possible` also creates the possible duplicates, after they are
   checked to be separate charges.
   When one statement is supplied in several formats, import one and move all of them.
3. **Check the totals** against the statement's opening and closing balance before writing anything.
4. Before creating Bank Statement Lines, query the existing lines for that account and date range.
5. A line with the same **Bank Reference** and amount as an existing one is that line, even when its date differs
   (a date corrected by hand). Then compare by **count per (date, amount, description)** and create only the shortfall, because identical
   purchases on one day are real. Use **Bank Reference** when the bank gives one, **Running Balance** or
   **Line Number** otherwise, to separate identical lines.
6. A **PDF or spreadsheet statement is final**: update the matching screenshot rows (description, balance) and
   create only the leftovers.
7. Flag description or amount differences as **possible duplicates**.
8. Show a summary (new, existing, possible duplicates) **before writing**.
9. Parse with `scripts/statement_parse.py` and `scripts/wise_lines.py`, then compare and write with
   `scripts/statement_import.py` (dry run by default, `--apply` to write). Keep the
   downloaded and parsed files outside the repo.
10. **Then always reconcile.** Processing the inbox is not finished when the lines are written: reconcile
    every Unmatched or Partly Matched bank line (all accounts, not only the new ones) against the Finance
    Transactions as far as the Reconciliation rules below allow, without being asked. Confirm what the
    rules allow, leave the rest Proposed or unmatched, and report what was matched, proposed and left.
    `statement_import.py --apply` does this itself (not in parallel sessions, see "Parallel sessions"): after
    the lines it runs `reconcile.py --apply --verbose`,
    which holds the lock `lzw_ReconcileLock`, writes only what the rules allow and recalculates the rollups of
    the rows it matched. Check its output and report it. If it says NOT RUN (another session holds the lock),
    wait and retry as under "Parallel sessions". On its own,
    `python scripts/reconcile.py` is a dry run (`--verbose` lists the transfer pairs). Then suggest Payees for
    the linked transactions that have none (Reconciliation rule 7).

Columns: **Transaction Date** is the purchase date ("Effective Date" on ANZ, "Transaction Date" on Kogan,
"Date" on AMEX). **Posted Date** is the date the bank processed it. **Card Holder** is the card member on AMEX
(a name other than the owner's = supplementary card; those lines are imported like the others).
**Fee Amount** and **Bank Category** come from Wise. **Bank Reference**: the ANZ receipt number (`#123456`),
the AMEX Reference, the Wise ID. **Line Number** is the order in the statement, oldest first.
AMEX `.xlsx` totals: the "Transaction Summary" sheet (Previous Balance, Payments & Credits, Charges &
Adjustments, Statement Balance); Opening / Closing Balance are stored signed like the bank (owed = negative).

ANZ New Zealand (2026-11-21): Bank Account "ANZ NZ Go" (`NZGo`, bank "ANZ New Zealand", Account Currency
NZD). PDF named `<account number>_Statement_<date>.pdf` by the bank (`ANZ NZ Go <period end> - Statement.pdf` once processed; the parser reads both); pypdf gives no text, so the parser uses pdfplumber.
The account stays in NZD: statements and lines have row currency NZD, Amount and balances in NZD as printed,
Original Amount / Currency = the same NZD amount. Transaction Date = "Orig date" under Visa lines, else the
statement date. `statement_import.py` sets the currency per account (`CURRENCY`). Statements imported: May to Oct 2026
(the parser checks a renamed `ANZ NZ Go ...` file before the ANZ Plus prefix).
A Finance Transaction paid from ANZ NZ Go stays AUD like every other: Amount = NZD / the platform NZD rate
(1.2273), rounded to cents, Original Amount / Currency = the NZD amount, Notes say the rate. The match is written
in NZD (row currency NZD, Allocated Amount = the line amount) and the rollup converts it back at the same rate,
so the difference is 0. `reconcile.py` finds no candidate for these (AUD Amount against an NZD line): link them
by hand (Method Manual) and check the difference after the rollup. `split_match.py` compares the NZD line with the AUD
Amount, so it reports a false difference and sets Partly Reconciled: set Reconciled by hand when the rollup gives 0.

Wise (owner's rules, 2026-11-20). Wise is one Bank Account; its export is a transaction list, not a statement:
- One Bank Statement "Wise <year>", period 1 Jan to 31 Dec, no balances. Each month the owner uploads a
  newer full-year export; compare it against the existing lines and create only the new ones.
- Skip REFUNDED rows and conversions between balances (Direction NEUTRAL). They are not imported.
- Amount is AUD. AUD-funded rows: source amount plus fee. Original Amount and Original Currency are the
  target (merchant) amount and currency; Fee Amount is the Wise fee.
- Rows paid from a foreign balance: AUD = foreign amount / the rate of the last AUD-to-that-currency
  conversion before the row (effective rate, fee included). Without one: the first later conversion, then
  the rate of an AUD-funded card payment in that currency, then a cross rate through another currency's
  conversion. Notes say which rate was used. This applies to USD, NZD, THB, EUR, JPY, CAD and SGD balances.
- A payment split across two balances (the CSV repeats its ID) is one line; Notes list the parts.
- A transaction hidden in the Wise app is missing from the export: enter it by hand with Bank Reference
  `TRANSFER-<transaction number>` (or the ID the CSV would give), so the next export finds it and does not
  create it again. 28 Oct 2026 "Money added" +100 (TRANSFER-2457903123) was entered this way; check it
  matches when the next export arrives.

## Reconciliation rules

1. **Rules first**:
   - Pair transfers: opposite amount, two of my accounts, within 3 days. Set Status = Transfer and
     Transfer Counterpart on both lines. ANZ shows the same receipt number (Bank Reference) and the other
     account's number (Bank Account **Account Number**) on both sides. Credit card payments and Wise top-ups
     ("PAYMENT TO" my own name) are transfers too.
   - Exact matches: same amount, date and account.
   - Bank Rules (`lzw_bankrule`) by priority (lowest number first) for payee, description, category and
     share type defaults. The rules are data in Dataverse, not in this repo.
   - **Estimated transactions** (Source = Recurring, Notes contain "Payment Type: Estimated"): they never
     match on amount. Match a bank line with the same payee (directly or through a Bank Rule) on the same
     account, within 4 days of the Transaction Date, any amount. Auto-confirm only when exactly one line
     fits; otherwise Proposed. After confirming, set Needs Details = No (the bank line gives the actual).
2. **Then AI** for the rest.
3. Auto-confirm at or above a confidence of **0.95**. Otherwise set Match Status = Proposed and ask in the session.
4. **Never auto-confirm** a pair whose transaction Payee shares no word with the line (spaces in the line
   ignored, so "Didi" fits "DIDIMOBILITY"): for example "Maru Grill House" against "ZLR*KINN IMM".
   **Never auto-confirm** when more than one candidate shares the same amount, date and account, unless
   the transaction's Payee equals the line's merchant (for example "Qrcode7684 - Alipay") and no other
   open line with that merchant fits: then it is not ambiguous. `reconcile.py` applies this.
   Not rivals: a candidate whose payee does not fit (the first rule above would never confirm it), and
   **totally identical rows**: transactions with the same account, amount, day, description and payee, and
   lines with the same account, amount, day and description, are interchangeable and paired one each
   (for example two "Beer jug" transactions and two identical karaoke bar lines on the same day).
   Candidates are within 4 days, so the same weekly payment a week away is never a rival.
5. For **Wise**, match on Original Amount in the original currency, not AUD.
6. After writing matches, run `python scripts/recalc.py` to recalculate the rollup columns, then update Bank Statement Line Status and Finance Transaction Reconciliation Status.
7. Then suggest a Payee for every linked Finance Transaction that has none (see "Payee" under Categories).

### Cash lines

Cash has no bank statement, so `cash_lines.py` generates its Bank Statement Lines (Source **Generated**) every
time `reconcile.py` runs (with each import). Cash accounts are those named "Cash" (AUD) and "<CUR> Cash".
- **Statements**: one "Cash" for AUD cash; foreign cash one per project, "<account> - <project>" (for example
  "CNY Cash - China Yunnan Trip"; "- No project" when the transaction has none). No period, no balances,
  Source Type Other.
- **One line per cash transaction** (Paid From or Transfer To a cash account), Bank Reference
  `FT-<transaction id>`, in AUD like the transaction (foreign cash also gets Original Amount / Currency).
  Expense -Amount, Income +Amount, Transfer out of cash -, into cash +. A split cash bill whose Notes start
  with the bill total ("76.35 - ...") gets the total, so with the repayments linked it reconciles to 0.
  Expense and Income lines are matched to their transaction (Manual, Confirmed) and the transaction becomes
  Reconciled when its difference is 0. Transfer lines get Status Transfer (not matched: the other side is
  already a bank line), with Transfer Counterpart when that side has one line.
- **Withdrawals and deposits** on bank lines ("ANZ ATM", "NON-ANZ ATM", "... WITHDRAWAL", "CASH DEPOSIT"):
  a Cash line with the opposite amount, Bank Reference `BL-<bank line id>`, both lines Status Transfer and
  each other's counterpart. "VISA DEBIT DEPOSIT" is a card refund, not cash.
- Editing a cash transaction (including its Type) updates its line and match on the next run; deleting or deactivating it removes
  the line. Never edit generated lines by hand.

### Split bills and refunds

One Finance Transaction per bill, linked to **every** bank line involved: the charge, each friend's repayment
and any refund. Its **Amount** is my share as the Notes work it out (the bill less what each friend paid, for
example "419 - <friend> 60 - <friend> 60 - <friend> 60" = 239; "<friend> 26 from 53.80" = 26 of a 53.80
repayment belongs to this bill). The charge is allocated in full (negative), each repayment or refund with its
amount (positive), so **Actual Amount** = what I really paid and **Reconciliation Difference** = 0 when
everyone has paid. Until then the difference shows what is still owed. A repayment covering two bills is
split between them (`line=amount`). No separate transactions for the friends' shares. `reconcile.py` does not
find these (no line equals the Amount): after an import, look for open transactions whose Notes subtract
amounts, find the "PAYMENT FROM" credits (Everyday) and refunds with those amounts within 14 days, check the
dry run of `split_match.py`, then `--apply`. A friend paying back more than their share: the excess is Income
(Reimbursement). A note "Repayment for <bill> ..." is not a Finance Transaction: it names the friend's
"PAYMENT FROM" line, which is linked to the bill. A note "Refund for <item> ..." works the same way: no transaction of its own; the bill's Amount is
the charge less the refund (Notes "89.48 - 12.35 refund ...") and the refund line is linked to the bill.
**One purchase, two kinds of item** (a note like "Pants 39.99, the rest shared with A"): one Finance Transaction
per part, each with its own Category and Share Type, and the one bank line split between them
(`split_match.py <ft> <line>=<-part>` once per part): 5 Oct TK Maxx 82.96 = Pants 39.99 (Clothing, Mine) +
Household items 42.97 (Home and Hardware, A).
An AMEX Travel Credit is a refund of the booking it paid for (12 Aug Finnair flight: +450 linked, Amount 1,608.60 - 450).
A refund on another account than the charge is linked too (7 Oct ALDI container refund on Everyday against a
1 Sep grocery paid with Supermarket Slayer card 7850). Paid back in cash: no bank line, so use the Foreign cash rule (Transfer to the cash
account). **Bill paid in cash, repaid by bank transfer**: link the repayments; the difference stays at the
cash paid (it has no bank line), so the transaction stays Partly Reconciled until its cash line is generated (see "Cash lines"), then it is 0.
**Work expense claims**: a purchase noted "TO CLAIM" is paid by me and repaid by the employer
("ANZ INTERNET BANKING TRANSFER EXPENSE CLAIMS ..." on Everyday). Link the claim credit to those transactions
the same way, split between them by their amounts (`line=amount`), so each one's Actual Amount is 0.
The Reconciliation Difference then equals the Amount, so `split_match.py` sets Partly Reconciled: once every
line of a claimed transaction is linked, set it to Reconciled by hand. A claim paid at another rate than the
platform's leaves a few cents of Actual Amount on the foreign rows (6 Nov claim: 0.41 on the two NZD meals).

Bank Rules are for statement lines that have no Keep note behind them (rent, salary, interest, tolls, card
fees, supermarkets). When such a line stays unmatched, the first rule whose Match Text fits its description
supplies the payee, category and share type for a new Finance Transaction. A line that matches a Keep note
never needs a rule: the note's own category wins.

**Asset purchases** (for example "Washing Machine from Appliances Online Mykin 8kg ..."): the Finance Transaction
Description is the item name only ("Washing Machine") and the rest of the note goes to its Notes. Create a
Finance Asset with the same name (Asset Type, Brand, Model, Notes with the full item text and where it was
bought) and a Finance Asset Link (Role Purchase, Allocated Amount = the transaction Amount), then recalculate the
asset's Total Cost. Assets so far: Washing Machine, Compact Freezer (1 Oct 2026, AMEX), Outdoor sleeping bags x2 (3 Aug, Cash, A),
Switch Joy-con x3 (6 Aug, Cash).

Projects: Start Date and End Date are the travel dates from the owner's Google Calendar "Travel" calendar.
They are a guide only. Flights, hotels and tickets are often bought earlier, and the Keep note says which
project they belong to.

**Paying for someone who pays back into another of my accounts** (12 Oct: a money order and its envelope
for a friend, paid back in NZD into ANZ NZ Go): one Transfer per charge (Paid From the charged account,
Transfer To the receiving account, no Category), each matched to its charge line. The receiving line gets
Status Transfer with the largest charge line as Transfer Counterpart; Notes give the rate.
Paid in cash instead (6 Aug: NZD 160 money order for a friend's passport, AUD 133.40 out of a 173.40 Australia Post
withdrawal): the Transfer is Paid From Cash, so its generated Cash line and the NZ Go repayment line are each other's
Transfer Counterpart (set by hand), and the transaction is set Reconciled by hand (it has no match).

Foreign cash bought from a friend for a trip that is over, and spent on it, is one Travel expense with Original
Amount / Currency, no cash account (USD 1400 for Yunnan). Exception: when the notes list the cash spends, the cash is
a Transfer into the currency's cash account and each spend is entered from it (JPY 40,000 for Tokyo, paid back on
1 Sep 2026: two Transfers Everyday to "JPY Cash", 30,000 dated 22 Aug (the line is 1 Sep) and the 10,000 "Cash from <friend>" on 30 Aug, sharing
the one Everyday line; Last Rate 110.619469). Leftover JPY 1,500 from an earlier Japan trip is Income
(Other Income, 22 Aug, owner's choice, as the CNY leftover above), the 30,000 spent without notes is one
"Cash Trip Expenses" (Travel, A, 22 Aug), and JPY Cash ends at JPY 2,200 as in the notes.

Supermarket Slayer cards: Bank Accounts `Special<last 4 digits>` (2486, 3054, 4481, 7195, 7850, 8979, 9873), Account Type Other.
Add a card the same way when a note names a new one.
Each card has one Bank Statement named after it (no statements from the issuer: lines typed from screenshots of the
card's activity in the app, opening and closing balance 0, period from the first Load to the screenshot date).
The Load is a Transfer paired with the "SPECIAL.GIFT ..." charge on the card that bought it (7850: AMEX, 3 Jul;
3054: AMEX 250.00, 12 Jun).
8979 (added 2026-11-23): Load 200.00 on 23 Dec 2025 and 9 supermarket purchases to 17 Feb 2026, balance 0. Its Load
stays Unmatched: the charge that bought it is before the first imported bank line (9 Jan 2026).

Payments to "ANZ Access Advantage" are an expense (Support Payments), not a transfer. NZD payments from Wise to
the owner's own name belong to the project "NZ House".

## Web page (`web/index.html`)

A single static page, published with GitHub Pages by `.github/workflows/pages.yml`, for entering and editing
Finance Transactions. It has no build step and no dependencies.

- Two tabs: **Create** (the single-transaction form, then Bulk entry) and **View** (date range and the
  transaction list, with reordering). Editing a row from View opens it in the Create form; saving or
  cancelling the edit returns to View.
- Third tab **Reconcile**: Finance Transactions with Reconciliation Status other than Reconciled, and Bank
  Statement Lines with Status Unmatched or Partly Matched (both active only), filtered by account and search.
  Suggested pairs: same remaining amount (or the same original amount, or for an estimated transaction the
  same account and a shared payee word), the same account when the transaction has Paid From, within 4 days;
  best first, each row used once; a pair with another equally good candidate is flagged. Each pair has a
  checkbox, ticked by default except flagged pairs (never auto-confirm those). Confirm (one pair) or Confirm
  selected (the ticked pairs, one after another, stopping at the first error) creates a match with Method Rule. Manual: one transaction with several lines (each line gives its remaining amount)
  or one line over several transactions (each takes its remaining amount, the last takes the rest), Method
  Manual. Matches are Confirmed with Confirmed On. The page then recalculates the rollups
  (CalculateRollupField), sets the line to Matched (nothing left) or Partly Matched, and the transaction to
  Reconciled (difference 0, or "fully reconciled" ticked) or Partly Reconciled; an estimated transaction
  that is reconciled gets Needs Details = No.

- The page is public, so it contains no environment details. On first use it asks for the Dataverse URL,
  tenant ID and app ID and keeps them in the browser. Never put those values in the file.
- Sign-in is the owner's own Microsoft account (authorization code flow with PKCE) through the app
  registration "Finance Tracker Web". Rows are created as the owner, not as the automation identity.
- The time part of **Transaction Date** is the order within a day. A new row for today gets the current
  time; for another day, one minute after that day's last row. Reordering hands the day's existing times
  out again in the new order. Bulk entry saves the rows of a day 10 minutes apart in the pasted order
  (closer together if they would pass midnight).
- Bulk entry takes `Description Amount [A|AA] [Account or Project]` lines (the amount is the last number)
  or `Date | Description | Merchant | Amount | Share flag | Account | Project or Notes` (tab or `|`). A line
  with only a date (`19 Nov`, `19/11`, `2026-11-19`) sets the date below it; without a year it is this year,
  or last year for a month after the current one.
- A negative amount is saved as Type = Income with a positive Amount. The last field is the project when it
  matches one, otherwise it goes to Notes: the owner writes how a split bill was shared there (who owes
  what), which is used to reconcile refunds and friends' transfers back.
- Cash payments use the Bank Account "Cash" (short name `Cash`, Account Type Other, no bank, no statements;
  its lines are generated, see "Cash lines").
- The page writes the amount to Finance Transaction `lzw_amount`.
- Page entries have Source = Manual, bulk entries Source = Keep.
- Test changes with a browser against Dataverse before merging, and remove the test rows afterwards.

## Keep Inbox sheet

**Retired on 2026-11-20.** The web page replaces the sheet and its flow. The flow "Finance Tracker - Import
Keep Rows" was deleted (backup outside the repo); `build_flow.py` refuses to recreate it without
`--recreate`. The environment variable `lzw_KeepInboxSheetId` and the connection reference
`lzw_FinanceTrackerGoogleSheets` were used only by that flow and still exist (owner to decide).

The layout below is kept because the web page's bulk entry accepts rows pasted from the sheet as they are.

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

Columns K and L and the `__PowerAppsId__` column were used only by the deleted flow.

## Outstanding work

Details and reasoning are in [docs/decisions.md](docs/decisions.md). State as of 2026-11-21:
Finance Transactions start on 9 Oct 2026 (notes entered back to that day, plus older notes as listed in item 8); bank lines go back to March.

| # | Item | Who |
|---|---|---|
| 1 | Test Claude Code GitHub Actions: comment `@claude` on an issue and check the run, including the Azure sign-in (`.github/workflows/claude.yml`, never run yet) | Owner |
| 2 | Decide whether to delete `lzw_KeepInboxSheetId` and `lzw_FinanceTrackerGoogleSheets` (used only by the deleted Keep flow) | Owner |
| 3 | Reconciliation runs with every inbox run (statement import rule 10, `reconcile.py`). 2026-11-21: 155 transfer pairs and 23 matches written. Decide whether `reconcile.py` should create Finance Transactions from Bank Rules for unmatched lines (478 lines fit a rule) | Owner |
| 4 | Import the next Wise export (after the Thailand trip) into "Wise 2026". Check that the hand-entered 28 Oct "Money added" +100 (`TRANSFER-2457903123`) is recognised, not duplicated | Claude |
| 5 | Test `statement_compare.py --apply` with real rows (`recalc.py` and the formula columns were checked on real rows 2026-11-21) | Claude |
| 6 | The editable grid setting for Reconciliation Match works but could not be added to the solution (error 0x80048536). Matters only for a solution export | Claude |
| 7 | Web page support for foreign cash, Transfer and Category (Dataverse side done 2026-11-21; page entries get no Category yet) | Owner to ask |
| 8 | Enter the notes before 9 Oct 2026 (3 to 19 Aug entered 2026-11-23; 20 to 29 Aug, 31 Aug, 1 Sep, 5 Sep, 12 Sep to 1 Oct and 2 to 12 Oct entered 2026-11-22). The friend's flight AKL to BNE (23 Sep) is linked to its NZ Go line and Reconciled (Payee Air New Zealand). "Hotel Deposit" (15 Oct note) has no bank line and was not created. "Fuel" 85.73 (22 Nov) and "Toll Road Top-up" 20 (23 Nov), no account, wait for their bank lines | Owner, then Claude |
| 9 | Confirm guessed categories: "Drinks at Lake View Cafe" / "Mountain View Cafe" and "Drink" (Lawson) set as Food and Soft Drinks; "Drinks" at Waterloo Hotel, Funny Funny, Hey Chica as Alcohol. Project for "Taxi from Home to Airport" (24 Oct, none now). Project Japan Tokyo Trip for "Taxi from Airport to Home" (31 Aug); Payee "Just Vapes" for the 31 Aug vapes (note: OZ Shop). Washing Machine and Compact Freezer (1 Oct) set as Home and Hardware. 6 Aug "Dog Hotel Booking Deposit" as Pets; "Switch Joy-con x3" (6 Aug) and "Outdoor sleeping bags x2" (3 Aug) as Shopping. | Owner |
| 11 | Everyday credits waiting for the October notes the owner will import: the two Duolingo repayments +28.54 and +57.08 (19 Nov) are linked to "Send Amazon Gift Card ... for Duolingo Family" (22 Oct, Partly Reconciled); a third friend's 28.54, expected into Flex, is still missing. ING Savings Booster +200.36 (12 Nov) against two transactions of 100.36 (11 and 12 Nov): the owner will upload the ING statements (ING is not a Bank Account yet; it needs one and a parser) | Owner, then Claude |

Done 2026-11-20: GitHub Pages is on (Source = GitHub Actions, latest deploy succeeded); the web page replaced
the Keep Inbox sheet and the Keep flow was deleted.
