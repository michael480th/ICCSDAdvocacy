# Iowa DOM data (state, unaudited)

Extracted from the Iowa Department of Management **Unspent Authorized Budget Report**
workbook (hidden `data_UAB` and `CashReserveLevyHistory` tabs). These are **state-computed,
unaudited** figures derived from the Aid & Levy / certified data — they exist independent of
each district's audit, so coverage includes districts whose audits are missing (e.g., Iowa
City FY2024–FY2025).

District codes verified against the workbook's UAB_List (lookalikes excluded: Louisa-Muscatine,
West Burlington, Western Dubuque are NOT in our 15).

## `unspent-authorized-budget.csv`
Per district × FY2020–FY2025. **UAB is Iowa's #1 financial-health indicator** (framework metric A2).
- `max_authorized_budget` — Maximum Authorized Budget (spending-authority ceiling)
- `unspent_authorized_budget` — UAB ("unspent balance"); **negative = unlawful, triggers SBRC review**
- `uab_pct_of_max` — UAB ÷ max authorized budget (the comparable ratio)

## `cash-reserve-levy.csv`
Per district × FY2020–FY2025. The property-tax "lever" districts use to bolster cash/solvency
(framework metric A9). A district leaning on a large/rising cash reserve levy is propping up its
solvency through taxation rather than operations.

Source file: DOM "Unspent Authorized Budget Report" (dom.iowa.gov school resources).
