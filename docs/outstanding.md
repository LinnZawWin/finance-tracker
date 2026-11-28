# Outstanding work

Open items. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

Details and reasoning are in [decisions.md](decisions.md). State as of 2026-11-28:
Finance Transactions start on 9 Oct 2026 (notes entered back to that day, plus older notes as listed in item 8); bank lines go back to March.

| # | Item | Who |
|---|---|---|
| 1 | Claude Code GitHub Actions (`.github/workflows/claude.yml`): one run on 15 Nov from an `issues` event succeeded, including "Sign in to Azure"; the `@claude` comment run was skipped. Owner to confirm whether that was the test, or comment `@claude` on an issue and check the run | Owner |
| 3 | Bank Rules: 28 of the 228 open lines fit a rule (2026-11-28; `reconcile.py` lists them in its details file as `rule:`). All are dated 30 Dec 2025 to 2 Apr 2026, before the entered notes: Supermarket Slayer card groceries, AMEX 13 to 20 Mar (DiDi, Uber, BWS, BP, Uber Eats) and Wise bookings 9 Mar to 1 Apr (Airbnb, Trip.com, Booking.com). Owner to decide per group: create Finance Transactions from the rules, or wait for notes | Owner |
| 4 | Import the next Wise export after the Thailand EDC Trip (12 Dec 2026 to 3 Jan 2027) into "Wise 2026". Check that the 28 Oct "Money added" +100 (`TRANSFER-2457903123`, now a Transfer) is recognised, not duplicated. Reminder set for 4 Jan 2027 | Owner, then Claude |
| 7 | Web page: pasted Keep entries get no Category (by design, owner 2026-11-28). The page has no Type Transfer (with Transfer To) and no foreign cash entry (original amount and currency); trip notes go through Claude Code for now | Owner to ask |
| 8 | Notes before 9 Oct 2026 are entered (see decisions-archive for the batches and the rows asked about). New rows wait for their bank lines and are reconciled at the end of the next session: on 2026-11-28 still open were Toll Road Top-up 20 (23 Nov), Parking Fine 129 Kogan, Lottery, Pitbull Concert Ticket, Lunch Burger, Groceries 33.75 and Snacks Cake 2.95 (25 Nov). "Hotel Deposit" (15 Oct note, New Zealand trip) has no bank line, probably a hold that was released, so it was not created | Owner, then Claude |
| 9 | Confirm guessed categories: "Drinks at Lake View Cafe" / "Mountain View Cafe" and "Drink" (Lawson) set as Food and Soft Drinks; "Drinks" at Waterloo Hotel, Funny Funny, Hey Chica as Alcohol. Project Japan Tokyo Trip for "Taxi from Airport to Home" (31 Aug); Payee "Just Vapes" for the 31 Aug vapes (note: OZ Shop). Washing Machine and Compact Freezer (1 Oct) set as Home and Hardware. 6 Aug "Dog Hotel Booking Deposit" as Pets; "Switch Joy-con x3" (6 Aug) and "Outdoor sleeping bags x2" (3 Aug) as Shopping. 11 to 15 Jul: "Mask Wolf" (Shopping), "Card Game" (Gambling), the gloves bought from a friend (Clothing). 4 to 10 Jul: "Intercom App Access" (Rent), project Canberra Ski Trip (not Japan Tokyo Trip as the comment said) on the BNE to Canberra flight. | Owner |
| 11 | Duolingo: the two repayments +28.54 and +57.08 (19 Nov) are linked to "Send Amazon Gift Card ... for Duolingo Family" (22 Oct, Partly Reconciled); a third friend's 28.54, expected into Flex, is still missing. Reminder to chase set for 5 Dec 2026 | Owner, then Claude |
| 12 | The ticket sale row (26 Jun, Amount 0, Partly Reconciled) waits for the earlier ticket resale payment to me: the owner will find that statement and import it | Owner, then Claude |
| 13 | Contract invoices (2026-11-27): the two are Planned Transactions (future estimates). When the flow creates the Transfer FTs of "GST Payment (for 2026-09 income)" (28 Feb 2027) and "Income Tax (for 2026-06 to 2026-09 income)" (24 Nov 2027), add the ATO line and pair it with the bank payment; when the FY2027 assessment arrives, correct the four estimated tax lines and their net Salary FTs ("Contract invoices" in statement-import.md) | Owner, then Claude |
| 14 | The ATO lines before the bank history (GST paid to the Sep to Nov 2025 quarter, Income tax paid FY2025) stay Unmatched until those Flex Saver statements are imported; then `contract_link.py` pairs them as Transfers | Owner, then Claude |
| 15 | Planned Transactions Payee (flow changed 2026-11-28): check that the first Recurring rows (Rent 29 Nov, Health Insurance and W Support 30 Nov) get Payee Madison Heights, AHM and Joint Main from their series | Claude |
| 16 | `reconcile.py` could pair a card payment when the line descriptions name the card ("AMERICAN EXPRESS") even with a same-amount rival on another payee (the 23/24 Nov 1,000 AMEX payment was paired by hand) | Claude |

Done 2026-11-28: the Keep flow's environment variable `lzw_KeepInboxSheetId` and connection reference
`lzw_FinanceTrackerGoogleSheets` were deleted; `statement_compare.py` became compare-only (imports write through
`statement_import.py`); the editable grid item was dropped (owner rarely edits in the app); the ING Savings Booster
+200.36 is paired as a Transfer (ING statements imported); "Income Tax 82,434.30 AMEX" is spread over the contract
payments of that financial year.
