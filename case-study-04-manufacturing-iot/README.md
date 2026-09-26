# Case Study 4 of 6: Manufacturing / IoT

**Scenario:** Kestrel Industrial Components (fictional, composite) is a ~$1.6B Tier-1 automotive and industrial components supplier with 12 plants in the US, Mexico, and Germany, grown by acquisition. Its machine data is trapped in five kinds of historian (or none), its plant networks are flat, and nothing moves plant-floor data to where decisions are made. Four pressures force the issue: $31M/year of unplanned downtime, a ransomware incident that crossed from IT into OT, an OEM's serial-level traceability requirement gating new business, and no comparable OEE across plants.

**Angle:** A device fleet ingesting telemetry at scale. The case study is built on event-driven architecture, streaming data pipelines, and IT/OT convergence. Its central question is *what runs at the edge versus in the cloud, and how data crosses that boundary without opening a path back into the control network.*

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs **three** cloud implementation tracks (Azure, AWS, and GCP), and each one includes the plant-edge layer as a first-class part of the design rather than a black box. There is no separate private-cloud track. The edge already *is* the on-premises component of every option here, and a full private-cloud comparison is reserved for Case Study 6 (Hybrid / Private-Cloud), where it is the central question rather than a repeat.

Two contrasts with earlier case studies run through this one:

- **Resiliency moves to the edge.** In Case Studies 2 and 3 the cloud platform carried the availability and DR obligation. Here, plants must run with no WAN or cloud connection (NFR-1), so the cloud target is 99.9% (NFR-11) and the hard engineering sits in edge autonomy and lossless backfill.
- **Security is sequenced first on purpose.** OT segmentation is ranked driver #1 even though downtime is the bigger dollar figure, because connecting unsegmented plants to a cloud platform would widen the exact attack path of the November 2025 incident.

## Status

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md); diagram not yet drawn |
| 2–3. Capabilities, requirements, and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Not started |
| 5. Vendor-neutral logical design | Not started |
| 6. Azure implementation (incl. edge) | Not started |
| 7. AWS implementation (incl. edge) | Not started |
| 8. GCP implementation (incl. edge) | Not started |
| 9. Decision matrix | Not started |
| 10. Recommended platform / target architecture | Not started |
| 11. Migration roadmap and ADRs | Not started |
| 12. Cost and risk analysis | Not started |

## Repository Structure

```
case-study-04-manufacturing-iot/
│
├── README.md
├── docs/
│   ├── problem-statement.md   # organization, 4 forcing functions, 5 ranked drivers (done)
│   ├── current-state.md       # 12-plant estate, Purdue-level architecture, data flows, OT security as-is (done)
│   └── requirements.md        # 7 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
├── adr/
└── diagrams/
```
