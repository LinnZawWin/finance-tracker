# Finance Tracker: decisions and pending items

Why things were built the way they were, and what is still open. Read this with [schema.md](schema.md)
and the rules in [../CLAUDE.md](../CLAUDE.md).

## Pending items

| # | Item | Who | Notes |
|---|---|---|---|
| 6 | Delete `lzw_KeepInboxSheetId` and `lzw_FinanceTrackerGoogleSheets`? | Owner | Used only by the deleted Keep flow. Kept until the owner decides |
| 2 | Test Claude Code GitHub Actions | Owner | `.github/workflows/claude.yml` was added on 2026-11-15 and has never run. Comment `@claude` on an issue and check the run, including the Azure sign-in |
| 3 | Test `statement_compare.py --apply` with real rows | Claude | `recalc.py` and the formula columns were checked on real rows on 2026-11-21 (Reconciliation Difference 0, My Cost 0 for Transfers) |
| 5 | Add the Reconciliation Match editable grid setting to the solution | Claude | The setting is active, but `AddSolutionComponent` fails with 0x80048536. Only matters for a solution export |
| 7 | Web page: foreign cash entry (`CNY100`, a cash account's currency), Type Transfer and Transfer To | Owner to ask | Dataverse side done 2026-11-21. The owner enters trip notes through Claude Code for now |
| 8 | Notes before 9 Oct 2026 | Owner, then Claude | Finance Transactions start on 9 Oct (9 to 20 Oct entered 2026-11-22; 5 and 18 to 26 Sep too; 14 to 19 Aug on 2026-11-23). Fuel 85.73 (22 Nov) waits for its bank line |
| 9 | Guessed categories and one project | Owner | Café "Drinks" and the Lawson "Drink" were set as Food and Soft Drinks, bar "Drinks" as Alcohol. "Taxi from Home to Airport" (24 Oct) has no project |
| 10 | `reconcile.py` refinements | Owner to decide | Identical same-day lines (rounds of drinks) could pair either way, as transfers already do |

Done on 2026-11-15: the five formula columns were created and put on forms and views; base currency
verified as AUD; `lzw_KeepInboxSheetId` verified against the sheet URL; both connection references
verified as bound; confidence threshold agreed at 0.95. `verify.py`: 370 checks, 0 problems.

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
- Kept in Entertainment by the owner's choice: sports tickets (Baseball Tickets x2, Tokyo), club entry fees,
  karaoke, attractions (Disney Premier Access, maze, gondola, glowworms, hot tubs, thermal park).
- An event ticket bought for someone is Events, not Gifts, so the Events rule comes before the Gifts rule.

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

### Notes of 18 to 20 Oct 2026 (entered 2026-11-22)
- 17 rows (Source Keep, 12:00 Brisbane then 10 minutes apart), all Reconciled: 10 by `reconcile.py`, 7 by hand
  (W Support, whose payee never fits "ANZ ACCESS ADVANTAGE", and the 6 ANZ NZ Go rows).
- Not created: "Weekly Allowance" (Growth Saver to Flex 3,000) and "Wise Top-up for Vapes" (Flex to Wise 50),
  both own-account transfers whose bank lines were already paired.
- ANZ NZ Go rows: Amount = NZD / 1.2273 (the platform NZD rate), so the rollup of the NZD match gives a
  difference of 0. The alternative, the Wise NZD rate of the same days (about 1.226), would leave a few cents
  of difference on every row.
- Owner's answers (2026-11-22): "Breakfast Dumplings NZD12" is the NZ Go line "EP Uncle Eric" (Uncle Eric's
  Dumplings, Taupo); it and "Breakfast Pumpkin Soup" are AA. "Taxi from Airport to Home with DiDi" (TO CLAIM)
  stays Mine (the claim pays it back) and belongs to the NZ trip project. The Gondola payee is "Skyline Rotorua".
  Own-account Transfer notes are never created as Finance Transactions. Still guesses: Swimming Pants =
  Shopping (as the T-shirt rule), Vapes = Smoking, Waiotapu, Gondola and the Hardstyle tickets = Entertainment.

### Notes of 9 to 12 Oct and 22 Nov 2026 (entered 2026-11-22)
- 29 rows (Source Keep, 12:00 Brisbane then 10 minutes apart), Paid From taken from the matching bank line. 28 are
  Reconciled: 17 by `reconcile.py`, 11 by hand with `split_match.py` (same-amount Oktoberfest rounds paired by
  merchant, the 12 Oct commute, W Support, the envelope, and the two split dinners). Fuel (22 Nov) was not reconciled
  at the owner's request.
