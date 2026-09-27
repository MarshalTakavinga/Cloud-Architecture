# ADR-007: Oracle Runs on Dedicated, Licence-Bounded Clusters

**Status:** Approved
**Date:** Step 5 of the Case Study 6 pipeline

## Context

Core banking runs on Oracle 19c RAC. Oracle is licensed per processor on dedicated clusters: 640 cores across DC1 and DC2 (`current-state.md` §3), or **320 processor licences** at Oracle's 0.5 core factor for current x86 processors. Under Oracle's partitioning policy, most hypervisors count as *soft* partitioning, so every core in a cluster that could run Oracle must be licensed. A platform change could widen that boundary by accident, or narrow it by design. Either way, the effect can be larger than the whole hypervisor saving (`requirements.md` risks).

## Decision

- Oracle runs **only on dedicated physical clusters** in both sites. The Data Guard standby in DC2 is licensed.
- The **licence boundary is the physical cluster**, enforced by the platform:
  - Oracle VMs cannot be placed or live-migrated outside the cluster.
  - Management and automation cannot move them.
  - Storage paths are dedicated.
- The boundary is **visible and audited**. The governance plane tags every Oracle VM and host. A monthly report of the licensed cores is reconciled against the Oracle agreement.
- **A hypervisor change requires an Oracle licensing review before the order.** Each track (Steps 6–9) states its partitioning treatment. A track that relies on *hard* partitioning must name the Oracle-recognized mechanism and its constraints.
- **Consolidation is allowed only with batch evidence.** Moving to fewer, faster cores at refresh can reduce the count, provided the month-end batch holds 30 minutes of headroom (NFR-4). Step 13 tests this.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Run Oracle in the general-purpose clusters with host-affinity rules.** Rejected. Under soft partitioning, the whole cluster would need licensing.
2. **Move core banking's database to another engine.** Rejected. That changes the core package, which is out of scope, and the vendor wouldn't support it.
3. **Oracle's own cloud or engineered systems.** Out of scope for this initiative. It is noted as a later option if Oracle licensing becomes the dominant cost.

## Consequences

- **Positive:** The largest licence risk in any platform change becomes explicit, bounded, and auditable.
- **Negative / accepted trade-off:** Dedicated clusters are less efficient than pooling. The cost is visible in Step 13, and it is small relative to the licence exposure it avoids.
