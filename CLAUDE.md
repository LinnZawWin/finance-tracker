# Finance Tracker

Personal finance tracker on Dataverse: capture expenses (Google Keep notes entered through the web page),
import bank statements, reconcile bank lines against transactions, and track assets.
Model-driven app **Finance Tracker**. Schema as built: [docs/schema.md](docs/schema.md).
Decisions, their reasoning and pending items: [docs/decisions.md](docs/decisions.md). Read it before changing the schema,
the flows, the scripts or the web page. Entering notes, imports and reconciliation do not need it: the topic files
hold the rules. Old note-batch logs are in [docs/decisions-archive.md](docs/decisions-archive.md); read it only to look
up how a past batch was handled.

## Topic files: read the one the task needs

This file holds only the rules every session needs. Before a task, read its topic file in full:

| Task | Read |
|---|---|
| Entering notes as Finance Transactions (categories, payees, foreign cash, assets, trips, gift cards) | [docs/entering-notes.md](docs/entering-notes.md) |
| Importing statements from the Drive inbox (ANZ, AMEX, Kogan, ANZ NZ Go, Wise, AustralianSuper, payslips); run from the Windows desktop session, which renames and moves the files on `G:` | [docs/statement-import.md](docs/statement-import.md) |
| Reconciling, cash lines, split bills, refunds, work claims | [docs/reconciliation.md](docs/reconciliation.md) |
| Planned / Recurring Transactions and the scheduled flow | [docs/planned-transactions.md](docs/planned-transactions.md) |
| The web page, the retired Keep sheet | [docs/web-page.md](docs/web-page.md) |
| What is still open | [docs/outstanding.md](docs/outstanding.md) |

Entering notes usually ends with a reconciliation, so read both files for that. Rules in one file refer to sections
in another by name (for example "Cash lines" is in the reconciliation file, "Payee" in the entry file).

## Rules

- **Keep this file current.** After every change to Dataverse, the flows, the scripts or the data, update
  this file and the topic file it concerns (see the table above) in the same session so a new session can
  start from it without losing context: the current state
  (tables, columns, flows and whether they are on, sign conventions, rules learned), not a history.
  Put the reasoning and the pending items in `docs/decisions.md`, and the log of a note batch (what was entered,
  what was closed by hand) in `docs/decisions-archive.md`. Do this before reporting the work as done.
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
- **Model: Sonnet by default, Opus when the rules do not settle it.** `.claude/settings.json` sets
  `"model": "sonnet"`, so new sessions start on Sonnet for routine work (entering notes, imports, rule-based
  reconciliation). When a Sonnet session meets something the rules in this file do not settle clearly (a split
  bill, a netted repayment, an ambiguous match, a new kind of transaction, a schema or flow change), stop before
  writing that part, say what is unclear and suggest switching with `/model opus`. Carry on with the parts the
  rules do settle. Claude cannot switch the model itself.
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

Plus `account.lzw_isbank` and the Account view "Banks". Employer accounts (clearing accounts for payslips): Delta Insights, Paxus. Global choice `lzw_sharetype`:
Mine, Shared with Partner (A), All for Partner (AA), Paid for Others.
Finance Transaction **Source**: Keep (859130000), Manual, Import, Recurring (859130003).
Finance Transaction **Type**: Expense (859130000), Income, Transfer (859130002).
Finance Transaction **Claim Type**: Employer (859130000), Income Tax; **Claim Status**: Pending (859130000), Claimed;
**Claim Amount** (money, empty = the whole Amount). Views "Owed to me" and "Claims".