- Split dinners (owner): the "Repayment for Dinner ..." notes are the friends' PAYMENT FROM lines, not transactions.
  Dinner Korean (Gamdang 163.30) = 81.30 after 40 + 42; Dinner Vietnamese (LS Rung 392) = 196 after 98 + 98.
- Money order 794 (Everyday) and envelope 8.15 (AMEX) for a friend, paid back as NZD 1,002.31 into ANZ NZ Go
  (owner: Transfers). Two Transfers to ANZ NZ Go; the NZ Go line is Status Transfer, counterpart the 794 line.
  AUD 802.15 = NZD 1,002.31 (1.249530) is in the Notes. The NZ Go side is not a match, so no rate difference shows.
- Payee "Hamilton's Hospility" in the notes was written as "Hamilton's Hospitality" (the bank line). The 28.00
  "Square Australia FoodFruitGourmet" round is the Hamilton's Hospitality Strathfield line.

### Notes of 5 and 18 to 26 Sep 2026 (entered 2026-11-22)
- 49 rows (Source Keep, 12:00 Brisbane then 10 minutes apart), 48 linked and Reconciled (24 by `split_match.py`, 24 by another session's
  `reconcile.py` run while this one waited for the lock; every difference is 0).
  Paid From from the note, else from the matching bank line. Claude Pro (note 5 Sep) is the AMEX line of 4 Sep, Khao
  Kluk Kapi (note 20 Sep) the AMEX line of 19 Sep.
- Salary (25 Sep): Amount and Payee from the Everyday line ("SALARY DELTA INSIGHTS P", 5,318.67), Income.
- "Refund for Taxi from Superordinary to home" (19 Sep note, AMEX +1.22 on 18 Sep) is no transaction of its own:
  the taxi is 7.16 - 1.22 = 5.94 with both lines linked. "Refund Taxi from Juan to Home" (AMEX +13.48 on 18 Sep) belongs
  to the 5 Sep "Taxi from Juan to Home" (owner): 30.92 - 13.48 = 17.44, both lines linked, Reconciled.
- A friend's flights for the Auckland team event (AA, project Delta Insights Team Event Auckland Trip): BNE to AKL on
  Flex (Jetstar 319, booking reference in Notes, linked) and AKL to BNE on ANZ NZ Go (NZD 367 = AUD 299.03 at 1.2273,
  linked 2026-11-22 to the Air New Zealand line -367.00 NZD on 24 Sep, Manual, Reconciled, difference 0).
  Payee changed from "Jetstar" to Air New Zealand (owner agreed, 2026-11-22), as on the line.
- ANZ NZ Go statements May to Sep 2026 imported 2026-11-22 (13 lines, balances chain 53.28 to 35.36 into
  October's opening). The lines before September (a Crunchyroll share, insurance, KiwiSaver, a ticket sale
  transfer, two repayments from a friend) have no Finance Transactions (those start in Sep).
- Payees as written in the notes (Quitmed for the Kogan line "Quick Rx Pty Ltd", Urban Purveyor Group for
  "WINGHAS"), except "DiDi" for "DiDi Mobility" and "Yuen's Market" for "Yeun's Market" (as on 13 Sep).
- Car wash = Car Maintenance (owner agreed). Khao Kluk Kapi stays on 20 Sep, the note's date (owner); the
  AMEX line is dated 19 Sep. Claude Pro: the AMEX charge is dated the 4th every month, the notes the 5th.

### Notes of 20 and 21 Aug and 23 Nov 2026 (entered 2026-11-23)
- 10 rows (Source Keep, 12:00 Brisbane then 10 minutes apart). 8 linked to their lines with `split_match.py`:
  Travel eSIM Japan 500MB x8 days (Trip.com, Wise 3.53 = USD 2.52, Travel, Japan Tokyo Trip), two Commutes (Translink
  1.50, Everyday), Coffee (The Lord Lamington Bar 7.49, AMEX, AA), W Support (Joint Main 1,000, Flex), Internet (Rush
  Broadband 71.95, AMEX, Utilities), Beer (3.40) and "Beer and wine with <two friends>" (41.33, me&u line, Alcohol, Mine;
  first entered as "for others" under Gifts, renamed by the owner), both AMEX with Payee Brunswick Hotel and the note's merchant in Notes.
- Pokies 50 (20 Aug, Cash, Gambling): its cash line is generated by the next `reconcile.py` run.
- Toll Road Top-up 20 (23 Nov, Tolls): no account and no bank line yet, like the 22 Nov Fuel.

