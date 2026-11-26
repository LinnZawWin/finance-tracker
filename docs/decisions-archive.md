# Finance Tracker: note-batch logs (archive)

How past batches of notes were entered and which open lines were closed by hand, moved out of
[decisions.md](decisions.md) on 2026-11-25 to keep it short. History only: the rules they led to are in the topic
files listed in [../CLAUDE.md](../CLAUDE.md).

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

### Open lines from April to August closed by hand (2026-11-23)
- Owner's instructions, for lines with no note behind them. 29 rows (27 after 2026-11-24), Source Manual, linked
  with one `split_match.py --batch`, all Reconciled:
  - W Support 5 and 12 Jul (Flex 1,000, Payee Joint Main); Salary 7 Jul (Everyday 30,250, Delta Insights).
  - Two AMEX charges spent by W and paid back by PayID on 13 Jul (Air New Zealand 353.40, Malee Mad 206.86): first
    created as Amount 0 / Share AA transactions linked to both lines; on 2026-11-24 the owner preferred no
    transaction, so both were deleted with their matches and each charge is paired with its credit as Status
    Transfer (Transfer Counterpart both ways). It is not my money, so no cost or category is recorded.
  - Parking 27 Jul: "EASYPARK PRAHRAN" is the EasyPark app (Australian office in Melbourne), so the descriptor's
    suburb is not where the car was; the owner was in Canberra, project Canberra Ski Trip stays.
  - Crunchyroll 21 May, 22 Jun and 21 Jul (ANZ NZ Go NZD 6.66 = AUD 5.43), set Reconciled by hand (rollup difference 0).
  - Parking 27 Jul (EasyPark, AMEX 11.82, project Canberra Ski Trip).
  - All open Credit Interest and Bonus Credit Interest lines (30 Apr, 29 May, 30 Jun, 31 Jul; Flex and Growth Saver;
    Interest, Payee ANZ).
  - Taxi from Badminton to Burmese Restaurant 1 Aug (DiDi, AMEX 11.32, A); Commute 5 Aug (Translink, Everyday 1.00).
  - All open AHM lines as Health Insurance (7 Apr, 20 Apr, 4 May, 18 May, 1 Jun, 15 Jun, 10 Aug; Everyday 163.05).

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

## 2026-11-26: notes for 24 to 26 Apr 2026 (Sydney Microsoft AI Tour 2026 Trip)

- 32 rows (Source Keep) with `create_transactions.py`, amounts and accounts from the bank lines where the note had none
  (AMEX unless the note said ANZ). Project Sydney Microsoft AI Tour 2026 Trip on every row except the Powerball bought for a friend
  (The Lott 6.30, Everyday, Gifts, as the note said Gift). "Cash Withdraw 140" (25 Apr) was already a Cash transfer pair: no transaction.
- Matched with `reconcile.py --apply`; the four pairs it left to the owner (The Lott / TATTS ONLINE, Eventbrite / "EB *SAT 25
  APRIL-ANZAC", the two identical Wahlburgers 26.71 lines one each to "Beer" and "Beer Jug") linked with `split_match.py --batch`.
- The 24 Apr Ivy Heinekens are on Ivy lines of 24 Apr (8.76 x2) and 25 Apr (9.87 x4, 19.73), posted after midnight.
- Owner's answers (2026-11-26): 24 Apr DiDi 11.68 = "Opera house to Club", 13.04 = "club to hotel" (descriptions and
  times swapped). "Mover Van Rental" (62.16, Everyday PAYMENT TO a friend, no project) in the new category Moving & Relocation.
  eBike Rental rows for ARIO 15.69, Lime 16.39 and Hello Bike 2.50 (A, Transport). Opal 25 Apr 4.62 and 26 Apr 27.57
  (Mine, Public Transport, Payee Transport for NSW). "Taxi from Airport to Home" (27 Apr 00:17, DiDi 34.75 line of 26 Apr, A,
  in the trip project). Line left open: 25 Apr PAYMENT TO a person 8.00.
- Still guessed: "Oyster" = Christies Seafood Glebe 34.41 (Everyday), "Salmon Sashimi" = Sushi Bar at the Fish 19.96 (AMEX);
  LIV Sydney club entry as Entertainment; Payees "Caffe Lev" (note said "Cafee Lev") and "Don & J Pty Ltd".

## 2026-11-25: notes for 5 to 16 Jun and 24 to 25 Nov 2026

