# Finance Tracker: decisions and pending items

Why things were built the way they were, and what is still open. Read this with [schema.md](schema.md)
and the rules in [../CLAUDE.md](../CLAUDE.md).

## Pending items

| # | Item | Who | Notes |
|---|---|---|---|
| 2 | Test Claude Code GitHub Actions | Owner | `.github/workflows/claude.yml` (added 2026-11-15) ran once on 15 Nov from an `issues` event and succeeded, including the Azure sign-in; the `@claude` comment run was skipped. Owner to confirm |
| 7 | Web page: foreign cash entry (`CNY100`, a cash account's currency), Type Transfer and Transfer To | Owner to ask | Dataverse side done 2026-11-21. The owner enters trip notes through Claude Code for now. Pasted Keep entries get no Category, by design (owner, 2026-11-28) |
| 8 | Notes waiting for bank lines | Owner, then Claude | Notes before 9 Oct are entered. New rows are reconciled at the end of the next session once their lines are imported |
| 9 | Guessed categories | Owner | Café "Drinks" and the Lawson "Drink" were set as Food and Soft Drinks, bar "Drinks" as Alcohol |
| 14 | Bank Rules for unmatched lines | Owner to decide | 28 lines fit a rule (2026-11-28), all from 30 Dec 2025 to 2 Apr 2026 |
| 15 | Card payment pairing | Claude | `reconcile.py` could pair a card payment when the description names the card even with a same-amount rival |
| 12 | FY2027 income tax assessment | Owner, then Claude | When it arrives, replace the four estimated `Income Tax - 2026-06..09` lines and the net of their Salary FTs ("Estimated tax" in `statement-import.md`) |

Done on 2026-11-15: the five formula columns were created and put on forms and views; base currency
verified as AUD; `lzw_KeepInboxSheetId` verified against the sheet URL; both connection references
verified as bound; confidence threshold agreed at 0.95. `verify.py`: 370 checks, 0 problems.

2026-11-25: **Claim columns** on Finance Transaction (owner): Claim Type (Employer, Income Tax), Claim Status (Pending,
Claimed), Claim Amount. Chosen over one four-value choice so views can filter on type or status alone, and Claim Amount
holds a half claim without Notes. One transaction has one type: the ATO allows no deduction for what the employer
reimburses. The claim keeps the full price as Amount (option 2, Amount = cost after the claim, was shown and not
taken: category totals would lose the claimed spend). "Owed to me" (first made in the app) is now built by `build_ui.py`:
Partly Reconciled with a negative difference, or Employer + Pending; "Claims" lists every claim. The 7 claimed rows
(Oct taxis and meals, two 7 Apr flights) were set Employer, Claimed; the 29 Apr Melbourne ticket and its surcharge Employer,
Pending; "TO CLAIM" was removed from their Notes. `create_transactions.py` takes an 11th field `claim`.
2026-11-25: Claims checked against the owner's Xero expense list. Oct 2026 Claim Amounts set to the Xero figures
(three NZD rows a few cents below Amount). 12 claimed rows from Oct 2024 to Nov 2025 created (no bank lines, so no
Paid From or matches), in three new projects dated from the Travel calendar (2-3 Oct 2024, 4-7 Sep 2025, 25-30 Nov
2025). Xero shows the 29 Apr Virgin Australia ticket at 262.50 paid; the row's Claim Amount 525.00 Pending and the
11.13 surcharge Pending are left as they are on purpose (owner has emailed HR about them).

2026-11-25: `reconcile.py --apply` posted each match without a check, so a connection reset during the TLS handshake
stopped the run (three times in one session) before the rollups were recalculated. The POST now checks for the match
before retrying, as `split_match.py` does. After a crashed run, run `recalc.py --days 1`.

2026-11-23: the cloud environment's setup script never installed its tools (`|| true` hid the errors): pip could not
replace the Debian `argcomplete`, and PAC CLI 2.x needs .NET 10, not 8. The script now uses
`--ignore-installed argcomplete` and `dotnet-sdk-10.0` and also installs the script dependencies. Its commands were
run in that session (`az` 2.93.0, PAC CLI 2.16.1); the script itself is proven only once a new session starts.

2026-11-23: `dv.py` signs the Azure CLI in as the service principal (AZURE_CLIENT_* variables) when it is not
signed in, because each cloud session starts in a new container without the previous sign-in. Tested from a
signed-out container: WhoAmI succeeded.

2026-11-21: the transaction-to-line window in `reconcile.py` and the web page's Reconcile tab is 4 days (was 7, owner's
request), so a weekly payment (Rent, W Support) 7 days away is no longer a rival candidate. It applies to estimated
transactions too.

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