### Notes of 23 Aug 2026 (entered 2026-11-23)
- 10 bank rows (Source Keep, 12:00 Brisbane then 10 minutes apart), each linked to its line with `split_match.py`
  and Reconciled. Project Japan Tokyo Trip except Rent (Madison Heights 560, Everyday, Rent, Mine, no project: the
  owner marked it as an Australian transaction). Wise rows: Love Hotel (Stellate 138.41, JPY 15,730, A,
  Accommodation; its Wise line was redated from 22 to 23 Aug at the owner's request, see below), Costume and Alcoholic Drinks at
  Love Hotel (12.32, Alcohol, owner), Lunch (Gyukatsu Motomura 51.22), Hotel Early Check-in (Hotel Ginza Daiei 8.79,
  Accommodation), Beer (FamilyMart 2.74, Alcohol), Shopping Clothes (Uniqlo 226.06, Clothing, Mine), Socks
  (Cocokarafine 22.87, Clothing, Mine), Alcoholic Drinks (FamilyMart 14.07, Alcohol, owner).
  AMEX: Hotel Booking for Matsumoto Hotel Morschein (Agoda 295.77, A, Accommodation).
- JPY cash (owner's choice, 2026-11-23): Bank Account "JPY Cash" (`JPYCash`, Account Currency JPY, Last Rate
  110.619469 from 1 Sep 2026) was added. The 1 Sep "Japanese Cash in Tokyo Trip 40k" (AUD 361.60, JPY 40,000,
  bought from a friend) changed from a Travel expense to a Transfer from Everyday into JPY Cash (still matched to
  its Everyday line, no Category), so the cash spends are recorded one by one instead. Cash spends on 23 Aug at
  that rate: Orange Juice (JPY 350 = 3.16, AA), JPY cash gift to a friend (JPY 200 = 1.81, AA, Gifts), Cash Card
  Topup (JPY 950 = 8.59, Public Transport). Whatever of the JPY 40,000 is not entered stays on JPY Cash.
- A Wise line's date can be corrected by hand (the Love Hotel line, Wise ID CARD_TRANSACTION-4228729316, 22 to 23
  Aug; Notes say so). So that the next export does not create it again, `statement_compare.py` now first pairs
  incoming and existing lines with the same Bank Reference and amount, whatever the date (tested offline).