- 60 rows (Source Keep, 12:00 Brisbane then 10 minutes apart in the note's order per day). 49 linked with one
  `split_match.py --batch` run and Reconciled; the four Cash rows (Vape Moggin 60, Pokies 90, Pokies Win 50.55 as
  Income, Office Chair 190) by their lines from `cash_lines.py`. The 24 and 25 Nov rows wait for their bank lines.
- Later the same day (owner): Pitbull Concert Ticket and Lunch Burger changed to A; added 25 Nov Groceries 33.75 (A)
  and Snacks Cake 2.95 (AA, Food and Soft Drinks). No account in the notes.
- Owner's answers: "Income Tax" 82,434.30 is an Expense (Tax) on AMEX as written; Salary 12,557.33 is Everyday;
  the cash vape has no Payee; "Ayanochan Goodbye and Salmon Party" (Everyday 80 to a friend) is Food and Soft Drinks.
- Parking fines are now **Parking Fines** (owner's comment). The 30 Jun and 3 Jul parking fines were already Parking
  Fines when checked, and so was "Car Tow Collect" (2 Jul). The owner then moved the tow rule to Parking Fines too.
- Payees written (owner, 2026-11-25): the suggested ones, the party row as the friend's name, and "Sabzi Mandi (24x7
  Fruit and Vege)" for the 247FRUITV line. Every Pokies Win row was already Gambling (Income).
- Not transactions: "Special Grocery Gift Card 3054" (already the AMEX SPECIAL.GIFT / card 3054 Load pair) and
  "Cash Withdraw for Office chair" (already a Cash transfer pair). Office Chair is a Finance Asset (Furniture,
  Purchase link 190, Total Cost 190).
- Amounts from the lines where the note had none: Homeware and Games Kmart 52.00, Table tennis 20.19, Dinner skewer
  49.37, Fruits and vegetables 16.17 (247FRUITV), Grocery Indian 22.47 (Gol Gappa), Breakfast Bread 9.94, x3 Beer
  39.27, Bowling 39.80, Yakiniku 86.58, Lunch Ramen 42.00. Accounts from the lines where the note had none.
- The 16 Jun Commute is the 15 Jun Everyday Translink line; the 6 Jun MET rows are on 7 Jun Everyday lines.
- Guessed (to confirm): Bowling as Sport and Fitness, Board game entry as Entertainment, Kmart homeware as Home and
  Hardware, Office Chair as Home and Hardware.
- Left open (no notes): 9 and 12 Jun Everyday Translink lines, 15 Jun AMEX Prime Video 2.99, 1 to 5 Jun lines
  (notes before 5 Jun not entered yet).

## 2026-11-24: notes for 17 to 26 Jun 2026

- 49 rows (Source Keep, 12:00 Brisbane then 10 minutes apart in the note's order per day), 48 linked with one
  `split_match.py --batch` run; the cash Vape (Punk Apes, 25 Jun, A) by its line from `cash_lines.py`.
- Account from the bank line where the note had none (AMEX for most, Everyday for "ANZ"). "Rent" had the account in
  the share field: Everyday, Mine.
- "Badminton and Lunch" (22 Jun note, one Everyday payment of 52.10 to a friend) is two rows on 21 Jun (owner):
  Badminton 19.10 (Sport and Fitness) and Lunch 33.00 (Food and Soft Drinks), both A, the line split between them.
- New category "Investment" (Expense, no parent), owner's choice: "Kiwi Saver" (ANZ NZ Go NZD 1,042.86 = AUD 849.72
  at 1.2273, Payee "Milford KiwiSaver Plan", no project), set Reconciled by hand (rollup difference 0).
- The ticket sale row (26 Jun, ANZ NZ Go NZD 482.21): the owner is a middle man. A ticket resale company paid the owner
  earlier for the friend's ticket and this passes it on. Amount 0 (Other Expense), the outgoing line linked; it stays
  Partly Reconciled until the earlier resale payment is found and linked.
- The 25 Jun Wise payment to my own name (NZD 1,568.45, AUD 1,288.95) and the ANZ NZ Go credit of the same NZD
  amount are paired as a transfer by hand (different currencies, so `reconcile.py` does not pair them).
- "A Return ..." notes (24 Jun) are Partner's repayments: the two Everyday PAYMENT FROM lines (+51.25, +63.90) stay
  open until the bills (before 17 Jun) are entered.
- Payees from the lines where the note's merchant was a processor or another name (note's merchant in Notes):
  "JJ & PK" (note Square), "Chattahoochee Joe's" (note Bank Vault Lounge), "Hair Studio Monochrome" as before.
  "Grove Social" for the EatClub line (venue rule). "1l4.50" (Ice for house party) is 4.50, the line.
