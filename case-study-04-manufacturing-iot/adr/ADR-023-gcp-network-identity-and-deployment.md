# ADR-023: GCP Network Connectivity, Identity, and Pull-Based Edge Deployment

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

The [ADR-003](ADR-003-ot-segmentation-reference-architecture.md) rules and Step 5's deployment contract apply, as on the other tracks. GCP has a region in **Columbus, Ohio (us-east5)**, the same city as Kestrel's data center, MPLS hub, and SAP ECC. GDC clusters keep running Config Sync while disconnected if their Git source is reachable. Google documents that MCe authenticates to Pub/Sub with a service-account key.

## Decision

**Network**
- **US and Mexico plants:** MPLS to Columbus, then **Cloud HA VPN** to **us-east5**, a metro-local hop.
- **German plants:** HA VPN per plant to **europe-west3**.
- **Private Service Connect** endpoints for Google APIs, and **VPC Service Controls** perimeters, one per region, around the data projects.
- **Organization Policy:** resource-location constraints plus Pub/Sub message storage policies (NFR-10).
- **Plant DMZ:** an HTTPS forward proxy with an allowlist, a **Git mirror**, and a **Harbor registry mirror** that syncs from Artifact Registry. Level 3 reaches only these.

**Identity**
- **Humans:** **Workforce Identity Federation with Entra ID**. Plant break-glass accounts exist for disconnected operation ([ADR-018](ADR-018-gcp-edge-platform.md)).
- **Workloads:** GDC workloads use **fleet Workload Identity**. There are no service-account keys at plants, because MCe does not publish directly to the cloud ([ADR-019](ADR-019-gcp-store-and-forward-implementation.md)).
- **Plant-local mTLS** uses a plant-local CA.

**Deployment (P9)**
- **Configuration:** **Config Sync** on each cluster *pulls* from the plant's DMZ Git mirror.
- **Images and models:** images and ONNX model containers are built into Artifact Registry and signed with Sigstore (cosign). The DMZ Harbor mirror pulls only the repositories that plant needs. The Sigstore policy controller rejects unsigned images at admission.
- **Model activation:** the Kestrel activation controller enforces shadow → plant approval → active. Rollback is a Git revert.
- **MCe:** MCe configuration (drivers, tag mappings, templates) is managed through **Litmus Edge Manager**, which is a second deployment channel that must follow the same approval discipline.

**Landing zone**
- A Resource Manager folder per region (US, EU), with separate projects for data, analytics, genealogy, and the network host.
- As on the other tracks, the 2024 SageMaker PoC account is handled outside this platform: its model code is extracted, its data purged, and the AWS account closed.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Dedicated or Partner Interconnect.** Rejected as disproportionate to about 60 Mbps, as on the other tracks.
2. **MCe publishing directly to Pub/Sub with a service-account key (Google's documented default).** Rejected. It would put a long-lived credential in every plant and bypass the lane semantics.
3. **Connect gateway for operator access to plant clusters.** Retained for connected operation, but not relied on, because it is unavailable during disconnection.

## Consequences

- **Positive:** us-east5 in Columbus gives the shortest US path of any track, which is a small but real advantage for SAP integration and incident troubleshooting.
- **Positive:** VPC Service Controls provide the strongest API-layer data-residency boundary of the three tracks.
- **Negative / accepted trade-off:** Each plant DMZ hosts three services (the proxy, the Git mirror, and the Harbor mirror), the heaviest DMZ footprint of the three tracks.
- **Negative / accepted trade-off:** There are two deployment channels at the edge (Config Sync for Kestrel workloads and Litmus Edge Manager for MCe), so change control must cover both.
