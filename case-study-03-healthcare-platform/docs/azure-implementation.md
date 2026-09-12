# Azure Implementation — Meridian Health Network

This document implements the vendor-neutral logical design once on Microsoft Azure. It is one of four parallel implementations (Azure, AWS, GCP, private cloud) that will be scored against each other in a weighted decision matrix — nothing here is the final platform choice. The point of building this thoroughly, rather than sketching it, is that a fair comparison requires each platform to actually be designed, not guessed at.

This document covers the platform as a whole — service selection, networking, security, DR, IaC. For a deeper, per-application treatment of exactly how each of CareLink PM, MeridianConnect Portal, Telehealth, and LinkEngine is hosted, connects to its data, is reached by users, and scales — see [`application-architecture.md`](application-architecture.md).

## 1. Service Mapping

| Logical Component | Azure Service | Tier / Notes | Why |
| --- | --- | --- | --- |
| Identity Provider | Microsoft Entra ID, synced from on-prem Active Directory via Entra Connect (hybrid) | Entra ID P2 (for Conditional Access + Identity Protection) | Extends the existing AD forest rather than replacing it — matches the Replatform posture for identity from the logical design |
| API Gateway | Azure API Management | Premium tier (VNet integration + multi-region support) | Single ingress, per-call token validation, and the seam that makes the Strangler Fig possible |
| Portal Service | Azure App Service (Linux, container-based) | Premium v3, VNet-integrated | Owned code (Refactor) — a standard PaaS web tier is the simplest fit, no need for AKS at this scale (see ADR-010) |
| Telehealth Service | Third-party SaaS, integrated via Entra ID (SSO/SAML or OIDC) and APIM | N/A (vendor-hosted) | Repurchase decision — Meridian integrates, doesn't host |
| Core PM Service (CareLink PM) | Citrix Virtual Apps and Desktops, hosted on Azure VMs (Windows Server), Availability Zone-spread | Azure VMs (Dsv5-series), 2+ instances across zones | Replatform, not Refactor — Citrix already publishes CareLink PM today; moving the same delivery model onto Azure infrastructure is the actual replatform, not a rebuild |
| Event / Integration Bus | Azure Service Bus | Premium tier (VNet integration, higher throughput, guaranteed availability SLA) | Native topics/subscriptions, built-in dead-lettering, session support for ordered HL7 message handling (see ADR-011) |
| Primary Relational Database | Azure SQL Managed Instance | Business Critical tier, zone-redundant | Near-100% SQL Server engine compatibility (SQL Agent jobs, cross-database queries, linked servers) — the realistic choice for a vendor app that expects full SQL Server behavior, not just T-SQL |
| Object / Blob Storage | Azure Blob Storage | Hot tier + immutability policy (WORM) + soft delete | Native, time-based immutable storage satisfies the "immutable, geographically separate backup" requirement directly |
| Secrets Manager | Azure Key Vault | Standard tier, RBAC-enabled | Centralizes credentials and certificates; every other service authenticates against this instead of embedded secrets |
| Centralized Logging | Azure Monitor + Log Analytics workspace + Microsoft Sentinel | Sentinel = SIEM layer | Directly closes the "no SIEM, manual multi-system review" gap named in the current-state assessment |
| Secondary Region (DR) | Paired Azure region | SQL MI auto-failover group, Azure Site Recovery for the VM tier, geo-redundant storage (GRS) for Blob | Implements the warm-standby design from ADR-004 with Azure-native replication tooling |
| Shared-Services / Landing Zone | Azure Landing Zone (Cloud Adoption Framework pattern): management groups, platform + application subscriptions, Azure Policy | — | Turns "onboard a new clinic" into deploying against a governed, pre-approved pattern |
| Hub-and-Spoke Network | Hub VNet (Azure Firewall, Bastion, DNS) + spoke VNets per workload tier, VNet peering | — | Direct Azure implementation of the hub-and-spoke shape carried forward from the current state |

## 2. Compute — Hosting CareLink PM (see ADR-005)

