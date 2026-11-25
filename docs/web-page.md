# Web page and Keep Inbox sheet

The entry page and the retired Keep sheet layout it still accepts. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

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