2026-11-27: **AustralianSuper and payslips imported as statements** (owner). Account Type options Super and Employer
added. Bank Accounts "AustralianSuper" (Super) and "Delta Insights" (Employer). The super CSV exports (FY24 to FY26 and
the current year) are 313 lines in four statements; every closing balance matches the annual statement, and the current
one (23,160.78 at 27 Nov) matches the app's estimate 22,916.83 once its estimated returns (-243.95, not yet credited) are
counted. Payslips (Sep and Oct 2026; the owner mentioned three, the inbox had two) are statements on the employer
account, which works as a clearing account (nets to 0 per payslip). Reasoning: the Salary FT cannot be matched to both
the payslip and the bank line, because Actual Amount sums every confirmed match; so income is recorded at **gross** on
the payslip line, PAYG tax and employer super get their own FTs, and the bank salary line and the super contribution are
**Transfers** from the employer account. This matches the Planned Transaction "Salary", already gross. Option shown and
not taken: keep super and payslips as files only (no bank line behind super). Rules: "AustralianSuper and payslips"
in `statement-import.md`.

2026-11-28: **Paxus pay advices Nov 2023 to Sep 2024** (owner asked to import "the payslips from Brisbane City Council";
the issuer is Paxus, the client Brisbane City Council). Bank Account "Paxus" (Employer), 40 weekly statements, treated
like the Delta Insights payslips. Paxus paid super monthly, so one contribution covers 2 to 5 pay advices: a Transfer
Counterpart is one line, so a per-advice "Superannuation paid" line could not pair. Chosen: a monthly
`Paxus_Super_<yyyy-mm>` statement with one line that pairs 1:1 with the contribution, as the contract invoices'
`DeltaInsights_ATO_<date>` statements pair the ATO payments; the account balance is then the super not yet paid. The
per-advice super is the month-to-date increase (exact) rather than the printed, rounded amount, so the months add up.
Net pay has no bank line (bank history starts 2026) and stays Unmatched. Rules: "Paxus pay advices" in
`statement-import.md`.

2026-11-27: **Contract invoices Sep 2024 to Sep 2026** (owner) from the Fiscal Planner "Salary" sheet, rows 2 to 24 and
27 to 30, treated like payslips: income at the invoice total incl GST, GST and income tax as Expenses. The owner wanted the
GST and tax payments linked to the months they cover, so each month has GST and tax lines on the Delta Insights clearing
account, the payment FT is matched to those lines, and the bank or AMEX payment becomes a Transfer into the account
(matching the FT to both would count it twice). The account balance is then what is still owed (35,325.00: Sep 2026 GST
and Jun to Sep 2026 tax), with one-off Planned Transactions on the due dates the owner gave. A year's tax is split by
Net Amount rather than the sheet's Est. Tax, so the lines add up to what was paid (FY2026 estimate 90,418.75, paid
82,434.30). Rules: "Contract invoices" in `statement-import.md`.

2026-11-27: **Net-only Salary** (owner). The Salary FT is the net, as a split bill is the cost after friends repay:
one Salary FT per payslip or invoice matched to the gross line (+) and the GST and tax lines (-) on Delta Insights,
so Actual Amount = Amount = net. The 11 GST Payment, 2 Income Tax, 3 Income Tax withheld and 3 Employer super FTs were
deleted (their matches moved to the Salary FTs, or removed for super). Reasoning: the owner reports on money that is
theirs to spend; gross, GST and tax stay on the clearing account lines, which now carry a Bank Category ("Gross income",
"GST", "Income tax", "Employer super") so reports can total them. Lost: Tax category totals among FTs. The ATO payments
stay Transfers into the account, so its balance is still what is owed (35,325.00). A quarter's GST rounding goes to the
Salary FT of its last month. **Estimated tax**: Jun to Sep 2026 are net of the sheet's Est. Tax; when the FY2027
assessment arrives the four lines and those Salary FTs are corrected (owner chose this over a separate adjustment FT).
**Owed payments** become Transfers: new column **Transfer To** on Planned and Recurring Transaction, and the flow
creates Type Transfer when it is set (an Expense would count the tax twice); the two owed Planned Transactions have
Transfer To Delta Insights and no Category. **Super**: locked until preservation age, so nothing inside the fund is an
FT: the payslip's employer super line and the AustralianSuper fees, insurance, contributions tax, tax benefits and
returns are Ignored (closes pending item 11); a voluntary contribution is an Expense FT, Category Investment (owner),
with its fund line Ignored. The Salary series became the Nov net pay, -12,557.33. The Paxus pay advices (imported the
same day with the gross rule) were converted the same way.

