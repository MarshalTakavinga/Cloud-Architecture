# Case Study 3 of 6: Healthcare Platform — On-Premises to Cloud Migration

**Scenario:** Meridian Health Network (fictional, composite) — a regional health system with 46 sites and ~2 million patient records, running a single-site, out-of-support, on-premises appointment and practice-management platform. Strong HIPAA/compliance and HA/DR angle. One of six case studies in the [Cloud Architecture](../README.md) portfolio.

## Status

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| 2. Capabilities required | Captured within problem statement |
| 3. Requirements and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md), [current-state diagram](diagrams/current-state-architecture.png) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-migration-strategy-carelink-pm-core.md), [ADR-002](adr/ADR-002-target-style-owned-components.md), [migration strategy map](diagrams/Migration-Strategy-Map.xlsx), [detailed ADR-002 diagram](diagrams/target-architecture-style-detail.png) |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-003](adr/ADR-003-primary-database-technology.md), [ADR-004](adr/ADR-004-dr-strategy.md), [detailed logical design diagram](diagrams/logical-architecture-detail.png) (components, flows, HA/DR — earlier simpler diagrams superseded, kept for history) |
| 6. Azure implementation | In progress — [`docs/azure-implementation.md`](docs/azure-implementation.md), [`docs/application-architecture.md`](docs/application-architecture.md), ADR-005 through ADR-011, all sized ([ADR-005](adr/ADR-005-azure-compute-hosting-carelink-pm.md), [ADR-006](adr/ADR-006-azure-database-service.md), [ADR-008](adr/ADR-008-integration-processing-compute.md), [ADR-010](adr/ADR-010-azure-compute-hosting-portal.md), [ADR-011](adr/ADR-011-azure-messaging-platform.md)) — all core Azure resources now have concrete configuration, ready for final review before commit/push, 18 diagrams (platform + per-application, see `diagrams/`) |
| 7. AWS implementation | Next |
| 8. GCP implementation | Not started |
| 9. Private-cloud implementation | Not started |
| 10. Decision matrix | Not started |
| 11. Recommended platform / target architecture | Not started |
| 12. Migration roadmap and ADRs | Not started |
| 13. Cost and risk analysis | Not started |

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
│   └── application-architecture.md        # per-app hosting, DB connectivity, public/private, scaling/HA
│
├── adr/                         # architecture decision records — ADR-001 through ADR-011 so far
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
    ├── target-architecture-style.png/.drawio    # Step 4 target-style sketch
    ├── target-architecture-style-detail.png     # Step 4 detailed ADR-002 diagram, hand-reproduced
    ├── logical-architecture.png/.drawio         # Step 5 vendor-neutral component view (superseded, kept for history)
    ├── ha-dr-logical-view.png/.drawio           # Step 5 region/replication view (superseded, kept for history)
    ├── logical-architecture-detail.png          # Step 5 detailed logical design, hand-reproduced (current)
    ├── azure-deployment-architecture.png/.drawio # Step 6 hub-and-spoke deployment view
    ├── azure-dr-view.png/.drawio                 # Step 6 paired-region DR view
    ├── network-addressing.png/.dot               # Step 6 subnet/CIDR/NSG plan
    ├── landing-zone.png/.mmd                     # Step 6 management group/subscription hierarchy
    ├── sequence-lab-result.png/.mmd              # Step 6 end-to-end transaction trace
    ├── dr-failover-runbook.png/.mmd              # Step 6 DR runbook with RTO time budget
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
    └── servicebus-linkengine-messaging-architecture.png  # Step 6 Service Bus messaging detail incl. Geo-DR gap note (ADR-011), hand-reproduced
```
