# AWS Implementation — Meridian Health Network

This document implements the vendor-neutral logical design once on Amazon Web Services. It is one of four parallel implementations (Azure, AWS, GCP, private cloud) that will be scored against each other in a weighted decision matrix — nothing here is the final platform choice. The point of building this thoroughly, rather than sketching it, is that a fair comparison requires each platform to actually be designed, not guessed at — the same discipline [`azure-implementation.md`](azure-implementation.md) applied.

This document covers the platform as a whole — service selection, networking, security, DR, IaC. For a deeper, per-application treatment of exactly how each of CareLink PM, MeridianConnect Portal, Telehealth, and LinkEngine is hosted, connects to its data, is reached by users, and scales — see [`application-architecture-aws.md`](application-architecture-aws.md).

Where a decision is genuinely platform-neutral (the migration strategy, the DR topology, the database engine family, the target architecture style), it is not re-litigated here — it's inherited from ADR-001 through ADR-004 and ADR-009 unchanged. This document and its ADRs (ADR-012 through ADR-018) only decide the AWS-specific *how*.

## 1. Service Mapping

| Logical Component | AWS Service | Tier / Notes | Why |
| --- | --- | --- | --- |
| Identity Provider (workforce) | AWS Directory Service for Microsoft AD (Standard Edition), two-way trust to the existing on-prem AD forest | Standard Edition | Extends the existing AD forest rather than replacing it — matches the Replatform posture for identity, direct parity with Entra Connect hybrid sync |
| Identity Provider (patients) | Amazon Cognito User Pools | — | Deliberately separate consumer identity population from workforce (see ADR-016) |
| API Gateway | Amazon API Gateway (REST API, Regional endpoint, VPC Link to private integrations) | — | Single ingress, per-call token/API-key validation, and the seam that makes the Strangler Fig possible — direct parity with APIM |
| Portal Service | Amazon ECS on AWS Fargate | Linux containers, VPC-private tasks behind an internal ALB | Owned code (Refactor) — a standard serverless-container web tier is the simplest fit, no need for EKS at this scale (see ADR-017) |
| Telehealth Service | Third-party SaaS, integrated via Amazon Cognito (SSO/SAML or OIDC) and API Gateway | N/A (vendor-hosted) | Repurchase decision — Meridian integrates, doesn't host, platform-neutral (ADR-002) |
| Core PM Service (CareLink PM) | Citrix Virtual Apps and Desktops, hosted on Amazon EC2 (Windows Server), Availability Zone-spread | EC2 `m6i.2xlarge`, 2+ instances across zones | Replatform, not Refactor — Citrix already publishes CareLink PM today; moving the same delivery model onto AWS infrastructure is the actual replatform, not a rebuild (see ADR-012) |
| Event / Integration Bus | Amazon SNS (FIFO topics) + Amazon SQS (FIFO queues) | Per-message-group ordering, dead-letter queues via redrive policy | Native fan-out/queue combination with per-patient ordering and dead-lettering, fully serverless (see ADR-018) |
| Primary Relational Database | Amazon RDS Custom for SQL Server | Multi-AZ, OS/filesystem access for compatibility | Closest AWS analog to near-full SQL Server engine compatibility a vendor app may depend on — the realistic choice for CareLink PM, at the cost of some of standard RDS's hands-off automation (see ADR-013) |
| Object / Blob Storage | Amazon S3 | Standard tier + S3 Object Lock (Compliance mode, WORM) + Versioning | Native, time-based immutable storage satisfies the "immutable, geographically separate backup" requirement directly |
| Secrets Manager | AWS Secrets Manager (credentials) + AWS Certificate Manager (TLS certificates) | — | Centralizes credentials and certificates; every other service authenticates against these instead of embedded secrets |
| Centralized Logging | Amazon CloudWatch Logs + Amazon OpenSearch Service + Amazon Security Lake + AWS Security Hub + Amazon GuardDuty | Security Lake/Security Hub/GuardDuty = SIEM layer | Directly closes the "no SIEM, manual multi-system review" gap named in the current-state assessment — see Section 7 for why this is four services, not one, unlike Azure's single-product Sentinel |
| Secondary Region (DR) | Paired AWS region (us-west-2) | AWS DMS CDC replication for the database, AWS Elastic Disaster Recovery for the EC2 tier, S3 Cross-Region Replication for object storage | Implements the warm-standby design from ADR-004 with AWS-native replication tooling — see Section 8 for the gaps this surfaces that Azure's equivalent design doesn't have |
| Shared-Services / Landing Zone | AWS Organizations + AWS Control Tower: Organizational Units holding per-environment AWS accounts | — | Turns "onboard a new clinic" into deploying against a governed, pre-approved account pattern — see ADR-014's structural note on accounts vs. subscriptions |
| Hub-and-Spoke Network | Transit Gateway hub + Inspection VPC (AWS Network Firewall) + Application/Data VPC spokes, attached via Transit Gateway | — | Direct AWS implementation of the hub-and-spoke shape carried forward from the current state (see ADR-014) |

