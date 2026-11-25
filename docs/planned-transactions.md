# Planned Transactions and flows

The scheduled flow and the Planned / Recurring Transaction rules. Part of the project rules: read with [../CLAUDE.md](../CLAUDE.md).

## Flows

| Flow | Schedule | State | Script |
|---|---|---|---|
| Scheduled: Create Finance Transactions from Planned Transactions | Daily 6 AM Brisbane | **On** since 2026-11-19. Tested 2026-11-20 (manual runs: one Succeeded, one Cancelled with nothing due) | `build_recurring_flow.py` |

It uses the connection reference `lzw_FinanceTrackerDataverse` (bound). The build scripts update a flow's
definition only while it is off. `build_recurring_flow.py --update-on` turns the flow off, updates it and
turns it back on. Name new flows `<Table>: <Flow Name>`
(`Scheduled:` for recurrence).

To run a flow by hand, call the Power Automate API with an Azure CLI token for
`https://service.flow.microsoft.com/`: `POST .../environments/<env id>/flows/<workflowid>/triggers/<trigger>/run`
(api-version 2016-11-01). Take the environment ID from the `environments` list in that API, matching
`instanceUrl`: the PAC profile and FlowAgent on this machine are signed in to another account.

## Planned Transactions

- The scheduled flow takes open or scheduled appointments with Processed = No and Start before tomorrow
  (Brisbane) and creates a Finance Transaction for each: Description and Payee = Subject, Date = Start,
  Type = Income if Amount < 0 else Expense, Estimated Amount = abs(Amount), Share Type = Mine, Source =
  Recurring, Source Row ID = appointment ID, Paid From and Category from the appointment or else its
  series, Needs Details = Yes when Paid
  From is empty or Payment Type = Estimated, Notes = "Created from Planned Transaction. Payment Type: <x>"
  plus the appointment's Description on a new line, currency = the appointment's (AUD if none). Then it
  sets Processed = Yes. It skips an appointment that already has a Recurring transaction with that Source
  Row ID.
- The appointment **Description** holds the payee or how to pay ("Manual - ..." = paid by hand). Every
  series has a Paid From (the account the money leaves), including Manual ones.
- **Current series** (owner's list, applied 2026-11-19; all AUD; amounts positive = expense):

| Series | Amount | Pattern | Paid From | Payment Type | Finance Category |
|---|---|---|---|---|---|
| Salary | -18,333.33 | Monthly, 5th | Everyday | Auto | Salary and Contract Income |
| Rent | 560.00 | Weekly, Sunday | Flex | Auto | Rent and Housing |
| Health Insurance | 81.50 | Weekly, Monday | Flex | Auto | Insurance |
| Broadband | 71.95 | Monthly, 20th | AMEX | Auto | Utilities |
| Utility (Electricity/Gas) | 140.55 | Monthly, 24th (from 24 Dec 2026) | Flex | Estimated | Utilities |
| YouTube Premium | 6.60 | Monthly, 25th | Flex | Auto | Subscriptions |
| Claude Pro | 34.00 | Monthly, 4th | AMEX | Auto | Subscriptions |
| Crunchyroll | 3.33 | Monthly, 21st | Flex | Manual | Subscriptions |
| Water Use | 130.00 | Every 3 months, 1st (from 1 Jan 2027) | Flex | Estimated | Utilities |
| Spotify Premium | 34.23 | Every 6 months, 28th (Jan, Jul) | Flex | Manual | Subscriptions |
| Mobile | 154.00 | Yearly, 12 Aug | AMEX | Manual | Utilities |
| Super Duolingo | 28.54 | Yearly, 12 Oct | Flex | Manual | Subscriptions |
| Car Servicing | 400.00 | Yearly, 1 Dec | AMEX | Manual | Car Maintenance |
| Car Insurance and Roadside Assist | 602.42 | Yearly, 11 Mar | AMEX | Manual | Insurance |
| Car Registration | 1,049.72 | Yearly, 28 Feb | AMEX | Manual | Transport |

  These 15 are the only series with an Amount. All other old series (24 open, 59 cancelled) were deleted on
  2026-11-19 at the owner's request. 2 cancelled series without an Amount are calendar items: leave them.
- **Bills whose amount or date varies:**
  - Regular (monthly, for example electricity): a series on the typical debit day with Payment Type =
    Estimated and the average of recent bills. When a bill arrives, put its exact amount and due date in a
    one-off appointment and move the series start past it, or edit the Finance Transaction if it already
    exists. "Utility (Electricity/Gas)" is set up this way: monthly on the 24th from 24 Dec 2026, $140.55
    (average of May to Oct 2026), plus a one-off $122.22 on 24 Nov 2026 (Payment Type Auto).
  - Irregular (for example water, about quarterly): no series. Create a one-off appointment from each invoice
    (exact amount, due date, Payment Type Manual).
  - Changing a series' recurrence pattern deletes and regenerates its open instances (tested). Editing
    a single instance has not been tested: a later series edit may overwrite it.
- Platform behaviour, tested:
  - Updating a series rewrites the same columns on **all its open instances**, past and future. Completed
    and cancelled appointments are read-only and keep their values.
  - Amount, Payment Type, Description and currency are copied from a series to its instances (on create
    and on update). **Paid From and Finance Category are not** (tested 2026-11-19: empty on every instance),
    so the flow reads them from the series (`seriesid`) when the instance has none. Set them on the series.
  - Keep Processed = No on series.
  - Deleting every instance of a series deletes the series too.
- Past planned transactions (before 2026-11-19) were deleted. 20 past appointments without an Amount are
  real meetings: leave them.