- Wise 23 Aug lines Big Echo Ginzasukiyabas 40.04 (JPY 4,550) and Lawson 10.11 (JPY 1,148) are in the 24 Aug notes
  (created on the note's date, lines left on 23 Aug).

### Notes of 30 Aug 2026 (entered 2026-11-23)
- 12 rows (Source Keep, 12:00 Brisbane then 10 minutes apart in the note's order). Rent (Madison Heights 560,
  Everyday, Rent, Mine, no project), linked and Reconciled. The rest project Japan Tokyo Trip.
- "Cash from <friend> JPY10000": Transfer Everyday to JPY Cash, AUD 90.40 at 110.619469, Payee the friend. The JPY
  40,000 paid back on 1 Sep (PAYMENT TO <friend> -361.60) included it, so "Japanese Cash in Tokyo Trip 40k"
  became JPY 30,000 / 271.20 (name kept, Notes say so) and the line is split -271.20 / -90.40 (Method Manual).
- Cash spends at JPY Cash Last Rate: Takoyaki (JPY 700 = 6.33, A), Shaved Ice (500 = 4.52, AA), Bomber Jacket Ueno
  (6,600 = 59.66, Mine, Clothing). No Payee (the note names none). Food and Soft Drinks for the first two.
- Wise rows, linked with `split_match.py` by amount and note order: Lunch Oyakodon (Payee Azuma, from the line
  "あづま", 33.68, A), Bedsheet (Nitori 55.93, A, Home and Hardware), Coffee (Cafe Veloce 8.83, A), Alcoholic Drinks
  (Lawson 4.19 / JPY 479, Alcohol), Dinner Tonkatsu (Narita Airport 62.47), Cosmetics for mom (Narita Airport 58.85,
  Gifts), Snacks flight (Lawson 5.61 / JPY 641). Empty share flag = Mine.
- JPY Cash tally (owner, 2026-11-23): the 10,000 is part of the 40,000; the 2,200 in the notes is what was left after
  the 10,000 that morning and the 30 Aug cash spends. The 23 Aug cash spends (JPY 1,500) came from cash left over from
  an earlier trip: "Leftover JPY from Previous Japan Trip", Income from JPY Cash, 22 Aug (first day), JPY 1,500 =
  13.56, Other Income (guessed), Mine. The other 30,000 is "Cash Trip Expenses", 22 Aug, JPY 30,000 = 271.20, A,
  Travel. Both cash lines generated and Reconciled. JPY Cash now ends at JPY 2,200 (AUD 19.89). The 30,000 Transfer
  was redated from 1 Sep to 22 Aug 11:50 Brisbane (owner), so the running balance never goes below 0; its Everyday
  line stays on 1 Sep, still matched.

### Notes of 28 and 29 Aug 2026 (entered 2026-11-23)
- 17 rows (Source Keep, project Japan Tokyo Trip, Paid From Wise, Original Amount JPY, 12:00 Brisbane then 10 minutes
  apart in the note's order per day), each linked to its line with `split_match.py`. 28 Aug: Beer (Lawson 25.64,
  line dated 27 Aug), Love Hotel Stay at Sara Grande (Payee Hotel Sara Grande, owner, 236.79, Accommodation), Lunch
  pasta (Yomenya Goemon), Accommodation Tax (Hotel Sunroute Plaza Shinjuku 1.75, Accommodation), Clubbing Ticket
  (Zouk Tokyo 43.64, Entertainment), Alcoholic Drinks (FamilyMart 2.20), Soft Drinks (7-Eleven 4.36 / JPY 500, owner),
  three Alcoholic Drink in the Club x2 (Zouk Tokyo 23.61, 17.50, 17.51; the note's single "Alcoholic Drink in the
  Club" was dropped, owner), Taxi from Club to Hotel (Uber 37.05 / JPY 4,233, Taxi, last of the day, owner).
  29 Aug: Haircut (Kuefu 56.00, Mine, Personal Care), Lunch Tempura (Tempura Hisago), Dinner sushi (Tachizushi
  Yokocho), Alcoholic Drinks and snacks (FamilyMart 26.01, Alcohol), Airport Shuttle Bus (Limousine Web 62.99 /
  JPY 7,200, Payee Airport Limousine, Travel, owner). All A except Haircut.
- Taxi from Ayano House to Train Station (28 Aug, Uber, Taxi, A): the note said 8.79 / JPY 1,008, but no line has
  that amount; linked to the Uber line 12.25 / JPY 1,400 at the owner's request (Amount 12.25, Notes say so).

### Notes of 26 and 27 Aug 2026 (entered 2026-11-23)
- 23 rows (Source Keep, project Japan Tokyo Trip, 12:00 Brisbane then 10 minutes apart in the note's order per day),
  each linked to its line with `split_match.py`. AMEX: Hotel Booking Sunroute Plaza Shinjuku (Agoda 331.94, A,
  Accommodation; line dated 26 Aug). The rest Paid From Wise with Original Amount JPY; three 27 Aug rows (Breakfast
  JR East, Coffee Starbucks, Breakfast FamilyMart) have Wise lines dated 26 Aug. Categories: meals, coffee, soft
  drinks as Food and Soft Drinks; beers and alcoholic drinks as Alcohol; train and bus tickets as Public Transport;
  Baseball Tickets as Entertainment; Locker as Travel; T-shirt (Mine) as Shopping; Socks and earrings as Clothing
  (guessed); Band-aid (AA) as Health. The bus ticket note had no merchant: Payee "Alpico Kotsu" from the Wise line
  "Alpicokotsuticket" (guessed). Empty share flag = Mine.

### Notes of 25 Aug 2026 (entered 2026-11-23)
- 13 rows (Source Keep, 11:40 Brisbane then 10 minutes apart in the note's order), each linked to its line with
  `split_match.py` and Reconciled. Utility Bill (Altogether 145.77, Utilities) and YouTube Premium (6.60, Payee a
  family member as in Sep and Oct, Subscriptions): Everyday, Mine, no project (owner: the lines between the
  separators). The 11 Wise rows: project Japan Tokyo Trip, A, Paid From Wise, Original Amount JPY: two Beer at
  Combini (Fua-Sutoshiyotsupuguran 8.01 and 8.02, lines dated 24 Aug; JPY 910 each as on the lines; the note's 510 was
  a typo, owner confirmed), Beer, three Alcoholic Drinks rows (Don Quijote, Jms Furinkazan, 7-Eleven "and snacks") as
  Alcohol; Coffee and breakfast, Bento Boxes, Dinner (Kuranomukou) as Food and Soft Drinks; Train Tickets from Tokyo
  to Matsumoto (JR Central 126.29) as Public Transport; Karaoke (Joyjoy Matsumoto Stn) as Entertainment.

### Notes of 24 Aug 2026 (entered 2026-11-23)
- 15 Wise rows (Source Keep, project Japan Tokyo Trip, 12:00 Brisbane then 10 minutes apart, Paid From Wise,
  Original Amount JPY), each linked to its line with `split_match.py`. Karaoke (Big Echo 40.04, Entertainment),
  Alcoholic Drinks (Lawson, Alcohol), three Disney Premier Access (Entertainment), Cold Drinks, Popsicle, Lunch,
  Snacks and Cold Drinks, Gyoza Dog and Beer, Popcorn, Dinner Monjayaki (Moheji) (Food and Soft Drinks), Hotel near
  Disneyland (Grandnikko Tokyobay Mai 183.89, Accommodation), all A; Keychain and Balloon Disney (AA, Gifts, owner).
- W Support (Joint Main 1,000, Flex, Support Payments) and Health Insurance (AHM 163.05, Everyday, Insurance): Mine,
  no project (owner), 11:40 and 11:50 Brisbane (before the trip rows, as in the note), linked and Reconciled.
- Wise 24 Aug lines Fua-Sutoshiyotsupuguran 8.01 and 8.02 are in the 25 Aug notes (Beer at Combini).

### Notes of 3 to 6 Aug 2026 (entered 2026-11-23)
- 13 transactions, all Reconciled. Virgin Australia BNE to Bali x2 (1,260.08, project Thailand EDC Trip) is linked to
  its three AMEX lines (623.43, 623.43, 13.22) with `split_match.py`. AirAsia Bali to Phuket (Wise, IDR 5,650,064) has
  the Wise line of 4 Aug. Commute 4 Aug linked by hand to the 4 Aug Translink line (the 2 and 5 Aug -1.00 lines stay
  open: no notes).
- 3 Aug ATM 290: no transaction; its Cash line already existed (BL- reference).
- 6 Aug Australia Post withdrawal 173.40: 40 kept as cash, 133.40 bought an NZD 160 money order for a friend's passport
  extension, repaid NZD 160 into ANZ NZ Go the same day. Owner: only the 133.40 is a Transfer. Recorded as a Transfer
  Paid From Cash to ANZ NZ Go (Original NZD 160), so the Cash account keeps the 40.
- Joy-con x3 and sleeping bags x2 (cash, Facebook Marketplace) added as Finance Assets with Purchase links.
- Guessed categories (owner to confirm): Pets for the dog hotel deposit, Shopping for the Joy-cons and sleeping bags.

### Notes of 7 to 13 Aug 2026 (entered 2026-11-23)
- Rows from the notes (Source Keep, 12:00 Brisbane then 10 minutes apart in the note's order per day), all linked
  with `split_match.py` (the Finnair flight to both AMEX "AMERICAN EXPRESS INT'L" lines of 804.30), difference 0.
  Project Thailand EDC Trip for the two flights.
- "Grocery Woolworths AMEX" (13 Aug, no amount): the AMEX line MACARTHUR BRISBANE 120.77 (the rest after the
  Special9873 0.05 and Special3054 0.75 parts; those card lines are dated 14 Aug). Share A guessed from the other parts.
- The AMEX Travel booking fee 1.42 has no AMEX line and is not a row of its own (owner, 2026-11-23): it is in the
  Notes of the Finnair flight. The 12 Aug "Platinum Annual Travel Credit" +450 is linked to the flight as its
  refund, so its Amount is 1,158.60 (1,608.60 - 450), Reconciled with difference 0. 20 rows in all.
- Payees: "Osso" for the EatClub line (venue rule), "Satay Boss" for PAYO PAYMENTS (note merchant PAYO in Notes),
  "ATO" for the GST BPAY as on the earlier GST row, "Joint Main" for W Support (ANZ Access Advantage line, 10 Aug),
  "CSIS Espresso Bowen Hills" (the note's "Expresso" in Notes).
- Camping Expenses (paid to a friend) = Food and Soft Drinks (owner; there is no activity category). Concert Ticket =
  Entertainment (guessed).
- AMEX MCDONALDS BEAUDESERT 18.95 (8 Aug, no note): "Lunch Fast Food", Payee McDonald's, A, Food and Soft Drinks,
  Source Manual (owner), 12:50 Brisbane after the day's notes, linked and Reconciled.

### Notes of 14 to 19 Aug 2026 (entered 2026-11-23)
- 32 rows (Source Keep, 12:00 Brisbane then 10 minutes apart in the note's order per day), each linked to its bank
  line (`split_match.py`, or another session's `reconcile.py` run that picked some up first). Paid From from the note,
  else from the line. No project except Hotel Ginza Daiei (Agoda 73.66, AMEX, A, Japan Tokyo Trip).
- Two items paid for friends and paid back into another of my accounts are Transfers (the "Paying for someone"
  rule), no Category, each matched to its charge line; the receiving line is Status Transfer with the charge line
  as Transfer Counterpart. The "Return" / "Transfer back" notes are not transactions of their own:
  - 19 Aug money transfer at Australia Post (Everyday 148.40) for a friend's sister's passport tax, paid back as
    NZD 179.00 into ANZ NZ Go the same day (1.206199 NZD per AUD, in the Notes): Transfer Everyday to ANZ NZ Go.
  - 17 Aug Kogan Mobile voucher (Kogan card 154.00) for a friend, paid back 154.00 into Everyday (PAYMENT FROM):
    Transfer Kogan to Everyday. The note's last field "Help" is not a project, so it is in the Notes.
- "Taxi from Juan House Party to Home" (16 Aug note, no amount): the DiDi AMEX line of 15 Aug, 18.50.
- Payees: "Just Vapes" for OZ SHOPS AUBURN as on 31 Aug (the note's merchant is in Notes); "Artie and Mai" for the
  EatClub line (venue rule); "Calida" for the note's "Califa" (the line). Both Vape Pod rows (17 Aug Kogan, 18 Aug
  AMEX) have Payee "Quit Hero" (owner, 2026-11-23); the notes said "Quitmed" and "Quit Rx", both lines read "Quick Rx Pty Ltd".
- Categories: Parking for the airport parking (AA), Pets for the dog hotel, Smoking for vapes, Gifts for the
  chocolate present, Food and Soft Drinks for the Chocolate Macadamia and the show food.

### Notes of 22 Aug 2026 (entered 2026-11-22)
- 3 rows (Source Keep, project Japan Tokyo Trip, 12:00 Brisbane then 10 minutes apart), each linked to its line with
  `split_match.py` and Reconciled: Taxi from Home to Airport (Uber 18.14, AMEX, Taxi), Medicine (Welcia, Wise JPY 1,188
  = AUD 10.46: the note's 10.44 is the AUD-funded part with its fee, plus JPY 2 from the JPY balance = 0.02; Health)
  and Shisha bar (Suutopia, Wise JPY 8,107 = AUD 71.34, A, Entertainment like club entry fees, owner's choice). Amount = the Wise line's AUD.

### Notes of 31 Aug 2026 (entered 2026-11-22)
- 4 rows (Source Keep), all linked by hand and Reconciled: W Support (Flex), Taxi from Airport to Home (Uber 32.94 on
  AMEX, no amount in the note; project Japan Tokyo Trip, as the NZ airport taxi), Vape x3 (108.85, line OZ SHOPS
  AUBURN; Payee "Just Vapes" as the 30 Sep vapes, the note's merchant is in Notes) and Halloween Tickets x2 (Everyday
  -160, fully refunded by the 4 Oct PAYMENT FROM +160: Amount 0, both lines linked, Entertainment, A).

### October bank lines without notes (entered 2026-11-22, owner's request)
- 8 rows (Source Manual), each linked to its line and Reconciled: W Support (5 Oct, Flex 1,000), Commute (13 Oct),
  Crunchyroll (21 Oct, ANZ NZ Go NZD 6.66 = AUD 5.43, Subscriptions, Mine, as the Recurring rows) and five interest
  credits as Income, Interest (ANZ: Flex 6.29, Growth Saver 7.87 and 408.08 on 30 Oct; ING Savings Booster 0.16 and
  0.20 on 31 Oct). Left in October: the 4 Oct Everyday credit +160 (no note yet) and the two items in "Notes of 12 Sep".

### Notes of 12 Sep to 1 Oct 2026 (entered 2026-11-22)
- 18 rows (Source Keep, 12:00 Brisbane then 10 minutes apart), all linked by hand with `split_match.py` and Reconciled.
- Late Lunch Banquet x5 (Longwang Chopstick 412.70, A) = 165.20 after two friends' PAYMENT FROM lines (165 and
  82.50), both linked to it. The "Transfer back" notes were not created (split bill rule).
- Yunnan Trip Tour x2 (Flex 2,092.05 to a person, currency exchange USD 1500): one Travel expense, project China
  Yunnan Trip, Original Amount USD 1500, like the USD 1400 one.
- 2026-11-23 (owner): the two "Yunnan Trip Tour x2" transactions (13 Sep USD 1,500 = AUD 2,092.05, 22 Oct
  USD 1,400 = AUD 2,032.14) were merged into one dated 22 Oct, "Yunnan Trip Tour for Mom and me", Amount 4,124.19,
  Original Amount USD 2,900, Notes listing both exchanges. Both bank lines are linked to it (difference 0); the
  13 Sep transaction was deleted. Then dated 31 Oct (owner: the cash was paid to Mom that night), last row of
  that day. The tour is USD 1,650 each less USD 450 for the owner (no flight and visa) = USD 2,850; the other
  USD 50 was a gift to the owner's brother (no small notes). AUD at the blended rate of both exchanges
  (4,124.19 / 2,900 = 1.422134): tour 4,053.08, gift 71.11 (Gifts, Mine, 31 Oct), the gift split off the 22 Oct
  line (its match there is -71.11, the tour's -1,961.03).
- First Finance Assets (owner's request): Washing Machine (Mykin MFLW800W, 479) and Compact Freezer (Devanti 31L,
  169.95), each with a Purchase link. Category Home and Hardware is a guess. The last note field "Major" is not a
  project, so it went to Notes.
- Payees (owner, 2026-11-22): "Appliances Online" (not "WinningComAu") and "Just Vapes" (line VITAL SQUAD
  CHATSWOOD, not "Iron Squad"). "Bunnings Online" kept.

### Notes of 13 to 17 Oct and the rest of 18 Oct 2026 (entered 2026-11-22)
- 24 rows (owner's notes without amounts, matched to the bank lines by Claude and agreed by the owner), all
  linked one to one by hand (Method Manual) and Reconciled. NZ Go rows at 1.2273 as above; Wise rows take the
  Wise AUD and original amount (Vio.com in EUR). "Lunch Indian" is dated 17 Oct, its NZ Go line 19 Oct.
- An NZD 100 transfer to a friend for personal use in NZ is an expense, Gifts, AA (owner's decision).
- "Hotel Deposit" (15 Oct) has no bank line (probably a released hold) and was not created.
- The 6 Nov expense claim +107.06 is split across the five TO CLAIM rows: 27.66, 18.36 and 20.71 in full, and
  the remaining 40.33 over the two NZD meals in proportion (Lunch Sushi 16.14 of 16.30, Dinner Chicken Burger
  24.19 of 24.44). The 0.41 left is the gap between the employer's NZD rate and 1.2273. The five are set to
  Reconciled by hand (every line linked).
- Guesses: Driver licence renew and Car rental = Transport, Hot Tub Spa = Entertainment, payee "AA New Zealand"
  for "EP AA Palmerston North", "Bicorre" for "ZLR*BICORRE BICORRE EAGLE FARM". "Major" in the concert ticket
  note went to Notes (no such project).

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

### Notes of 1 Sep and 6 to 8 Oct (2026-11-22)
- 12 transactions. Refunds are linked to their bill, not separate transactions (split bill rule): Household
  Items 89.48 less the 12.35 hose refund = 77.13 (AMEX lines -89.48 and +12.35, difference 0); the 1 Sep
  grocery 111.07 less the 14.99 container refund = 96.08 (Everyday refund line linked; the card charge has no
  bank line, so it stays Partly Reconciled with a difference of 111.07). The earlier separate refund
  transactions (for example "Refund for Taxi from Airport to Home") were left as they are.
- The note named a card "Special7850" that did not exist: Bank Account "Supermarket Slayer Card 7850" was added
  like the other three.
- JPY 40,000 cash for the Tokyo trip (22 to 30 Aug), paid back to a friend on 1 Sep: Travel expense like the
  USD cash for Yunnan, Original Amount JPY 40,000, no JPY cash account (the trip was over).
- Pokies Win 15.65 in cash: Income, Gambling; its cash line was generated and matched.
- Card 7850 lines from the owner's screenshot: Load 200.00 (3 Jul, paired with the AMEX SPECIAL.GIFT line),
  ALDI 84.80 (14 Jul), ALDI 111.07 (3 Sep, linked to the 1 Sep grocery, now Reconciled), Woolworths 4.13 (7 Sep).
  The 14 Jul and 7 Sep purchases have no transaction yet (no notes for them).

### Notes of 2 to 5 Oct (2026-11-22)
- New project "SEQ to Northern NSW Loop Road Trip", 2 to 5 Oct (dates from the notes). In it: all of 2 Oct
  except the 7-Eleven fuel, all of 3 Oct except the commute, all of 4 Oct except rent, and only the KFC lunch
  and the coffee on 5 Oct.
- 25 transactions. The TK Maxx line (82.96) is split over two transactions (Pants 39.99 Mine, Household items
  42.97 A) instead of one with Notes, so each part has its own category and share.
- "Hotel Warwick Vines Motel at Expedia" (payee "Travel Reservation") against EXPEDIA -110.93 on AMEX: not
  auto-confirmed (payee shares no word with the line), linked by hand at the owner's request.
- "Drinks Iced Chocolate" payee corrected to "Wisteria Heavenly" as on the Kogan line.

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

### Open lines from 14 Aug closed by hand (2026-11-23)
- Owner's instructions, for lines with no note behind them. All Source Manual, linked with `split_match.py`
  (Method Manual), all Reconciled:
  - Crunchyroll 21 Aug and 21 Sep (ANZ NZ Go, NZD 6.66 = AUD 5.43 at 1.2273, Subscriptions, Payee Crunchyroll),
    as the 21 Oct one. Set Reconciled by hand (the rollup difference is 0).
  - Credit Interest and Bonus Credit Interest of 31 Aug and 30 Sep on Flex and Growth Saver (Interest, Payee ANZ).
  - Commute 14 Sep (Translink); Parking 26 Sep (Payee CellOPark, from the Bank Rule); two DiDi taxis 18 and
    26 Sep (Taxi, A); Grocery 29 Sep on card 4481 (ALDI, Groceries, A).
- "Leftover CNY from Previous China Trip" is now Other Income from CNY Cash, like the leftover JPY. That showed
  `cash_lines.py` did not update a line whose Type changed while amount, date and name stayed the same: it now
  also compares Transfer or not.
- Still open from 14 Aug: the 14 Aug Woolworths remnants on cards 9873 (-0.05) and 3054 (-0.75), the Flex
  transfers from Growth Saver in November (Growth Saver lines end on 30 Oct) and the transactions waiting for
  newer statements.
- Two `split_match.py` runs in a row stopped with `Busy` naming another split_match run less than a minute
  old, although nothing else was running here. They wrote nothing and worked on retry.

### Repository
- No solution export is committed, because it contains the publisher's display name.
- The publisher unique name and environment URL are read from environment variables, never stored here.
- Statement files and parsed lines stay outside the repo (see `.gitignore`).

## 2026-11-23: notes for 1 and 2 Aug 2026

- 15 rows (Source Keep), each linked by hand and Reconciled. 1 Aug: Commute (Kogan 0.50, line 31 Jul), six Poker
  settlements (Gambling, Everyday, Payee the friend; three wins as Income), Badminton 20.88 (Sport and Fitness, A),
  Lunch Burmese for x5 (Sorai, AMEX, A, 153.42 less two friends' 61.80 and 24.40 = 67.22), the Quit Hero vape
  starter kit (Smoking, Kogan; Payee "Quit Hero" from the description and the "Paypal *Quithero" line, the note's
  merchant in Notes). 2 Aug: Commute (Everyday 1.00), Rent (Everyday 560), W Support 12 (Flex 1,000, Payee "Joint
  Main" as the earlier rows, the note's "ANZ Joint" in Notes), Cake for potluck lunch (Kurtosh, AMEX, Food and Soft
  Drinks), Grocery Asian (Genki Mart, Kogan, AA).
- A friend's 2 Aug payment of 3.52 is their 24.40 lunch share less the 20.88 badminton they paid: matched +24.40 to
  the lunch and -20.88 to Badminton by hand. The other friend's 61.80 is linked to the lunch.
- One Poker note had 17.40 as paid, but its bank line is a 17.40 payment received: entered as a win (Income), to
  confirm with the owner.
- Left open: the 1 Aug Everyday Translink 2.00 line (no note).

## 2026-11-23: notes for 28 to 31 Jul 2026

- 16 rows (Source Keep), each linked to its line with `split_match.py` and Reconciled (difference 0).
- Account taken from the bank line where the note had none (AMEX for the beer, Kinn Imm, Criterion, Moshtix,
  Sunlit and PAYO lines). The 31 Jul Commute 2.00 is the 1 Aug Everyday Translink line left open before.
- Categories by the owner's comments: the club tickets (Flex, paid to a friend) as Events; the 28 Jul card 7195 Load
  of 70.00 is a gift from a friend, so Income (Other Income) matched to the Load line, not a Transfer.
- "Spotify Family Plan" (Notes "Payment to TLO with Amazon Gift Card", Wise, USD 23.80 = AUD 34.23, line 28 Jul): Subscriptions, not Gifts,
  because it equals the Spotify Premium series amount (to confirm with the owner).
- Payees: "David's Noodle" for the PAYO line (PAYO is the payment processor; note merchant in Notes);
  "The Criterion Tavern" from the line. "Major" (Oktoberfest note) is not a project, so it went to Notes.

## 2026-11-23: notes for 26 and 27 Jul 2026

- 16 rows (Source Keep), each linked with `split_match.py` and Reconciled, except the cash Vape (its cash line comes
  from `cash_lines.py`). Project Canberra Ski Trip on all except the owner's marked rows: Vape (Cash), Health
  Insurance (AHM, Everyday), Grocery Beef Minced (IGA, AMEX), Rent (Everyday) and W Support 11 (Flex, Payee "Joint Main").
- "Coffee at Perisher Base" (26 Jul note) is the AMEX FARWILL line of 25 Jul. "Park Use Fee" is the Service NSW line
  of 27 Jul, set as Travel (to confirm). The note's "Tax from Airport to Home" was saved as "Taxi from Airport to Home".
- Payees from the lines: "Cafe Arboretum" (note "Arobretum"), "Kinn Thai" (note "Kinn Canberra"), "Metro Petroleum".
- Left open: the AMEX DiDi credit +7.27 of 27 Jul (no note; probably a fare adjustment).
