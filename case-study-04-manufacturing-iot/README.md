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
| 6. Azure implementation (incl. edge) | Done — [`docs/azure-implementation.md`](docs/azure-implementation.md), [ADR-006](adr/ADR-006-azure-edge-platform.md) to [ADR-011](adr/ADR-011-azure-network-identity-and-deployment.md), [Azure diagram (Mermaid)](diagrams/azure-implementation-architecture.md): Azure IoT Operations on 3-node Arc-enabled K3s per plant; four-lane outbox built from native data flows plus a Kestrel journal forwarder and gap-based backfill uploader; Event Hubs Premium (live/alerts/backfill/genealogy hubs); Fabric Eventhouse + Lakehouse, Stream Analytics hot path (live only), Logic Apps to SAP; Azure SQL Hyperscale append-only ledger tables for genealogy; Envoy DMZ proxy, ACR connected registry, and Flux for pull-only deployment. Two documented deviations carried to Step 9: IoT Operations' 72-hour offline ceiling, and JSON/CloudEvents rather than Sparkplug B |
| 7. AWS implementation (incl. edge) | Done — [`docs/aws-implementation.md`](docs/aws-implementation.md), [ADR-012](adr/ADR-012-aws-edge-platform.md) to [ADR-017](adr/ADR-017-aws-network-identity-and-deployment.md), [AWS diagram (Mermaid)](diagrams/aws-implementation-architecture.md): Greengrass v2 + SiteWise Edge (MQTT-enabled) on an active/passive pair (Pacemaker/DRBD, which Kestrel must productionize, since Greengrass isn't natively HA); stream manager supplies the four lanes natively (priorities, TTL, bandwidth cap); Kinesis + Managed Flink; Timestream for InfluxDB + S3 Tables/Athena (Timestream for LiveAnalytics closed to new customers June 2025); Aurora PostgreSQL insert-only + S3 Object Lock for genealogy (QLDB retired July 2025); IoT Core per-node X.509; Identity Center federated to Entra |
| 8. GCP implementation (incl. edge) | Done — [`docs/gcp-implementation.md`](docs/gcp-implementation.md), [ADR-018](adr/ADR-018-gcp-edge-platform.md) to [ADR-023](adr/ADR-023-gcp-network-identity-and-deployment.md), [GCP diagram (Mermaid)](diagrams/gcp-implementation-architecture.md): Google Distributed Cloud (bare metal, 3-node) + Manufacturing Connect edge (Litmus) with native Sparkplug B and 270+ protocols, plus a commercial MQTT broker (three edge vendors); a fully Kestrel-built four-lane outbox; Pub/Sub + Manufacturing Data Engine → Bigtable/BigQuery, Dataflow hot path + Vertex AI; Cloud SQL insert-only + Bucket Lock for genealogy; us-east5 is in Columbus itself; VPC Service Controls for residency. GDC local operations have no documented offline limit |
| 9. Decision matrix | Done — [`docs/decision-matrix.md`](docs/decision-matrix.md), [ADR-024](adr/ADR-024-cloud-platform-selection.md): a 7-criterion weighted matrix (the provisional weights plus a disclosed 10% genealogy-integrity criterion). **GCP wins narrowly, 3.95/5.00 (79.0%)**, over Azure at 3.83 (76.6%) and AWS at 3.34 (66.8%), on plant autonomy with native HA and the industrial protocol ecosystem (native Sparkplug B). Azure leads on genealogy integrity (engine-enforced ledger) and edge operating simplicity. Sensitivity: GCP wins even without the added criterion (4.00 vs 3.70), and only a genealogy weight of 20% or more flips the result to Azure. The decision carries 4 conditions and 4 review triggers |
| 10. Recommended platform / target architecture | Done — [`docs/target-architecture.md`](docs/target-architecture.md): confirms GCP (ADR-024), gives the at-a-glance edge and cloud architecture, builds ADR-024's four conditions into the design (a separate genealogy evidence project, a single edge managed-service owner, the outbox as a hard gate, the MCe capacity guardrail), traces all 4 forcing functions and the driver-5 invariant to mechanisms, and adds an NFR coverage table. Carries rollout sequencing to Step 11 and the cost trigger test to Step 12 |
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
│   ├── logical-design.md                    # (Step 5) component model, OEE definition, 5 flows, security (done)
│   ├── azure-implementation.md              # (Step 6) service mapping incl. edge, sizing, network, deviations (done)
│   ├── aws-implementation.md                # (Step 7) service mapping incl. edge, sizing, network, deviations (done)
│   ├── gcp-implementation.md                # (Step 8) service mapping incl. edge, sizing, network, deviations (done)
│   ├── decision-matrix.md                   # (Step 9) weighted matrix, sensitivity, what the others do better (done)
│   └── target-architecture.md               # (Step 10) GCP target architecture, conditions designed in, driver tracing (done)
├── adr/
│   ├── ADR-001-edge-cloud-responsibility-split.md          # edge-first, cloud-for-scale (done)
│   ├── ADR-002-plant-data-integration-pattern.md           # Unified Namespace: MQTT + Sparkplug B, ISA-95 topics (done)
│   ├── ADR-003-ot-segmentation-reference-architecture.md   # IEC 62443 zones/conduits, outbound-only DMZ bridge (done)
│   ├── ADR-004-genealogy-exactly-once-record-path.md       # hash-chained edge journal + idempotent keyed insert (done)
│   ├── ADR-005-store-and-forward-and-backfill-lanes.md     # 4-lane priority outbox, separate backfill stream (done)
│   ├── ADR-006-azure-edge-platform.md                      # Azure IoT Operations on 3-node K3s (done)
│   ├── ADR-007-azure-store-and-forward-implementation.md   # native data flows + journal forwarder + backfill uploader (done)
│   ├── ADR-008-azure-ingestion-and-streaming.md            # Event Hubs Premium, 4 hubs per region (done)
│   ├── ADR-009-azure-time-series-analytics-and-hot-path.md # Fabric RTI + Lakehouse, Stream Analytics, Logic Apps→SAP (done)
│   ├── ADR-010-azure-genealogy-store.md                    # Azure SQL Hyperscale append-only ledger tables (done)
│   ├── ADR-011-azure-network-identity-and-deployment.md    # Envoy DMZ proxy, VPN, ACR connected registry, Flux (done)
│   ├── ADR-012-aws-edge-platform.md                        # Greengrass v2 + SiteWise Edge, active/passive Pacemaker/DRBD (done)
│   ├── ADR-013-aws-store-and-forward-implementation.md     # stream manager lanes + backfill controller (done)
│   ├── ADR-014-aws-ingestion-and-hot-path.md               # Kinesis on-demand + Managed Flink, SQS→Lambda→SAP (done)
│   ├── ADR-015-aws-time-series-and-analytics.md            # Timestream for InfluxDB + S3 Tables/Athena (done)
│   ├── ADR-016-aws-genealogy-store.md                      # Aurora PostgreSQL insert-only + S3 Object Lock (done)
│   ├── ADR-017-aws-network-identity-and-deployment.md      # proxy, VPN+TGW, IoT Core X.509, Identity Center→Entra (done)
│   ├── ADR-018-gcp-edge-platform.md                        # GDC bare metal + Manufacturing Connect edge (Litmus) (done)
│   ├── ADR-019-gcp-store-and-forward-implementation.md     # Kestrel-built 4-lane outbox service (done)
│   ├── ADR-020-gcp-ingestion-and-hot-path.md               # Pub/Sub + Dataflow + Vertex AI, Cloud Run→SAP (done)
│   ├── ADR-021-gcp-time-series-and-analytics.md            # Manufacturing Data Engine → Bigtable + BigQuery, Looker (done)
│   ├── ADR-022-gcp-genealogy-store.md                      # Cloud SQL PostgreSQL insert-only + Bucket Lock (done)
│   ├── ADR-023-gcp-network-identity-and-deployment.md      # HA VPN to us-east5, PSC, VPC-SC, Config Sync, Harbor mirror (done)
│   └── ADR-024-cloud-platform-selection.md                 # GCP selected, with conditions and review triggers (done)
└── diagrams/
    ├── target-architecture-style.md         # (Step 4) Mermaid target-style diagram (done)
    ├── logical-architecture.md              # (Step 5) Mermaid component model + genealogy sequence (done)
    ├── azure-implementation-architecture.md # (Step 6) Mermaid Azure deployment diagram (done)
    ├── aws-implementation-architecture.md   # (Step 7) Mermaid AWS deployment diagram (done)
    └── gcp-implementation-architecture.md   # (Step 8) Mermaid GCP deployment diagram (done)
```
