# ADR-028: Teradata Contract Decision and Exit Sequencing — Notice + One-Year Bridge, Exit by Domain

**Status:** Approved (decision taken at M3, after gate G0)
**Date:** Step 11 of the Case Study 5 pipeline

## Context

The Teradata dates are fixed:
- **notice by 31 December 2026**
- **term ends 30 June 2027**
- a **one-year bridge at +25%** is available to 30 June 2028

A multi-year renewal would cost about $3.9M a year plus a ~$6M appliance refresh.

The workload is about 1,800 procedures and macros, BTEQ scripts, the targets of about 2,400 Informatica jobs, and about 4,200 reports that survive rationalization. [ADR-005](ADR-005-teradata-migration-approach.md) requires a dual-run per domain, and NFR-8 needs the reserving close proven over parallel quarterly closes. Gate G0 ([ADR-027](ADR-027-cloud-platform-selection.md)) delivers a translation proof of concept by M3.

## Decision

At **M3**, with the G0 results in hand:

1. **Give notice of non-renewal.** No multi-year renewal, and no appliance refresh.
2. **Sign the one-year bridge to 30 June 2028**, negotiating:
   - extended hardware support for the current appliance
   - the right to **reduce licensed capacity** as domains are frozen
3. **Exit by domain:**
   - claims: M4–M10
   - policy and billing: M8–M13
   - reserving and actuarial: M11–M17, with two parallel quarterly closes
   - regulatory: M14–M18

   **Teradata freeze at M18 and switch-off at M20**, one month inside the bridge.
4. **Stop all new Teradata development at M3.**

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Exit by 30 June 2027 with no bridge.** That leaves about six months after G0 to translate, reconcile, and sign off every domain, including a reserving domain that needs two parallel quarterly closes. Rejected as not credible. Missing the date would mean an emergency renewal on the vendor's terms.
2. **A multi-year renewal "to be safe".** It locks in the platform driver 3 exists to leave, plus a $6M refresh. Rejected.
3. **Decide on the bridge later, at M8–M9.** Rejected, because the notice date forces the decision at M3. Waiting would only mean negotiating the bridge with less leverage.

## Consequences

- **Positive:** The exit is paced by reconciliation evidence rather than by the contract. The bridge is bought as insurance for a migration already under way, not as a renewal.
- **Negative / accepted trade-off:** **The bridge premium** (about $3.9M × 1.25 for one year) plus **dual-running costs** are the price of a safe exit. Both are modeled in Step 12.
- **Negative / accepted trade-off:** The ageing appliance runs for another year. Extended hardware support is a negotiated term, and hardware failure during the bridge is a named risk. Frozen domains reduce the blast radius over time.
- **Review trigger:** if the G0 translation proof of concept shows more than 90% automated translation, **and** the claims-domain dual-run passes gate D by M8, Harborline can revisit whether to seek early termination under the bridge. That is not assumed.

## Addendum — Step 12 Cost and Schedule Check

[`docs/cost-and-risk-analysis.md`](../docs/cost-and-risk-analysis.md) modeled the exit in [`finance/TCO-Analysis.xlsx`](../finance/TCO-Analysis.xlsx):

- **The bridge year costs about $5.1M** (licence at +25% plus extended hardware support). About **$1.2M of that is premium** over the current rate.
- **The five-year data-platform saving is about $6.9M**, with payback in Year 4. It depends heavily on avoiding the ~$6M appliance refresh.
- **A 3-month slip past the bridge costs about $1.6M.** No contract term currently covers it, and the plan has only one month of margin.

**Added negotiating term:** the bridge must include a **month-to-month extension option at the bridge rate** (for example, up to six months), so that a late reserving close cannot force an emergency renewal. Status is unchanged: Approved.