Planned and Recurring Transaction are in the solution as shells: only these components, not the whole table.
Columns (same on both): Amount `lzw_amount`, Payment Type `lzw_paymenttype` (global choice: Auto, Manual,
Estimated, Budget 859130003 = a weekly spending allowance the flow never turns into an FT), Paid From `lzw_paidfrom` (Bank Account), Transfer To `lzw_transferto` (Bank Account; set = the flow creates
a Transfer), Finance Category `lzw_financecategory`, Payee `lzw_payee` (text; the flow's Payee, else the series', else
Subject). On Recurring Transaction all custom columns are linked (LinkedAttributeId) to the Planned Transaction ones, so
a series copies them to its instances. The scheduled flow sets a done Planned Transaction to Status = Completed (there is no Processed column). Forms "Planned Transaction" / "Recurring Transaction", views
"Planned Transactions" / "Recurring Transactions". Both tables are under Capture in the app. The old lookups
Financial Account and Transaction Category (to the old MoneyManagement tables) were deleted.

## Sign convention

- Bank Statement Line **Amount** and Reconciliation Match **Allocated Amount** are signed like the bank:
  negative = money out (also on AustralianSuper and the employer clearing account Delta Insights). They are AUD except on "ANZ NZ Go", which is NZD (row currency NZD).
- Finance Transaction **Estimated Amount** is positive.
- Finance Transaction **Actual Amount** (rollup of confirmed matches) is signed like the bank. **Actual Cost**
  flips the sign for expenses.
- Finance Transaction Original Amount is positive, like Amount. Transfer: money out of Paid From.
- **Salary is net** (owner, 2026-11-27): one Salary FT per payslip or invoice, matched to the gross line (+) and the
  GST and tax lines (-) on the Delta Insights clearing account, like a split bill. No FTs for GST, income tax or
  employer super; their totals come from the Delta Insights lines by Bank Category ("Gross income", "GST",
  "Income tax", "Employer super"). Nothing inside the super fund is an FT.
- **Leave** is kept in the owner's Google Calendar "Leave" (one all-day event per Xero request). Salary is annual / 12
  (176 hours a month); each payslip import checks the hours against it and each Leave Without Pay lowers that month's
  Salary Planned Transaction ("Leave check" in `docs/statement-import.md`).
- Planned and Recurring Transaction **Amount** is the opposite of the bank: positive = expense, negative =
  income (with Transfer To set: positive = money out of Paid From). The open series were converted to this on 2026-11-19.

## Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| `dv.py`, `spec.py` | Web API helper and the schema specification. `dv.batch(ops, done=...)` sends writes and reads in `$batch` requests of 25 (one atomic change set each, reads after it); use it for any script that writes more than a few rows |
| `build_schema.py`, `build_formulas.py`, `build_ui.py`, `build_icons.py`, `seed.py` | Idempotent build, in this order. `build_schema.py` adds missing choice options; `build_formulas.py` updates a formula that differs from `spec.py`; `build_ui.py` rewrites the forms and views. `build_flow.py` only provides flow helpers (the Keep flow and its components are deleted) |
| `build_week_view.py` | System view "Current Week Pending Transactions" on Planned Transaction (idempotent) |
| `build_appointments.py`, `build_recurring_flow.py` | Planned / Recurring Transactions: columns, rename, forms, views, app and the scheduled flow (created off; an existing flow that is on is left untouched) |
| `verify.py [--write-docs]` | Checks everything exists in the solution, regenerates `docs/schema.md` |
| `statement_parse.py <inbox> <out>` | Parse and check ANZ, ANZ New Zealand, Kogan and AMEX files into lines files (no writes) |
| `wise_lines.py <csv> <out json>` | Convert the Wise export into AUD lines by the Wise rules below |
| `super_lines.py <out> <csv> ...`, `payslip_lines.py <out> <pdf> ...` | AustralianSuper CSV exports and payslip PDFs (Delta Insights `DeltaInsights_<yyyy-mm>.pdf`, Paxus `Paxus_<payment date>.pdf` plus its monthly `Paxus_Super_<yyyy-mm>` statements) into a lines folder for `statement_import.py` (no writes to Dataverse; see "AustralianSuper and payslips" and "Paxus pay advices" in `docs/statement-import.md`) |
| `contract_lines.py <out> <csv> <payments json>`, `contract_link.py <payments json> [--apply]` | Contract invoices from the Fiscal Planner "Salary" sheet into Delta Insights statements, then their net Salary FTs (no GST or tax FTs), the ATO payment transfer pairs and Transfer Planned Transactions for what is owed (see "Contract invoices" in `docs/statement-import.md`; link holds the lock, dry run by default) |
| `payslip_link.py [--apply]` | Link imported payslips: the net Salary FT (earnings and tax lines; no tax or super FTs, the super line Ignored), and the transfer pairs net pay <-> bank salary line and super paid <-> super contribution; holds the lock (dry run by default) |
| `create_transactions.py <notes file> [--apply] [--verbose]` | Create Finance Transactions from a notes file in the fixed format ("Notes file" in `docs/entering-notes.md`): looks up accounts, projects and categories, skips duplicates, sets the order times; writes nothing while any row has a problem (dry run by default) |
| `statement_import.py <out> [--apply] [--include-possible] [--reconcile]` | Create the Bank Statements and only the missing lines (dry run by default); a hand-typed screenshot statement (kind "Screenshot", see `docs/statement-import.md`) too. `--reconcile` also runs `reconcile.py --apply` afterwards; normally reconcile once at the end of the session instead |
| `report.py` | Short output for `reconcile.py` and `cash_lines.py`: counts and the pairs for the owner on screen, every detail in a file outside the repo whose path is printed (`--verbose` prints it all). Read that file only when a detail is needed |
| `statement_compare.py` | The comparison used by `statement_import.py`; its CLI only prints the comparison for one statement (never writes) |
| `reconcile.py [--apply] [--verbose]` | Reconcile open bank lines: transfers, then transaction-to-line pairs (as the web page suggests them, confirmed only without a rival and when the transaction's Payee shares a word with the line), then a count of lines a Bank Rule fits (each listed as `rule:` in the details file) (dry run by default). `--apply` holds the lock and recalculates the rollups of the rows it matched |
| `lock.py [--release]` | The reconciliation lock: environment variable `lzw_ReconcileLock` ("<holder> <UTC time>", empty = free), taken with If-Match so only one session reconciles at a time; older than 60 minutes = abandoned. `--release` clears it after a crashed run |
| `split_match.py <ft id> <line id>[=<amount>] ... [--apply]`, `split_match.py --batch <file> [--apply]` | Link one Finance Transaction to several bank lines (split bill or refund, see "Split bills and refunds"): Method Manual, Confirmed; sets line and transaction status; holds the lock (dry run by default). `--batch`: one `<ft id> <line id>[=<amount>] ...` per line (`#` starts a comment), checked as a whole (nothing written if any part does not fit), written under one lock. **Use `--batch` whenever there is more than one transaction**: about 5 calls per transaction instead of 15 (27 rows: about 2.5 minutes instead of 13) |
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
  Each request takes about a second through the proxy, so write in batches: `dv.batch` (25 operations per request)
  re-checks a dropped request with its `done(chunk)` callback before resending, as `call()` does. A PATCH to an id that
  does not exist creates that row (upsert).
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
- **Reconcile once, at the end of every session** (owner, 2026-11-23; the default for every session since
  2026-11-25). Batches of notes and imports only create rows (`create_transactions.py --apply`,
  `statement_import.py --apply`). Links that `reconcile.py` cannot find (split bills, refunds, one line split over
  several parts, ANZ NZ Go, claims) are run with one `split_match.py --batch <file> --apply` at the end of the session,
  not one by one. Then one `reconcile.py --apply` and the Payee suggestions (Reconciliation rule 7) close the session.
  Report the lines and transactions left open.
- When the owner says other sessions are running, only the last session to finish (or a new one the owner starts)
  runs `reconcile.py --apply`.
- **When the lock is held, wait and retry without asking.** Check it with `python scripts/lock.py` every few
  minutes (in a cloud session use Monitor with an until-loop, not a foreground `sleep`) and rerun the step as
  soon as it shows "(free)". Do not run `lock.py --release` while the holder is under 60 minutes old: only a
  lock older than that is abandoned (the next run takes it over by itself). Report how long you waited.
- Each session updates this file and `docs/decisions.md`. Before pushing, merge the latest `main` and keep
  both sessions' changes.
