# ADR-027: OpenStack Track — Certified Hyper-V Island, Ceph RBD Mirroring, and a Bank-Built Orchestrator

**Status:** Approved (OpenStack track, subject to the Step 10 platform selection)
**Date:** Step 9 of the Case Study 6 pipeline

## Context

OpenStack runs on KVM, which the core banking vendor does not certify, so the same constraint applies as on the GCP track ([ADR-022](ADR-022-gcp-certified-island.md)). OpenStack has no packaged DR orchestration between regions. Ceph offers **RBD mirroring** (snapshot-based, on a schedule) between clusters.

## Decision

- **A certified island:** core banking and Oracle run on **Windows Server 2025 Hyper-V failover clusters** in each site (about 16 hosts per site), with Data Guard and Hyper-V Replica. This is the same pattern as [ADR-022](ADR-022-gcp-certified-island.md).
- **Stateful Tier-0/1 volumes:** Ceph RBD mirroring every **5 minutes**, DC1→DC2.
- **Recovery:** a bank-built orchestrator (Terraform + Ansible) re-creates instances in the DC2 region on the promoted volumes and runs groups G0–G6, spanning OpenStack and the island.
- **Readiness:** the daily job reads the mirroring state from Ceph ([ADR-006](ADR-006-recovery-plan-model-and-readiness.md)).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Trilio restore as the DR mechanism.** Rejected for Tier 0. Restores at scale take too long for the RTO.
2. **A third-party OpenStack DR product.** Considered. It adds a vendor for a function the Git-plan model already requires the bank to own.

## Consequences

- **Positive:** Plans stay in Git and are portable.
- **Negative / accepted trade-off:** Two platforms and two recovery paths, and the recovery machinery is bank code, like the GCP and Azure tracks.