2026-11-28: **Salary series on payday** (owner): monthly on the 25th from 25 Dec 2026 (was the 5th, which the payslip
link could not pair with the payday). `payslip_link.py` reuses the flow's Salary FT (Source Recurring, any amount) from
1 day before to 2 days after the payday, so a weekend 25th paid on the Friday still pairs. The GST and income tax ATO
lines before the bank history stay Unmatched until those bank statements are imported (owner).

2026-11-27: **`dv.batch`** (owner): the contract link run made about 400 single requests (about a second each through
the proxy, 10 to 15 minutes). `dv.batch` sends 25 operations per `$batch` request, the writes as one change set (all or
nothing) and the reads (rollup recalculations) after them. A dropped request with a POST or DELETE is checked with the
caller's `done(chunk)` before it is resent, the same rule as `call()`. Tested against the environment: creates, updates,
deletes and rollups; a failing change set wrote nothing; `split_match.py --batch --apply` on throwaway rows. 25 keeps each
request well inside the proxy's 10-second limit. Used by `contract_link.py`, `split_match.py` and `payslip_link.py`;
the other scripts still write one request at a time.

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
- "Banks" in the site map is a table sub-area on Account with the title "Banks" (2026-11-26, was a URL
  sub-area). A table sub-area cannot pin a view, but the app holds only the Account view "Banks", so that
  view opens, and the sub-area shows the standard Account icon.
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
- **Processed was removed on 2026-11-25** from both tables (owner's request: it has no purpose on the series, and
  Status Reason = Completed says the same on the appointment). The 6 appointments with Processed = Yes were set to
  Completed, the column was taken off the forms and views and deleted. Side effect: the old filter
  `lzw_processed eq false` skipped rows where it was null (12 Salary instances); the new filter does not.
- **Sign convention:** Amount on the series is positive = expense, negative = income (the reverse of the
  bank). The old data used negative = money out, so the open series were flipped on 2026-11-19 (the
  platform carried the change to their open instances). Appointments were not patched directly.
- **Updating a series rewrites all its open instances** (past and future), tested on Netflix: 21 open
  instances took the new amount, the 3 completed ones kept the old one. Completed and cancelled
  appointments are read-only. The flow checks for an existing transaction before creating one.
- The flow runs daily at 6 AM Brisbane and takes open or scheduled appointments and
  Start before tomorrow (Brisbane). Each gets a Finance Transaction: Description and Payee = Subject, Date =
  Start (Brisbane), Type = Income if Amount < 0 else Expense, Amount = abs(Amount), Share Type =
  Mine, Source = Recurring (new option 859130003), Source Row ID = appointment ID, currency = the
  appointment's currency (AUD if it has none). The flow then sets the appointment to Completed. A failed appointment
  stays Open, is retried next run, and the run ends Failed.

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

### Categories (2026-11-21)
- At the owner's request every existing Finance Transaction (157, all but the two Transfers) got a Category by
  keyword rules on the description, and Claude now sets one on every transaction it creates (table in
  CLAUDE.md). Drinks covers all beverages, not only alcohol; Dining covers meals and snacks; anything bought
  "for <someone>" is Gifts. At the owner's request two categories were added (in `seed.py`): Gambling,
  Category Type Both, so wins and losses net against each other, and Accommodation under Travel.
- Owner, same day: "Drinks" renamed **Alcohol** and "Dining" renamed **Food and Soft Drinks** (meals,
  takeaway, snacks, non-alcoholic drinks); 16 non-alcoholic rows moved out of Alcohol. A meal with drinks
  is Food and Soft Drinks; the owner splits out the alcohol as its own line when it is the bigger part.
  Interlock device costs are Fines, not Car Maintenance.

