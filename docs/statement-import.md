# Statement import

Importing bank statements from the Drive inbox, including ANZ New Zealand and Wise. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

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
**Run statement imports from Claude Code on the owner's Windows machine** (owner, 2026-11-27). Google Drive is
mounted there as `G:\My Drive\Statements`: read the files from `G:\My Drive\Statements\Inbox` and, once a statement is
imported and its check passes, rename and move it with PowerShell, for example
`Move-Item -LiteralPath 'G:\My Drive\Statements\Inbox\PaySlip.pdf' -Destination 'G:\My Drive\Statements\Processed\DeltaInsights_2026-11.pdf'`
(mid-cycle exports to `Processed\Mid-cycle`). Check the target name does not exist first. A cloud session can only
reach the files through the Drive connector, which cannot move or rename files it did not create
(`canMoveItemWithinDrive` is false on files the owner uploads): there it imports, reports the new names, and the owner
moves them.

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
   **Kogan app screenshots** (2026-11-26): Kogan has no export between statements, so a screenshot of the app's
   Transaction history is typed into a lines file (date, description as shown, amount, line number) and an entry in
   `_statements.json` with `"kind": "Screenshot"` and `"interim": true` (period from the day after the last statement
   to the screenshot date, opening = the last closing balance, closing = opening + the new lines).
   `statement_import.py` then creates an Interim placeholder with Source Type and line Source Screenshot, named
   `KoganMoneyBlackCard_<yyyymmdd start> to <yyyymmdd end>`. Only lines not on an earlier statement are typed (a
   line dated before the period that the last PDF did not include is new). The next Kogan PDF updates the placeholder
   and finalises the screenshot lines (rule 6).
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
10. **Then always reconcile, once, at the end of the session.** Processing the inbox is not finished when the lines are written: reconcile
    every Unmatched or Partly Matched bank line (all accounts, not only the new ones) against the Finance
    Transactions as far as the Reconciliation rules below allow, without being asked. Confirm what the
    rules allow, leave the rest Proposed or unmatched, and report what was matched, proposed and left.
    Run `reconcile.py --apply` once after the last import and note batch of the session (or
    `statement_import.py --apply --reconcile` when the import is the session's only task; not in parallel
    sessions, see "Parallel sessions"). It holds the lock `lzw_ReconcileLock`, writes only what the rules allow and recalculates the rollups of
    the rows it matched. Check its output and report it. If it says NOT RUN (another session holds the lock),
    wait and retry as under "Parallel sessions". On its own,
    `python scripts/reconcile.py` is a dry run. It prints counts and the pairs for the owner; every pair is in the
    details file it names (`--verbose` prints them all). Then suggest Payees for
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

## AustralianSuper and payslips (2026-11-27)

Two Bank Accounts that are not banks, Account Type **Super** and **Employer** (options added 2026-11-27):

- **AustralianSuper** (short name `Super;AustralianSuper`, account key `Super`). Source: the portal's
  "MemberTransactions" CSV, one per financial year (`AustralianSuper.MemberTransactions.<start>__<end>.<member>.csv`)
  and one for the year so far (`...Current-statement.<member>.csv`). `scripts/super_lines.py <out> <csv> ...`
  writes the lines and `_statements.json`; then `statement_import.py` as for a bank.
  - One Bank Statement per financial year, "AustralianSuper <period end>"; the current year is an Interim placeholder
    "AustralianSuper <1 Jul> to <last date>", updated by the next Current-statement export and finalised by the year's CSV.
  - The CSV has no balances: opening = the previous closing (first statement 0, the account opened 7 Nov 2023),
    closing = opening + the lines. Check every closing against the annual statement (FY24 10,552.34, FY25 19,665.06,
    FY26 21,686.63, all exact) and the current one against the app: the app's estimated balance also counts
    **estimated returns**, which are not a transaction until they are credited (at 30 June or a switch), so
    app estimate = closing + estimated returns (28 Nov 2026: 23,160.78 - 243.95 = 22,916.83).
  - Line: Description "<Title> - <Description>" (for example "Insurance - Premium - Death",
    "Contribution - Employer - Delta Insights Pty Ltd"), Bank Category = the CSV Category (CONTRIBUTIONS, FEES,
    INSURANCE, GOVERNMENT_TAXES, INVESTMENTS), Notes = a contribution's payment period, Line Number = the order in the file.
  - Super is locked in the fund until preservation age, so nothing inside the fund is a Finance Transaction (owner,
    2026-11-27): fees, insurance, contributions tax, tax benefits and returns are Status **Ignored** (set on import),
    and the fund's money shows only as this account's balance. Leave accounts of type Super and Employer out of any
    cash forecast or "available money" figure.
  - A **voluntary contribution** from a bank account: an Expense FT, Category **Investment**, Paid From that account,
    matched to the bank line; the "Contribution - Personal" line on AustralianSuper is Ignored (linking it too would
    count the money twice). For a tax deduction set Claim Type Income Tax, Pending. The 6 Feb 2026 $10 contribution is
    before the bank history: Ignored, no FT.
  - An employer contribution is a transfer from the employer account: Transfer Counterpart = the payslip's
    "Superannuation paid" line (set by hand, the dates are days apart). Fees, insurance, taxes and returns have no
    Finance Transactions yet (owner to decide); they stay Unmatched. Paxus contributions (Dec 2023 to Oct 2024) wait for
    their payslips.
