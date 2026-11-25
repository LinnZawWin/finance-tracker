# Reconciliation

Matching bank lines to Finance Transactions, cash lines, split bills, refunds and claims. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

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
**A repayment netted against what I owe that friend** (1 Aug: a friend owed 24.40 for a lunch and I owed them 20.88 for
badminton they paid, so they sent 3.52): the badminton is its own transaction, and the 3.52 line gets two matches
by hand, +24.40 on the bill and -20.88 on the badminton (`split_match.py` cannot: it allows only the line's sign).
**Poker** with friends: one Gambling transaction per settlement line, Payee the friend, Income when they paid me.
**A charge on my card spent by Partner and paid back in full** (PayID credit on AMEX): no Finance Transaction.
The charge and the credit are paired like a transfer (both Status Transfer, each other's Transfer Counterpart,
set by hand: same account, so `reconcile.py` does not pair them). 9 and 11 Jul 2026, owner's choice 2026-11-24.
An AMEX Travel Credit is a refund of the booking it paid for (12 Aug Finnair flight: +450 linked, Amount 1,608.60 - 450).
A refund on another account than the charge is linked too (7 Oct ALDI container refund on Everyday against a
1 Sep grocery paid with Supermarket Slayer card 7850). Paid back in cash: no bank line, so use the Foreign cash rule (Transfer to the cash
account). **Bill paid in cash, repaid by bank transfer**: link the repayments; the difference stays at the
cash paid (it has no bank line), so the transaction stays Partly Reconciled until its cash line is generated (see "Cash lines"), then it is 0.
**Work expense claims**: a purchase noted "TO CLAIM" is paid by me and repaid by the employer
("ANZ INTERNET BANKING TRANSFER EXPENSE CLAIMS ..." on Everyday). Link the claim credit to those transactions
the same way, split between them by their amounts (`line=amount`), so each one's Actual Amount is 0.
The Reconciliation Difference then equals the Amount, so `split_match.py` sets Partly Reconciled: once every
line of a claimed transaction is linked, set it to Reconciled by hand. **Half claims and pending claims** (owner, 2026-11-25): a flight claimed half has the full Amount; the claim credit is
split onto it with half the amount, so its Actual Amount is the half I paid, and it is set Reconciled by hand. A claim
not yet paid ("pending claim, keep it open"): link the charge only and set the transaction to Partly Reconciled by hand
(Notes "TO CLAIM ... pending"), so it stays open until the claim line arrives. 25 May Delta Insights claim 471.50 =
262.50 (29 Apr Melbourne flight for Partner) + 131.00 (7 Apr flight for Partner) + 78.00 (7 Apr own flight, in full).
A claim paid at another rate than the
platform's leaves a few cents of Actual Amount on the foreign rows (6 Nov claim: 0.41 on the two NZD meals).

Bank Rules are for statement lines that have no Keep note behind them (rent, salary, interest, tolls, card
fees, supermarkets). When such a line stays unmatched, the first rule whose Match Text fits its description
supplies the payee, category and share type for a new Finance Transaction. A line that matches a Keep note
never needs a rule: the note's own category wins.