- Categories confirmed by the owner (2026-11-24): Health for "Grocery medicine", Groceries for "Ice for house party",
  Entertainment for the Eat Street night market entry, Gifts for the GoFundMe donation, Food and Soft Drinks for the
  AA birthday lunch for Partner. The Payees taken from the lines stay. The cash vape's Payee is "Valley Tobacco" (owner).

## 2026-11-23: notes for 27 Jun to 3 Jul 2026

- 37 rows (Source Keep) plus one Manual, all linked with `split_match.py --batch` and Reconciled. Account taken from
  the bank line where the note had none (AMEX for most; Everyday for "ANZ").
- Split bills (repayment notes are not transactions): "Dinner Skewer with friends" (3 Jul, Soul Memory Restaurant,
  Everyday, A) Amount 70.22 = 184.22 less three friends' 45, 35 and 34 (Everyday 3 and 4 Jul, linked); the 2 Jul
  Death and Taxes drinks (AMEX, Mine) Amount 40.58 = 100.58 less a friend's 60 (Everyday 2 Jul, linked).
- "Special Grocery Gift Card 7850" (Karta 200, Transfer) was already the AMEX SPECIAL.GIFT / card 7850 Load pair:
  no transaction. The AMEX "KARTA PD STRIPE" +20.00 of 3 Jul is "Refund AMEX Special Grocery Gift Card" (Income,
  Refund, Payee Karta, Source Manual), as the 9 Sep one (owner).
- Parking fines (owner): the 137.50 one is the 30 Jun note, on the 1 Jul Flex BPAY line. The 3 Jul note is the
  Everyday BPAY of 333.00 (Amount and account changed from the note's 137.50 Flex). Payee "Brisbane City Council",
  the fine number in Notes. "Major" went to Notes on these, the lawyer and the tow.
- "Car Tow Collect" is Parking Fines, like the parking fines (Fines until 2026-11-25); "Hyokatsu for JC" is Alcohol like the other Hyokatsu rows (owner).
- Guessed (to confirm): Ekka tickets as Events; the Kmart / Target household rows as Home and Hardware; the Health
  Insurance note's share flag "W" as Mine (as before).

## 2026-11-23: notes for 4 to 10 Jul 2026

- 36 rows (Source Keep), all Reconciled: 34 linked with one `split_match.py --batch` run (36 matches); the two Cash
  rows (Pokies at Casino 50.00, Vape x2 85.00) by their lines from `cash_lines.py` in the following `reconcile.py --apply`.
- Combined at the owner's request: the 7 Jul dinner at The Lex (Amount 171.38) is linked to the AMEX W Brisbane line
  (-161.38) and the 6 Jul First Table reservation (-10.00).
- The 4 Jul lunch at Chu The Phat (EatClub, Payee the venue) and the badminton a friend paid are separate (owner, after
  first combining them): lunch Amount 51.76 = 77.63 less the friend's 25.87 share; "Badminton" 17.50 (Sport and Fitness,
  Everyday, A, Payee the friend). The friend's +8.37 (5 Jul) has two matches by hand, +25.87 on the lunch and -17.50
  on Badminton, as on 1 Aug. The note's "badminton 17" is 17.50 (owner).
