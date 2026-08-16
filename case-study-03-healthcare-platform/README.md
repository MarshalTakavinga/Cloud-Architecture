# Case Study 3 of 6: Healthcare Platform — On-Premises to Cloud Migration

**Scenario:** Meridian Health Network (fictional, composite) — a regional health system with 46 sites and ~2 million patient records, running a single-site, out-of-support, on-premises appointment and practice-management platform. Strong HIPAA/compliance and HA/DR angle. One of six case studies in the [Cloud Architecture](../README.md) portfolio, following the 13-step case-study pipeline (Section 22.1 of the reference guide).

## Status

| Pipeline Step | Status |
| --- | --- |
| 1. Business problem | ✅ Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| 2. Capabilities required | ✅ Captured within problem statement |
| 3. Requirements and NFRs | ✅ Done — [`docs/requirements.md`](docs/requirements.md) |
| Current-state architecture | ✅ Done — [`docs/current-state.md`](docs/current-state.md) |
| 4. Architecture options and styles | ✅ Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-migration-strategy-carelink-pm-core.md), [ADR-002](adr/ADR-002-target-style-owned-components.md), [migration strategy map](diagrams/Migration-Strategy-Map.xlsx), [target style diagram](diagrams/target-architecture-style.png) |
| 5. Vendor-neutral logical design | ⬜ Next |
| 6. Azure implementation | ⬜ Not started |
| 7. AWS implementation | ⬜ Not started |
| 8. GCP implementation | ⬜ Not started |
| 9. Private-cloud implementation | ⬜ Not started |
| 10. Decision matrix | ⬜ Not started |
| 11. Recommended platform / target architecture | ⬜ Not started |
| 12. Migration roadmap and ADRs | ⬜ Not started |
| 13. Cost and risk analysis | ⬜ Not started |

## Repository Structure

Follows Section 20 of the reference guide:

```
case-study-03-healthcare-platform/
│
├── README.md
├── docs/
│   ├── current-state.md                   # on-prem architecture, as-is
│   ├── problem-statement.md               # business problem, drivers, stakeholders
│   ├── requirements.md                    # NFRs, requirement/constraint/assumption/risk
│   └── architecture-options-and-styles.md # 6-R migration strategy + target style options
│
├── adr/                         # architecture decision records — ADR-001, ADR-002 so far
├── architecture/
│   ├── context/                 # executive context view
│   ├── solution/                # solution / physical deployment
│   ├── network/                 # network architecture
│   ├── security/                # security architecture
│   ├── data/                    # data architecture
│   └── dr/                      # HA/DR architecture
├── terraform/                   # IaC (populated once a platform is chosen)
└── diagrams/
    ├── Migration-Strategy-Map.xlsx      # color-coded 6-R map, Step 4
    ├── target-architecture-style.png    # rendered preview of the Step 4 target-style diagram
    └── target-architecture-style.drawio # editable draw.io source for the same diagram
```

## Read Next

Start with [`docs/current-state.md`](docs/current-state.md) for the as-is architecture, then [`docs/problem-statement.md`](docs/problem-statement.md) for why it has to change, then [`docs/requirements.md`](docs/requirements.md) for the constraints any target design has to satisfy.
