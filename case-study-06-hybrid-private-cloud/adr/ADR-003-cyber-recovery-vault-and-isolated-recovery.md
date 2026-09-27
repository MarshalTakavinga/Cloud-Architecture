# ADR-003: Cyber Recovery — Immutable Copies, an Isolated Vault, and a Clean-Room Recovery Environment

**Status:** Approved
**Date:** Step 4 of the Case Study 6 pipeline

## Context

The MRA cited backups that were immutable only for Tier 0 (`current-state.md` §4). A DR site doesn't protect against a destructive attack by someone with administrator rights in both sites. NFR-7 requires immutable *and* logically isolated copies of all Tier-0 and Tier-1 data, an isolated recovery environment for Tier 0, and quarterly restore tests. Tier-0 data includes customer NPI, which must stay in bank-controlled facilities.

## Decision

Three layers:
1. **Immutable local copies in each DC** (hardened repositories or object lock) for fast operational restores, covering Tier 0, Tier 1, and Tier 2.
2. **A logically isolated vault:**
   - It has its **own administrative identity domain**, separate from production AD and Entra ID, with MFA and no trust relationship to production.
   - Retention is **time-locked**, and no single administrator can shorten it.
   - Replication into the vault is pull-based, through a controlled path.
   - **Tier-0 vault copies stay on premises.** Tier-1 and Tier-2 vault copies may use **public-cloud object storage in compliance mode**, encrypted with **bank-held keys**.
3. **An isolated recovery environment (clean room) in DC2:** a small cluster with no production network trust, where Tier 0 is restored, scanned, and validated before it is released to production.

The bank also evaluates **Sheltered Harbor** participation (a daily immutable archive of customer account data in the industry-standard format) alongside this design. Weekly tape stays as the last layer.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Extend today's immutable repositories to Tier 1.** Rejected as sufficient: they share the production administrative domain.
2. **Rely on offsite tape.** Rejected as the primary layer, because it means up to a week of data loss and days to restore.
3. **Put every vault copy in public cloud.** Rejected for Tier 0, because of NPI and board policy.

## Consequences

- **Positive:** It answers the MRA's backup finding directly, and it gives a recovery path when *both* sites are compromised.
- **Positive:** The vault design is platform-neutral. Each track only has to show that its backup tooling can feed it.
- **Negative / accepted trade-off:** A second identity domain and a clean-room cluster are more to run. The clean room is kept small (Tier 0 only), and it is exercised in the quarterly restore test.
- **Negative / accepted trade-off:** Backup-tool support differs by hypervisor. A track without mature support for the bank's backup product must name its alternative (Steps 6–9).