- "Tokyo DisneySea x2" (Wise, 167.48): Original Amount JPY 18,800 (Wise split it 18,798 JPY + 0.02 AUD; the note says 0.03).
- The cash withdrawal note (ANZ Queen Street 90, 4 Jul) was already a Cash transfer pair (5 Jul lines): no transaction.
- "Rent" note had the account in the share field ("ANZ"): Everyday, Mine. "Returnt" saved as "Return"; "Major" went to Notes.
- Guessed (to confirm): "Intercom App Access" as Rent (Payee from the line, the note's PayPal merchant in Notes);
  the BNE to Canberra flight in Canberra Ski Trip although the comment said Japan Tokyo Trip; the Kogan Mobile voucher
  as Utilities.

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

## 2026-11-23: notes for 20 to 25 Jul 2026

- 25 rows (Source Keep), 24 linked to their lines with `split_match.py` and Reconciled. Project Canberra Ski Trip on
  all except the owner's marked rows: YouTube Premium (Everyday), the TMR seatbelt fine (Flex, Fines, AA), Utility
  Bill (Altogether, Everyday, A), Commute 23 Jul and 22 Jul (Everyday), Prescriptions and shoe insoles (Chemist
  Warehouse, AMEX, Health), and (owner, later) the 20 Jul Commute, 20 Jul Broadband and 21 Jul movie ticket.
- "ANZ" in a note is Everyday. Notes without an account took it from the line (AMEX; Flex for the fine).
- "Korean Dinner" (24 Jul, A) has Amount 0 and no line: a friend paid (Notes). Set Reconciled by hand.
- "Min Maw Kun Movie Ticket" (21 Jul, Everyday 50.00, comment "Donation"): Gifts (owner). "Major" on the Kookaburra Lodge note is not a project, so it went to Notes.
- Guessed categories (to confirm): Skitube add-ons as Public Transport (a train), "Ski gear upgrade" as Travel.
- The three Brumby beers are paid to "LS S AND D WILLIAMS NO" (the note's merchant): Payee "Brumby Bar & Grill"
  from the description, the note's merchant in Notes.
- The two 1 Day Skitube Add On rows (Mine and AA, Kogan 63.00) are on the 24 Jul lines (note 25 Jul).
- Left open: the AMEX DiDi credit +1.25 of 23 Jul (no note).

## 2026-11-23: notes for 26 and 27 Jul 2026

- 16 rows (Source Keep), each linked with `split_match.py` and Reconciled, except the cash Vape (its cash line comes
  from `cash_lines.py`). Project Canberra Ski Trip on all except the owner's marked rows: Vape (Cash), Health
  Insurance (AHM, Everyday), Grocery Beef Minced (IGA, AMEX), Rent (Everyday) and W Support 11 (Flex, Payee "Joint Main").
- "Coffee at Perisher Base" (26 Jul note) is the AMEX FARWILL line of 25 Jul. "Park Use Fee" is the Service NSW line
  of 27 Jul, set as Travel (to confirm). The note's "Tax from Airport to Home" was saved as "Taxi from Airport to Home".
- Payees from the lines: "Cafe Arboretum" (note "Arobretum"), "Kinn Thai" (note "Kinn Canberra"), "Metro Petroleum".
- The AMEX DiDi credit +7.27 of 27 Jul is a refund on "Taxi from Airport to Home" (owner): Amount 44.62 - 7.27 = 37.35, both lines linked, Reconciled.

## 2026-11-23: notes for 16 to 19 Jul 2026

- 23 rows (Source Keep); 21 linked with `split_match.py` and Reconciled. The two Cash rows (Vape 65.00, Pokies 21.90)
  wait for their lines from `cash_lines.py` at the final `reconcile.py --apply` (a parallel session was running). Project Canberra Ski Trip only on the two Perisher lift passes (Kogan, 16 Jul).
- Friend's repayments, as the owner decided: the 19 Jul +90 "dinner return" is split 18.42 (half of the drinks, renamed
  "Alcoholic Drinks for two with HKM", Amount 18.42) and 71.58 to "Seafood share plates" (Amount 52.91). The 17 Jul +80
  covers both Carindale drinks bills (57.99 and 21.25, both Amount 0); the extra 0.76 is an Income row "Drink for HKM
  Return" (Reimbursement).
- Ski Lift Pass: new category "Activities & Attractions" under Entertainment (Expense), created at the owner's request.
- Guessed categories (to confirm): "Drink for HKM" as Alcohol (repaid, so not Gifts);
  "Badminton and Mexican Lunch" as Sport and Fitness (as the 14 Sep "Badminton and Lunch").
- Payees: "The Criterion Tavern" (note "Criterion"), "BWS" (note "BWS Albion Hotel"), "IGA", "The Boundary Hotel".
- Left open: the 15 Jul Kogan Perisher lines (-228.00 x2) and other lines before 16 Jul have no notes yet.

## 2026-11-23: notes for 11 to 15 Jul 2026

- 27 rows (Source Keep), all Reconciled: each linked with `split_match.py`; the cash "Dinner and Drinks Korean"
  (14 Jul, Sul.Zip, A) has Amount 134.10 = 254.10 less two friends' repayments (+45 and +75, Everyday 15 Jul, linked)
  and its cash line (-254.10) from `cash_lines.py`. That `reconcile.py --apply` run also created the cash lines of the
  16 to 19 Jul Vape and Pokies rows. "Return for ..." and "... Return" / "Badminton Share" notes are repayments,
  not transactions. The ATM withdrawal note (300, Transfer) was already a Cash transfer pair: no transaction.
- "Badminton Court Hire" (11 Jul, AMEX, A): Amount 20.02 = 36.16 less two friends' repayments (+5.14 on 14 Jul and
  +11 on 12 Jul, Everyday), all three lines linked.
