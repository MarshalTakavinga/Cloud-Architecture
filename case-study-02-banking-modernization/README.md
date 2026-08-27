# Case Study 2 of 6: Banking Modernization

**Scenario:** Palisade Financial Group (fictional, composite) – a super-regional bank holding company, ~$21B in assets, 84 branches across the Mid-Atlantic. Core deposits and loan servicing run on a 30-year-old COBOL/CICS mainframe; a real-time-payments mandate, rising mainframe cost, a regulatory resiliency mandate, and a real-time-payments fraud wave are forcing a deliberate decision about what moves off the mainframe and what stays.

**Angle:** Core banking/payments workload — strong security, resiliency, and regulatory-reporting angle — a natural fit for the mainframe workload-placement question.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs all **four** implementation tracks — Azure, AWS, GCP, and private cloud — because the central design question here is precisely *where the workload should run*, not just which hyperscaler is best. A bank with a 30-year mainframe investment and heightened regulatory scrutiny is exactly the profile where "stay on dedicated/private infrastructure for the core, extend to public cloud for the new capability" is a live, defensible option — so the private-cloud/VMware Cloud Foundation track is a first-class comparison, not an afterthought.

## Status

**Steps 1–4 of 13 complete.**

| Step | Status |
| --- | --- |
| 1. Business problem | Done — `docs/problem-statement.md` |
| Current-state architecture | Done — `docs/current-state.md` |
| 2–3. Requirements and NFRs | Done — `docs/requirements.md` |
| 4. Architecture options and styles | Done — `docs/architecture-options-and-styles.md`, ADR-001, ADR-002, target-style diagram — 6-R disposition per component; mainframe integration approach (hybrid sync-hold + CDC); build-vs-buy for the payments rail/fraud/ledger-of-intent layer |
| 5. Vendor-neutral logical design | Not started |
| 6. Azure implementation | Not started |
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
│   └── architecture-options-and-styles.md # (Step 4) 6-R disposition, integration options, target style (done)
│
├── adr/
│   ├── ADR-001-mainframe-integration-approach.md   # hybrid sync-hold + CDC pattern (done)
│   └── ADR-002-payment-hub-build-vs-buy.md         # buy the rail gateway, build fraud/ledger-of-intent (done)
├── architecture/
│   ├── context/
│   ├── solution/
│   ├── network/
│   ├── security/
│   ├── data/
│   └── dr/
├── terraform/                     # IaC — not started, platform not yet chosen
└── diagrams/
    └── target-architecture-style.md   # (Step 4) Mermaid target-style diagram, diagrams-as-code (done)
```
