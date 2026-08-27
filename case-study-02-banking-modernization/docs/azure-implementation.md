# Step 6: Azure Implementation

## Purpose of This Step

[Step 5](logical-design.md) defined nine logical components and their contracts without naming a single platform service. This step answers, for Azure specifically: what does each of those components actually run on, what does the network and identity model look like, and what decisions were forced by Azure's own service boundaries? Steps 7–9 will ask the same questions independently for AWS, GCP, and private cloud — none of those tracks are allowed to simply copy this one's answers, and where a later track's answer differs for a genuinely platform-native reason, that's the point of running all four.

## Service Mapping

| Logical Component (Step 5) | Azure Service | Decision Recorded In |
|---|---|---|
| ISO 20022/FedNow Gateway (bought, ADR-002) | Deployed as a vendor appliance/SaaS integration, connecting into the landing zone via private networking | [ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md) |
| Hold/Release Adapter | Azure Container Apps | [ADR-005](../adr/ADR-005-azure-compute-platform.md) |
| Fraud Orchestration Service | Azure Container Apps | [ADR-005](../adr/ADR-005-azure-compute-platform.md) |
| Ledger-of-Intent Service (application) | Azure Container Apps | [ADR-005](../adr/ADR-005-azure-compute-platform.md) |
| Ledger-of-Intent Service (data store) | Azure SQL Database | [ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md) |
| Event Bus | Azure Service Bus (Premium, sessions enabled) | [ADR-007](../adr/ADR-007-azure-messaging.md) |
| CDC Connector / Hold-Release path to the mainframe | Azure ExpressRoute (VPN as backup) | [ADR-008](../adr/ADR-008-hybrid-connectivity.md) |
| Identity (workforce + workload) | Microsoft Entra ID, federated to Palisade's on-prem Active Directory; Managed Identities for service-to-service auth | [ADR-009](../adr/ADR-009-azure-identity.md) |
| Landing zone / network segmentation | Azure Landing Zone (hub-spoke), private endpoints, Azure Policy, Microsoft Defender for Cloud | [ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md) |
| Audit/Compliance Log | Azure SQL Database (append-only table, immutability via Azure SQL Ledger feature) with long-term archive to Azure Blob Storage (immutable/WORM policy) for the 7-year NFR-7 retention | [ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md) |
| 2021 AWS account workloads (Replatform, Step 4) | Migrated into this same landing zone as Azure Container Apps + Azure Notification Hubs, under the governance this step establishes | [ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md) |

## Why Five Decisions, Not Eight

Case Study 1's per-platform tracks each carried 8 ADRs because that case study had multiple independent customer-facing services (storefront, catalog, checkout, orchestration) each needing its own compute/database choice. This case study's new-build layer is smaller and more uniform — three services (Hold/Release Adapter, Fraud Orchestration, Ledger-of-Intent) share one compute platform, and there is exactly one new data store, not several. What this track adds instead is the hybrid-connectivity decision ([ADR-008](../adr/ADR-008-hybrid-connectivity.md)), which Case Study 1 never needed at all — Solstice was already fully cloud-native. That difference is itself a real signal of how this case study's architecture differs in kind, not just in scenario.

## Network and Security Summary

- **Segmentation:** A dedicated spoke virtual network hosts the new payment-processing workloads, connected to Palisade's on-premises data center via ExpressRoute ([ADR-008](../adr/ADR-008-hybrid-connectivity.md)) through a hub VNet. The 2021 AWS-equivalent workloads land in a separate spoke once migrated, kept segmented from the payment-processing spoke per the landing zone's policy ([ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md)).
- **Private connectivity to PaaS:** Azure SQL Database and Azure Service Bus are reached only via private endpoints inside the spoke VNet — nothing in this architecture accepts traffic over the public internet.
- **Identity:** Human access is federated through Entra ID to Palisade's existing on-prem Active Directory (no second identity system to administer); every service-to-service call (Container Apps → Service Bus, Container Apps → SQL) uses a Managed Identity, so no connection string or credential is stored in application configuration.
- **Governance guardrails:** Azure Policy enforces the private-endpoint-only rule, the approved region (US-only, satisfying NFR-6), and mandatory diagnostic logging on every resource; Microsoft Defender for Cloud provides continuous posture assessment across the landing zone.

## Observability

Every Container Apps service, the Service Bus namespace, and Azure SQL Database emit diagnostic logs and metrics to a single Log Analytics workspace scoped to this landing zone. This is also where the Audit/Compliance Log's application-level event stream is queried from for exam and BSA/AML purposes — infrastructure telemetry and business-event audit trail live in the same observability platform, which is deliberate: an OCC examiner asking "show me everything that happened to payment X" should not require correlating two separate systems.

## Known Deferred Items

Consistent with how Case Study 1 tracked its own deferred work: Bicep IaC modules for this landing zone and its workloads are not yet built (`terraform/` remains empty pending the Step 10 platform decision, per this case study's convention of not building IaC for a platform that might not be selected); detailed sizing (Container Apps replica counts, Azure SQL Database service tier) is deferred to Step 13's cost analysis; and the specific CICS transaction exposed for the ADR-001 hold/release call is a mainframe-team decision still outstanding, noted originally in ADR-001 and unresolved here as well.
