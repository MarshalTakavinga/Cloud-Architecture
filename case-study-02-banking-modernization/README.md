# Case Study 2 of 6: Banking Modernization

**Scenario:** Palisade Financial Group (fictional, composite) – a super-regional bank holding company, ~$21B in assets, 84 branches across the Mid-Atlantic. Core deposits and loan servicing run on a 30-year-old COBOL/CICS mainframe; a real-time-payments mandate, rising mainframe cost, a regulatory resiliency mandate, and a real-time-payments fraud wave are forcing a deliberate decision about what moves off the mainframe and what stays.

**Angle:** Core banking/payments workload — strong security, resiliency, and regulatory-reporting angle — a natural fit for the mainframe workload-placement question.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs all **four** implementation tracks — Azure, AWS, GCP, and private cloud — because the central design question here is precisely *where the workload should run*, not just which hyperscaler is best. A bank with a 30-year mainframe investment and heightened regulatory scrutiny is exactly the profile where "stay on dedicated/private infrastructure for the core, extend to public cloud for the new capability" is a live, defensible option — so the private-cloud/VMware Cloud Foundation track is a first-class comparison, not an afterthought.

## Status

**Steps 1–9 of 13 complete.**

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md), [current-state architecture diagram](diagrams/current-state-architecture.png) |
| 2–3. Requirements and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-mainframe-integration-approach.md), [ADR-002](adr/ADR-002-payment-hub-build-vs-buy.md), [target-style diagram (Mermaid)](diagrams/target-architecture-style.md), [target-style diagram](diagrams/target-architecture-style.png) — 6-R disposition per component; mainframe integration approach (hybrid sync-hold + CDC); build-vs-buy for the payments rail/fraud/ledger-of-intent layer |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-003](adr/ADR-003-provisional-vs-confirmed-state-model.md), [ADR-004](adr/ADR-004-idempotency-and-exactly-once-delivery.md), [logical-architecture diagram (Mermaid)](diagrams/logical-architecture.md), [logical-architecture diagram](diagrams/logical-architecture.png) — logical component model, end-to-end payment data flow, provisional-vs-confirmed reconciliation model, idempotency/exactly-once approach |
| 6. Azure implementation | Done — [`docs/azure-implementation.md`](docs/azure-implementation.md), [ADR-005](adr/ADR-005-azure-compute-platform.md), [ADR-006](adr/ADR-006-azure-ledger-of-intent-database.md), [ADR-007](adr/ADR-007-azure-messaging.md), [ADR-008](adr/ADR-008-hybrid-connectivity.md), [ADR-009](adr/ADR-009-azure-identity.md), [ADR-010](adr/ADR-010-azure-landing-zone-and-segmentation.md), [Azure implementation diagram](diagrams/azure-implementation-architecture.png) — compute platform (Container Apps for the three real-time services + a Container Apps Job for nightly reconciliation), data store (Azure SQL + Ledger), messaging (Service Bus Premium/sessions), hybrid connectivity (ExpressRoute), identity (Entra ID + Managed Identities), landing zone/segmentation (hub-spoke) |
| 7. AWS implementation | Done — [`docs/aws-implementation.md`](docs/aws-implementation.md), [ADR-011](adr/ADR-011-aws-compute-platform.md), [ADR-012](adr/ADR-012-aws-ledger-of-intent-database.md), [ADR-013](adr/ADR-013-aws-messaging.md), [ADR-014](adr/ADR-014-aws-hybrid-connectivity.md), [ADR-015](adr/ADR-015-aws-identity.md), [ADR-016](adr/ADR-016-aws-landing-zone-and-segmentation.md) — compute platform (Fargate on ECS for the three real-time services + a scheduled Fargate task for nightly reconciliation), data store (Aurora PostgreSQL + S3 Object Lock archive), messaging (SNS FIFO + per-consumer SQS FIFO queues), hybrid connectivity (Direct Connect), identity (IAM Identity Center + AD Connector + IAM roles for tasks), landing zone (Control Tower multi-account Organization, enrolling the existing 2021 account rather than rebuilding it) |
| 8. GCP implementation | Done — [`docs/gcp-implementation.md`](docs/gcp-implementation.md), [ADR-017](adr/ADR-017-gcp-compute-platform.md), [ADR-018](adr/ADR-018-gcp-ledger-of-intent-database.md), [ADR-019](adr/ADR-019-gcp-messaging.md), [ADR-020](adr/ADR-020-gcp-hybrid-connectivity.md), [ADR-021](adr/ADR-021-gcp-identity.md), [ADR-022](adr/ADR-022-gcp-landing-zone-and-segmentation.md) — compute platform (Cloud Run for the three real-time services + a Cloud Run Job for nightly reconciliation), data store (Cloud SQL for PostgreSQL + Cloud Storage Bucket Lock archive), messaging (a single Pub/Sub topic with ordering keys and four subscriptions), hybrid connectivity (Dedicated Interconnect), identity (Workforce Identity Federation + Workload Identity), landing zone (Resource Manager folders/projects, Organization Policy, Security Command Center) |
| 9. Private-cloud implementation | Done — [`docs/private-cloud-implementation.md`](docs/private-cloud-implementation.md), [ADR-023](adr/ADR-023-private-cloud-platform-and-facility-strategy.md), [ADR-024](adr/ADR-024-private-cloud-compute-platform.md), [ADR-025](adr/ADR-025-private-cloud-database.md), [ADR-026](adr/ADR-026-private-cloud-network-topology.md), [ADR-027](adr/ADR-027-private-cloud-identity.md), [ADR-028](adr/ADR-028-private-cloud-messaging.md) — VMware Cloud Foundation built in Palisade's own existing primary + secondary data centers (no new facility needed), Tanzu Kubernetes Grid compute (the one track that can't avoid the Kubernetes-ops burden every hyperscaler track avoided), self-managed HA PostgreSQL, NSX micro-segmentation with zero hybrid-connectivity cost (same facility as the mainframe), direct on-prem AD join for identity, self-managed RabbitMQ for messaging |
| 10. Decision matrix | Not started |
| 11. Recommended platform / target architecture | Not started |
| 12. Migration roadmap and ADRs | Not started |
| 13. Cost and risk analysis | Not started |