- The two 228.00 lift passes (Kogan, Mine and AA, project Canberra Ski Trip) are on the 15 Jul lines (note 14 Jul).
  The ALDI grocery on Supermarket Slayer card 7850 is on the 14 Jul card line (note 11 Jul).
- "Rent" note had the account in the share field ("ANZ"): saved as Everyday, Mine. The Health Insurance note's share
  flag "W": Mine (owner). "Heath Insurance" saved as "Health Insurance".
- Assets (Purchase links): Mask Wolf (Other), Jean Pants x2, Shoes White and Green, Shoes Navy Blue Tommy Hilfiger,
  Underwear three pack x2, Men's Snow Drift Gloves (37 Degrees South, bought from a friend), all Clothing.
- Ski Gear Hire (14 Jul) and Ski gear upgrade (25 Jul) set to Activities and Attractions (owner).
- Guessed categories (to confirm): Mask Wolf as Shopping, Card Game as Gambling (as Poker),
  Bag for A as Gifts, the flight as Flights.

## 2026-11-25: notes for 30 May to 4 Jun 2026

- 27 rows (Source Keep), nothing reconciled yet (owner: reconcile later). The 1 Jun Health Insurance already existed (skipped).
- "Return for Thai Dinner" notes are the friends' repayments, not transactions: "Thai Dinner for whole table" (4 Jun,
  Dodee Boran, A) has Amount 41.75 = 148.15 less 24.50, 40, 19.90 and 22 (Notes). Link the four PAYMENT FROM lines with `split_match.py`.
- Air Fryer (1 Jun, Everyday, 50.00, Home and Hardware): Finance Asset (Appliance, Brand Philips) and Purchase link; Payee "Marketplace" as noted.
- Not entered (no amount): 30 May "Uber to pickup A", "Uber by A (Returned by <friend> at a later date)", "Taxi from casino to home".
- Guessed (to confirm): Batting cage as Activities and Attractions; Milksha as Payee (note field said "We Partner");
  "Thi Ngoc Dung Tran" kept as Payee as written; Royal George written as "Royal George Hotel" (as before); Kmart Mount as "Kmart".


## 2026-11-25: notes for 21 May to 30 May 2026, the April flights and reconciliation to 4 Jun

- 28 rows (Source Keep) with `create_transactions.py`, accounts and amounts from the bank lines where the note had none.
- Flights (Flights, Sydney AI Tour Trip / Melbourne Estia Health Trip): 7 Apr "Flight Ticket from Sydney to Brisbane JW44UJ"
  78.00 (Everyday, Mine) and "... for both NJ9VFI" 262.00 (Flex, AA, one booking for both), 8 Apr "Flight Ticket from
  Brisbane to Sydney for Partner RVLQMR" 83.00 (Flex, AA), 29 Apr own return ticket 525.00, the 11.13 card surcharge and
  Partner's return ticket 525.00 (AMEX, AA). The 25 May Delta Insights claim +471.50 is split 78.00 (JW44UJ, in full,
  Reconciled), 131.00 (my half of NJ9VFI, Reconciled by hand) and 262.50 (own 29 Apr ticket: half claimed, the other half
  pending, Partly Reconciled). The surcharge (claim pending) is linked to its charge and Partly Reconciled. Partner's
  29 Apr ticket is not claimed (Reconciled). The 262.50 was first put on Partner's ticket and moved at the owner's request.
- The two identical 29 Apr Virgin 525.00 lines were assigned one each. The 23 May DiDi rides (owner): 10.59 "Charmy to Yoyo",
  16.75 "Yoyo to home". "Dinner with HKM Couple" is the Goukai 101.65 line (the note named no place).
- Small desk (27 May, Everyday 30.00, Payee Marketplace): Finance Asset (Furniture) and Purchase link.
- Casino Win 4.05 (Income, Gambling, Cash): its cash line came from `cash_lines.py`.
- Reconciled to 4 Jun: `reconcile.py --apply` confirmed the plain pairs; `split_match.py --batch` linked the claims, the
  Thai dinner (charge and four repayments), the desk, the Commutes, Air Fryer, Milksha, Hanaromart and the identical
  Ballpark and Royal George rows. The 30 May to 4 Jun rows are all Reconciled.
- `reconcile.py` crashed three times on a connection reset during a match POST; it now checks for the match before
  retrying (as `split_match.py`), and `recalc.py --days 1` recalculated the rollups the crashed runs skipped.
