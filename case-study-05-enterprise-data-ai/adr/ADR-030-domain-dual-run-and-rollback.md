# ADR-030: Domain Dual-Run, Cutover, and Rollback

**Status:** Approved
**Date:** Step 11 of the Case Study 5 pipeline

## Context

[ADR-005](ADR-005-teradata-migration-approach.md) sets the migration approach (dual-run by domain with automated reconciliation). [ADR-028](ADR-028-teradata-contract-and-exit-sequencing.md) sets the sequence and the M18 freeze. Warehouse outputs feed regulatory filings and the reserving close, so a wrong number is a regulatory and financial-statement issue, not just a data bug.

## Decision

For each domain:

1. **Translate and deploy** to the lakehouse (Dataform) while Teradata remains the source of truth.
2. **Dual-run.** Both platforms process the same inputs daily. The migration reconciler (D5) compares row counts, control totals, and the domain's **critical reports**, a list agreed with the business owner.
3. **Gate D.** Twenty consecutive business days of clean reconciliation, then business-owner sign-off. **Reserving** instead requires **two consecutive quarterly closes** reconciled in parallel (Q3 2027 in M13 and Q4 2027 in M16).
4. **Cutover.** The domain's consumers are repointed to the lakehouse (Tableau data sources, notebooks, exports), and the Teradata objects for that domain are **frozen** (read-only).
5. **Rollback, until the global freeze at M18:** consumers are repointed back to the frozen Teradata objects, which are refreshed from the last clean reconciliation point. This is possible because Teradata keeps running under the bridge.
6. **After M18:** there is no rollback to Teradata. A defect is fixed forward on the lakehouse. That is why gate D is strict.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cut over without dual-run, relying on pre-migration testing.** Rejected. With about 1,800 procedures carrying 12 years of accumulated logic, only production-equivalent parallel running exposes the edge cases.
2. **Dual-run every domain until the end.** Rejected. Running two full platforms for all domains simultaneously is the most expensive option, and it delays the capacity reductions ADR-028 negotiates.

## Consequences

- **Positive:** Every domain's exit is independently evidenced, and the reserving evidence spans real quarter closes rather than synthetic tests.
- **Negative / accepted trade-off:** Dual-run doubles compute for each domain while it runs. This is visible as its own FinOps line (a dedicated migration reservation, [ADR-026](ADR-026-gcp-network-identity-finops.md)) and modeled in Step 12.
- **Negative / accepted trade-off:** After M18, the organization depends entirely on the new platform. The Step 12 risk register carries this, and it is why the regulatory domain is signed off before the freeze.
