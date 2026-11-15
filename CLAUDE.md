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
- Never delete anything (tables, columns, rows, solutions, flows). If something blocks an item, skip it,
  continue, and report it.
- If a host is blocked ("Host not in allowlist"), stop that step, report the host and wait. Do not work around it.
- Match tables and columns by logical name. Add only what is missing. If a column exists with a different
  type, leave it and report it.
- After pushing work to a `claude/` branch, open a pull request to `main` and merge it straight away,
  without waiting for review. Never push to `main` directly.
- Conventions: logical name = `lzw_` + display name in lowercase without spaces. Primary column `lzw_name`.
  Tables are user-owned, no security roles. Dates are Date Only. Money has precision 2. Lookups are 1:N with
  Restrict delete.

## Environment and sign-in

- `DATAVERSE_URL`: the environment URL. `DATAVERSE_USER`: the sign-in account. Both come from the environment,
  never from files in this repo. `DATAVERSE_PUBLISHER` (unique name of the `lzw` publisher) is only needed
  to create the solution.
- No browser or password is available. Sign in with device code for both tools, as `$DATAVERSE_USER`:
  - `az login --use-device-code --allow-no-subscriptions`
  - `pac auth create --environment $DATAVERSE_URL --deviceCode`
- Verify with `pac auth list` and a WhoAmI call. Scripts take their token from the Azure CLI sign-in.

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
| `build_schema.py`, `build_formulas.py`, `build_ui.py`, `build_flow.py`, `seed.py` | Idempotent build, in this order |
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
  (`pip install azure-cli azure-identity` in a virtual environment). Sign-ins do not carry over: repeat the
  device-code sign-in for both tools.
- Skills: the dataverse skills (dv-*) come from the plugin. The model-apps and power-automate skills are in
  the public repo `microsoft/power-platform-skills` under `plugins/`.
- The network proxy drops any request that is silent for about 10 seconds, but Dataverse usually still
  completes it. `dv.py` handles this by re-checking before retrying a write. Keep that pattern.
- Check the real state first with `python scripts/verify.py`. It lists anything missing from the solution.
- The base currency is AUD (verified 2026-11-15). Scripts and the flow still set AUD on the rows they create.
  Other currencies: CAD, CNY, EUR, GBP, NZD, USD. Exchange rates are units per 1 AUD and are only changed
  when the owner asks.

## Statement import rules

1. Before creating Bank Statement Lines, query the existing lines for that account and date range.
2. Compare by **count per (date, amount, description)** and create only the shortfall, because identical
   purchases on one day are real.
3. Use **Running Balance** to separate identical lines.
4. A **PDF statement is final**: update the matching screenshot rows (description, balance) and create only
   the leftovers.
5. Flag description or amount differences as **possible duplicates**.
6. Show a summary (new, existing, possible duplicates) **before writing**.
7. Do the comparison with `scripts/statement_compare.py` (dry run by default, `--apply` to write). Keep the
   parsed lines file outside the repo.

## Reconciliation rules

1. **Rules first**:
   - Pair transfers: opposite amount, two of my accounts, within 3 days. Set Status = Transfer and
     Transfer Counterpart on both lines.
   - Exact matches: same amount, date and account.
   - Bank Rules (`lzw_bankrule`) by priority for payee, description, category and share type defaults.
2. **Then AI** for the rest.
3. Auto-confirm at or above a confidence of **0.95**. Otherwise set Match Status = Proposed and ask in the session.
4. **Never auto-confirm** when more than one candidate shares the same amount, date and account.
5. For **Wise**, match on Original Amount (CNY), not AUD.
6. After writing matches, run `python scripts/recalc.py` to recalculate the rollup columns, then update Bank Statement Line Status and Finance Transaction Reconciliation Status.

## Keep Inbox sheet

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
| 3 | Test `recalc.py`, `statement_compare.py --apply` and the formula columns with real rows (tables are empty) | Claude |
| 4 | The editable grid setting for Reconciliation Match works but could not be added to the solution (error 0x80048536). Matters only for a solution export | Claude |
