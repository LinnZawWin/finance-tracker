# Entering notes

How to turn the owner's notes into Finance Transactions: foreign cash, categories, payees, assets, projects and gift cards. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

## Notes file (`scripts/create_transactions.py`)

Enter notes in two steps, so no creation code is written per batch:

1. Turn the owner's notes, however they are written, into a notes file in the scratchpad (outside the repo),
   one line per Finance Transaction with every field filled from these rules (Category, Payee, account, project):

   ```
   date | description | payee | amount | share | account | project | category | notes | original
   2026-11-24 | Lunch Burger | Grill'd | 21.90 | A | AMEX | | Food and Soft Drinks
   2026-10-23 | Dinner | Some Restaurant | 42.86 | | CNYCash | China Yunnan Trip | Food and Soft Drinks | rate 4.666043 | CNY 200
   ```

   Amount is AUD, negative = Income. Share: empty (Mine), A, AA or P (Paid for Others). Account: the Bank Account
   name or a Short Name alias. Original: a foreign amount (`CNY 200`) for Original Amount / Currency.
2. `python scripts/create_transactions.py <file>` (dry run: counts, duplicates and problems), then `--apply`.
   It writes nothing while any line has a problem. Rerunning the same file creates only what is missing.

Lines whose meaning is unclear (no amount, unknown account or payee, no category rule fits) are not put in the
file: ask about them all in one list. What the format cannot hold is created by hand as before: Transfers, split
bills with friends' shares, one purchase split into parts, assets (Finance Asset and Link), foreign cash spends
that need a rate worked out, netted repayments. Keep the script output short: do not pass `--verbose` unless a
row needs checking.

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
  line when the note has none. Reconcile once at the end of the session (`reconcile.py`).

## Categories

Every Finance Transaction Claude creates gets a Category from its description (the payee only when the
description says nothing). Transfers have none. The first rule that fits wins; when none fits, ask.

| Description says | Category |
|---|---|
| Concert, festival, gig, show or event tickets (also clubbing event tickets such as "ULTRA PRE-PARTY"; also a ticket bought for someone). Not sports tickets, club entry or attractions | Events (under Entertainment) |
| "for <someone>" (for example "for Mom"), gift, present, souvenir (also snacks or cosmetics bought for someone, and AA trip items such as a keychain or balloon) | Gifts |
| Hotel, accommodation | Accommodation (Travel) |
| Flight, airline membership (Club Jetstar) | Flights (Travel) |
| Tour guide tips, other trip costs | Travel |
| W Support (Joint Main) | Support Payments |
| Rent | Rent and Housing |
| Insurance | Insurance |
| Utility, broadband, electricity, water, mobile | Utilities |
| YouTube, Claude Pro, Prime Video, Crunchyroll, Spotify, Duolingo, DiDi Pass | Subscriptions |
| Annual fee, bank fees | Fees and Charges |
| Interlock device | Fines |
| Parking fine, car tow (owner, 2026-11-25) | Parking Fines |
| Fuel | Fuel (Transport) |
| Taxi, DiDi, Uber (not Uber Eats) | Rideshare and Taxi (Transport) |
| Train, metro, commute, Translink | Public Transport (Transport) |
| Pokies, casino, betting (win or loss) | Gambling (Category Type Both) |
| KiwiSaver or other retirement / investment contributions | Investment (added 2026-11-24) |
| Attractions and paid activities: ski lift pass, ski gear hire or upgrade, theme park passes (Disney Premier Access), maze, gondola and luge, thermal park, glowworms, hot tubs; also sports tickets (rare, while travelling) | Activities and Attractions (under Entertainment) |
| National park entry or park use fee | Parking (Transport) |
| Club entry, cover charge, cat cafe entry, shisha bar, karaoke | Entertainment |
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

## Other entry rules

**Asset purchases** (for example "Washing Machine from Appliances Online Mykin 8kg ..."): the Finance Transaction
Description is the item name only ("Washing Machine") and the rest of the note goes to its Notes. Create a
Finance Asset with the same name (Asset Type, Brand, Model, Notes with the full item text and where it was
bought) and a Finance Asset Link (Role Purchase, Allocated Amount = the transaction Amount), then recalculate the
asset's Total Cost. Assets so far: Washing Machine, Compact Freezer (1 Oct 2026, AMEX), Outdoor sleeping bags x2 (3 Aug, Cash, A),
Switch Joy-con x3 (6 Aug, Cash), Men's Snow Drift Gloves (11 Jul, Everyday), Jean Pants x2, Shoes White and Green,
Shoes Navy Blue Tommy Hilfiger, Underwear three pack x2 (12 Jul, AMEX), Mask Wolf (14 Jul, AMEX), Office Chair
(12 Jun, Cash, Furniture), Air Fryer (1 Jun, Everyday, Appliance, bought on Marketplace), Small desk (27 May, Everyday, Furniture, bought on Marketplace).

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
Amount / Currency, no cash account (USD 2,900 bought for Yunnan, 13 Sep USD 1,500 and 22 Oct USD 1,400: "Yunnan Trip Tour for Mom and me",
31 Oct (paid to Mom that night), USD 2,850 = AUD 4,053.08 at the blended rate 1.422134, linked to both exchange lines;
the other USD 50 = AUD 71.11 is "Gift for <brother>" (Gifts, 31 Oct), split off the 22 Oct line). Exception: when the notes list the cash spends, the cash is
a Transfer into the currency's cash account and each spend is entered from it (JPY 40,000 for Tokyo, paid back on
1 Sep 2026: two Transfers Everyday to "JPY Cash", 30,000 dated 22 Aug (the line is 1 Sep) and the 10,000 "Cash from <friend>" on 30 Aug, sharing
the one Everyday line; Last Rate 110.619469). Leftover JPY 1,500 from an earlier Japan trip is Income
(Other Income, 22 Aug, owner's choice, as the CNY leftover above), the 30,000 spent without notes is one
"Cash Trip Expenses" (Travel, A, 22 Aug), and JPY Cash ends at JPY 2,200 as in the notes.

Supermarket Slayer cards: Bank Accounts `Special<last 4 digits>` (2486, 3054, 4481, 7195, 7850, 8979, 9873), Account Type Other.
Add a card the same way when a note names a new one.
A card received as a gift: its Load is Income (Other Income) Paid From the card, matched to the Load line
(7195: 28 Jul, 70.00, from a friend).
Each card has one Bank Statement named after it (no statements from the issuer: lines typed from screenshots of the
card's activity in the app, opening and closing balance 0, period from the first Load to the screenshot date).
The Load is a Transfer paired with the "SPECIAL.GIFT ..." charge on the card that bought it (7850: AMEX, 3 Jul;
3054: AMEX 250.00, 12 Jun).
8979 (added 2026-11-23): Load 200.00 on 23 Dec 2025 and 9 supermarket purchases to 17 Feb 2026, balance 0. Its Load
stays Unmatched: the charge that bought it is before the first imported bank line (9 Jan 2026).

Payments to "ANZ Access Advantage" are an expense (Support Payments), not a transfer. NZD payments from Wise to
the owner's own name belong to the project "NZ House".