## 2. Compute — Hosting CareLink PM (see ADR-012)

CareLink PM is a Windows thick-client application currently published via Citrix Virtual Apps 7. The lowest-risk AWS implementation keeps that exact delivery model and moves only the infrastructure underneath it: Citrix Virtual Apps and Desktops has native AWS support, so the instances Citrix publishes from simply move to EC2, spread across Availability Zones instead of living in a single converted server room. This is what "Replatform, not Refactor" means concretely at the compute layer on AWS, the same as it did for Azure — see ADR-012 for the full comparison against Amazon AppStream 2.0 and a full container-based rebuild, and [`application-architecture-aws.md` §1](application-architecture-aws.md#1-carelink-pm-core-pm-service) for the full Cloud Connector / Machine Catalog hosting architecture and how it reaches its database.

## 3. Database — Amazon RDS Custom for SQL Server (see ADR-013)

The logical design (ADR-003) already decided "managed relational, not NoSQL." The AWS-specific question is which managed relational offering — and unlike the Azure comparison, this isn't a two-way choice. Amazon RDS Custom for SQL Server is chosen over standard Amazon RDS for SQL Server specifically because CareLink PM, as a mature on-prem vendor product, is more likely to depend on OS-level integrations, CLR functionality, or linked-server configurations that standard RDS's fully-managed, no-OS-access model doesn't support but RDS Custom does. See ADR-013, including its Proposed Configuration table for the concrete instance class, storage type, and redundancy settings, and its explicit callout of RDS Custom's cross-region DR limitation relative to standard RDS/Aurora. Both CareLink PM and MeridianConnect Portal use this same instance, as separate databases — see `application-architecture-aws.md` for exactly how each application connects to it.

## 4. Networking and Landing Zone

- **Inspection VPC (hub)**: AWS Network Firewall (egress control and threat/intrusion filtering), a Transit Gateway attachment, and the Site-to-Site VPN / Direct Connect Gateway attachment for any remaining on-prem/clinic connectivity during migration. Unlike Azure Bastion's dedicated subnet, remote administrative access uses **AWS Systems Manager Session Manager** instead of a bastion host — no inbound management port is ever opened at all, not even through a jump box, which is a genuine simplification over the Azure design rather than a like-for-like substitute.
- **Application VPC (spoke)**: API Gateway's VPC Link, ECS Fargate tasks (Portal), EC2 Citrix instances, Lambda functions (LinkEngine subscribers), and VPC interface endpoints for SNS/SQS.
- **Data VPC (spoke)**: RDS Custom for SQL Server (which requires a DB subnet group spanning at least two Availability Zones) and VPC interface endpoints for Secrets Manager and CloudWatch.
- **Landing zone structure**: AWS Control Tower over AWS Organizations, with a Platform OU (log archive, security tooling, network accounts) separate from the Workload OU this application lives in — see ADR-014's structural note for why this is an *account* boundary on AWS, not a subscription boundary the way Azure's Landing Zone is. See ADR-014 for Transit Gateway hub-and-spoke vs. AWS Cloud WAN.

### 4.1 Network Addressing Plan

Named services and boxes on a diagram aren't a network — an implementable design needs actual address space, the same principle `azure-implementation.md` §4.1 applied. The same non-overlapping CIDR scheme used for the Azure design is reused here deliberately: it's already been validated not to collide with anything, and using the same ranges across platform implementations makes the eventual side-by-side comparison in Step 10 easier to read, not harder.

**A correction worth flagging explicitly.** An earlier version of this table listed one subnet per tier (e.g. a single `subnet-citrix`, 10.20.3.0/24) for resources this document elsewhere describes as spread across 3 Availability Zones. That's not just imprecise — it's not realizable in AWS at all: unlike an Azure VNet subnet, which spans every Availability Zone in the region, **an AWS VPC subnet is scoped to exactly one Availability Zone**. A resource pool meant to span 3 AZs needs 3 subnets, one per zone, not one subnet claiming all three. The table below fixes that for every tier that genuinely needs multi-AZ presence; RDS Custom's `subnet-rds-az1`/`az2` pair was already correct, since Multi-AZ only requires 2 zones and that's what it had.

| VPC | Address space | Subnet | Range | Purpose |
| --- | --- | --- | --- | --- |
| Inspection VPC (hub) | 10.10.0.0/16 | subnet-tgw-attach-az1/az2/az3 | 10.10.0.0/28, 10.10.0.16/28, 10.10.0.32/28 | Transit Gateway VPC attachment ENIs — one per AZ, matching AWS's own recommended pattern for TGW attachments |
| | | subnet-firewall-az1/az2/az3 | 10.10.1.0/27, 10.10.1.32/27, 10.10.1.64/27 | AWS Network Firewall endpoints — one per AZ (Network Firewall deploys a firewall endpoint per zone; a single shared subnet can't host all three) — forced-tunnel next hop for both spokes |
| | | subnet-vpn-dx | 10.10.2.0/27 | Site-to-Site VPN / Direct Connect Gateway attachment — attaches to the Transit Gateway itself rather than to a per-AZ subnet the way TGW VPC attachments and Network Firewall endpoints do, so this one deliberately stays a single allocation |
| Application VPC | 10.20.0.0/16 | subnet-apigw-vpclink-az1/az2/az3 | 10.20.1.0/26, 10.20.1.64/26, 10.20.1.128/26 | API Gateway VPC Link ENIs (private integration to internal NLB/ALB targets) — one subnet per AZ for HA |
| | | subnet-ecs-portal-az1/az2/az3 | 10.20.2.0/26, 10.20.2.64/26, 10.20.2.128/26 | ECS Fargate tasks (Portal), behind an internal ALB — one subnet per AZ, matching the 3-AZ autoscale floor in ADR-017 |
| | | subnet-citrix-az1/az2/az3 | 10.20.3.0/26, 10.20.3.64/26, 10.20.3.128/26 | Citrix / CareLink PM EC2 instances — one subnet per AZ (62 usable addresses each), comfortably covering ADR-012's ~42-per-zone day-one figure with room to grow toward the 36-month ceiling |
| | | subnet-sns-sqs-endpoints-az1/az2/az3 | 10.20.4.0/26, 10.20.4.64/26, 10.20.4.128/26 | VPC interface endpoints for SNS/SQS — one subnet per AZ |
| | | subnet-lambda-linkengine-az1/az2/az3 | 10.20.5.0/26, 10.20.5.64/26, 10.20.5.128/26 | AWS Lambda functions (LinkEngine's four subscribers, ADR-015, plus the ingest-side Publish Function, ADR-018 — five functions sharing this tier) — one subnet per AZ for genuine multi-AZ resilience, still isolated from the other tiers' subnets for IP-exhaustion reasons, not because AWS requires a dedicated subnet per function the way Azure requires one per App Service Plan (see ADR-015's explicit note on this platform difference) |
| | | subnet-cloud-connectors-az1/az2/az3 | 10.20.6.0/27, 10.20.6.32/27, 10.20.6.64/27 | Citrix Cloud Connectors — one per Availability Zone plus a spare (the spare lands in whichever zone's subnet has room), separated from the `subnet-citrix-*` session-hosting compute since Cloud Connectors are the control-plane bridge to Citrix Cloud, not session hosts (see ADR-012) |
| Data VPC | 10.30.0.0/16 | subnet-rds-az1 | 10.30.1.0/25 | RDS Custom for SQL Server — Availability Zone 1 half of the DB subnet group |
| | | subnet-rds-az2 | 10.30.1.128/25 | RDS Custom for SQL Server — Availability Zone 2 half of the DB subnet group (Multi-AZ requires ≥2 AZs, not 3 — this pair was already correct) |
| | | subnet-vpc-endpoints-az1/az2 | 10.30.2.0/25, 10.30.2.128/25 | VPC interface endpoints for Secrets Manager and CloudWatch, one subnet per AZ matching the 2-AZ RDS footprint. Amazon S3 is reached via a Gateway endpoint, which attaches to route tables rather than consuming subnet IP addresses — no dedicated subnet needed for S3 access specifically |
| Non-Prod VPC | 10.40.0.0/16 | (subnets mirror the Application VPC pattern at smaller scale) | — | Dev/Test/UAT environments and CI/CD runners (CodeBuild/CodePipeline), in the `meridian-healthcare-nonprod` account (§4.2) — same landing-zone pattern as production, not detailed subnet-by-subnet here since it doesn't carry production traffic |
| DR region mirror (us-west-2): Inspection VPC-DR | 10.110.0.0/16 | same per-AZ pattern as the primary Inspection VPC | — | `meridian-network-dr` account (§4.2) |
| DR region mirror: Application VPC-DR | 10.120.0.0/16 | same per-AZ pattern as the primary Application VPC | — | `meridian-healthcare-dr-app` account — AWS DRS/ECS Fargate/Lambda failover targets |
| DR region mirror: Data VPC-DR | 10.130.0.0/16 | same per-AZ pattern as the primary Data VPC | — | `meridian-healthcare-dr-data` account — DMS warm-standby SQL Server target |
| DR region mirror: Shared Services VPC-DR | 10.140.0.0/16 | (not detailed subnet-by-subnet — monitoring/backup tooling, not a failover target) | — | `meridian-healthcare-dr-shared` account (§4.2) — DR-side monitoring/logging and backup, no primary-region counterpart since these tools run region-locally |

Two controls make this addressable network actually enforce the Zero Trust posture, not just draw it:

- **Route table default route** on both spoke VPCs: `0.0.0.0/0` targets the Transit Gateway, which routes through the Inspection VPC's AWS Network Firewall endpoint before reaching a NAT Gateway/Internet Gateway — the AWS-native equivalent of Azure's UDR-forced-tunnel pattern, achieved through Transit Gateway route table associations rather than a per-subnet user-defined route.
- **Security groups**, attached at the resource/ENI level (stateful, allow-only) — for example, the RDS Custom instance's security group only accepts inbound 1433 from the Citrix, ECS Portal, and Lambda LinkEngine security groups, and denies everything else by default. **Network ACLs** at the subnet level provide a stateless secondary backstop. This is a genuine model difference worth naming: Azure's NSGs are the single primary control at the subnet/NIC level, while AWS splits that responsibility between stateful security groups (the primary, resource-attached control used here) and stateless NACLs (a coarser, subnet-level backstop) — not a one-to-one terminology swap.

Secrets Manager, CloudWatch, and S3 are reached over VPC endpoints from both spokes — Secrets Manager by the Citrix instances (CareLink PM's database login) and ECS Fargate tasks (the Portal's connection string), CloudWatch by everything that emits logs/metrics, S3 by everything that reads/writes the object archive. None of these need a *new* dedicated subnet the way the RDS Custom DB subnet group does; their interface endpoints sit inside the existing `subnet-ecs-portal-*`/`subnet-citrix-*` subnets in the Application VPC and `subnet-vpc-endpoints-*` in the Data VPC, alongside the resources that call them.

See `diagrams/aws-network-addressing.png` for the full subnet and security-group map, `diagrams/aws-deployment-architecture.png` for the consolidated hub-and-spoke topology and public entry points (ADR-014), and `diagrams/aws-dr-view.png` for the paired-region DR view.

### 4.2 Governance — Organizational Units and Accounts

Landing zone structure isn't just a paragraph — it's a specific AWS Organizations hierarchy under AWS Control Tower: a **Security** OU holding the log-archive and audit accounts every workload's logs and CloudTrail events flow into, an **Infrastructure** OU holding the shared networking account(s) (Transit Gateway, Inspection VPC, Direct Connect Gateway), and a **Workloads** OU holding the actual per-environment accounts. The Workloads OU is split finer than one account per environment: **two Production accounts** in the primary region (one holding the Application VPC — Citrix EC2, ECS Fargate, Lambda — one holding the Data VPC — RDS Custom), separating compute and data at the account boundary rather than just the VPC boundary, plus one **Non-Production** account for Dev/Test/UAT. The Infrastructure OU adds a **Network** account for the primary region's Inspection VPC. The paired DR region in us-west-2 mirrors this same shape rather than collapsing to a single DR account — specific to this case study's DR design: a **DR Production** account for the DR Application VPC (the AWS DRS/ECS/Lambda failover targets), a second **DR Production** account for the DR Data VPC (the DMS warm-standby SQL Server target), a **DR Network** account for the DR Inspection VPC, and a **DR Shared Services** account for DR-side monitoring/logging and backup tooling. Eight workload/network accounts total across both regions, not three — see ADR-014's structural note for why AWS's account-per-boundary model pushes toward this finer split rather than the single-subscription-per-environment shape `azure-implementation.md` §4.2 uses. This is the direct structural analog to `azure-implementation.md` §4.2's management-group/subscription hierarchy, with the account substituted for the subscription as the isolation boundary (see ADR-014). See [`../diagrams/aws-network-topology-hub-spoke.png`](../diagrams/aws-network-topology-hub-spoke.png) for the full account/VPC layout across both regions, and `diagrams/aws-landing-zone.png` for the OU hierarchy.

## 5. Identity and Security

- AWS Directory Service for Microsoft AD, in a two-way forest trust with Meridian's existing on-prem Active Directory, lets Citrix EC2 instances domain-join and clinical staff authenticate with their existing credentials — direct parity with Entra Connect hybrid sync.
- AWS IAM Identity Center, layered on top of the directory trust, provides federated SSO for AWS-hosted web resources and the AWS Console access the platform team itself needs, using SAML against the trusted directory.
- **A gap worth naming plainly, not glossed over.** AWS IAM Identity Center's risk-based/adaptive sign-in and device-compliance evaluation capabilities are materially less mature than Microsoft Entra ID P2's Conditional Access and Identity Protection — there is no direct AWS-native equivalent to policies like "block sign-in from a non-compliant device" or "require additional verification on an atypical sign-in risk score" at the same level of built-in sophistication. Closing that specific gap on AWS realistically requires either a third-party identity/CASB layer (e.g., Okta, Duo) in front of or alongside IAM Identity Center, or accepting a materially weaker Conditional-Access-equivalent posture than the Azure design achieves natively. This is flagged here as a genuine, not cosmetic, difference that should carry real weight in the Step 10 decision matrix — the March 2026 credential-compromise incident is exactly the failure mode Conditional Access-style controls exist to prevent, and MFA enforcement alone (which IAM Identity Center *does* support natively) closes part but not all of that gap.
- Every PaaS service (API Gateway, ECS Fargate, SNS/SQS, RDS Custom, S3) is reached through a **VPC endpoint or private VPC integration**, not the public internet, mirroring the Azure design's private-endpoint-everywhere posture.
- AWS Secrets Manager holds every credential; AWS Certificate Manager holds every TLS certificate. IAM roles (not embedded secrets) let ECS tasks, Lambda functions, and EC2 instances authenticate to Secrets Manager and to each other — directly retiring the shared/generic service accounts named in the current-state assessment.
- Amazon GuardDuty provides workload-level threat detection across the EC2, database, and storage layers, with findings aggregated into AWS Security Hub.
- Patients remain a deliberately separate identity population from staff — see ADR-016. Extending AWS Directory Service to also hold ~2 million patient identities was considered and rejected for the same reason ADR-009 rejected it for Azure; Amazon Cognito keeps that consumer population out of the directory that governs clinical-system access.

## 6. Integration — Amazon SNS + SQS

HL7 and API events route through SNS FIFO topics fanning out to SQS FIFO queues, one pair per message category (lab results, imaging, e-prescribing, appointment events), each with its own redrive policy to a dead-letter queue. Built-in dead-lettering means a failed or malformed message doesn't just disappear — the same direct fix for LinkEngine's current "if CareLink PM is down, the message is lost" behavior that Azure's design achieves. `MessageGroupId` = patient ID preserves message ordering where a downstream consumer needs it (a sequence of updates to the same patient record). Getting that patient ID onto the message in the first place is a small AWS Lambda **Publish Function** (ADR-018), invoked by API Gateway's proxy integration right after mTLS/rate-limit validation — it parses the raw HL7v2 payload, extracts the patient ID, and publishes to the matching SNS FIFO topic, since API Gateway's own mapping templates can't reliably do that extraction against pipe-delimited HL7v2 text the way they could against JSON. The subscriber logic that actually reacts to these messages runs on AWS Lambda, not the Citrix EC2 tier — see ADR-015 for why interactive session compute and background message processing are deliberately kept on separate, independently-scaling platforms, the identical reasoning ADR-008 used for Azure Functions.

## 7. Observability

Every component above ships logs and metrics to Amazon CloudWatch. Unlike Azure, where Microsoft Sentinel is a single product sitting on top of Log Analytics as the SIEM layer, AWS's native security-operations stack is composed of several purpose-specific services working together: **Amazon Security Lake** centralizes security-relevant log data from across the environment into a normalized, queryable format; **Amazon GuardDuty** provides continuous threat detection; **AWS Security Hub** aggregates findings from GuardDuty and other AWS security services into one place; and **Amazon OpenSearch Service** provides the query/dashboard surface a security analyst actually works in. This is a genuine architectural difference worth naming rather than assuming AWS has a single Sentinel-equivalent product — four services are stitched together here to close the same "no SIEM, manual multi-system review" gap Azure's single-product Sentinel closes more directly. CloudWatch Alarms are tied to the same RTO/RPO-relevant signals (replication lag, failed sign-ins, SQS dead-letter queue depth) that matter operationally, not just infrastructure health.

## 8. Disaster Recovery Implementation

| Element | AWS Mechanism |
| --- | --- |
| Database replication | AWS DMS continuous CDC replication from the primary RDS Custom instance to a warm-standby instance in us-west-2 — **not** a native cross-region read replica the way standard RDS/Aurora offers; see ADR-013's explicit gap callout |
| VM tier replication | AWS Elastic Disaster Recovery (AWS DRS) replicates the Citrix/CareLink PM EC2 tier to the secondary region at the block level, low-RPO continuous replication |
| Storage replication | Amazon S3 Cross-Region Replication (CRR) |
| Messaging | **No native replication at all** — matching infrastructure (topics/queues) is pre-provisioned in us-west-2 via the same IaC, with no message content carried over; see ADR-018's explicit gap callout, which is materially larger than Azure Service Bus's equivalent gap |
| Failover trigger | Manual-initiated (ADR-004) — an operator triggers DMS target promotion and AWS DRS failover through a documented runbook, not an automatic process |
| Traffic cutover | Amazon Route 53 failover routing policy with health checks, in front of Amazon CloudFront | 

This is the AWS-specific implementation of the warm-standby topology decided in ADR-004 — the strategy didn't change, only the tooling that realizes it, and that tooling has real, explicitly-documented gaps (RDS Custom's cross-region DR maturity, SNS/SQS's total lack of cross-region replication) that the Azure implementation doesn't have in the same form. Both are real trade-offs to weigh in Step 10, not defects to hide.

## 9. Infrastructure as Code

AWS CloudFormation (or the AWS CDK, for teams that prefer authoring in a general-purpose language over declarative YAML/JSON) is the primary IaC tool for this AWS implementation — AWS-native, first-class support for every resource type used above. Terraform is reserved for the cross-platform comparison work in the decision-matrix stage, the same posture `azure-implementation.md` §9 takes with Bicep — one tool spanning all four candidate platforms matters more than native fluency on any single one at that stage.

## 10. Alignment Check

A quick gut-check against AWS's own Well-Architected Framework pillars, before moving on — mirroring the same exercise `azure-implementation.md` §10 ran against Microsoft's pillars:

| Pillar | How this design addresses it |
| --- | --- |
| Reliability | Zone-redundant compute and database (Multi-AZ), paired-region warm standby, SQS dead-lettering |
| Security | VPC-private connectivity everywhere, Secrets Manager-managed credentials, GuardDuty/Security Hub-based detection — with the IAM Identity Center Conditional-Access gap named explicitly in Section 5, not hidden |
| Cost Optimization | Deferred to the cost/risk analysis stage — sizing above is directional, not final |
| Operational Excellence | Control Tower landing zone pattern for repeatable clinic onboarding, centralized CloudWatch logging for a single operational view |
| Performance Efficiency | API Gateway and ECS Fargate scale independently of the CareLink PM EC2 tier, so a portal traffic spike doesn't compete with clinical scheduling load |

## 11. End-to-End Transaction Walkthrough

Every component in the service mapping and the deployment diagram exists because it does something in an actual data flow. The clearest way to prove that is the same one `azure-implementation.md` §11 used: trace one real transaction through every hop it touches, including what happens when it fails.

Scenario: a new lab result arrives from LabCorp for an existing patient.

1. LabCorp posts the HL7 v2 result to Amazon API Gateway over mutual TLS with an API key. API Gateway validates the client certificate and key, applies a usage-plan rate limit, and publishes the message to the `lab-results` SNS FIFO topic, using the patient ID as the `MessageGroupId` so results for the same patient stay ordered. API Gateway returns `202 Accepted` immediately — LabCorp doesn't wait on downstream processing.
2. On the happy path, the SNS topic fans out to its SQS FIFO subscriber queue, and the corresponding Lambda function (triggered by the queue's event source mapping) writes the structured result to the patient's record in RDS Custom for SQL Server over a private VPC connection, archives the raw HL7 payload to immutable S3 storage, and the message is deleted from the queue on successful completion.
3. On the failure path — for example, the patient ID doesn't match an existing record — the Lambda function's invocation fails and the message becomes visible again in the queue. SQS retries up to the configured `maxReceiveCount`, then the redrive policy moves it to the dead-letter queue and a CloudWatch alarm fires to on-call, instead of silently dropping it — the direct fix for the current LinkEngine's "if CareLink PM is down, the message is lost" failure mode.
4. Later, when a provider opens the patient's chart in CareLink PM, the query against RDS Custom returns the record with the new result already in it — the write from step 2 and the read in step 4 are decoupled in time by design, the same "event-driven" property the Azure design achieves.

Every hop above also ships logs and metrics to CloudWatch, which is what makes the dead-letter alarm in step 3 possible in the first place. See `diagrams/sequence-lab-result-aws.png` for the full sequence, including the alternate failure path.

## 12. Disaster Recovery Runbook

ADR-004 set the target: warm standby, manual-initiated failover, RTO ≤ 4 hours, RPO ≤ 15 minutes — platform-neutral. Section 8 named the AWS mechanisms, including two gaps (RDS Custom's cross-region DR maturity, SNS/SQS's lack of any native replication) that Azure's equivalent runbook doesn't have to account for in the same way. What's still missing is proof that those mechanisms, run in the realistic order an on-call engineer would actually run them, fit inside the 4-hour budget.

1. **T+0 to T+15 min** — Amazon CloudWatch alarms page on-call; the engineer confirms the outage is real and declares a disaster per the documented runbook, rather than failing over on a single alert.
2. **T+15 to T+45 min** — the engineer promotes the DMS-replicated warm-standby SQL Server instance in us-west-2 to primary. This step is allotted more time than ADR-004's Azure equivalent (T+15-30 min) specifically because DMS CDC promotion is a less turnkey operation than an Azure SQL MI auto-failover group's native failover — the extra 15 minutes is a deliberate, honest margin for a mechanism this design has already flagged as less mature, not an optimistic number.
3. **T+45 to T+105 min**, run in parallel with database promotion where possible — the engineer triggers AWS Elastic Disaster Recovery failover for the Citrix/CareLink PM EC2 tier (instances launch in the secondary region from continuously-replicated block data) **and** confirms the pre-provisioned SNS/SQS resources in us-west-2 are reachable and correctly configured (there is no failover action to trigger for messaging — the resources already exist, since nothing is replicated into them).
4. **T+105 to T+165 min** — before any traffic is cut over, the engineer runs smoke tests against the secondary region (authentication, database read/write, SNS/SQS publish-and-receive against the DR-region resources) to confirm it's actually healthy, not just "up," and separately initiates source-system reconciliation for the failover window — LabCorp, Quest, and Surescripts are queried for results/messages sent during the gap, since nothing in flight at the moment of failure was carried over (a larger version of the same reconciliation step ADR-011/ADR-018 already establish for Azure and AWS respectively). This reconciliation runs in the background and does not block the traffic cutover in step 5.
5. **T+165 to T+195 min** — the engineer updates the Amazon Route 53 failover routing policy to point at the secondary region's CloudFront distribution; once DNS propagates, users are routed to the secondary region.

Total: **195 minutes actual against a 240-minute (4-hour) target** — a smaller margin than the Azure design's 180-minute total, and that's an honest reflection of the two gaps named in Section 8, not an oversight. If real-world DMS promotion or AWS DRS failover times run longer than this estimate during an actual DR test, this runbook's margin erodes faster than the Azure design's does — worth weighing directly in the Step 10 comparison. See `diagrams/dr-failover-runbook-aws.png`.

## 13. CI/CD and Environment Promotion

CloudFormation/CDK (Section 9) is the authoring tool; this section is how a change actually reaches production, using AWS CodePipeline and CodeBuild. Every change flows through the same landing-zone accounts named in Section 4.2: the non-production workload account for Dev and Test/QA, the production workload account for production.

- **On every pull request**: `cfn-lint` (or `cdk synth` + `cdk diff` for CDK-authored stacks) catches syntax and type errors; a `cfn-guard` policy check enforces security and Well-Architected rules against the templates; `aws cloudformation deploy --no-execute-changeset` (a CloudFormation change set, not yet executed) posts the predicted resource changes directly on the PR, so a reviewer sees the actual diff, not just the code diff — direct parity with `azure-implementation.md`'s `az deployment what-if` step.
- **Human review**: the platform team reviews both the code and the change-set output before approving.
- **On merge to main**: CodePipeline deploys to Dev automatically, runs automated smoke tests, then stops at a manual approval gate before Test/QA, and a second manual approval gate — paired with a change record — before production. Production deployment ends with a post-deploy validation pass and an AWS Config compliance scan, not just a "deployment succeeded" status.

The two manual gates are deliberate, not a process gap — the identical reasoning `azure-implementation.md` §13 applied: infrastructure changes to a clinical system's database or network tier are exactly the kind of change that should require a human decision immediately before it happens, the same reasoning behind DR failover being manual-initiated in ADR-004. See `diagrams/cicd-pipeline-aws.png`.

## 14. Explicitly Deferred

- Exact instance/database sizing and cost modeling — Step 13
- Final platform recommendation — Step 10, after GCP and private-cloud implementations exist to compare against
- Detailed IAM role/policy definitions
- Terraform modules (built once, during the migration roadmap stage, for whichever platform is chosen)
- A third-party identity/CASB layer to fully close the IAM Identity Center Conditional-Access gap named in Section 5 — flagged as a real, not cosmetic, decision point, not silently assumed away

## 15. Diagrams

- `diagrams/aws-deployment-architecture.png` — consolidated one-page AWS implementation overview, hand-corrected: service mapping, hub-and-spoke network architecture (Route 53 → CloudFront → WAF → Portal, API Gateway kept separate for background integrations only, CareLink PM/Telehealth explicitly called out as *not* reachable via API Gateway), infrastructure, identity/security, HA/DR, and current-state operational incidents driving the migration. Superseded an earlier AI-generated deployment diagram after two real review rounds — see the diagram's own callout boxes for the corrections (Core PM/Telehealth access paths, CloudFront/Route 53 ordering, the DMS RPO caveat, the SNS/SQS DR gap).
- `diagrams/aws-dr-view.png` — paired-region DR view with AWS-specific replication mechanisms and their gaps.
- `diagrams/aws-network-addressing.png` — subnet-level addressing plan, security groups, and forced-tunnel routing via Transit Gateway.
- `diagrams/aws-landing-zone.png` — Organizational Unit and account hierarchy (eight workload/network accounts across both regions — see §4.2).
- `diagrams/aws-network-topology-hub-spoke.png` — ADR-014 detail diagram, hand-reproduced: primary and DR region account/VPC layout, Transit Gateway hub-and-spoke attachments, and the full eight-account structure from §4.2.
- `diagrams/sequence-lab-result-aws.png` — end-to-end transaction trace, happy path and dead-letter path.
- `diagrams/dr-failover-runbook-aws.png` — DR failover runbook with an RTO time budget, including the two AWS-specific gaps called out explicitly.
- `diagrams/cicd-pipeline-aws.png` — IaC deployment pipeline from pull request to production.
- `diagrams/carelink-pm-architecture-aws.png` — CareLink PM hosting architecture (Cloud Connectors, Machine Catalog, RDS Custom connectivity).
- `diagrams/portal-architecture-aws.png` — MeridianConnect Portal hosting architecture (CloudFront, ECS Fargate, dual identity providers).
- `diagrams/telehealth-architecture-aws.png` — Telehealth integration architecture (SSO federation, appointment-sync webhook, no Meridian compute).
- `diagrams/linkengine-architecture-aws.png` — LinkEngine message flow architecture (SNS/SQS FIFO, Lambda subscribers).

These are generated as a baseline diagram set, the same starting point the Azure implementation had before its hand-drawn detail diagrams were added on top. As with Step 6, more detailed versions of any of these are welcome any time — they'll be checked against this document and its ADRs the same way every Azure diagram was.

See [`application-architecture-aws.md`](application-architecture-aws.md) for the prose walkthrough of all four application-level diagrams above.