### Events category (2026-11-23)
- Owner added the category **Events** (Expense, Parent Category Entertainment) for concert, festival, show and
  event tickets, and relinked 10 transactions to it: Post Malone, Together For Tomorrow (both, including the ticket
  bought for a friend, which was Gifts), ULTRA PRE-PARTY, Shokk Halloween, Guns N' Roses, Hardstyle Carnival,
  Ultra, YOASOBI, Blanc de Blanc.
- Kept in Entertainment by the owner's choice: club entry fees, karaoke, shisha bar. Attractions and sports tickets
  moved to Activities and Attractions later the same day (below).
- An event ticket bought for someone is Events, not Gifts, so the Events rule comes before the Gifts rule.

### Activities and Attractions (2026-11-23)
- Owner moved 9 transactions from Entertainment to **Activities and Attractions**: the three Disney Premier Access
  rows, Maze for two, Waiotapu Thermal Wonderland, Gondola and Ludge (Skyline Rotorua), Redwood Glowworms, Hot Tub
  Spa, and Baseball Tickets x2 (sports tickets are rare and bought while travelling). The two ski lift passes were
  already there.
- "Park Use Fee Perisher Kosciuszko National Park" (26 Jul) moved from Travel to Parking (Transport).
- Ice Skate stays in Sport and Fitness. Club entry, karaoke and shisha bar stay in Entertainment.

### Flights category and trip reporting (2026-11-23)
- Trip reports use the Finance Project (Project Type Trip), not travel copies of each category: one trip is its
  project grouped by Category; the overall report counts every transaction of a Trip project as Travel Expenses.
- New category **Flights** (Expense, Parent Category Travel). The 7 flight rows moved there from Travel, plus
  "Club Jetstar membership" (6 Sep), which also got the project Thailand EDC Trip.
- Projects for trip-like rows (owner): China Yunnan Trip on "Taxi from Home to Airport" (24 Oct) and "Taxi from
  airport to home" (2 Nov). No project, as the owner decided: 2 Oct fuel (before the road trip), the 24 Oct airport
  coffee and taxi home (seeing a friend off), 2 Nov Lotte Duty Free cosmetics (a gift, bought after the trip; its
  Category changed from Personal Care to Gifts).
- 24 Oct "Taxi from Airport to Home" and its refund combined into one transaction: Amount 24.12, Notes "31.37 - 7.25
  refund", the refund line's match moved to it, the refund transaction deleted. Reconciled, difference 0.
- New project **Ultra Beach Gold Coast 2027** (Project Type Event, 18 Apr 2027 from the owner's calendar event
  "Ultra Beach 2027"): "Ultra Tickets x2" and "Gold Coast Hotel at Surfers Chateau for Ultra x2 nights" (5 Nov).

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
- **China Yunnan Trip, 24 Oct to 1 Nov 2026** (entered 2026-11-21), with the owner's other notes of those
  days: all reconciled except the cash Tour Guide Tips and "Taxi from station to hotel" (no amount, Needs
  Details). The 2 Nov Health Insurance had been matched to the 26 Oct AHM line; the match was moved to the
  26 Oct note and the 2 Nov one waits for its own line. `reconcile.py` treats the same weekly payment 7
  days earlier as a rival (Rent, W Support), so those were confirmed by hand. Same-amount ties on one Wise day were confirmed where the note's merchant
  equals the line's merchant and no other open line has that merchant and amount (owner asked to
  reconcile). `reconcile.py` now applies this tie-break (rule 4 in CLAUDE.md); a replay of the trip with
  every match removed confirmed all 33 pairs with none left for the owner.
- **Notes of 21 to 23 Oct 2026** (entered 2026-11-21, 22 rows, Source Keep, 12:00 Brisbane then 10 minutes
  apart). Owner's answers: the David Jones belt is 48.96 (the AMEX line; the note said 48.06); the S Money
  payment (Flex 2032.14 for USD 1400 cash, used for the Yunnan tour x2) is one Travel expense, Share Mine,
  Original Amount USD 1400, no USD cash account; the Wise Duolingo Family top-up (USD 100) is Subscriptions.
  The 23 Oct TRIP.COM -5.05 is the China eSIM (Travel). 18 matched by `reconcile.py`, the two Translink
  commutes (one -1.00 line each day) by hand. The two bank Transfers and the cash casino loss stay
  Unreconciled (both bank lines already have Status Transfer).