- Added after the owner's answers: 30 May "Uber to pickup A" 60.48 and "Taxi from casino to home" 14.00 (Uber, AA);
  "Uber by A" (AA) Amount 0: the 29 May 51.25 charge and Partner's 24 Jun +51.25 repayment are both linked. "Cookies for
  house party" (24 May, 54.02, Payee Kürtősh, the West End bakery behind "LS KÜRT_SH"). 19 May "Household items at Kmart"
  Amount 60.00 = 79.00 (18 May Kmart Stafford line) - 19.00 refund (21 May, laundry basket), both lines linked. All Reconciled.

## 2026-11-25: notes for 5 to 20 May 2026 and 26 Nov

- 52 rows (Source Keep) with `create_transactions.py`, amounts and accounts from the bank lines where the note had none.
  49 linked with `split_match.py --batch` and Reconciled; the two Cash rows (Vape Alibaba 60.00 A, Drying hanger 5.00)
  get their lines from `cash_lines.py`; Commute 0.50 (26 Nov, Everyday) waits for its Translink line.
- Two lines on one row: "Asian groceries" (6 May, A) = both Sunlit Asian Supermarket charges 120.32 + 26.99;
  "Trolley hire" (6 May) Amount 15.00 = Bunnings 115.00 charge less the 100.00 refund the same day, both linked.
- "Scam Vape" (20 May) is the Everyday PAYMENT TO 100.00 the same day, Other Expense (no scam or loss category).
- Guessed (to confirm): The Met 17 May lines 40.56 = "entry x2", 18.25 = "x2 Corona"; 6 May notes on the 4 and 5 May
  lines (Kmart 133.00 = household essentials, Bunnings 45.87 = household items, Chemist 25.00 = medicine, 35.97 = hair
  products, ALDI 148.19 and Woolworths Metro 8.20 = the two groceries); "Ketchup" on the Collins Restaurants 2.40 line,
  Payee KFC (Collins Foods runs KFC); "Beer and fried chicken" as Food and Soft Drinks; Whisper API (OpenAI) as
  Subscriptions; Pearson VUE exam as Education, not a claim; "Club Entry for two friends" as Gifts ("for <someone>").
- After the owner's answers (2026-11-26), 11 more rows, all linked and Reconciled except the cash washing machine:
  - DiDi lines of 16 May are both rides of the night of 17 May: 18.17 "Taxi from Funny Funny to The Met" (00:35),
    14.83 "Taxi from club to home" (03:01); the two rows were swapped and dated with those times.
  - "Bowling x2 and Escape Room Fun Bundle - group of 6" (10 May, A, Strike 296.14) Amount 96.14: 50 from each of four
    repayments (a friend's 50 in full, and 50 of the 67, 84 and 100). "Thai Dinner for 7" (A, Kinn Imm 126.88 with the
    8.12 credit) Amount 17.76: the rest of those repayments (17, 34 and 50). The 100 was first all on the bowling and
    split at the owner's request.
  - "Clubbing YoYo table" (9 May, A, Entertainment, Everyday) Amount 160, linked to the 160 PAYMENT TO the friend who
    booked it, Reconciled. 65 per person; the extra 30 is the owner's contribution to the table, not owed back.
  - 9 May Funny Funny from the Square receipts in Gmail: 20:55 40.25 (Cass 3+1, sweet potato fries, Milkis) =
    "Drinking at Funny Funny" (A); 22:11 24.15 (Cass 3+1) and 23:33 56.35 (Cass 7+3) = "Beer at Funny Funny". Items in
    Notes, times from the receipts.
  - 8 May "Club entry for 4 Yenda" is the Vegas Group (Fabric Nightclub) 60.99 line, split in halves: "Club Entry for two
    friends" 30.50 (Mine) and "Club Entry" 30.49 (A); "Beer x2" (A) is the 22.36 line. Payee Fabric Nightclub. Owner:
    no uneven shares needed.
  - 7 May Felons Barrel Hall: 79.83 "Drinks for x3 and snacks", 41.19 "Drinks" (both A), receipt items in Notes.
  - "Washing machine" (6 May, 150.00, Cash, Payee Marketplace, paid to the seller in cash): Finance Asset (Appliance)
    and Purchase link.
- Still open: Hotel Beach House 13.24 and Strike 1.02 (10 May),
  Thai Jing Jing 16.16 (17 May): no notes.

## 2026-11-25: past work claims from Xero

