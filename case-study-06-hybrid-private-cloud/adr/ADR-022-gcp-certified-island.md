# ADR-022: GCP Track — A Certified Island on Windows Server Hyper-V for Core Banking and Oracle

**Status:** Approved (GCP track, subject to the Step 10 platform selection)
**Date:** Step 8 of the Case Study 6 pipeline

## Context

VM Runtime on GDC is KubeVirt, running on KVM. The core banking vendor certifies **vSphere and Hyper-V only** (`requirements.md`). [ADR-001](ADR-001-platform-strategy-and-workload-placement.md) allows a **certified island** where the primary platform isn't certified, with its cost carried by the track.

## Decision

- **Core banking (application tier + Oracle RAC) runs on Windows Server 2025 Hyper-V failover clusters** in each site, about 16 hosts per site. It is licensed with the bank's existing Windows Server Datacenter + SA.
- **Oracle** stays on its dedicated clusters on the island (soft partitioning, 320 processor licences, [ADR-007](ADR-007-oracle-cluster-and-licence-boundary.md)).
- **Recovery:** Data Guard + Hyper-V Replica, run by the same Git-driven orchestrator as the GDC side.
- **Governance:** Arc-enabled servers in the guests. The island is outside the GDC fleet.
- **Exit from the island** happens only when the core vendor certifies KVM. At that point the island is migrated into VM Runtime.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A vSphere island.** Rejected. It keeps a Broadcom subscription and the licence-stop dependency ([ADR-012](ADR-012-vcf-control-plane-and-governance.md)).
2. **An Azure Local island.** Rejected. It adds a second cloud-managed platform to a Google track.
3. **Run core banking on VM Runtime unsupported.** Rejected. An uncertified Tier-0 platform is unacceptable to the vendor and to examiners.

## Consequences

- **Positive:** Core banking stays certified at no new licence cost.
- **Negative / accepted trade-off:** **Two platforms, two recovery paths, and two backup products** for a 24-person team. This is the main driver-5 and NFR-12 penalty of the track.