- The eSIM (AUD 9.58 on AMEX) was paid back as CNY 70 cash. Valued at Last Rate 4.666043 that is AUD 15.00,
  so "Cash Received for eSIM from <friend>" is a Transfer of 15.00 (AMEX to CNY Cash) and the eSIM row is
  Income 5.42 (owner's decision: the friend paid more than the cost). The AMEX line is split -15.00 / +5.42.
  The rate was briefly set from the eSIM (70 / 9.58 = 7.306889) and set back at the owner's request.
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

### ANZ New Zealand account (2026-11-21)
- The owner's ANZ NZ "Go" account was added as Bank Account "ANZ NZ Go" (short name `NZGo`, Account Type
  Everyday, Account Currency NZD) under a new bank "ANZ New Zealand" (separate from ANZ Australia).
- Owner's choice: the account is kept in NZD. Its Bank Statements and lines have row currency NZD and
  Amount, Opening / Closing / Running Balance in NZD exactly as printed, so the balance check holds.
  Original Amount and Original Currency repeat the NZD amount, so matching on the original amount works.
  Dataverse converts to AUD through the NZD exchange rate (base columns). The alternative, converting
  to AUD at one rate, was rejected because the balances would no longer match the statement.
- The PDF gives no text in pypdf layout mode, so `statement_parse.py` reads it with pdfplumber
  (the label words come out joined, for example "Statementperiod"). Transaction Date is the "Orig date"
  under Visa lines; Posted Date is the statement date. Checks: running balance per line, withdrawal and
  deposit totals, closing balance.