- **Delta Insights** (`DeltaInsights`), a clearing account: one Bank Statement per payslip, named after the file
  (`DeltaInsights_<yyyy-mm>`), opening and closing 0, every line dated the Payment Date.
  `scripts/payslip_lines.py <out> <pdf> ...` reads the payslip and checks its totals. Lines and their links:

  | Line | Sign | Linked to |
  |---|---|---|
  | `Salary & Wages - <item> <hours> x <rate>` (one per earnings item), Bank Category "Gross income" | + | FT "Salary" (Income, **net pay**, Salary and Contract Income, Paid From Delta Insights) |
  | `Tax - PAYG`, Bank Category "Income tax" | - | the same Salary FT |
  | `Superannuation - SGC - AustralianSuper ...`, Bank Category "Employer super" | + | none: Status **Ignored** (the employer's contribution is locked in the fund) |
  | `Superannuation paid - SGC - AustralianSuper ...` | - | Transfer Counterpart: the AustralianSuper "Contribution - Employer" line |
  | `Net pay - <bank account> Salary` | - | Transfer Counterpart: the Everyday "ANZ INTERNET BANKING TRANSFER SALARY DELTA INSIGHTS P" line |

  So the Salary FT is the **net**, like a split bill: Amount = gross less PAYG = Actual Amount (owner, 2026-11-27; there
  are no "Income Tax withheld" or "Employer super" FTs). The Everyday salary line is a **Transfer**, not matched to a
  Finance Transaction (linking the Salary FT to both the payslip and the bank line would count it twice in Actual
  Amount). Gross income and tax come from the Delta Insights lines by Bank Category. The payslip date and the bank date are the same day.
  Payslips processed: Sep, Oct and Nov 2026. The Everyday "ANZ INTERNET BANKING TRANSFER <yyyymm01> DELTA INSIGHTS P" lines
  (8 Apr to 7 Oct 2026) keep their Salary FTs matched to the bank line until their payslips arrive. The Nov payslip's
  "Superannuation paid" line waits for its AustralianSuper contribution (not in the export to 27 Nov); rerun
  `payslip_link.py --apply` after the next super import to pair it.
  In Processed the files keep their names (`DeltaInsights_<yyyy-mm>.pdf`; super CSVs as downloaded).

## Contract invoices (Delta Insights, Sep 2024 to Sep 2026)

Before the payslips (from 25 Sep 2026) the owner invoiced Delta Insights as a contractor. Source: the "Salary" sheet of
the owner's Fiscal Planner (Google Sheets), one row per invoice month. Download it as CSV (or read it with the Sheets
connector and write a CSV with the same headers) and write the payments file by hand, both outside the repo:
`{"gst": {"<quarter's last month>": "<paid date>"}, "tax": [{"fy", "from", "to", "paid", "amount"}],
"owed": {"gst": "<due>", "tax": "<due>"}}`. Then `contract_lines.py <out> <csv> <payments>`,
`statement_import.py <out> --apply` and `contract_link.py <payments> --apply`.

The Delta Insights account is the clearing account, as for payslips, but its balance is **what is still owed to the
ATO**:

