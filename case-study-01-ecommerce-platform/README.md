# Case Study 1 of 6: Global E-Commerce Platform

**Scenario:** Solstice Retail Group (fictional, composite) — a mid-market DTC apparel/home-goods retailer, ~$310M revenue, expanding from US/Canada into the UK, Germany, France, Australia, and Singapore. Strong seasonal-elasticity, global-latency, and cost-optimization angle. One of six case studies in the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study compares **Azure, AWS, and GCP** — no private-cloud track. Solstice is already cloud-native (a single-region AWS deployment since 2019), and a physical-facility alternative doesn't fit a workload whose entire premise is elastic, bursty demand; three hyperscalers is the right comparison set, not four. Full implementation depth per platform and a full migration roadmap, matching Case Study 3's rigor.

## Status

**Steps 1–6 of 12 are complete.** Business case, current state, requirements, architecture options/styles, vendor-neutral logical design, and the Azure implementation (docs + ADRs + diagram) are done. Steps 7–12 (AWS/GCP implementations through cost/risk analysis) are not yet started.

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md), [current-state diagram](diagrams/current-state-architecture.png) |
| 2–3. Requirements and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-modernization-strategy-sce-components.md), [ADR-002](adr/ADR-002-target-architecture-style.md), [target-style diagram](diagrams/target-architecture-style.png) |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-003](adr/ADR-003-multi-region-data-topology.md), [ADR-004](adr/ADR-004-payment-tokenization-approach.md), [logical architecture diagram](diagrams/logical-architecture.png), [multi-region data topology diagram](diagrams/multi-region-data-topology.png), [payment tokenization approach diagram](diagrams/payment-tokenization-approach.png) |
| 6. Azure implementation | Done — [`docs/azure-implementation.md`](docs/azure-implementation.md), [`docs/application-architecture.md`](docs/application-architecture.md), [Azure implementation architecture diagram](diagrams/azure-implementation-architecture.png), ADR-005 through ADR-012 ([ADR-005](adr/ADR-005-azure-compute-customer-facing-services.md) compute/customer-facing, [ADR-006](adr/ADR-006-azure-database-regional-transactional-store.md) database/transactional, [ADR-007](adr/ADR-007-azure-database-global-catalog.md) database/catalog, [ADR-008](adr/ADR-008-azure-compute-order-orchestration.md) compute/orchestration, [ADR-009](adr/ADR-009-azure-messaging-event-bus.md) messaging, [ADR-010](adr/ADR-010-azure-customer-identity.md) identity, [ADR-011](adr/ADR-011-azure-network-topology.md) network, [ADR-012](adr/ADR-012-azure-global-entry-cdn-api-gateway.md) CDN/API gateway) — kept deliberately on the same PostgreSQL engine Solstice runs today (no unscoped database migration), Azure Container Apps chosen over AKS/App Service specifically for KEDA's fast reaction to the 20–25x/single-digit-minute traffic ramps this case study exists to survive, and Checkout & Payment given its own dedicated compute environment and subnet as the structural implementation of its PCI isolation boundary. Known deferred items: Bicep IaC modules not yet built, cost analysis is Step 12 by design. |
| 7. AWS implementation | Not started |
| 8. GCP implementation | Not started |
| 9. Decision matrix (Azure / AWS / GCP) | Not started |
| 10. Recommended platform / target architecture | Not started |
| 11. Migration roadmap and ADRs | Not started |
| 12. Cost and risk analysis | Not started |

## Repository Structure

```
case-study-01-ecommerce-platform/
│
├── README.md
├── docs/
│   ├── problem-statement.md               # business problem, 4 forcing functions, ranked drivers
│   ├── current-state.md                   # existing single-region AWS deployment, as-is
│   ├── requirements.md                    # NFRs, requirement/constraint/assumption/risk
│   ├── architecture-options-and-styles.md # (Step 4) 6-R strategy per component + target style
│   ├── logical-design.md                  # (Step 5) vendor-neutral logical architecture
│   ├── azure-implementation.md            # (Step 6) Azure service mapping, network, security, observability, IaC
│   ├── application-architecture.md        # (Step 6) per-service hosting, connectivity, public/private, scaling/HA (Azure)
│   ├── aws-implementation.md              # (Step 7) AWS service mapping, network, security, DR, IaC
│   ├── gcp-implementation.md              # (Step 8) GCP service mapping, network, security, DR, IaC
│   ├── decision-matrix.md                 # (Step 9) weighted vendor-neutral scoring of all three platform tracks
│   ├── target-architecture.md             # (Step 10) recommended platform and target architecture summary
│   ├── migration-roadmap.md               # (Step 11) phased migration plan, rollback strategy
│   └── cost-and-risk-analysis.md          # (Step 12) 3-5yr TCO comparison and consolidated risk register
│
├── adr/                          # architecture decision records — ADR-001 through ADR-012 so far (own numbering, separate from Case Study 3)
├── architecture/
│   ├── context/                  # executive context view
│   ├── solution/                 # solution / physical deployment
│   ├── network/                  # network architecture
│   ├── security/                 # security architecture
│   └── data/                     # data architecture
├── terraform/                    # IaC (populated once a platform is chosen)
└── diagrams/
    ├── current-state-architecture.png       # Current-state deployment diagram, hand-drawn, verified against docs/current-state.md across 3 review rounds
    ├── target-architecture-style.png        # Step 4 target-style diagram (ADR-001/ADR-002), hand-drawn, checked against both ADRs
    ├── logical-architecture.png             # Step 5 vendor-neutral logical design diagram (component/flow view, ADR-003/ADR-004)
    ├── multi-region-data-topology.png       # Step 5 ADR-003 detail diagram (catalog single-writer/multi-region-read topology + regional-primary transactional stores), checked against ADR-003 across 2 review rounds
    ├── payment-tokenization-approach.png    # Step 5 ADR-004 detail diagram (server-side/hybrid/client-side options as data flows), checked against ADR-004
    ├── azure-implementation-architecture.png # Step 6 Azure implementation diagram (global entry, per-region compute/data/integration/network, Global Catalog topology, Virtual WAN), checked against azure-implementation.md and ADR-005–ADR-012
    ├── adr-006-database-service.png         # Step 6 ADR-006 detail diagram (per-region Flexible Server primary, no cross-region replication, proposed-configuration table), checked against ADR-006 across several review rounds
    └── adr-007-database-service.png         # Step 6 ADR-007 detail diagram (single-writer US primary, async read replicas in EU/APAC, per-region Redis read-through cache, proposed-configuration table), checked against ADR-007
```