## Repository Structure

```
case-study-02-banking-modernization/
│
├── README.md
├── docs/
│   ├── problem-statement.md               # business problem, 4 forcing functions, ranked drivers (done)
│   ├── current-state.md                   # existing mainframe + ad hoc digital/cloud estate, as-is (done)
│   ├── requirements.md                    # capabilities, NFRs, requirement/constraint/assumption/risk (done)
│   ├── architecture-options-and-styles.md # (Step 4) 6-R disposition, integration options, target style (done)
│   ├── logical-design.md                  # (Step 5) logical component model, data flow, ADR-003/ADR-004 (done)
│   ├── azure-implementation.md            # (Step 6) service mapping, ADR-005–ADR-010, network/security/observability (done)
│   ├── aws-implementation.md              # (Step 7) service mapping, ADR-011–ADR-016, network/security/observability (done)
│   ├── gcp-implementation.md              # (Step 8) service mapping, ADR-017–ADR-022, network/security/observability (done)
│   └── private-cloud-implementation.md    # (Step 9) service mapping, ADR-023–ADR-028, network/security/observability (done)
│
├── adr/
│   ├── ADR-001-mainframe-integration-approach.md         # hybrid sync-hold + CDC pattern (done)
│   ├── ADR-002-payment-hub-build-vs-buy.md               # buy the rail gateway, build fraud/ledger-of-intent (done)
│   ├── ADR-003-provisional-vs-confirmed-state-model.md   # reconciliation between real-time and batch state (done)
│   ├── ADR-004-idempotency-and-exactly-once-delivery.md  # end-to-end idempotency key, exactly-once posting (done)
│   ├── ADR-005-azure-compute-platform.md                 # Azure Container Apps for the three services + a Container Apps Job for nightly reconciliation (done)
│   ├── ADR-006-azure-ledger-of-intent-database.md        # Azure SQL Database + SQL Ledger + Blob archive (done)
│   ├── ADR-007-azure-messaging.md                        # Azure Service Bus Premium, sessions (done)
│   ├── ADR-008-hybrid-connectivity.md                    # ExpressRoute + VPN failover (done)
│   ├── ADR-009-azure-identity.md                         # Entra ID federation + Managed Identities (done)
│   ├── ADR-010-azure-landing-zone-and-segmentation.md    # hub-spoke landing zone, policy, Defender for Cloud (done)
│   ├── ADR-011-aws-compute-platform.md                   # Fargate on ECS for the three services + a scheduled task for nightly reconciliation (done)
│   ├── ADR-012-aws-ledger-of-intent-database.md          # Aurora PostgreSQL + S3 Object Lock archive (done)
│   ├── ADR-013-aws-messaging.md                          # SNS FIFO + per-consumer SQS FIFO queues (done)
│   ├── ADR-014-aws-hybrid-connectivity.md                # Direct Connect + VPN failover (done)
│   ├── ADR-015-aws-identity.md                           # IAM Identity Center + AD Connector + IAM roles for tasks (done)
│   ├── ADR-016-aws-landing-zone-and-segmentation.md      # Control Tower multi-account Organization, enrolling the 2021 account (done)
│   ├── ADR-017-gcp-compute-platform.md                   # Cloud Run for the three services + a Cloud Run Job for nightly reconciliation (done)
│   ├── ADR-018-gcp-ledger-of-intent-database.md          # Cloud SQL for PostgreSQL + Cloud Storage Bucket Lock archive (done)
│   ├── ADR-019-gcp-messaging.md                          # Pub/Sub, ordering keys, four subscriptions (done)
│   ├── ADR-020-gcp-hybrid-connectivity.md                # Dedicated Interconnect + Cloud VPN failover (done)
│   ├── ADR-021-gcp-identity.md                           # Workforce Identity Federation + Workload Identity (done)
│   ├── ADR-022-gcp-landing-zone-and-segmentation.md      # Resource Manager folders/projects, Org Policy, Security Command Center (done)
│   ├── ADR-023-private-cloud-platform-and-facility-strategy.md  # VMware Cloud Foundation in Palisade's existing data centers (done)
│   ├── ADR-024-private-cloud-compute-platform.md         # Tanzu Kubernetes Grid for the three services + a CronJob for reconciliation (done)
│   ├── ADR-025-private-cloud-database.md                 # Self-managed HA PostgreSQL (Patroni) (done)
│   ├── ADR-026-private-cloud-network-topology.md         # NSX micro-segmentation, no hybrid-connectivity circuit needed (done)
│   ├── ADR-027-private-cloud-identity.md                 # Direct on-prem AD join + mutual TLS via internal PKI (done)
│   └── ADR-028-private-cloud-messaging.md                # Self-managed RabbitMQ, Consistent Hash Exchange (done)
├── architecture/
│   ├── context/
│   ├── solution/
│   ├── network/
│   ├── security/
│   ├── data/
│   └── dr/
├── terraform/                     # IaC — not started, platform not yet chosen
└── diagrams/
    ├── target-architecture-style.md        # (Step 4) Mermaid target-style diagram, diagrams-as-code (done)
    ├── target-architecture-style.png       # (Step 4) target-style diagram, verified against docs (done)
    ├── logical-architecture.md             # (Step 5) Mermaid sequence diagram — end-to-end payment flow (done)
    ├── logical-architecture.png            # (Step 5) numbered swim-lane flow diagram, verified against docs (done)
    ├── current-state-architecture.png      # (Step 1) current-state deployment diagram, verified against docs/current-state.md (done)
    └── azure-implementation-architecture.png # (Step 6) deployment diagram — landing zone, spokes, services, verified against docs (done)
```