| Statement | Line | Sign | Linked to |
|---|---|---|---|
| `DeltaInsights_Invoice_<yyyy-mm>` (dated Paid On) | `Invoice - <m> - <days> days, <net> + GST <gst>`, Bank Category "Gross income" | + Total incl GST | FT "Salary" (Income, **net**, Salary and Contract Income, Paid From Delta Insights) |
| | `GST - <m>`, Bank Category "GST" | - | the month's Salary FT |
| | `Income Tax - <m>`, Bank Category "Income tax" | - | the month's Salary FT (Notes name the year, or "Est. Tax" while owed) |
| | `Paid to bank - <m>` | - | Transfer Counterpart: the Everyday "ANZ INTERNET BANKING TRANSFER <yyyymm01> DELTA INSIGHTS P" line (Apr to Oct 2026 only; earlier months stay Unmatched, owner) |
| `DeltaInsights_ATO_<date>` | `GST paid - <first>..<last month>` | + BAS amount (whole dollars) | Transfer Counterpart: the Flex Saver BPAY TO TAX OFFICE line (Apr 2026 on) |
| | `GST rounding - <...>`, Bank Category "GST" | + cents | the Salary FT of the quarter's last month |
| | `Income tax paid - <fy>` | + | Transfer Counterpart: the AMEX ATO line (FY2026) |

- **Net only** (owner, 2026-11-27): the Salary FT's Amount = Total incl GST less the month's GST and income tax (plus a
  quarter's GST rounding on its last month), matched to those lines, so Actual Amount = Amount. GST and income tax have
  no FTs; their totals come from the lines (Bank Category "GST", "Income tax"; gross from "Gross income"). The ATO
  payments are Transfers into the account. "GST paid" and "Income tax paid" lines before the bank history (to Feb 2026
  GST, FY2025 tax) have no bank line and stay Unmatched.
- **Estimated tax** (Jun to Sep 2026): those four Salary FTs are net of the sheet's Est. Tax (33,575.00); their Notes
  and the `Income Tax - 2026-0x` lines say so. When the FY2027 assessment arrives, replace the four lines with the
  assessed amount split by Net Amount (cents on the last month), set each Salary FT's Amount to the new net (Invoice +
  GST + tax lines) and its Notes to final, and recalculate the rollups. No new FT.
- A year's tax is split over its months by Net Amount (cents on the last month): FY2025 = Sep 2024 to Jun 2025,
  77,415.45 paid 12 Nov 2025 from Flex Saver (no bank line); FY2026 = Jul 2025 to May 2026, 82,434.30
  paid 24 Nov 2026 on AMEX. Jun to Sep 2026 use the sheet's Est. Tax (33,575.00) and are owed.
- GST quarters follow the sheet's Total GST column (Sep 2024; Oct to Dec 2024; Jan to Mar, Apr to Jun, Jul to Aug,
  Sep to Nov 2025; Dec 2025 to Feb, Mar to May, Jun to Aug 2026). The six payments before the bank history are FTs
  "GST Payment (for <a> to <b> income)", Paid From Flex Saver, dated from the sheet's "GST Account Transfer Out Total"
  column (the first new date after the quarter). The owner confirmed the rule: the column's 27 Apr 2026 is the day the
  Dec 2025 to Feb 2026 GST was paid (the Flex line posted 28 Apr). Sep 2026 GST (1,750.00) is owed. (The GST
  Payment and Income Tax FTs were deleted on 2026-11-27, net only.)
- Owed amounts have one-off Planned Transactions with **Transfer To Delta Insights** and no Category: "GST Payment (for
  2026-09 income)" 1,750.00, 28 Feb 2027, Manual, Flex Saver; "Income Tax (for 2026-06 to 2026-09 income)" 33,575.00,
  24 Nov 2027, Estimated, no Paid From. The flow creates **Transfer** FTs from them (the tax is already off the net
  Salary FTs, so an Expense would count it twice). Then: add a `DeltaInsights_ATO_<date>` line (`GST paid - 2026-09..2026-09`
  or `Income tax paid - FY2027`, + the amount paid), match the Transfer FT to the bank payment line (-) with
  `split_match.py`, and set the ATO line Status Transfer with the bank line as Transfer Counterpart.
- The Salary FTs that existed (7, from 8 Apr to 7 Oct 2026, entered from the bank line) were moved to the invoice line.
- `contract_link.py` now links net: the invoice, GST and tax lines to the Salary FT, and pairs each ATO line with its
  bank payment (an Expense FT entered from a note for that payment, matched only to it, is deleted).

