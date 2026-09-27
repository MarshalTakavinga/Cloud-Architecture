# ADR-023: GCP Track — GitOps Reapply, Array Replication, and Kasten, Orchestrated by Bank Code

**Status:** Approved (GCP track, subject to the Step 10 platform selection)
**Date:** Step 8 of the Case Study 6 pipeline

## Context

GDC has no first-party VM replication between clusters. VM definitions are Kubernetes objects, so they can be re-applied from Git. Stateful VM disks can be protected by **storage-array replication through the CSI vendor**, or by **Veeam Kasten** (KubeVirt backup). The island uses Hyper-V Replica + Data Guard ([ADR-022](ADR-022-gcp-certified-island.md)).

## Decision

- **Stateless VMs:** recovered by re-applying their Git manifests to the DC2 clusters from pipeline images, with no replication.
- **Stateful Tier-0 and Tier-1 VMs:** **array replication** DC1→DC2 (asynchronous, ≤ 5 minutes), with replica promotion scripted into the plan.
- **Backup and vault:** Kasten for GDC VMs and Veeam B&R for the island, both into the same vault ([ADR-003](ADR-003-cyber-recovery-vault-and-isolated-recovery.md)).
- **Orchestrator:** bank-built, running from DC2. It executes the Git plans (groups G0–G6) across the GDC clusters and the island.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Kasten backup/restore as the Tier-0 DR mechanism.** Rejected. The restore time is too long for a 4-hour RTO at scale.
2. **A stretched GDC cluster.** Rejected ([ADR-002](ADR-002-recovery-as-code-active-standby.md)).

## Consequences

- **Positive:** "Recovery = apply" is natural here, and the plans are portable.
- **Negative / accepted trade-off:** **The most bank-built recovery machinery of any track**: VMs, array promotion, island, and two backup products.