Created 12 Finance Transactions (Source Keep, Claim Type Employer, Claim Status Claimed, Claim Amount = Amount, no Paid
From or project): 2 Oct 2024 hotel 221.25, taxi 53.82, lunch 22.90 (Road to AI Sales conference); 6 Sep 2025 Air New
Zealand checked bag 40.00, hotel car parking for a colleague 35.72 (Parking); 7 Sep 2025 DiDi 63.22 and 34.78;
25-30 Nov 2025 DiDi 31.62, lunch 14.43, dinner 23.61, lunch 14.01, DiDi 48.59. Oct 2026 Claim Amounts corrected to
16.05, 20.63 and 24.36. Projects created and linked: Sydney Microsoft AI Tour 2024 Trip (3 rows), New Zealand
Palmerston North and Auckland for NZTA and DI Team Event 2026 Trip (4), New Zealand Palmerston North and Wellington
NZTA NZBAS Trip (5). 15 Oct 2026 dinner Payee changed from "Mexico" to "Brew'd Hawt Chicken" (as in Xero).

## 2026-11-25: notes for 28 Apr to 4 May 2026 (Melbourne Estia Health Trip)

- 29 rows (Source Keep) with `create_transactions.py`, amounts and accounts from the bank lines where the note had none.
  Project Melbourne Estia Health Trip on every 30 Apr to 4 May row and the 29 Apr hotel (Super.com 326.87, A, Everyday),
  except Cirque Du Rave. 27 linked with `split_match.py --batch`; the two Cash rows (Vacuum cleaner 175.00, Vape 60.00 A)
  got their lines from `cash_lines.py`. All 29 Reconciled.
- Vacuum cleaner (28 Apr, Marketplace 189.00 = 175.00 cash + 14.00 Everyday PAYMENT TO the seller): two transactions,
  one Finance Asset (Appliance) with two Purchase links, Total Cost 189.00.
- Guessed (to confirm): 1 May Beer x3 = the three Francis Hotel 14.08 lines and Retro club entry = Francis Hotel 20.12
  (posted 2 May, note said 20); Pinot Noir Carafe = Main Bar 59.00; 30 Apr Asahi Beer x2 = QT Melbourne 30.45; Udon
  Izakaya lines 107.65 dinner, 27.25 Sake (AA), 18.20 Udon; 2 May USB cable = Ampol Apollo Bay 25.00; 3 May Fuel before
  car return = 7-Eleven 11.10; Cirque Du Rave (Events, A) = Everyday FIXR.CO 88.00 (note said Stripe); Twelve Apostles
  Motel Payee Agoda (note said Booking.com, the line is Agoda).
- Added after the owner's answers (2026-11-26): 28 Apr Japanese Dinner 74.00 = the Everyday PAYMENT TO the friend who paid
  the bill (Mine). 29 Apr Bowling 35.90 + Malay Dinner (with two friends, Payee Ya Hoo Kitchen) 114.60 = 150.50; one friend
  paid 100.00 for two of the three portions, split in proportion: 23.85 to Bowling (Amount 12.05), 76.15 to the dinner
  (Amount 38.45), the +100.00 line split between them. 30 Apr "City Express Bus refunded" (Skybus, Public Transport):
  Amount 0, the BTI Pty Ltd Melbourne Airport -83.40 charge and the +33.60 Skybus refund both linked, so 49.80 is not
  refunded yet: Partly Reconciled, difference -49.80, in "Owed to me". 2 May Beer 6 pack (A) = Port Campbell Hotel 29.41;
  "Dinner Confectionary" was paid by someone else (not entered). 3 May 18:46 "Taxi from Museum of Desire to MEL Airport"
  DiDi 39.57 (A); 4 May "Taxi from BNE airport to home" = the 3 May DiDi 35.46 (A). The "Cirque Du Rave Fixr AMEX refund"
  has no bank line: ignored. 1 May 09:35 "Bernie Dieter's Club Kabarett - Melbourne 2026" (Events, A, Payee
  Bernie Dieter) = the AMEX 156.85 line, Reconciled (2026-11-26).

## 2026-11-26: notes for 17 to 23 Apr and 26 May 2026

- 45 rows (Source Keep) with `create_transactions.py`, amounts and accounts from the bank lines where the note had none
  (AMEX unless the note or the line said ANZ Plus Everyday). Project Sydney Microsoft AI Tour 2026 Trip on the 20 Apr hotel
  (Metro Aspire Hotel Sydney, Vio.com 658.66, Wise, A) and the 22 to 23 Apr rows (not the Translink commutes).
  43 linked with `split_match.py --batch`; the two Cash rows (Cannabis Gummies x2 bag 120.00, Entertainment as the owner
  said; Pokies win 35.00, Income, Gambling) get their lines from `cash_lines.py`.
- 18 Apr taxis from the DiDi and Uber receipts in Gmail: DiDi 23.66 (17:33) = "Airbnb to The Star casino", Uber 12.77
  (18:36) = "The Star casino to Brisbane Showgrounds". The DiDi 31.24 (22:47) has no note.
