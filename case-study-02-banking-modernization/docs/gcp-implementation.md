# Step 8: GCP Implementation

## Purpose of This Step

[Step 5](logical-design.md) defined nine logical components and their contracts without naming a single platform service. [Steps 6](azure-implementation.md) and [7](aws-implementation.md) answered that question for Azure and AWS. This step answers it independently for GCP: what does each of those nine components actually run on, what does the network, identity, and governance model look like, and what decisions were forced by GCP's own service boundaries — not Azure's or AWS's? Step 9 will ask the same question again for private cloud; none of the four tracks may simply copy another's answers.

Like the Azure track, and unlike AWS's, the 2021 AWS account is a genuine cross-cloud migration destination question on this track, not an in-place enrollment — see [ADR-022](../adr/ADR-022-gcp-landing-zone-and-segmentation.md).

## Service Mapping

| Logical Component (Step 5) | GCP Service | Decision Recorded In |
|---|---|---|
| ISO 20022/FedNow Gateway (bought, ADR-002) | Deployed as a vendor appliance/SaaS integration, connecting into the landing zone via Private Service Connect where the vendor supports it | [ADR-022](../adr/ADR-022-gcp-landing-zone-and-segmentation.md) |
| Hold/Release Adapter | Google Cloud Run | [ADR-017](../adr/ADR-017-gcp-compute-platform.md) |
| Fraud Orchestration Service | Google Cloud Run | [ADR-017](../adr/ADR-017-gcp-compute-platform.md) |
| Ledger-of-Intent Service (application) | Google Cloud Run | [ADR-017](../adr/ADR-017-gcp-compute-platform.md) |
| Ledger-of-Intent Service (data store) | Cloud SQL for PostgreSQL (regional HA) | [ADR-018](../adr/ADR-018-gcp-ledger-of-intent-database.md) |
| Event Bus | Google Cloud Pub/Sub (single topic, ordering keys, four subscriptions) | [ADR-019](../adr/ADR-019-gcp-messaging.md) |
| CDC Connector / Hold-Release path to the mainframe | Dedicated Interconnect (Cloud VPN as backup) | [ADR-020](../adr/ADR-020-gcp-hybrid-connectivity.md) |
| Reconciliation Process (nightly, [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) | A Cloud Run Job, triggered nightly by Cloud Scheduler, in the same Cloud Run environment as the three always-on services | [ADR-017](../adr/ADR-017-gcp-compute-platform.md) |
| Identity (workforce + workload) | Workforce Identity Federation to Palisade's on-prem AD FS; IAM service accounts + Workload Identity for service-to-service auth | [ADR-021](../adr/ADR-021-gcp-identity.md) |
| Landing zone / network segmentation | Resource Manager folders/projects (Payments, Legacy-Digital-Channels), Organization Policy, Security Command Center | [ADR-022](../adr/ADR-022-gcp-landing-zone-and-segmentation.md) |
| Audit/Compliance Log | Cloud SQL for PostgreSQL (append-only table) with archive to Google Cloud Storage (Bucket Lock / WORM) for the 7-year NFR-7 retention | [ADR-018](../adr/ADR-018-gcp-ledger-of-intent-database.md) |
| 2021 AWS account workloads (Replatform, Step 4) | Migrated into the Legacy-Digital-Channels project as Cloud Run + a GCP-native notification/analytics pipeline, under the governance this step establishes | [ADR-022](../adr/ADR-022-gcp-landing-zone-and-segmentation.md) |

## Why Six Decisions, Not Eight

Same reasoning as [Step 6](azure-implementation.md) and [Step 7](aws-implementation.md): this case study's new-build compute layer is small and uniform, so this track needed six ADRs, not Case Study 1's eight. What replaces the difference is the same hybrid-connectivity decision every hyperscaler track in this case study needs ([ADR-020](../adr/ADR-020-gcp-hybrid-connectivity.md)) — Solstice never needed one — plus a landing-zone decision built on GCP's own resource hierarchy rather than either other track's shape.

## Network and Security Summary

- **Segmentation:** Resource Manager folders separate the **Payments project** (Cloud Run, Cloud SQL, Pub/Sub, and the Dedicated Interconnect attachment) from the **Legacy-Digital-Channels project** hosting the migrated 2021 AWS-equivalent workloads ([ADR-022](../adr/ADR-022-gcp-landing-zone-and-segmentation.md)). Only the Payments project connects to Palisade's data center.
- **Private connectivity to PaaS:** Cloud SQL is reached only via private IP within the Payments project's VPC; Pub/Sub is reached over Private Google Access / VPC Service Controls, so nothing in this architecture's payment path crosses the public internet.
- **Identity:** Human access federates through Workforce Identity Federation directly to Palisade's on-prem AD FS (no directory sync, no replicated identity data); every service-to-service call (Cloud Run → Cloud SQL, Cloud Run → Pub/Sub) uses a dedicated IAM service account via Workload Identity, with no downloaded key file anywhere.
- **Governance guardrails:** Organization Policy, set once at the Organization node and inherited by both folders, enforces the approved region (US regions only, satisfying NFR-6) and denies public-facing PaaS resources; Security Command Center provides continuous posture monitoring and threat detection across both projects; Cloud Audit Logs aggregate centrally at the Organization level.

## Observability

Cloud Run service and job logs, Cloud SQL logs, and Pub/Sub metrics all publish to Cloud Logging and Cloud Monitoring, scoped by project but viewable in a single Log Analytics-backed view across the Organization. As with Steps 6 and 7, this is deliberate: an OCC examiner asking "show me everything that happened to payment X" should not require correlating systems across project boundaries, even though those boundaries exist for isolation.

## Known Deferred Items

Consistent with this case study's convention: Terraform modules for this landing zone and its workloads are not yet built (`terraform/` remains empty pending the Step 10 platform decision — and per this portfolio's own established practice, Terraform would be this track's primary IaC tool if selected, since Google's own Deployment Manager has been de-emphasized); diagrams for this track are not yet drawn; detailed sizing (Cloud Run instance counts, Cloud SQL tier, Pub/Sub throughput) is deferred to Step 13's cost analysis; the specific CICS transaction for the [ADR-001](../adr/ADR-001-mainframe-integration-approach.md) hold/release call remains an outstanding mainframe-team decision, unresolved here exactly as in Steps 6 and 7. As on the Azure track, the actual re-platforming of the 2021 AWS-equivalent workloads onto GCP-native services is a Step 12 migration-roadmap action item, not performed as part of this architecture step.
