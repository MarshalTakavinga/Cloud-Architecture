# Step 11: Recommended Platform and Target Architecture

## Confirmed Platform

**Microsoft Azure**, per [ADR-029](../adr/ADR-029-cloud-platform-selection.md) (85.0% weighted score, the highest of the four tracks evaluated in [Step 10](decision-matrix.md)). This step restates the target architecture at a glance and traces each of the four forcing functions from `problem-statement.md` to the specific mechanism that closes it. It does not re-litigate the platform choice — that work is done — nor does it re-specify anything already fixed at ADR depth in [Step 6](azure-implementation.md).

## Target Architecture at a Glance

The new real-time payment layer runs entirely on Azure, integrated with Palisade's unmodified mainframe via exactly one synchronous call and one change-data-capture feed ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)):

- **Compute:** Azure Container Apps hosts the Hold/Release Adapter, Fraud Orchestration Service, and Ledger-of-Intent Service (application tier) as three always-on container apps; the nightly Reconciliation Process runs as a Container Apps Job in the same environment ([ADR-005](../adr/ADR-005-azure-compute-platform.md)).
- **Data:** Azure SQL Database, with the SQL Ledger feature enabled for cryptographic audit immutability, serves both the Ledger-of-Intent store and the Audit/Compliance Log, with long-term archive to immutable (WORM) Blob Storage for the full 7-year NFR-7 window ([ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md)).
- **Messaging:** Azure Service Bus, Premium tier with sessions enabled, carries every event after the synchronous hold call, keyed by each payment's end-to-end ID for guaranteed per-payment ordering ([ADR-007](../adr/ADR-007-azure-messaging.md)).
- **Hybrid connectivity:** Azure ExpressRoute, with a site-to-site VPN as automatic failover, connects the Azure landing zone to Palisade's data center for the hold/release call and the CDC feed ([ADR-008](../adr/ADR-008-hybrid-connectivity.md)).
- **Identity:** Microsoft Entra ID, federated to Palisade's existing on-premises Active Directory, handles workforce access; Managed Identities handle every service-to-service call, with no stored credential anywhere ([ADR-009](../adr/ADR-009-azure-identity.md)).
- **Landing zone:** A hub-spoke Azure Landing Zone, with Azure Policy and Microsoft Defender for Cloud as guardrails, hosts the new payment-processing spoke and a second, separately governed spoke for the migrated 2021 AWS-equivalent workloads ([ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md)).

## Tracing Each Forcing Function to the Mechanism That Closes It

1. **Real-time payments has moved from roadmap to competitive necessity (driver 1, the 18-month board-committed deadline).** Closed by the ISO 20022/FedNow Gateway (bought, [ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md)) feeding the Hold/Release Adapter and Ledger-of-Intent Service on Container Apps — a payment initiated at 2pm on a Tuesday now posts (provisionally) within NFR-3's 5-second budget, not in the next overnight batch window, while the mainframe's batch settlement continues unmodified.
2. **Mainframe cost rising faster than the workload it serves (driver 3).** Closed structurally, not just financially: every unit of net-new real-time payment volume runs on Container Apps and Azure SQL Database, entirely off MIPS-billed mainframe capacity. The CDC Connector is a read-only tap on the DB2 transaction log ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)) — it adds no mainframe CPU load proportional to real-time volume, directly satisfying NFR-9's "net-new growth must not add proportional MIPS cost" target.
3. **A new regulatory resiliency bar the current DR posture cannot meet (driver 2).** Closed by Azure SQL Database's regional HA failover (well inside NFR-1's 2-hour RTO and NFR-2's 15-minute RPO) and the SQL Ledger feature's cryptographic audit trail, archived to immutable Blob Storage for the full NFR-7 7-year window ([ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md)) — replacing the current 36-hour, largely manual failover runbook with an automated, sub-NFR-target mechanism.
4. **Real-time payments fraud arrived ahead of real-time payments defenses (driver 4).** Closed by the Fraud Orchestration Service running on Container Apps with a minimum replica count of 2, specifically to avoid the cold-start risk that would otherwise threaten NFR-4's 300ms scoring budget ([ADR-005](../adr/ADR-005-azure-compute-platform.md)) — replacing the current batch-scored, hours-after-settlement fraud stack for the real-time-payments path specifically.

## What This Step Carries Forward, Not Resolves

Consistent with this case study's own discipline of naming open items rather than treating a decision as closing them: this step confirms *which* platform, not that every remaining question is answered.

- **US-cutover and rollout planning** — how the 18-month timeline actually sequences (this is [Step 12](migration-roadmap.md)'s job, not this one's).
- **Sizing and cost modeling** — exact Container Apps replica counts, Azure SQL Database service tier, and Service Bus messaging-unit provisioning remain a [Step 13](cost-and-risk-analysis.md) exercise, as every implementation-step ADR in this case study has consistently flagged.
- **IaC templates** — Bicep modules for this landing zone and its workloads are not yet built (`terraform/` and any future `bicep/` directory remain empty pending Step 12).
- **The 2021 AWS account's migration into Azure's second landing-zone spoke** — confirmed as in-scope now that Azure is selected ([ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md), [ADR-029](../adr/ADR-029-cloud-platform-selection.md)), but the actual migration mechanics are a [Step 12](migration-roadmap.md) item.
- **The specific CICS transaction** exposed for the [ADR-001](../adr/ADR-001-mainframe-integration-approach.md) hold/release call remains an outstanding mainframe-team decision, unresolved since Step 4 and unresolved here.
