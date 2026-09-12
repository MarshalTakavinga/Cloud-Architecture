# Step 7: AWS Implementation

## Purpose of This Step

[Step 5](logical-design.md) defined nine logical components and their contracts without naming a single platform service. [Step 6](azure-implementation.md) answered that question for Azure. This step answers it independently for AWS: what does each of those nine components actually run on, what does the network, identity, and governance model look like, and what decisions were forced by AWS's own service boundaries — not Azure's? Steps 8–9 will ask the same questions again for GCP and private cloud; none of those tracks may simply copy this one's answers, and where this track's answer differs from Azure's for a genuinely platform-native reason, that is the entire point of running four independent tracks.

This track carries one wrinkle none of the other three will have: the ungoverned 2021 AWS account (`current-state.md`) is *already a resource on this exact platform*, not merely a workload that needs replatforming somewhere. Every other track answers "where do those workloads go"; this track additionally has to answer "what happens to the literal AWS account that already exists" — see [ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md).

## Service Mapping

| Logical Component (Step 5) | AWS Service | Decision Recorded In |
|---|---|---|
| ISO 20022/FedNow Gateway (bought, ADR-002) | Deployed as a vendor appliance/SaaS integration, connecting into the landing zone via private networking (VPC endpoints / PrivateLink where the vendor supports it) | [ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md) |
| Hold/Release Adapter | AWS Fargate (Amazon ECS) | [ADR-011](../adr/ADR-011-aws-compute-platform.md) |
| Fraud Orchestration Service | AWS Fargate (Amazon ECS) | [ADR-011](../adr/ADR-011-aws-compute-platform.md) |
| Ledger-of-Intent Service (application) | AWS Fargate (Amazon ECS) | [ADR-011](../adr/ADR-011-aws-compute-platform.md) |
| Ledger-of-Intent Service (data store) | Amazon Aurora PostgreSQL (Multi-AZ) | [ADR-012](../adr/ADR-012-aws-ledger-of-intent-database.md) |
| Event Bus | Amazon SNS (FIFO topic) fanning out to per-consumer Amazon SQS FIFO queues | [ADR-013](../adr/ADR-013-aws-messaging.md) |
| CDC Connector / Hold-Release path to the mainframe | AWS Direct Connect (Site-to-Site VPN as backup) | [ADR-014](../adr/ADR-014-aws-hybrid-connectivity.md) |
| Reconciliation Process (nightly, [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) | A scheduled AWS Fargate task, triggered nightly by Amazon EventBridge Scheduler, in the same ECS cluster as the three always-on services — rather than a fourth always-on service | [ADR-011](../adr/ADR-011-aws-compute-platform.md) |
| Identity (workforce + workload) | AWS IAM Identity Center, federated to Palisade's on-prem Active Directory via AD Connector; IAM roles for ECS tasks for service-to-service auth | [ADR-015](../adr/ADR-015-aws-identity.md) |
| Landing zone / network segmentation | AWS Control Tower multi-account landing zone (AWS Organizations, Service Control Policies, AWS Config, Security Hub, GuardDuty) | [ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md) |
| Audit/Compliance Log | Amazon Aurora PostgreSQL (append-only table) with archive to Amazon S3 (Object Lock, Compliance mode / WORM) for the 7-year NFR-7 retention | [ADR-012](../adr/ADR-012-aws-ledger-of-intent-database.md) |
| 2021 AWS account workloads (Replatform, Step 4) | Enrolled as a member account into the new AWS Organization, under a separate Legacy-Digital-Channels OU, governed by the same Control Tower guardrails as the new Payments account — audited before enrollment, not rebuilt from scratch by default | [ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md) |

## Why Six Decisions, Not Eight

Same reasoning as [Step 6](azure-implementation.md): this case study's new-build compute layer is small and uniform (three services share one compute platform, one new data store), so this track needed six ADRs, not Case Study 1's eight. What replaces the two ADRs Case Study 1 needed and this case study doesn't is the same hybrid-connectivity decision Azure also needed ([ADR-014](../adr/ADR-014-aws-hybrid-connectivity.md)) — Solstice never needed one — plus a landing-zone decision ([ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md)) that is materially heavier here than Azure's equivalent, because it has to resolve a live, already-existing account rather than design a governance model on a blank slate.

## Network and Security Summary

- **Segmentation:** A multi-account AWS Organization, managed by AWS Control Tower, replaces Azure's single-subscription hub-spoke shape with AWS's own strongest isolation primitive — the account boundary ([ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md)). A dedicated **Payments account/VPC** hosts the new real-time services (Fargate, Aurora, SNS/SQS) and is the only VPC connected to Palisade's data center via Direct Connect ([ADR-014](../adr/ADR-014-aws-hybrid-connectivity.md)). The enrolled 2021 account's workloads live in a separate **Legacy-Digital-Channels account/VPC**, with no mainframe connectivity and no route to the Payments VPC.
- **Private connectivity to PaaS:** Aurora PostgreSQL sits in private subnets with security groups scoped to the three ECS services only; SNS and SQS are reached over VPC interface endpoints (AWS PrivateLink) rather than the public AWS API endpoints — nothing in this architecture's payment path crosses the public internet.
- **Identity:** Human access is federated through AWS IAM Identity Center and AD Connector to Palisade's existing on-prem Active Directory (no second directory to replicate or keep in sync); every service-to-service call (ECS tasks calling Aurora, SNS, or SQS) uses an IAM role attached to the task, with temporary credentials issued and rotated automatically — no access key is ever stored in application configuration.
- **Governance guardrails:** Service Control Policies, applied organization-wide from the management account, enforce the approved region (US regions only, satisfying NFR-6) and deny public-facing PaaS resources; an AWS Config conformance pack continuously evaluates both accounts against that same policy set; Security Hub aggregates findings and GuardDuty provides threat detection across the whole Organization from the dedicated Security/Audit account.

## Observability

ECS task logs and metrics, Aurora performance and audit logs, and SNS/SQS metrics all publish to Amazon CloudWatch within their own account. Because this track is multi-account (unlike Azure's single-subscription landing zone), a dedicated Monitoring/Log Archive account aggregates CloudWatch Logs and metrics from both the Payments and Legacy-Digital-Channels accounts via CloudWatch cross-account observability, so the Audit/Compliance Log's application-level event stream and infrastructure telemetry are queryable from one place. Same rationale as Step 6: an OCC examiner asking "show me everything that happened to payment X" should not require correlating systems across account boundaries, even though those boundaries exist deliberately for isolation.

## Known Deferred Items

Consistent with this case study's own convention: CloudFormation/CDK templates for this landing zone and its workloads are not yet built (`terraform/` remains empty pending the Step 10 platform decision); diagrams for this track are not yet drawn (same convention Case Study 1's own AWS-implementation step followed); detailed sizing (Fargate task CPU/memory, Aurora instance class, SNS/SQS throughput provisioning) is deferred to Step 13's cost analysis; the specific CICS transaction exposed for the [ADR-001](../adr/ADR-001-mainframe-integration-approach.md) hold/release call remains an outstanding mainframe-team decision, unresolved here exactly as it was in Step 6. One new item unique to this track: the 2021 AWS account's enrollment audit (IAM users, security groups, resource inventory, undocumented dependencies flagged in `requirements.md`) is named here as a concrete Step 12 migration-roadmap action item, not performed as part of this architecture step.
