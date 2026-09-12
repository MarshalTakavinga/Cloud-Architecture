# ADR-022: GCP Landing Zone Topology and Resource Hierarchy

**Status:** Approved
**Date:** Step 8 of the Case Study 2 pipeline

## Context

`current-state.md` documents the 2021 AWS account as having no landing zone, no network segmentation, no centralized identity federation, and no documented data-classification review, and `requirements.md` carries that account's governance gap forward as a named risk to be resolved by whatever platform this case study builds. Unlike the AWS track ([ADR-016](ADR-016-aws-landing-zone-and-segmentation.md)), where that account is already a resource of the platform being evaluated, this track's relationship to it is the same as Azure's ([ADR-010](ADR-010-azure-landing-zone-and-segmentation.md)): a genuine cross-cloud migration destination question, not an in-place enrollment. This ADR also has to place the ISO 20022/FedNow gateway (bought per [ADR-002](ADR-002-payment-hub-build-vs-buy.md)) and decide the resource hierarchy the new real-time capability lives in.

## Decision

GCP resources for this case study are organized under a new **Google Cloud Organization**, using **Resource Manager folders and projects** — GCP's own isolation and policy-inheritance primitive — rather than importing either Azure's subscription/VNet shape or AWS's account/Organization shape wholesale. A **Payments folder** contains a dedicated **Payments project** hosting the new real-time services (Cloud Run, Cloud SQL, Pub/Sub, and the Dedicated Interconnect attachment from [ADR-020](ADR-020-gcp-hybrid-connectivity.md)); a separate **Legacy-Digital-Channels folder/project** hosts the 2021 AWS-equivalent workloads once migrated (Cloud Run for the notification service, Pub/Sub or a managed analytics pipeline for the mobile-analytics workload), kept out of the Payments folder entirely. **Organization Policies**, set at the Organization node and inherited down through both folders, enforce the approved region (US regions only, per NFR-6) and deny public-facing PaaS resources; **Security Command Center** provides continuous posture monitoring and threat detection across both folders, and Cloud Audit Logs are centrally aggregated at the Organization level.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A single flat project for all workloads, with no folder-level separation.** Rejected — same reasoning [ADR-010](ADR-010-azure-landing-zone-and-segmentation.md) and [ADR-016](ADR-016-aws-landing-zone-and-segmentation.md) used to reject their equivalent flat topologies: this would put the OCC-scrutinized, real-time payment-processing workload in the same isolation boundary as the lower-sensitivity legacy notification/analytics workload, with no structural separation between them.
2. **A single project with the two workloads separated only by VPC-level segmentation**, mirroring Azure's hub-spoke-in-one-subscription shape rather than using GCP's own folder/project hierarchy. Rejected — GCP's own well-architected guidance treats the project boundary (not the VPC) as the primary IAM, quota, and billing isolation unit; using folders and separate projects is the platform-native answer here, the same way [ADR-016](ADR-016-aws-landing-zone-and-segmentation.md) chose AWS's account boundary over importing Azure's subscription shape.
3. **Migrate the 2021 AWS workloads into the Payments project directly**, rather than a separate Legacy-Digital-Channels project. Rejected — these workloads carry a materially different risk and compliance profile than real-time payment processing under BSA/AML and OCC scrutiny; a separate project lets Organization Policy and Security Command Center scope monitoring appropriately to each workload's actual sensitivity.

## Consequences

- **Positive:** The 2021 AWS account's governance gap is resolved by migrating its workloads into a project that inherits the same Organization Policy guardrails as the Payments project from day one, not treated as a separate, unaddressed problem.
- **Positive:** Organization Policy inheritance means new projects added under either folder automatically pick up the region-restriction and public-resource guardrails without being individually configured — a structural advantage of GCP's resource hierarchy over having to apply policy per-resource.
- **Negative / accepted trade-off:** Standing up a full Organization-level policy hierarchy for what is currently a two-project footprint is more setup effort than a single project would need — accepted deliberately, for the same reason the equivalent setup cost was accepted on the Azure and AWS tracks: the entire point of this initiative includes closing the governance gap the current state carries.
- **Carried to Step 12:** The actual migration of the 2021 AWS-equivalent workloads into the Legacy-Digital-Channels project — including re-platforming from AWS-specific services (the managed notification service, the mobile-analytics pipeline) to their GCP equivalents — is a migration-roadmap action item, not resolved here.
- **Carried to Step 13:** Organization-level logging and Security Command Center tier costs are a sizing detail deferred to Step 13.
