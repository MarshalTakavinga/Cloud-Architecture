# ADR-009: VCF Track — One VCF 9.1 Instance per Site, Domains by Zone, vSAN ESA

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

[ADR-001](ADR-001-platform-strategy-and-workload-placement.md) needs one private cloud in two **independent** sites. [ADR-007](ADR-007-oracle-cluster-and-licence-boundary.md) needs licence-bounded Oracle clusters. The December 2027 refresh covers 44 hosts and the DC1 Fibre Channel array. VCF 9.1 (released 3 September 2026) includes vSphere, vSAN, NSX, VKS, VCF Operations, VCF Automation, and HCX in the core subscription.

## Decision

- **One VCF instance per site**, each with its own management domain, so that DC2 stays a separate failure and administrative domain. One VCF Operations fleet view spans both instances.
- **Workload domains per site:**
  - **Tier-0 + PCI** (Z0, Z0-PCI, Z0-DMZ)
  - **Oracle** (dedicated, licence boundary)
  - **General** (Z1, Z2)
  - **VDI**
- **vSAN Express Storage Architecture** on refreshed NVMe ReadyNodes. **The DC1 Fibre Channel array is retired rather than refreshed**, subject to an Oracle batch proof of concept (p99 write ≤ 2 ms at the month-end peak, 30-minute batch headroom).
- **In-place upgrade path:** vSphere 8 moves to VCF 9.1 on existing hosts. Workloads move to refreshed hosts with vMotion and HCX, with no conversion.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **One VCF instance stretched across both sites.** Rejected. It is one failure domain ([ADR-002](ADR-002-recovery-as-code-active-standby.md)).
2. **Refresh the Fibre Channel array like for like.** Rejected as the default. It costs a large share of the ~$4.2M refresh for storage that vSAN ESA, already licensed within the entitlement, can provide. Kept as the fallback if the Oracle proof of concept fails.
3. **A single general-purpose domain with resource pools.** Rejected. It weakens the Oracle licence boundary and the PCI scope boundary.

## Consequences

- **Positive:** The lowest migration effort of any track, with no workload conversion.
- **Positive:** Retiring the array reduces refresh capital.
- **Negative / accepted trade-off:** vSAN capacity beyond the included entitlement is an add-on, which grows with data (about 8% a year).
- **Negative / accepted trade-off:** More domains mean more lifecycle work. It is managed through VCF Operations fleet lifecycle with an offline depot.
