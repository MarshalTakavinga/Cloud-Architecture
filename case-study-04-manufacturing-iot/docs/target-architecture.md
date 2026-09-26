# Step 10: Recommended Platform and Target Architecture

## Confirmed Platform

**Google Cloud**, per [ADR-024](../adr/ADR-024-cloud-platform-selection.md). It scored 3.95/5.00 (79.0%) against Azure's 3.83 and AWS's 3.34 in [Step 9](decision-matrix.md), **with four conditions and four review triggers** that are part of the decision itself.

This step does three things:
- restates the target architecture at a glance
- traces each forcing function and the driver-5 invariant to the specific mechanism that closes it
- folds ADR-024's conditions into the architecture, so they are designed in rather than attached afterwards

It does not re-argue the platform choice or re-specify what [Step 8](gcp-implementation.md) already fixed at ADR depth.

## Target Architecture at a Glance

**In every plant (×12), autonomous by design ([ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md), [ADR-018](../adr/ADR-018-gcp-edge-platform.md))**

- **Network ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)):** IEC 62443 zones and conduits. An industrial DMZ is the only crossing point between the plant and anything outside it, and it holds the HTTPS proxy, the Git mirror, the Harbor registry mirror, and the MFA-brokered secure-remote-access gateway.
- **Compute:** a 3-node **Google Distributed Cloud (bare metal)** cluster in the Level 3 zone, running:
  - **Manufacturing Connect edge (Litmus)**, which reads Level 2 over OPC UA and native drivers and publishes **Sparkplug B**
  - a clustered MQTT broker as the plant's **Unified Namespace** with ISA-95 topics ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md))
  - Kestrel's anomaly detector, feature extractor, genealogy recorder, and hash-chained journal ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md))
  - the **four-lane Outbox Service** ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md), [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md))
  - a 30-day local TimescaleDB store
- **Change:** everything deployed at the plant is pulled through **Config Sync**, signed, and activated only after plant approval ([ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md)).

**In Google Cloud (us-east5 Columbus for 10 US/MX plants · europe-west3 Frankfurt for Plants 11–12)**

- **Ingestion:** Pub/Sub, with `genealogy`, `alerts`, `telemetry-live`, and `telemetry-backfill` topics pinned to each region by message storage policy ([ADR-020](../adr/ADR-020-gcp-ingestion-and-hot-path.md)).
- **Hot path:** a Dataflow job reading **live and alerts only**, scoring remaining useful life (RUL) with Vertex AI and creating SAP PM notifications through Cloud Run.
- **Data:** **Manufacturing Data Engine**, which feeds **Bigtable** (90 days hot) and **BigQuery** (5 years, OEE, training data), with **Looker** on top. Only aggregated, non-personal KPIs are copied from the EU to the global dataset ([ADR-021](../adr/ADR-021-gcp-time-series-and-analytics.md)).
- **Genealogy:** **Cloud SQL for PostgreSQL**, insert-only, with a hash chain. Digests and the 15-year archive sit in **Bucket-Locked Cloud Storage** ([ADR-022](../adr/ADR-022-gcp-genealogy-store.md)), hardened further by ADR-024 condition 1 (below).
- **Boundary:** HA VPN, Private Service Connect, one **VPC Service Controls** perimeter per region, Workforce Identity Federation with Entra ID, and fleet Workload Identity. There are no stored keys at plants.

See [`diagrams/gcp-implementation-architecture.md`](../diagrams/gcp-implementation-architecture.md) (the reference source for the hand-drawn target diagram).

## ADR-024's Conditions, Designed In

| Condition | Where it lives in the target architecture |
|---|---|
| 1. Genealogy integrity hardening | Nightly Merkle digests are written to a Bucket-Locked bucket in a **separate evidence project**, administered by a **separate group** (Quality, not Platform). No single role can alter both the genealogy table and its evidence. A monthly digest is published to OEM customers, and quarterly verification drills are recorded in the audit log. |
| 2. One edge operations owner | A managed-service provider runs GDC, MCe, and the broker across all 12 plants, with Litmus and the broker vendor as named subcontractors. Kestrel keeps architecture authority, the plant approval gates, and ownership of the Outbox Service. |
| 3. Outbox built first and tested hardest | The Outbox Service has its own acceptance suite (outage injection, backfill under the rate cap, lane starvation, replay idempotency). It is a hard gate before any plant beyond the pilot ([Step 11](migration-roadmap.md)). |
| 4. MCe capacity guardrail | Tag headroom per MCe instance is a fleet metric. A forecast above 80% of the limit within 12 months triggers a second-instance plan. |

## Tracing Each Forcing Function to the Mechanism That Closes It