CareLink PM is a Windows thick-client application currently published via Citrix Virtual Apps 7. The lowest-risk Azure implementation keeps that exact delivery model and moves only the infrastructure underneath it: Citrix Virtual Apps and Desktops has native Azure support, so the VMs Citrix publishes from simply move to Azure, spread across Availability Zones instead of living in a single converted server room. This is what "Replatform, not Refactor" means concretely at the compute layer — see ADR-005 for the full comparison against Azure Virtual Desktop and a full App Service rebuild, and [`application-architecture.md` §1](application-architecture.md#1-carelink-pm-core-pm-service) for the full Cloud Connector / Machine Catalog hosting architecture and how it reaches its database.

## 3. Database — Azure SQL Managed Instance (see ADR-006)

The logical design (ADR-003) already decided "managed relational, not NoSQL." The Azure-specific question is which managed relational offering. Azure SQL Managed Instance is chosen over Azure SQL Database (the more common default) specifically because CareLink PM, as a mature on-prem vendor product, is more likely to depend on SQL Server Agent jobs, cross-database queries, or linked servers that Azure SQL Database's PaaS engine doesn't support but Managed Instance does. See ADR-006, including its Proposed Configuration table for the concrete tier, hardware generation, compute size, and redundancy settings. Both CareLink PM and MeridianConnect Portal use this same Managed Instance, as separate databases — see `application-architecture.md` for exactly how each application connects to it, and [`../diagrams/sql-managed-instance-architecture.png`](../diagrams/sql-managed-instance-architecture.png) for the zone layout, DR auto-failover group, and network path (SQL MI sits directly in the delegated `snet-sqlmi` subnet — it's subnet-injected, not fronted by a separate Private Endpoint resource, unlike Storage or Service Bus).

## 4. Networking and Landing Zone

- **Hub VNet**: Azure Firewall (egress control and threat intelligence filtering), Azure Bastion (no public RDP/SSH), private DNS zones, ExpressRoute or Site-to-Site VPN gateway for any remaining on-prem/clinic connectivity during migration.
- **Spoke VNets**: one for the application tier (APIM, App Service, Citrix VMs, Service Bus private endpoints), one for the data tier (SQL Managed Instance — which requires its own dedicated subnet — and Blob Storage private endpoints).
- **Landing zone structure**: a platform landing zone (identity, connectivity, management subscriptions) separate from the application landing zone this workload lives in, following the standard Cloud Adoption Framework separation — this is what makes the *next* clinic, or the *next* case study workload, provision against a pattern instead of a one-off design. See ADR-007 for hub-and-spoke vs. Azure Virtual WAN.

### 4.1 Network Addressing Plan

Named services and boxes on a diagram aren't a network — an implementable design needs actual address space. Non-overlapping ranges are chosen up front for both regions so the primary and paired-DR VNets can be peered or routed against each other during a failover without a later re-addressing exercise.

| VNet | Address space | Subnet | Range | Purpose |
| --- | --- | --- | --- | --- |
| Hub VNet | 10.10.0.0/16 | GatewaySubnet | 10.10.0.0/27 | VPN / ExpressRoute Gateway |
| | | AzureFirewallSubnet | 10.10.1.0/26 | Azure Firewall — forced-tunnel next hop for both spokes |
| | | AzureBastionSubnet | 10.10.2.0/27 | Azure Bastion |
| Application Spoke VNet | 10.20.0.0/16 | snet-apim | 10.20.1.0/24 | Azure API Management (VNet-injected) |
| | | snet-appsvc | 10.20.2.0/24 | App Service, delegated to `Microsoft.Web/serverFarms` |
| | | snet-citrix | 10.20.3.0/24 | Citrix / CareLink PM VMs |
| | | snet-svcbus-pe | 10.20.4.0/24 | Service Bus private endpoints |
| | | snet-func-linkengine | 10.20.5.0/24 | Azure Functions Premium plan (LinkEngine subscribers), delegated to `Microsoft.Web/serverFarms` — a dedicated subnet, separate from `snet-appsvc`, because Azure regional VNet Integration requires one subnet per App Service Plan (see ADR-008) |
| | | snet-cloud-connectors | 10.20.6.0/24 | Citrix Cloud Connectors (one per Availability Zone plus a spare) — separated from `snet-citrix`'s VDA session hosts since Cloud Connectors are the control-plane bridge to Citrix Cloud, not session-hosting compute (see ADR-005) |
| Data Spoke VNet | 10.30.0.0/16 | snet-sqlmi | 10.30.1.0/24 | SQL Managed Instance — dedicated subnet, delegated to `Microsoft.Sql/managedInstances`, no other resources permitted |
| | | snet-storage-pe | 10.30.2.0/24 | Blob Storage private endpoints |
| DR region mirror | 10.110.0.0/16, 10.120.0.0/16, 10.130.0.0/16 | same subnet pattern | — | Paired region, same structure, non-overlapping ranges |

Two controls make this addressable network actually enforce the Zero Trust posture, not just draw it:

- **User-defined route (UDR)** on both spoke VNets: default route `0.0.0.0/0` next-hop set to the Azure Firewall's private IP (10.10.1.4), forcing all egress through the hub instead of a direct internet path.
- **Network security groups (NSGs)**, one per subnet, allow-listing only the specific traffic each tier needs — for example, `snet-sqlmi` only accepts inbound 1433 from `snet-citrix`, `snet-appsvc`, and `snet-func-linkengine` (the Functions subscribers write results into SQL MI directly, per ADR-008), and denies everything else, including from other subnets in the same VNet.

Key Vault, Azure Monitor, Log Analytics, and Backup Vault are also reached over private endpoints from both spokes — Key Vault by the Citrix VMs (CareLink PM's SQL login) and App Service (Portal's connection string), the others by every resource that emits diagnostics or takes a backup. None of these need a dedicated subnet the way `snet-sqlmi` does; their private endpoints sit inside the existing `snet-appsvc`/`snet-citrix` subnets in the Application Spoke and `snet-sqlmi`'s spoke-level address space in the Data Spoke, alongside the resources that call them.

See [`../diagrams/network-addressing.png`](../diagrams/network-addressing.png) for the full subnet and NSG map, and [`../diagrams/azure-network-topology-hub-spoke.png`](../diagrams/azure-network-topology-hub-spoke.png) for the end-to-end hub-and-spoke topology (ADR-007), including on-prem connectivity, hub shared services, and the DR region mirror.

### 4.2 Governance — Management Groups and Subscriptions

Landing zone structure isn't just a paragraph — it's a specific management group and subscription hierarchy, following the Cloud Adoption Framework's standard shape: a **Platform** management group holding the shared connectivity, identity, and management subscriptions every workload depends on, and a **Landing Zones** management group holding the actual workload subscriptions (production, non-production, and — specific to this case study's DR design — a dedicated DR subscription in the paired region). See [`../diagrams/landing-zone.png`](../diagrams/landing-zone.png).

## 5. Identity and Security

- Entra ID Conditional Access policies enforce MFA on every sign-in — no exceptions, closing the gap that let the March 2026 incident happen.
- Every PaaS service (APIM, App Service, Service Bus, SQL Managed Instance, Blob Storage) is reached through a **private endpoint** inside the spoke VNets, not the public internet.
- Azure Key Vault holds every credential and certificate; managed identities let App Service, Service Bus, and other components authenticate to Key Vault and to each other without embedded secrets — directly retiring the shared/generic service accounts named in the current-state assessment.
- Microsoft Defender for Cloud provides workload-level threat detection across the VM, database, and storage layers.
- Patients are a deliberately separate identity population from staff — see ADR-009. Extending the workforce Entra ID tenant to also hold ~2 million patient identities was considered and rejected; Microsoft Entra External ID keeps that consumer population out of the directory that governs clinical-system Conditional Access.

## 6. Integration — Azure Service Bus

HL7 and API events route through Service Bus topics, one per message category (lab results, imaging, e-prescribing, appointment events), each with its own subscriptions per consumer. Built-in dead-lettering means a failed or malformed message doesn't just disappear — a direct fix for the current LinkEngine's "if CareLink PM is down, the message is lost" behavior. Session support preserves message ordering where a downstream consumer needs it (e.g., a sequence of updates to the same patient record). The subscriber logic that actually reacts to these messages runs on Azure Functions, not the Citrix VM tier — see ADR-008 for why interactive session compute and background message processing are deliberately kept on separate, independently-scaling platforms.

## 7. Observability

Every component above ships logs and metrics to a single Log Analytics workspace. Microsoft Sentinel sits on top as the SIEM layer, giving Meridian's security team one place to query "what happened," instead of the current state's manual, multi-system forensic process. Azure Monitor alerts are tied to the same RTO/RPO-relevant signals (replication lag, failed sign-ins, Service Bus dead-letter queue depth) that matter operationally, not just infrastructure health.

## 8. Disaster Recovery Implementation

| Element | Azure Mechanism |
| --- | --- |
| Database replication | SQL Managed Instance auto-failover group — asynchronous, continuous, automatic read-only replica in the paired region |
| VM tier replication | Azure Site Recovery replicates the Citrix/CareLink PM VM tier to the secondary region |
| Storage replication | Blob Storage geo-redundant storage (GRS) |
| Failover trigger | Manual-initiated (ADR-004) — an operator promotes the failover group and triggers Azure Site Recovery failover through a documented runbook, not an automatic process |
| Traffic cutover | Azure Traffic Manager or Front Door, DNS-based |

This is the Azure-specific implementation of the warm-standby topology decided in ADR-004 — the strategy didn't change, only the tooling that realizes it.

## 9. Infrastructure as Code

Bicep is the primary IaC tool for this Azure implementation — Azure-native, first-class support for every resource type used above, and a cleaner authoring experience than raw ARM JSON. Terraform is reserved for the cross-platform comparison work in the decision-matrix stage, where one tool spanning all four candidate platforms matters more than native fluency on any single one.

## 10. Alignment Check

A quick gut-check against Microsoft's own Azure Well-Architected pillars, before moving on:

| Pillar | How this design addresses it |
| --- | --- |
| Reliability | Zone-redundant compute and database, paired-region warm standby, Service Bus dead-lettering |
| Security | Zero Trust via Entra Conditional Access + private endpoints everywhere, Key Vault-managed secrets, Sentinel-based detection |
| Cost Optimization | Deferred to the cost/risk analysis stage — sizing above is directional, not final |
| Operational Excellence | Landing zone pattern for repeatable clinic onboarding, centralized logging for a single operational view |
| Performance Efficiency | APIM and App Service scale independently of the CareLink PM VM tier, so a portal traffic spike doesn't compete with clinical scheduling load |

## 11. End-to-End Transaction Walkthrough

Every component in the service mapping and the deployment diagram exists because it does something in an actual data flow. The clearest way to prove that — and the way a design review actually gets scrutinized — is to trace one real transaction through every hop it touches, including what happens when it fails.

Scenario: a new lab result arrives from LabCorp for an existing patient.

1. LabCorp posts the HL7 v2 result to Azure API Management over mutual TLS with an API key. APIM validates the client certificate and key, applies a rate-limit policy, and publishes the message to a Service Bus topic (`lab-results`), using the patient ID as the session ID so results for the same patient stay ordered. APIM returns `202 Accepted` immediately — LabCorp doesn't wait on downstream processing.
2. On the happy path, the CareLink PM integration subscriber picks up the message, writes the structured result to the patient's record in SQL Managed Instance over a private endpoint, archives the raw HL7 payload to immutable Blob Storage, and completes the message.
3. On the failure path — for example, the patient ID doesn't match an existing record — the subscriber abandons the message. Service Bus retries up to a configured maximum delivery count, then moves it to the dead-letter queue and fires an alert to on-call, instead of silently dropping it. That dead-letter behavior is the direct fix for the current LinkEngine's "if CareLink PM is down, the message is lost" failure mode named in the current-state assessment.
4. Later, when a provider opens the patient's chart in CareLink PM, the query against SQL Managed Instance returns the record with the new result already in it — the write from step 2 and the read in step 4 are decoupled in time by design, which is what "event-driven" actually buys here.

Every hop above also ships logs and metrics to Azure Monitor and Log Analytics, which is what makes the dead-letter alert in step 3 possible in the first place. See [`../diagrams/sequence-lab-result.png`](../diagrams/sequence-lab-result.png) for the full sequence, including the alternate failure path.

## 12. Disaster Recovery Runbook

ADR-004 set the target: warm standby, manual-initiated failover, RTO ≤ 4 hours, RPO ≤ 15 minutes. Section 8 named the Azure mechanisms. What was still missing was proof that those mechanisms, run in the realistic order an on-call engineer would actually run them, fit inside the 4-hour budget — a DR design is only as credible as its runbook.

1. **T+0 to T+15 min** — Azure Monitor pages on-call; the engineer confirms the outage is real and declares a disaster per the documented runbook, rather than failing over on a single alert.
2. **T+15 to T+30 min** — the engineer triggers the SQL Managed Instance auto-failover group failover through the Azure Portal or CLI; the secondary replica promotes to primary and read/write resumes.
3. **T+30 to T+90 min**, run in parallel with database promotion — the engineer triggers Azure Site Recovery failover for the Citrix/CareLink PM VM tier; VMs boot in the secondary region and attach their replicated disks.
4. **T+90 to T+150 min** — before any traffic is cut over, the engineer runs smoke tests against the secondary region (authentication, database read/write, Service Bus connectivity) to confirm it's actually healthy, not just "up."
5. **T+150 to T+180 min** — the engineer re-points Azure Traffic Manager or Front Door to the secondary region endpoint; once DNS propagates, users are routed to the secondary region.

Total: **180 minutes actual against a 240-minute (4-hour) target** — a real margin, not a number picked to just barely clear the requirement. See [`../diagrams/dr-failover-runbook.png`](../diagrams/dr-failover-runbook.png).

## 13. CI/CD and Environment Promotion

Bicep (Section 9) is the authoring tool; this section is how a change actually reaches production. Every change flows through the same landing-zone subscriptions named in Section 4.2: `meridian-healthcare-nonprod` for Dev and Test/QA, `meridian-healthcare-prod` for production.

- **On every pull request**: `bicep lint` and `bicep build` catch syntax and type errors; PSRule for Azure checks the templates against security and Well-Architected rules; `az deployment what-if` runs against the target environment and posts the predicted resource changes directly on the PR, so a reviewer sees the actual diff, not just the code diff.
- **Human review**: the platform team reviews both the code and the what-if output before approving.
- **On merge to main**: the pipeline deploys to Dev automatically, runs automated smoke tests, then stops at a manual approval gate before Test/QA, and a second manual approval gate — paired with a change record — before production. Production deployment ends with a post-deploy validation pass and an Azure Policy compliance scan, not just a "deployment succeeded" status.

The two manual gates are deliberate, not a process gap: infrastructure changes to a clinical system's database or network tier are exactly the kind of change that should require a human decision immediately before it happens, the same reasoning behind DR failover being manual-initiated in ADR-004. See [`../diagrams/cicd-pipeline.png`](../diagrams/cicd-pipeline.png).

## 14. Explicitly Deferred

- Exact VM/database sizing and cost modeling — Step 13
- Final platform recommendation — Step 10, after AWS, GCP, and private-cloud implementations exist to compare against
- Detailed IAM role/permission definitions
- Terraform modules (built once, during the migration roadmap stage, for whichever platform is chosen)

## 15. Diagrams

- [`../diagrams/azure-deployment-architecture.png`](../diagrams/azure-deployment-architecture.png) / [`.drawio`](../diagrams/azure-deployment-architecture.drawio) — primary-region hub-and-spoke deployment view.
- [`../diagrams/azure-dr-view.png`](../diagrams/azure-dr-view.png) / [`.drawio`](../diagrams/azure-dr-view.drawio) — paired-region DR view with Azure-specific replication mechanisms.
- [`../diagrams/network-addressing.png`](../diagrams/network-addressing.png) / [`.dot`](../diagrams/network-addressing.dot) — subnet-level addressing plan, NSG rules, and forced-tunnel routing.
- [`../diagrams/landing-zone.png`](../diagrams/landing-zone.png) / [`.mmd`](../diagrams/landing-zone.mmd) — management group and subscription hierarchy.
- [`../diagrams/sequence-lab-result.png`](../diagrams/sequence-lab-result.png) / [`.mmd`](../diagrams/sequence-lab-result.mmd) — end-to-end transaction trace, happy path and dead-letter path.
- [`../diagrams/dr-failover-runbook.png`](../diagrams/dr-failover-runbook.png) / [`.mmd`](../diagrams/dr-failover-runbook.mmd) — DR failover runbook with an RTO time budget.
- [`../diagrams/cicd-pipeline.png`](../diagrams/cicd-pipeline.png) / [`.mmd`](../diagrams/cicd-pipeline.mmd) — IaC pipeline from pull request to production.
- [`../diagrams/carelink-pm-architecture.png`](../diagrams/carelink-pm-architecture.png) / [`.dot`](../diagrams/carelink-pm-architecture.dot) — CareLink PM hosting architecture (Cloud Connectors, Machine Catalog, SQL MI connectivity).
- [`../diagrams/portal-architecture.png`](../diagrams/portal-architecture.png) / [`.dot`](../diagrams/portal-architecture.dot) — MeridianConnect Portal hosting architecture (Front Door, App Service, dual identity providers).
- [`../diagrams/telehealth-architecture.png`](../diagrams/telehealth-architecture.png) / [`.dot`](../diagrams/telehealth-architecture.dot) — Telehealth integration architecture (SSO federation, appointment-sync webhook, no Meridian compute).
- [`../diagrams/linkengine-architecture.png`](../diagrams/linkengine-architecture.png) / [`.dot`](../diagrams/linkengine-architecture.dot) — LinkEngine message flow architecture (Service Bus topics, Azure Functions subscribers).

See [`application-architecture.md`](application-architecture.md) for the prose walkthrough of all four application-level diagrams above.