- "Yakiniku Birthday Dinner" (21 Apr, A, Shimo Yakiniku 1,181.16) Amount 341.16 = 1,181.16 - 120 x 3 - 480, the four
  22 Apr PAYMENT FROM lines linked to it.
- 21 Apr Charmy lines: 21.24 x2 = the two beer packs (Mine), 20.22 = "Two wines" (A); Livewire 20.16 = "Heineken x2" (A),
  the 22 Apr Livewire 10.00 = "Heineken" (Mine).
- Guessed (to confirm): Payee "Royal National Agricultural and Industrial Association" for the RNA Queensland beer lines,
  "Sunnybank Hotel" for ALH GROUP 8780 SUNNYBANK.
- Owner's answers (2026-11-26): Ear plugs x2 is Shopping, and one pair is a Finance Asset "Ear plugs" (Other, Purchase
  link 25.50, half the shared 51.00). Payees of the cash rows: "GOAT - Squid (Telegram)" (the gummies seller) and
  "The Star" (pokies win at The Star Casino, as the 29 May Casino Win).
- Lines left open without notes: 17 Apr Translink 1.00, 18 Apr DiDi 31.24, 19 Apr Charmy 21.24, 20 Apr Woolworths Newstead
  113.20 and Translink 1.00, 21 Apr DiDi 11.49 and GloBird Energy 34.43, 22 Apr Opal 20.95.

## 2026-11-26: notes for 11 to 16 Apr 2026

- 48 rows (Source Keep) with `create_transactions.py`, amounts and accounts from the bank lines where the note had none
  (AMEX unless the note or the line said otherwise). No project (Ultra Beach Gold Coast 2026 has none). All 48 linked
  with one `split_match.py --batch`.
- "Wines for Partner at Liquor Legends Uptown CBD Hotel Beach House" (11 Apr, AA): Amount 9.30 = the 73.20 Hotel Beach
  House charge - the 24 Jun PAYMENT FROM Partner +63.90 (the "A Return" note had said 11 Jun), both lines linked.
- 15 Apr Linkt from the Linkt receipts in Gmail: "Pay Outstanding Toll" = 106.36 (invoices 59.56 + 46.80), "Top-up for
  Transfer Error" = 98.50 (toll invoice transfer 98.15). The 20.07 Linkt line has no note.
- "Airbnb at Kelvin Grove" (Rent) = the 14 Apr AMEX 199.86 (Airbnb receipt: Kelvin Grove 15 to 17 Apr). The 15 Apr 213.00
  is the Coopers Plains stay 17 to 19 Apr, no note.
- 14 Apr beers by the owner's rule (more than one beer A, else Mine): Charmy 24.27 and 21.24 A, Pineapple Hotel 12.23 and
  Alice Bar 10.18 Mine.
- Guessed (to confirm): the Ultra GC bar lines (12 Apr): 17.68 x2 = "Drink for Partner" (AA), 12.12 = the drink for a friend
  and "1 beer for me", 41.93 = "2 beer for Partner one for me and 1 drink for friend" (A), 24.25 x5 = four "2 beer for
  friend one for me" and one "2 beer for Partner one for me" (A); one of the five "2 beer for friend" notes has no line and
  was not created. "Japanese dinner and drinks shinobi" = Glad Kitchen 109.70, "Beer x2 at JP" = Glad Kitchen 24.72 (Payee
  Shinobi). Bedroom Lounge Bar (13 Apr): 26.14 = "Corona and Vodka cider for friend", 13.33 x2 = "1 Corona". "Hot chocolate at
  the hotel cafe" = Everyday Woodroffe Hotel 6.00; "Katsu curry" = Sushi Time 22.00; "Breakfast at Selah" = Everyday Cafe
  East Brisbane 15.70; "Japanese lunch at Umami" = Shen Gen Pty Ltd 60.96; Weekday 18.20 (line 12 Apr, note 13 Apr).
  "Ice from Liquorland" as Groceries; drinks for Partner as Alcohol (not Gifts, as "Drink for HKM").
- Lines left open without notes: 11 Apr DiDi 22.04; 12 Apr DiDi 22.45 and 15.66; 13 Apr Bedroom Lounge Bar 26.14 and
  50.55, Agoda 173.66, PAYMENT FROM a friend +40.50; 15 Apr Airbnb 213.00, Linkt 20.07, Prime Video 2.99;
  16 Apr Everyday PAYMENT TO Madison Heights Trust 1,120.00; the Translink lines.