- First statement: 1 to 30 Oct 2026, 19 lines, NZD 35.36 to 104.28. Those lines (12 to 21 Oct, NZ trip)
  are mostly before the first Finance Transaction (21 Oct), so they stay unmatched until the notes are entered.

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
- Table icons match the built-in Fluent icons (2026-11-26, owner): 20 px, 1 px line, `currentColor` and no
  hard-coded colour, so the app colours them like the standard tables in light and dark. Microsoft
  recommends `currentColor` for `IconVectorName` icons
  (https://learn.microsoft.com/power-apps/developer/model-driven-apps/image-web-resources). The app icon keeps
  its navy tile.
- The first GitHub Actions run (issue 7) wrote the script but did not run it, although the workflow had
  signed in to Azure, because `CLAUDE.md` then described only the device-code sign-in. `CLAUDE.md` now
  tells Claude to run and verify scripts itself.

### Interim exports and the payee check (2026-11-21)
- The inbox held two mid-cycle exports, not statements: an ANZ Plus Flex Saver "Transaction List" (31 Oct to
  20 Nov, opening 1,529.61 = October closing, closing 148.27) and the AMEX current-cycle export (from 14 Nov,
  Previous Balance 2,219.35 = the 13 Nov statement, Total Balance 3,165.74). Both are imported as their own
  Bank Statement because the line comparison is per account and date range, so the final statement later
  creates only what is missing. The cost: those lines stay under the interim statement.
- One AMEX line (DiDi -15.24, 12 Nov, posted 14 Nov) was flagged as a possible duplicate of DiDi -11.22 in the
  closed 13 Nov statement. Different amount and its own Reference, so it was created (`--include-possible`).
- `reconcile.py` confirmed "Dinner Korean BBQ for All (Maru Grill House)" -239 against "ZLR*KINN IMM"
  (same amount, 2 days, AMEX) although the note names another restaurant. A Payee that shares no word with
  the line now sends the pair to the owner. The match was deleted and both rows reset.

- **Placeholder instead of a separate statement** (owner, same day): a mid-cycle export now creates a
  placeholder Bank Statement that the final statement takes over, so each period has one statement. The
  two exports above were converted. The marker is the Notes prefix "Interim" rather than a new column.
- **File names** (owner): processed files are renamed to the period end (the names already used in
  Processed), mid-cycle exports to start and end dates in `Processed/Mid-cycle`. The ANZ NZ statement was
  renamed from the bank's name, which holds the full account number, and its Bank Statement with it.

- **Reconciliation chained into the import, with a lock** (owner, same day). `statement_import.py --apply`
  runs `reconcile.py --apply` itself, so the step cannot be forgotten. The lock is an environment variable
  value in Dataverse, not a file, because sessions run in separate containers; it is taken with If-Match
  (tested: of three runs started at once, one got it). A lock older than 60 minutes counts as abandoned.
  reconcile.py now recalculates only the rows it matched, because `recalc.py --days 1` took over 10 minutes.
  Trade-off: the confirmed pairs are no longer reviewed in a dry run first; the rules (single candidate,
  payee fits) are what keeps them safe, and the output lists every pair written.
- **Parallel sessions** (owner, 2026-11-22). Several sessions may create Finance Transactions at once; only
  reconciliation is serialised by the lock. A session that finds the lock held waits and retries by itself
  instead of stopping, because the lock only means another run is writing, not that something is wrong.
  Duplicates and same-day ordering are avoided by giving each session its own notes.
- **Reconcile once, at the end** (owner, 2026-11-23). Parallel sessions spent their time queued behind each
  other's lock. Now they only create transactions and import lines (`--no-reconcile`), run their own
  `split_match.py` links together at the end, and one session runs `reconcile.py --apply` after all have
  finished. A reconcile run during creation left rows open anyway, so the final run was needed regardless.
  A lock per account was rejected: transfers and split matches span two accounts.

- **Split bills** (owner, 2026-11-21): one transaction per bill linked to the charge and every repayment or
  refund, so Actual Amount is what was really paid and the matches list shows all the money involved. Chosen
  over a separate Transfer or "Paid for Others" transaction per friend: fewer rows, and the bill reads as one
  item. Applied to two shared dinners, two rideshare trips with refunds and one cash bill. `split_match.py`
  does it; matching the Notes automatically is not built, because the Notes use nicknames and one repayment
  can cover two bills.

- **Cash lines** (owner, 2026-11-21): generated Bank Statement Lines for cash, so cash reconciles like a bank
  account. One open-ended statement for AUD cash; foreign cash one statement per trip or project. Withdrawals
  and deposits are Transfers to and from Cash. Generated by a script step in `reconcile.py` (every import),
  not by a flow (owner: not needed). Lines are in AUD with the foreign amount as Original Amount, like the
  transactions. First run: 25 lines (18 withdrawals since April, 7 transactions), 8 cash transactions Reconciled.

- **Identical rows and payee rivals** (owner, 2026-11-21): totally identical transactions and lines are paired
  one each, and a candidate whose payee does not fit no longer blocks a pair. With the 4-day window this
  confirmed 9 November pairs that had been left for the owner (two bars, a vineyard, a karaoke bar, a
  restaurant booking).

### Supermarket Slayer Card 3054 (2026-11-23)
- New Bank Account "Supermarket Slayer Card 3054" (`Special3054`) and its statement from the owner's screenshot:
  Load 250.00 (12 Jun, Transfer paired with the AMEX SPECIAL.GIFT LANE COVE -250.00 line), ALDI 153.29 (16 Jun),
  ALDI 15.54 (7 Jul), ALDI 80.42 (31 Jul), Woolworths 2596 0.75 (14 Aug). Balance 0. The four purchases have no
  Finance Transaction (no notes for those days).

### Supermarket Slayer Card 8979 (2026-11-23)
- Bank Account "Supermarket Slayer Card 8979" (`Special8979`) and its Bank Statement added like card 7850, with the
  10 lines from the owner's screenshot: Load 200.00 (23 Dec 2025), then ALDI, WW Metro, Woolworths and Coles
  purchases to 17 Feb 2026 totalling 200.00 (balance 0, so the check passes). Dates as shown in the app.
- The Load has no counterpart: no "SPECIAL.GIFT" charge of 200.00 in Dec 2025 is imported (bank lines start
  9 Jan 2026). It stays Unmatched until that statement is imported. The purchases have no transactions
  (no notes for that period).

### Card 9873 (2026-11-23)
- Bank Account "Supermarket Slayer Card 9873" (`Special9873`) added like the others, with its Bank Statement
  (11 Mar to 23 Nov 2026, balances 0) and 9 lines from the owner's screenshot: Load 200.00 (11 Mar) and 8
  purchases (Coles x3, Seasons Supermarkets, IGA Bowen Hills, ALDI x2, Woolworths 0.05) totalling 200.00.
- No "SPECIAL.GIFT" charge for the Load: no -200 bank line near 11 Mar exists on any account, so the
  Load stays Unmatched (like card 7195's). The purchases have no notes or transactions yet.

### Repository
- No solution export is committed, because it contains the publisher's display name.
- The publisher unique name and environment URL are read from environment variables, never stored here.
- Statement files and parsed lines stay outside the repo (see `.gitignore`).

## 2026-11-25: cheaper note entry and reconciliation
Owner's request, to use less of the plan allowance:
- `scripts/create_transactions.py`: Claude turns the notes into a fixed-format file and the script does the
  lookups, duplicate check, order times and writes, instead of new Python per batch. Tested 2026-11-25: a dry run
  with a duplicate, a new row and a bad row (nothing written, every problem listed), then one test row written
  (all fields as expected, time one minute after the day's last row), a rerun found it, and it was deleted.
- `scripts/report.py`: `reconcile.py` and `cash_lines.py` print counts and the pairs for the owner (at most 15
  of each kind); every detail goes to a file outside the repo. Script output stays in the conversation and is
  re-sent every turn, so long lists were costly.
- Reconcile once at the end of every session, not after each import: `statement_import.py --apply` no longer
  reconciles unless `--reconcile` is given (the old `--no-reconcile` is now the default).
- `docs/decisions.md` is read only before changing the schema, flows, scripts or web page. The note-batch logs
  (32 sections) moved to `docs/decisions-archive.md`; text unchanged, checked line by line.

## 2026-11-25: CLAUDE.md split into topic files
- Owner's request, to use less of the plan allowance: CLAUDE.md (58 KB) was sent with every turn of every session.
  It now holds only the rules every session needs (16 KB) and a table of topic files in `docs/`: entering-notes,
  statement-import, reconciliation, planned-transactions, web-page, outstanding. A session reads the one its task
  needs. The text was moved unchanged (checked line by line); only the links and the "keep this file current" rule changed.

## 2026-11-25: Sonnet as the default model
- Owner's request, to use less of the weekly plan allowance: Opus uses up the limits faster than Sonnet
  (https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan).
- Set in the committed `.claude/settings.json` (`"model": "sonnet"`), not `settings.local.json`: a cloud session
  starts from a fresh clone, so a git-ignored file would not reach it. The model name is not sensitive.
- Claude cannot change the model of its own session, and a Sonnet subagent run from an Opus session would still
  pay for the Opus turns, so the rule in CLAUDE.md is to stop and suggest `/model opus` when the rules are unclear.
- Check in the next new session (`/model`) that it starts on Sonnet. A model chosen when starting a cloud session
  in the app may take precedence over the file.

## 2026-11-23: why linking is slow

- Measured: every Web API call through the proxy takes about 1 second, whatever its size. A `reconcile.py` dry run
  is 15 reads, 17 seconds. One `split_match.py --apply` makes about 12 to 15 calls (lock, match, line status, two
  rollups, transaction status, release), about 25 to 30 seconds, so 27 transactions took 13 minutes.
- Time grows with the number of writes in a run, not with the size of the tables: reads are paged 5,000 rows at a
  time and the matching is in memory.
- Removing the lock would save only its 6 calls per run and lose the protection for parallel sessions, so it stays.
- `split_match.py --batch` (owner's request): all transactions in one run. It reads the transactions and lines with a
  few `In()` filters, checks the whole batch before writing anything, takes the lock once, and recalculates and sets
  each line once after its matches (a line shared by two transactions in the batch is shared out in order). The line
  step is in a `finally`, so after a failed write the lines still show what was written and a rerun cannot allocate
  them twice; the line status comes from the recalculated Allocated Amount. A transaction that already has matches
  gets its rollup recalculated first (one rollup each), as before.
- Tested 2026-11-23 on four temporary transactions against three open 8 Jul lines (one line shared -20 / -10, so
  Partly Matched), then removed: all four Reconciled, lines correct. 28 calls, about 26 seconds plus one proxy drop
  (a dropped call costs about 25 seconds: the proxy cuts it after 10 silent seconds and `dv.py` waits 15 before the
  retry). The old way made about 15 calls per transaction.

### W Support series (2026-11-25)
- Created the weekly Monday W Support series ($1,000, Flex, Support Payments, Auto) from 23 Nov 2026, because the
  earlier one was missing. Payee: the flow sets Payee from Subject, so "Joint Main" is only in the Description.
  Pending: let the flow take Payee from the appointment (needs a flow change, Opus).

## 2026-11-26: inbox run, Kogan screenshot

- `statement_import.py` accepts a statement of kind "Screenshot" (Source Type and line Source Screenshot), so app
  screenshots go through the same compare and placeholder path as mid-cycle exports instead of hand-written rows.
  Used for the Kogan app screenshot (no export exists between statements).
- The Drive connector shows `canEdit` and `canMoveItemWithinDrive` false on every file the owner uploads (also the ones
  already in Processed); only items it created itself (the Mid-cycle folder) are true. A move tried on 2026-11-27 failed for
  all five files: "The request's OAuth scopes do not allow moving this file." The allow rules in `.claude/settings.json` only
  skip the prompt; they cannot widen the connector's access. The 21 Nov cloud session (ANZ NZ Go import) moved its PDF with the same connector call
  (`update_file` with `parentId` = the Processed folder) and it worked, so the connector's Google access has since narrowed
  (most likely a reconnect). Until the owner reconnects Google Drive with full access, the files stay in the inbox and the
  owner moves them; checked again 2026-11-28 (AustralianSuper CSVs and payslips: `canEdit` and `canMoveItemWithinDrive` false).
  Decision (owner, 2026-11-27): statement imports run from the Windows desktop session, which renames and moves the
  files on the mounted `G:\My Drive\Statements` with PowerShell; cloud sessions only report the names.
- The 23 Nov AMEX "DIRECT DEBIT RECEIVED" +1,000 and the 24 Nov Flex "PAYMENT TO AMERICAN EXPRESS" -1,000 were paired as a
  transfer by hand: `reconcile.py` did not pair them (another -1,000 Flex line the same day, W Support). Same for a 0.01
  test transfer between Everyday and Growth Saver on 25 Nov.
- Pending: `reconcile.py` could pair a card payment when the line descriptions name the card ("AMERICAN EXPRESS") even with
  a same-amount rival on another payee.

## 2026-11-28: outstanding items reviewed with the owner

- **Keep components deleted** (owner): the Keep-to-Dataverse flow idea is abandoned, the web page replaced it. The
  environment variable `lzw_KeepInboxSheetId` (with its value) and the connection reference
  `lzw_FinanceTrackerGoogleSheets` were deleted after checking that no flow used them. The Google Sheets connection
  itself (in Power Automate, not a solution component) is left. `build_flow.py` now holds only the helpers that
  `build_recurring_flow.py` uses; `verify.py` checks the two are gone.
- **Payee on Planned / Recurring Transactions** (flow change): text column `lzw_payee` (Payee, 200) on `appointment`
  and `recurringappointmentmaster`, on both forms and views, in the solution (`build_appointments.py`). The flow sets
  Finance Transaction Payee = the appointment's Payee, else its series' Payee, else the Subject
  (`build_recurring_flow.py --update-on`). Like the lookups, the platform does not copy Payee from a series to its
  existing instances (checked after patching six series), so the flow reads the series. Series Payees set from the
  owner's 26 Nov list: Rent, Health Insurance, W Support, Broadband, Utility (Electricity/Gas), YouTube Premium.
- **`statement_compare.py --apply` removed**: every import writes through `statement_import.py`, which uses the same
  `compare()` and `line_body()` and has run on real rows many times, so the second write path (one POST per line, AUD
  only) was not needed. The CLI only prints the comparison.
- **Editable grid in the solution** dropped (owner rarely edits in the app).
- **AustralianSuper lines**: all 313 are handled (300 Ignored, 13 Transfer), so the old pending item was removed.
- **Identical same-day lines**: `reconcile.py` already treats identical lines and transactions as interchangeable
  (transfers and transaction-to-line pairs), so that item was removed.
- **"Income Tax 82,434.30 AMEX"** (25 Nov note): not a single row; it is spread over the contract payments of that
  financial year to show net income (owner).
- `reconcile.py` now lists each line a Bank Rule fits in its details file (`rule:` with the rule, payee and category).
- Reminders (scheduled tasks in the cloud session): 5 Dec 2026, chase the third Duolingo repayment; 4 Jan 2027, import
  the Wise export after the Thailand trip.