1. **Unplanned downtime, about $31M a year (driver 2).**
   - **The mechanism:** online vibration and temperature sensing on the ~300 critical assets, features computed at the edge, and local anomaly alerts within 10 seconds with no WAN dependency ([ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md)). The Dataflow + Vertex AI hot path then turns fleet-wide history into RUL-based SAP PM notifications within 5 minutes (NFR-5).
   - **What changes:** the February 2026 Fort Wayne press failure happened because a bearing trend sat in a monthly spreadsheet. In the target state that trend is scored every second, and it is judged against every similar press in the fleet, not just its own history.
2. **Ransomware crossed a flat IT/OT network (driver 1).**
   - **The mechanism:** the IEC 62443 zone-and-conduit model at every plant, a DMZ as the only crossing point, outbound-only connections to the cloud, pull-only deployments, MFA-brokered remote access replacing TeamViewer and vendor modems, offline backups, and passive OT monitoring ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)).
   - **What changes:** the cloud connection makes each plant more secure, because it adds one narrow, monitored conduit to a network that today has none. It is the same set of controls the insurer made a condition of the July 2027 renewal, and the same set NIS2 expects at the German plants.
3. **Serial-level traceability is a condition of new business (driver 3).**
   - **The mechanism:** serials are recorded at the point of production into a synchronously replicated, hash-chained journal before the part is released. A genealogy fault diverts the part to a hold bin and never stops the line ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)). Records reach the cloud exactly once through a priority lane, into an insert-only store with 15-year locked evidence.
   - **What changes:** recall scoping by lot, tool, or process-parameter range drops from 19 days to minutes (NFR-7 requires ≤ 4 hours), which turns a 41,000-part containment into a roughly 3,000-part one.
4. **No comparable OEE across plants (driver 4).**
   - **The mechanism:** one asset model (ISA-95 UNS topics, contextualized once by MDE) and one OEE calculation in BigQuery. It treats a Sparkplug-reported data gap as "unknown", not downtime, and restates shifts when backfill arrives.
   - **What changes:** OEE is available the next shift instead of 7–10 days later, and the numbers are comparable across plants.
5. **The invariant: never compromise safety or line control (driver 5).**
   - **The mechanism:** Levels 0–2 are read-only, and nothing in the cloud can reach into a plant. GDC keeps plant workloads running through disconnection with no documented limit, and the outbox buffers at least 72 hours (about 4 weeks at an average plant's rate).
   - **What changes:** alerting and genealogy never depend on the WAN. This is the property every earlier ADR was written to protect, and the selected platform is the one that meets it with the fewest caveats.

## NFR Coverage Summary

| NFR | Met by |
|---|---|
| NFR-1 Autonomy, ≥ 72 h buffer | GDC disconnected operation (no documented limit), plus the Outbox and TimescaleDB |
| NFR-2 Control-path isolation | ADR-003 zones, the DMZ proxy, and pull-only Config Sync |
| NFR-3/4 Throughput and backfill | Pub/Sub (serverless). Separate backfill topic. Per-plant rate cap in the Outbox. |
| NFR-5 Alert latency | Edge detector (≤ 10 s); Dataflow → Cloud Run → SAP (≤ 5 min) |
| NFR-6 Completeness | Outbox acknowledgement after publish, gap-based backfill, the genealogy key constraint and hash chain |
| NFR-7 Genealogy queries | Indexed Cloud SQL lookups (≤ 5 s); recall scoping in minutes |
| NFR-8 Retention | Bigtable 90 days; BigQuery 5 years; Cloud SQL plus Bucket Lock for 15 years |
| NFR-9 IEC 62443 SL2 | ADR-003 reference model at all 12 plants |
| NFR-10 Residency | Separate EU region and VPC-SC perimeter; aggregates-only global layer |
| NFR-11 Cloud 99.9% | Regional managed services (not on the production-critical path by design) |
| NFR-12 Economics | To be tested in [Step 12](cost-and-risk-analysis.md) against ADR-024's cost review trigger |

## What This Step Carries Forward, Not Resolves

- **Rollout sequencing ([Step 11](migration-roadmap.md)).** Only the **December 2026** shutdown window falls before the **July 2027** insurer renewal. Segmentation (driver 1) therefore has to lead, and the data platform has to follow. The pilot plant choice, the wave plan, the Ramos Arizpe WAN resilience upgrade, the works-council track for the German plants, and closing the 2024 SageMaker account are also Step 11's to sequence.
- **Sizing and cost ([Step 12](cost-and-risk-analysis.md)).** This covers GDC vCPU licensing, MCe instance licensing, broker licensing, Pub/Sub and Dataflow volumes, Bigtable nodes, BigQuery, the managed-service contract, and edge hardware. Step 12 must test ADR-024's review trigger explicitly: is GCP's edge licence stack more than 20% above Azure's equivalent over 5 years?
- **IaC.** Terraform for the cloud tier and the Config Sync repository structure for the edge are named as a follow-on build artifact, as in the earlier case studies. They are not produced in this architecture portfolio step.
