# ADR-015: Azure Track — Azure Local Instances per Site and Role, Hyperconverged (L1)

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

[ADR-001](ADR-001-platform-strategy-and-workload-placement.md) needs two independent sites. [ADR-007](ADR-007-oracle-cluster-and-licence-boundary.md) needs licence-bounded Oracle clusters. Azure Local host fees are **$10 per physical core per month for L1 (hyperconverged)** and **$20.10 for L2 (external SAN)**. **Azure Hybrid Benefit waives the L1 fee** for Windows Server Datacenter with Software Assurance, which Alder Valley holds.

## Decision

- **Separate Azure Local instances per site and role:**
  - Tier-0/PCI
  - Oracle
  - General (Tier 1/2 + AKS)
  - VDI (Azure Virtual Desktop)

  Each instance is its own failure and update domain. No instance spans sites.
- **Hyperconverged Storage Spaces Direct on validated NVMe nodes (L1).** The DC1 Fibre Channel array is retired, subject to an Oracle batch proof of concept. External SAN (L2) is the fallback for Oracle only.
- **Azure Hybrid Benefit** applied to every host core, so that the host fee is waived. The Datacenter licences also cover unlimited Windows guests.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **One large instance per site with logical separation.** Rejected. It mixes update cadence across Tier 0 and Tier 2, and it blurs the Oracle and PCI boundaries.
2. **External SAN everywhere.** Rejected. It doubles the host fee (L2) and forgoes Azure Hybrid Benefit's waiver on the storage-heavy instances.

## Consequences

- **Positive:** The host fee is near zero on licences already owned, the strongest licensing position of any track.
- **Negative / accepted trade-off:** Eight instances (four roles × two sites) to update and operate. Storage Spaces Direct performance for Oracle must be proven before the array is retired.
