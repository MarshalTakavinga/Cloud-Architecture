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
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-edge-cloud-responsibility-split.md), [ADR-002](adr/ADR-002-plant-data-integration-pattern.md), [ADR-003](adr/ADR-003-ot-segmentation-reference-architecture.md), [target-style diagram (Mermaid)](diagrams/target-architecture-style.md): 6-R disposition per component; edge-first/cloud-for-scale split; a Unified Namespace per plant (MQTT + Sparkplug B, ISA-95 topics); IEC 62443 zones/conduits with an outbound-only DMZ bridge. Target style: edge-first, event-driven hub-and-spoke with a US/EU regional split |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-004](adr/ADR-004-genealogy-exactly-once-record-path.md), [ADR-005](adr/ADR-005-store-and-forward-and-backfill-lanes.md), [logical-architecture diagrams (Mermaid)](diagrams/logical-architecture.md): 10 plant-tier and 13 cloud-tier logical components; one OEE definition; five end-to-end flows (predictive maintenance, WAN outage/backfill, genealogy, recall scoping, model lifecycle); genealogy made exactly-once with a hash-chained edge journal + idempotent keyed insert (not MQTT QoS 2); four-lane priority outbox + separate cloud backfill stream so a reconnecting plant can't stall live processing |
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
│   ├── problem-statement.md                 # organization, 4 forcing functions, 5 ranked drivers (done)
│   ├── current-state.md                     # 12-plant estate, Purdue-level architecture, data flows, OT security as-is (done)
│   ├── requirements.md                      # 7 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
│   ├── architecture-options-and-styles.md   # (Step 4) 6-R disposition, 3 decisions, target style (done)
│   └── logical-design.md                    # (Step 5) component model, OEE definition, 5 flows, security (done)
├── adr/
│   ├── ADR-001-edge-cloud-responsibility-split.md          # edge-first, cloud-for-scale (done)
│   ├── ADR-002-plant-data-integration-pattern.md           # Unified Namespace: MQTT + Sparkplug B, ISA-95 topics (done)
│   ├── ADR-003-ot-segmentation-reference-architecture.md   # IEC 62443 zones/conduits, outbound-only DMZ bridge (done)
│   ├── ADR-004-genealogy-exactly-once-record-path.md       # hash-chained edge journal + idempotent keyed insert (done)
│   └── ADR-005-store-and-forward-and-backfill-lanes.md     # 4-lane priority outbox, separate backfill stream (done)
└── diagrams/
    ├── target-architecture-style.md         # (Step 4) Mermaid target-style diagram (done)
    └── logical-architecture.md              # (Step 5) Mermaid component model + genealogy sequence (done)
```
