# Case Study 3 of 6: Healthcare Platform — On-Premises to Cloud Migration

**Scenario:** Meridian Health Network (fictional, composite) — a regional health system with 46 sites and ~2 million patient records, running a single-site, out-of-support, on-premises appointment and practice-management platform. Strong HIPAA/compliance and HA/DR angle. One of six case studies in the [Cloud Architecture](../README.md) portfolio.

## Status

**All 13 steps of the case-study pipeline are complete.** Problem → requirements → vendor-neutral design → four honestly-compared platform implementations (Azure/AWS/GCP/private cloud) → weighted decision matrix → approved target platform (Azure) → phased migration roadmap → cost and risk analysis, each stage building on real artifacts from the one before it rather than restating conclusions.

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| 2. Capabilities required | Captured within problem statement |
| 3. Requirements and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md), [current-state diagram](diagrams/current-state-architecture.png) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-migration-strategy-carelink-pm-core.md), [ADR-002](adr/ADR-002-target-style-owned-components.md), [migration strategy map](diagrams/Migration-Strategy-Map.xlsx), [detailed ADR-002 diagram](diagrams/target-architecture-style-detail.png) |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-003](adr/ADR-003-primary-database-technology.md), [ADR-004](adr/ADR-004-dr-strategy.md), [detailed logical design diagram](diagrams/logical-architecture-detail.png) (components, flows, HA/DR — earlier simpler diagrams superseded, kept for history) |
| 6. Azure implementation | Done for this stage — [`docs/azure-implementation.md`](docs/azure-implementation.md), [`docs/application-architecture.md`](docs/application-architecture.md), ADR-005 through ADR-011, all sized ([ADR-005](adr/ADR-005-azure-compute-hosting-carelink-pm.md), [ADR-006](adr/ADR-006-azure-database-service.md), [ADR-008](adr/ADR-008-integration-processing-compute.md), [ADR-010](adr/ADR-010-azure-compute-hosting-portal.md), [ADR-011](adr/ADR-011-azure-messaging-platform.md)) — all core Azure resources sized, DR runbook accounts for the Service Bus Geo-DR in-flight-message gap, 18 diagrams (platform + per-application, see `diagrams/`). Known deferred items: Bicep IaC modules not yet built, cost analysis is Step 13 by design. |
| 7. AWS implementation | Done for this stage — [`docs/aws-implementation.md`](docs/aws-implementation.md), [`docs/application-architecture-aws.md`](docs/application-architecture-aws.md), ADR-012 through ADR-018 ([ADR-012](adr/ADR-012-aws-compute-hosting-carelink-pm.md), [ADR-013](adr/ADR-013-aws-database-service.md), [ADR-014](adr/ADR-014-aws-network-topology.md), [ADR-015](adr/ADR-015-aws-integration-processing-compute.md), [ADR-016](adr/ADR-016-aws-patient-identity.md), [ADR-017](adr/ADR-017-aws-compute-hosting-portal.md), [ADR-018](adr/ADR-018-aws-messaging-platform.md)) — mirrors the Azure implementation's rigor and reuses the same requirements.md/current-state.md sizing numbers, with two real platform-specific gaps documented rather than glossed over (RDS Custom's weaker cross-region DR vs. Azure SQL MI, and SNS/SQS's total lack of native cross-region replication vs. Service Bus Geo-DR). 10 diagrams (platform + per-application, see `diagrams/`). Known deferred items: CloudFormation/CDK IaC modules not yet built, cost analysis is Step 13 by design. |
| 8. GCP implementation | Done for this stage — [`docs/gcp-implementation.md`](docs/gcp-implementation.md), [`docs/application-architecture-gcp.md`](docs/application-architecture-gcp.md), ADR-019 through ADR-025 ([ADR-019](adr/ADR-019-gcp-compute-hosting-carelink-pm.md), [ADR-020](adr/ADR-020-gcp-database-service.md), [ADR-021](adr/ADR-021-gcp-network-topology.md), [ADR-022](adr/ADR-022-gcp-integration-processing-compute.md), [ADR-023](adr/ADR-023-gcp-patient-identity.md), [ADR-024](adr/ADR-024-gcp-compute-hosting-portal.md), [ADR-025](adr/ADR-025-gcp-messaging-platform.md)) — not a structural mirror of the Azure/AWS designs: reused where the underlying reasoning is genuinely platform-neutral (project/account split, DR topology), diverged where GCP's own primitives push toward a different answer (regional subnets, non-transitive VPC Peering pushing toward Network Connectivity Center, Pub/Sub's combined topic/queue model, Cloud Run's maturity relative to Container Apps/App Runner, no RDS-Custom-equivalent database tier). Real gaps and strengths named explicitly, both directions — see each ADR's Trade-off section. All 7 diagrams now done (CareLink PM hosting, SQL managed instance, network topology, LinkEngine functions hosting, patient identity, Portal hosting, and Pub/Sub messaging detail — see `diagrams/`), each checked against its ADR the same way every Azure/AWS diagram was. Known deferred items: Terraform modules not yet built, cost analysis is Step 13 by design. |
| 9. Private-cloud implementation | Done for this stage — [`docs/private-cloud-implementation.md`](docs/private-cloud-implementation.md), [`docs/application-architecture-private-cloud.md`](docs/application-architecture-private-cloud.md), ADR-026 through ADR-033 ([ADR-026](adr/ADR-026-private-cloud-platform-and-facility-strategy.md), [ADR-027](adr/ADR-027-private-cloud-compute-hosting-carelink-pm.md), [ADR-028](adr/ADR-028-private-cloud-database-service.md), [ADR-029](adr/ADR-029-private-cloud-network-topology.md), [ADR-030](adr/ADR-030-private-cloud-integration-processing-compute.md), [ADR-031](adr/ADR-031-private-cloud-patient-identity.md), [ADR-032](adr/ADR-032-private-cloud-compute-hosting-portal.md), [ADR-033](adr/ADR-033-private-cloud-messaging-platform.md)) — 8 ADRs, one more than every sibling platform, because private cloud needs an explicit, coupled platform-software-and-physical-facility decision (ADR-026: VMware Cloud Foundation across two colocation facilities, chosen deliberately over OpenStack/Nutanix as the smallest real operational-skill jump given Meridian's existing vSphere estate and staff skills) the hyperscaler tracks never had to make. Not a structural mirror of the Azure/AWS/GCP designs: reused where the reasoning is genuinely platform-neutral (migration strategy, DR topology, database engine family), diverged sharply where private cloud has no managed-service menu at all — self-managed SQL Server Always On (ADR-028) and self-managed RabbitMQ (ADR-033) are both named as real, heavy operational burdens carried back onto Meridian's own team, while a hybrid-identity bridge becomes unnecessary (ADR-031) and NSX microsegmentation comes bundled with the platform (ADR-029) rather than paid for separately — real gaps and real strengths named explicitly, both directions, mirroring the honesty standard set by the GCP track. 2 of 8 planned diagrams done (network addressing, facility/Workload Domain landing zone — see `diagrams/`); the remaining 6 hand-reproduced detail diagrams are not yet built. Known deferred items: Terraform/Ansible modules not yet built, SIEM/CDN-WAF/CIAM vendor selection deferred (decision made in principle, specific product not chosen), cost analysis is Step 13 by design. |
| 10. Decision matrix | Done — [`docs/decision-matrix.md`](docs/decision-matrix.md) — 9 Meridian-specific criteria (weighted, not the generic reference-guide example) scored across all four tracks, sourced from every named trade-off/gap in the Azure/AWS/GCP/private-cloud implementation docs and ADRs. Azure leads clearly (4.50/5.00), AWS edges GCP narrowly (3.30 vs. 3.20), private cloud trails (2.85), driven mainly by the 20%-weighted operational-burden criterion. Includes a sensitivity check reweighting toward regulatory fit/data control — Azure's lead holds, but AWS/GCP/private cloud's ordering below it is weight-sensitive (private cloud nearly closes the gap; AWS and GCP land in an exact tie). No recommendation made — that's Step 11; no cost figures — that's Step 13. |
| 11. Recommended platform / target architecture | Done — [`docs/target-architecture.md`](docs/target-architecture.md), [ADR-034](adr/ADR-034-target-platform-selection.md) — **Microsoft Azure selected**, driven primarily by the operational-burden requirement (Azure is the only track with no self-managed database or messaging tier) and the MFA/Conditional-Access requirement tied to the March 2026 credential-compromise incident (Azure is the only platform with native Conditional Access; the other three each need a follow-on third-party CASB purchase to fully close that gap). ADR-001 through ADR-011 (platform-neutral + Azure) flipped to Approved; ADR-012 through ADR-033 (AWS/GCP/private cloud) marked Superseded by ADR-034 and retained in full as the documented rejected alternatives, not deleted. Trade-offs accepted explicitly, not hidden: Azure does not lead on existing-skills fit, data-services maturity, regulatory/data-control fit, or portability. |
| 12. Migration roadmap and ADRs | Done — [`docs/migration-roadmap.md`](docs/migration-roadmap.md), [ADR-035](adr/ADR-035-migration-sequencing-model.md), [ADR-036](adr/ADR-036-rollback-and-dual-run-strategy.md), [ADR-037](adr/ADR-037-compliance-quick-wins-decoupling.md), [wave-timeline diagram](diagrams/migration-roadmap.png). Key structural insight (ADR-035): CareLink PM is one shared database/integration-bus/portal instance across all 46 sites, not 46 independent ones, so the database/LinkEngine/Portal/Telehealth cut over **once** (Wave 1) and only the per-site Citrix compute/session-routing layer phases across Waves 2–9 (2 pilot clinics → batches of 6–10 → 3 urgent care → 1 ASC, sequenced by risk, not alphabetically). Per-wave rollback (ADR-036) is routing-only after Wave 1, so it costs almost nothing to maintain. ADR-037 decouples the cyber-insurer's 4 renewal conditions from the full ~13-month rollout — MFA, encryption, and immutable backup are quick wins landed in Wave 0 (weeks), and a live DR test happens right after Wave 1 stabilizes, not at the end of the program. 9 acquired clinics onboard directly onto the finished platform in parallel, never touching legacy infrastructure. |
| 13. Cost and risk analysis | Done — [`docs/cost-and-risk-analysis.md`](docs/cost-and-risk-analysis.md), [`finance/TCO-Analysis.xlsx`](finance/TCO-Analysis.xlsx) (5 linked sheets, live formulas, zero recalc errors), [ADR-038](adr/ADR-038-finops-commitment-strategy.md). Honest result, not a "cloud is cheaper" story: migrating costs more than staying on-prem for the full 3–5 year window (cumulative delta narrows from +$754K in Year 1 to +$216K by Year 5), crossing over to favor Azure only around Year 6–7. The business case rests on `problem-statement.md`'s actual driver order — compliance/resilience/growth, not cost — not on infrastructure savings. Largest run-rate line: Entra ID P2 at $464K/year (46% of steady-state spend), flagged for a licensing-inventory check. 12-item risk register consolidates every risk named across Steps 1–12. **This closes the 13-step pipeline.** |

## Repository Structure

```
case-study-03-healthcare-platform/
│
├── README.md
├── docs/
│   ├── current-state.md                   # on-prem architecture, as-is
│   ├── problem-statement.md               # business problem, drivers, stakeholders
│   ├── requirements.md                    # NFRs, requirement/constraint/assumption/risk
│   ├── architecture-options-and-styles.md # 6-R migration strategy + target style options
│   ├── logical-design.md                  # vendor-neutral logical architecture + HA/DR view
│   ├── azure-implementation.md            # Azure service mapping, network, security, DR, IaC
│   ├── application-architecture.md        # per-app hosting, DB connectivity, public/private, scaling/HA (Azure)
│   ├── aws-implementation.md              # AWS service mapping, network, security, DR, IaC
│   ├── application-architecture-aws.md    # per-app hosting, DB connectivity, public/private, scaling/HA (AWS)
│   ├── gcp-implementation.md               # GCP service mapping, network, security, DR, IaC
│   ├── application-architecture-gcp.md     # per-app hosting, DB connectivity, public/private, scaling/HA (GCP)
│   ├── private-cloud-implementation.md              # VCF platform/facility, service mapping, network, security, DR, IaC
│   ├── application-architecture-private-cloud.md    # per-app hosting, DB connectivity, public/private, scaling/HA (private cloud)
│   ├── decision-matrix.md                 # Step 10 weighted vendor-neutral scoring of all four platform tracks
│   ├── target-architecture.md             # Step 11 recommended platform (Azure) and target architecture summary
│   ├── migration-roadmap.md               # Step 12 phased 46-site migration plan, rollback strategy, compliance quick-wins
│   └── cost-and-risk-analysis.md          # Step 13 3-5yr TCO comparison, methodology, and consolidated risk register
│
├── finance/
│   ├── TCO-Analysis.xlsx        # Step 13 cost model: Assumptions, AzureRunRate, OnPremBaseline, MigrationYr1, TCOSummary (live formulas + chart)
│   └── build_tco.py             # script that generates TCO-Analysis.xlsx — re-run after editing assumptions
│
├── adr/                         # architecture decision records — ADR-001 through ADR-038 (ADR-001–011 Approved, ADR-012–033 Superseded by ADR-034, ADR-034–038 Approved)
├── architecture/
│   ├── context/                 # executive context view
│   ├── solution/                # solution / physical deployment
│   ├── network/                 # network architecture
│   ├── security/                # security architecture
│   ├── data/                    # data architecture
│   └── dr/                      # HA/DR architecture
├── terraform/                   # IaC (populated once a platform is chosen)
└── diagrams/
    ├── current-state-architecture.png   # Current-state diagram, hand-reproduced, verified against docs/current-state.md
    ├── Migration-Strategy-Map.xlsx      # color-coded 6-R migration strategy map
    ├── target-architecture-style-detail.png     # Step 4 detailed ADR-002 diagram, hand-reproduced (current — earlier simple sketch removed)
    ├── logical-architecture.png/.drawio         # Step 5 vendor-neutral component view (superseded, kept for history)
    ├── ha-dr-logical-view.png/.drawio           # Step 5 region/replication view (superseded, kept for history)
    ├── logical-architecture-detail.png          # Step 5 detailed logical design, hand-reproduced (current)
    ├── azure-deployment-architecture.png/.drawio # Step 6 hub-and-spoke deployment view
    ├── azure-dr-view.png/.drawio                 # Step 6 paired-region DR view
    ├── network-addressing.png/.dot               # Step 6 subnet/CIDR/NSG plan
    ├── landing-zone.png/.mmd                     # Step 6 management group/subscription hierarchy
    ├── sequence-lab-result.png/.mmd              # Step 6 end-to-end transaction trace
    ├── dr-failover-runbook.png/.mmd              # Step 6 DR runbook with RTO time budget, incl. Service Bus Geo-DR alias failover + reconciliation step
    ├── cicd-pipeline.png/.mmd                    # Step 6 IaC deployment pipeline
    ├── carelink-pm-architecture.png/.dot         # Step 6 CareLink PM hosting architecture
    ├── portal-architecture.png/.dot              # Step 6 Portal hosting architecture
    ├── telehealth-architecture.png/.dot          # Step 6 Telehealth integration architecture
    ├── linkengine-architecture.png/.dot          # Step 6 LinkEngine message flow architecture
    ├── azure-network-topology-hub-spoke.png      # Step 6 network topology (ADR-007), hand-reproduced, addressing verified against network-addressing.dot incl. snet-func-linkengine (ADR-008) and snet-cloud-connectors (ADR-005)
    ├── sql-managed-instance-architecture.png     # Step 6 SQL MI zone/DR/network detail (ADR-006), hand-reproduced
    ├── carelink-pm-hosting-architecture.png      # Step 6 CareLink PM sizing/hosting detail (ADR-005), hand-reproduced
    ├── linkengine-functions-hosting-architecture.png  # Step 6 LinkEngine Functions sizing/hosting detail (ADR-008), hand-reproduced
    ├── patient-identity-architecture.png          # Step 6 two-tenant identity architecture (ADR-009), hand-reproduced
    ├── portal-hosting-architecture.png            # Step 6 Portal sizing/hosting detail incl. Front Door (ADR-010), hand-reproduced
    ├── servicebus-linkengine-messaging-architecture.png  # Step 6 Service Bus messaging detail incl. Geo-DR gap note (ADR-011), hand-reproduced
    ├── aws-deployment-architecture.png            # Step 7 consolidated one-page AWS overview, hand-corrected (2 review rounds)
    ├── aws-network-addressing.png/.dot            # Step 7 VPC/subnet/CIDR/security-group plan
    ├── aws-landing-zone.png/.mmd                  # Step 7 AWS Organizations OU/account hierarchy (8 workload/network accounts)
    ├── aws-network-topology-hub-spoke.png         # Step 7 network topology detail (ADR-014), hand-reproduced, account/VPC layout across both regions
    ├── carelink-pm-hosting-architecture-aws.png   # Step 7 CareLink PM sizing/hosting detail (ADR-012), hand-reproduced
    ├── sql-managed-instance-architecture-aws.png  # Step 7 RDS Custom zone/DR/network detail (ADR-013), hand-reproduced
    ├── linkengine-functions-hosting-architecture-aws.png  # Step 7 LinkEngine Lambda sizing/hosting detail (ADR-015), hand-reproduced
    ├── patient-identity-architecture-aws.png      # Step 7 two-identity-provider architecture (ADR-016), hand-reproduced, incl. IAM Identity Center SSO hop and private-path RDS access (2 review rounds)
    ├── portal-hosting-architecture-aws.png        # Step 7 Portal sizing/hosting detail incl. CloudFront (ADR-017), hand-reproduced
    ├── sns-sqs-linkengine-messaging-architecture-aws.png  # Step 7 SNS/SQS messaging detail incl. Publish Function ingest path (ADR-018), hand-reproduced
    ├── carelink-pm-hosting-architecture-gcp.png   # Step 8 CareLink PM sizing/hosting detail (ADR-019), hand-reproduced
    ├── sql-managed-instance-architecture-gcp.png  # Step 8 Cloud SQL for SQL Server zone/DR/network detail (ADR-020), hand-reproduced
    ├── gcp-network-architecture.png               # Step 8 NCC hub-and-spoke network topology detail (ADR-021), hand-reproduced, project/CIDR/subnet structure across primary + DR
    ├── linkengine-functions-hosting-architecture-gcp.png  # Step 8 LinkEngine message flow and VPC placement detail (ADR-022), hand-reproduced
    ├── patient-identity-architecture-gcp.png      # Step 8 patient sign-in flow and separate-population identity architecture detail (ADR-023), hand-reproduced
    ├── portal-hosting-architecture-gcp.png        # Step 8 Portal public entry/protection flow and private data path detail (ADR-024), hand-reproduced
    ├── pubsub-linkengine-messaging-architecture-gcp.png  # Step 8 end-to-end message flow, Pub/Sub fabric, and DR approach detail (ADR-025), hand-reproduced
    ├── private-cloud-network-addressing.dot/.png  # Step 9 NSX Tier-0/Tier-1 segment addressing plan (ADR-029), primary facility + DR facility mirror
    ├── private-cloud-landing-zone.mmd/.png        # Step 9 VCF Workload Domain hierarchy across both colocation facilities (ADR-026)
    └── migration-roadmap.mmd/.png                 # Step 12 wave timeline: Foundation -> Central Services -> compute waves -> Urgent Care -> ASC -> Decommission, plus the parallel acquired-clinic onboarding workstream (ADR-035/036/037)
```
