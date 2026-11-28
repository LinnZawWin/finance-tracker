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

- System view **Current Week Pending Transactions** (Start Time this week, Status Open; created 2026-11-25 by `build_week_view.py`, replaces a personal view that listed the deleted Financial Account column).
- The scheduled flow takes open or scheduled appointments with Start before tomorrow
  (Brisbane) and creates a Finance Transaction for each: Description = Subject, Payee = the appointment's Payee,
  else its series' Payee, else the Subject (2026-11-28), Date = Start,
  Type = Transfer when the appointment (or its series) has **Transfer To** (column added 2026-11-27, FT Transfer To
  set from it), else Income if Amount < 0 else Expense, Estimated Amount = abs(Amount), Share Type = Mine, Source =
  Recurring, Source Row ID = appointment ID, Paid From and Category from the appointment or else its
  series, Needs Details = Yes when Paid
  From is empty or Payment Type = Estimated, Notes = "Created from Planned Transaction. Payment Type: <x>"
  plus the appointment's Description on a new line, currency = the appointment's (AUD if none). Then it
  sets the appointment to Completed (Status = Completed, status reason Completed). It skips an appointment that already has a Recurring transaction with that Source
  Row ID.
- The appointment **Description** holds the payee or how to pay ("Manual - ..." = paid by hand). Every
  series has a Paid From (the account the money leaves), including Manual ones.
- **Current series** (owner's list, applied 2026-11-19; all AUD; amounts positive = expense):

| Series | Amount | Pattern | Paid From | Payment Type | Finance Category |
|---|---|---|---|---|---|
| Salary | -12,557.33 (net pay of the Nov 2026 payslip; gross 18,333.33 until 2026-11-27) | Monthly, 25th (payday; the 5th until 2026-11-28, first instance 25 Dec 2026) | Everyday | Auto | Salary and Contract Income |
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
| W Support | 1,000.00 | Weekly, Monday (from 23 Nov 2026) | Flex | Auto | Support Payments |

  These 16 are the only series with an Amount. All other old series (24 open, 59 cancelled) were deleted on
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
  - Amount, Payment Type, Payee, Paid From, Finance Category, Transfer To, Description and currency are copied
    from a series to its instances (on create and on update). A custom column is copied only when the series column's `LinkedAttributeId` points to the
    instance column ([Microsoft Learn](https://learn.microsoft.com/power-apps/developer/data-platform/link-custom-attributes-recurring-master-appointment-entities));
    Amount and Payment Type were linked by the older solution; Payee, Paid From, Finance Category and Transfer To by
    `build_appointments.py` (2026-11-28; before that the lookups were empty on every instance). Set them on the
    series. The flow still falls back to the series (`seriesid`) when an instance has none.
  - Deleting every instance of a series deletes the series too.
- **Creating a series by API:** set `utcconversiontimezonecode` = 260 (as the other series) and use the same start
  style as Health Insurance (`starttime` Monday 14:00Z, `patternstartdate` 2026-11-18T14:00Z, mask 2 = Monday).
  Without the time zone code the instances land a day late (Tuesday Brisbane); changing it afterwards does not
  regenerate them, so delete and recreate. Lookup binds are `lzw_PaidFrom_RecurringAppointmentMaster@odata.bind`
  and `lzw_FinanceCategory_RecurringAppointmentMaster@odata.bind`. A create can run twice through the proxy:
  check for a duplicate series afterwards.
- **Payee** (column `lzw_payee`, 2026-11-28): set it on the series to the payee the bank line names; the platform
  copies it to the open instances (all open instances were filled on 2026-11-28), and the flow also falls back to the
  series. Set on: Rent = Madison
  Heights, Health Insurance = AHM, W Support = Joint Main, Broadband = Rush, Utility (Electricity/Gas) = Altogether,
  YouTube Premium = the person the family share is paid to. The others fall back to the Subject.
- **Salary**: the flow's Salary FT (Paid From Everyday, the series' net) is reused by `payslip_link.py` when the
  payslip is linked: it moves to the employer account and takes the payslip's net (a 25th on a weekend is paid the
  Friday before; the script looks 1 day before to 2 days after the payday).
- **Leave without pay** (owner, 2026-11-28): when a "Leave Without Pay" event is added to the Google Calendar "Leave"
  ("Leave check" in `statement-import.md`), set that month's Salary instance to the estimated net: gross = (176 - 8 x
  its weekdays) x 104.1667, less PAYG from an earlier payslip with the same gross, else the ATO monthly withholding
  ([tax withheld calculator](https://www.ato.gov.au/calculators-and-tools/tax-withheld-calculator)). Put the working in
  its Description after "Delta Insights - " (the flow copies the Description to the FT Notes). An edit to the series
  rewrites its open instances, so redo these afterwards. Set: 25 Dec 2026 = -11,231.34 (24 hours, 16 to 18 Dec; gross
  15,833.34 and PAYG 4,602.00 as on the Oct 2026 payslip).
- **Owed to the ATO** (one-off, 2026-11-27, `contract_link.py`): "GST Payment (for 2026-09 income)" 1,750.00 on
  28 Feb 2027 (Manual, Flex Saver) and "Income Tax (for 2026-06 to 2026-09 income)" 33,575.00 on 24 Nov 2027
  (Estimated, no Paid From; correct it when the assessment arrives). Both have Transfer To Delta Insights and no
  Category, so the flow creates Transfer FTs ("Contract invoices" in `statement-import.md` says how to pair them).
- No series for Prime Video (unsubscribed) or GST activity statements (no longer a contractor): owner, 2026-11-26.
- Past planned transactions (before 2026-11-19) were deleted. 20 past appointments without an Amount are
  real meetings: leave them.
