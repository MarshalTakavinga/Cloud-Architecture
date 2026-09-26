# Case Study 5 of 6: Enterprise Data and AI Platform

**Scenario:** Harborline Mutual Insurance Group (fictional, composite) is a ~$4.2B-premium US property-and-casualty carrier with three post-acquisition data estates, a 12-year-old Teradata warehouse whose notice date is 31 December 2026, SAS-based actuarial work, and 95 million unsearchable claim documents. Four pressures force the issue:
- a shadow-AI incident, in which claim notes were pasted into a public chatbot
- the NAIC AI bulletin and state AI rules for insurers
- the Teradata contract deadline
- an 18-day reserving close caused by fragmented data

**Angle:** Data architecture, AI/RAG, and FinOps. The central question is **hyperscaler-native data and AI stack versus a cross-cloud data platform (Databricks or Snowflake) running on top of one**, while keeping data in open formats so this is the last proprietary warehouse migration.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs **three** implementation tracks: Azure, AWS, and GCP. Within each track, the cloud's native data and AI stack is evaluated against **Databricks and Snowflake running on that cloud**. That is the decision most enterprises actually face for data and AI, and treating the cross-cloud platforms as a lens *inside* each track avoids pretending that they are clouds of their own. There is no private-cloud track. On-prem and sovereign options are reserved for Case Study 6.

Contrasts with earlier case studies:
- **Governance is sequenced first,** as security was in Case Study 4. Here, the governance and AI control plane is ranked driver #1 even though the assistant and the Teradata exit carry the dollars.
- **FinOps is a design requirement, not a closing chapter.** Consumption-priced warehouses and token-priced inference are both easy to overrun, so unit costs (per query, per claim) are NFRs from Step 3.

## Status

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md); diagram not yet drawn |
| 2–3. Capabilities, requirements, and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Not started |
| 5. Vendor-neutral logical design | Not started |
| 6. Azure implementation (native vs. Databricks/Snowflake) | Not started |
| 7. AWS implementation (native vs. Databricks/Snowflake) | Not started |
| 8. GCP implementation (native vs. Databricks/Snowflake) | Not started |
| 9. Decision matrix | Not started |
| 10. Recommended platform / target architecture | Not started |
| 11. Migration roadmap and ADRs | Not started |
| 12. Cost, FinOps, and risk analysis | Not started |

## Repository Structure

```
case-study-05-enterprise-data-ai/
│
├── README.md
├── docs/
│   ├── problem-statement.md   # organization, 4 forcing functions, 5 ranked drivers, the invariant (done)
│   ├── current-state.md       # sources, Informatica, Teradata/SAS, ECM, governance, $6.8M/yr cost baseline (done)
│   └── requirements.md        # 8 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
├── adr/
├── diagrams/
└── finance/
```
