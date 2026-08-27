# Case Study 2 of 6: Banking Modernization

**Scenario:** Palisade Financial Group (fictional, composite) – a super-regional bank holding company, ~$21B in assets, 84 branches across the Mid-Atlantic. Core deposits and loan servicing run on a 30-year-old COBOL/CICS mainframe; a real-time-payments mandate, rising mainframe cost, a regulatory resiliency mandate, and a real-time-payments fraud wave are forcing a deliberate decision about what moves off the mainframe and what stays.

**Angle:** Core banking/payments workload — strong security, resiliency, and regulatory-reporting angle — a natural fit for the mainframe workload-placement question.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs all **four** implementation tracks — Azure, AWS, GCP, and private cloud — because the central design question here is precisely *where the workload should run*, not just which hyperscaler is best. A bank with a 30-year mainframe investment and heightened regulatory scrutiny is exactly the profile where "stay on dedicated/private infrastructure for the core, extend to public cloud for the new capability" is a live, defensible option — so the private-cloud/VMware Cloud Foundation track is a first-class comparison, not an afterthought.

## Status

**Steps 1–6 of 13 complete.**

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md), [current-state architecture diagram](diagrams/current-state-architecture.png) |
| 2–3. Requirements and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-mainframe-integration-approach.md), [ADR-002](adr/ADR-002-payment-hub-build-vs-buy.md), [target-style diagram (Mermaid)](diagrams/target-architecture-style.md), [target-style diagram (hand-drawn)](diagrams/target-architecture-style.png) — 6-R disposition per component; mainframe integration approach (hybrid sync-hold + CDC); build-vs-buy for the payments rail/fraud/ledger-of-intent layer |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-003](adr/ADR-003-provisional-vs-confirmed-state-model.md), [ADR-004](adr/ADR-004-idempotency-and-exactly-once-delivery.md), [logical-architecture sequence diagram](diagrams/logical-architecture.md) — logical component model, end-to-end payment data flow, provisional-vs-confirmed reconciliation model, idempotency/exactly-once approach |
| 6. Azure implementation | Done — [`docs/azure-implementation.md`](docs/azure-implementation.md), [ADR-005](adr/ADR-005-azure-compute-platform.md), [ADR-006](adr/ADR-006-azure-ledger-of-intent-database.md), [ADR-007](adr/ADR-007-azure-messaging.md), [ADR-008](adr/ADR-008-hybrid-connectivity.md), [ADR-009](adr/ADR-009-azure-identity.md), [ADR-010](adr/ADR-010-azure-landing-zone-and-segmentation.md), [Azure implementation diagram](diagrams/azure-implementation-architecture.md) — compute platform (Container Apps), data store (Azure SQL + Ledger), messaging (Service Bus Premium/sessions), hybrid connectivity (ExpressRoute), identity (Entra ID + Managed Identities), landing zone/segmentation (hub-spoke) |
| 7. AWS implementation | Not started |
| 8. GCP implementation | Not started |
| 9. Private-cloud implementation | Not started |
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
│   └── azure-implementation.md            # (Step 6) service mapping, ADR-005–ADR-010, network/security/observability (done)
│
├── adr/
│   ├── ADR-001-mainframe-integration-approach.md         # hybrid sync-hold + CDC pattern (done)
│   ├── ADR-002-payment-hub-build-vs-buy.md               # buy the rail gateway, build fraud/ledger-of-intent (done)
│   ├── ADR-003-provisional-vs-confirmed-state-model.md   # reconciliation between real-time and batch state (done)
│   ├── ADR-004-idempotency-and-exactly-once-delivery.md  # end-to-end idempotency key, exactly-once posting (done)
│   ├── ADR-005-azure-compute-platform.md                 # Azure Container Apps for the three new services (done)
│   ├── ADR-006-azure-ledger-of-intent-database.md        # Azure SQL Database + SQL Ledger + Blob archive (done)
│   ├── ADR-007-azure-messaging.md                        # Azure Service Bus Premium, sessions (done)
│   ├── ADR-008-hybrid-connectivity.md                    # ExpressRoute + VPN failover (done)
│   ├── ADR-009-azure-identity.md                         # Entra ID federation + Managed Identities (done)
│   └── ADR-010-azure-landing-zone-and-segmentation.md    # hub-spoke landing zone, policy, Defender for Cloud (done)
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
    ├── target-architecture-style.png       # (Step 4) hand-drawn target-style diagram, verified against docs (done)
    ├── logical-architecture.md             # (Step 5) Mermaid sequence diagram — end-to-end payment flow (done)
    ├── current-state-architecture.png      # (Step 1) current-state deployment diagram, verified against docs/current-state.md (done)
    └── azure-implementation-architecture.md # (Step 6) Mermaid deployment diagram — landing zone, spokes, services (done)
```
