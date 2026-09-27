# ADR-034: Wave Plan — Tier 2, Then Tier 1, Then Tier 0; Oracle Moves by Data Guard Switchover

**Status:** Approved
**Date:** Step 12 of the Case Study 6 pipeline

## Context

About 2,400 VMs must move: about 1,375 Tier-2 (after retiring about 15%), about 520 Tier-1, and about 260 Tier-0. The 44 end-of-support hosts must be empty by **December 2027 (M15)**. Core banking runs on Oracle RAC with a Data Guard standby in DC2. Azure Migrate supports agentless VMware → Azure Local migration.

## Decision

- **Order:** Tier 2 (M8–M13), then Tier 1 (M10–M15), then Tier-0 non-core (M15–M17), then core banking (M17–M19). Each wave passes **gate W**:
  - 10 business days stable
  - DR readiness green
  - source VMs kept off for 30 days
- **Tier-2/1 tooling:** Azure Migrate (agentless, static IPs retained), or Veeam restore to Hyper-V for appliance-adjacent VMs.
- **Oracle moves by Data Guard:**
  1. Build standbys on the new Oracle instances in both sites.
  2. Switch over in a planned window.
  3. Keep the VMware databases as standbys until gate D.

  **Rollback is a switchover back.**
- **Payments appliances** move only with vendor-supplied Hyper-V images and vendor test transactions.
- **Core application servers** are rehosted over a planned weekend after the month-end batch rehearsal on the new Oracle instances.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Move Oracle with VM-level migration.** Rejected. It needs a longer outage, and it gives no clean rollback.
2. **Move by application rather than by tier.** Considered. Waves are grouped by application within each tier, but tier order is kept so that each tier's recovery machinery is proven before the next.

## Consequences

- **Positive:** Core banking's database cutover is a routine Data Guard operation the DBAs already run monthly. Its rollback is the same operation in reverse.
- **Negative / accepted trade-off:** Dual running (VMware and Azure Local) lasts until M20. It is visible in the Step 13 cost model.
