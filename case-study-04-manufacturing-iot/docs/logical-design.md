# Step 5: Vendor-Neutral Logical Design

## Purpose of This Step

[Step 4](architecture-options-and-styles.md) fixed the *shape* of the solution. It did so in three decisions:

- the edge/cloud split ([ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md))
- a Unified Namespace per plant ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md))
- the IEC 62443 zone model with an outbound-only DMZ bridge ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md))

This step goes one layer deeper. It defines the logical components, what each is responsible for, and the contracts between them, precisely enough to implement. It still names no Azure, AWS, or GCP service, and no edge product. Those are named in Steps 6–8. If this document had to be rewritten to add a platform name anywhere, this step would have been done too early.

It also resolves the two questions Step 4 deferred: how a genealogy record is written **exactly once** end to end, and how a plant that has been offline catches up **without delaying everyone else's live data**.

## Logical Component Model

### Plant tier (one instance per plant; every component runs on at least two edge nodes)

| # | Component | Zone | Responsibility | Interface / Contract |
|---|---|---|---|---|
| P1 | **Edge Connector** | L3 | Reads Level 2 OPC UA servers (or native drivers via protocol gateways). Maps each source tag to the enterprise asset model once. Stamps the **source timestamp** and a per-source **sequence number**. Derives machine-state events (Running / Idle / Down + reason code) for OEE. | Publishes Sparkplug B telemetry to `kestrel/<site>/<area>/<line>/<asset>/<signal>`. Publishes `MachineStateChanged` events. Read-only toward Level 2. |
| P2 | **Plant UNS Broker** | L3 | The plant's single publish/subscribe hub ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)). An HA pair with local persistence. | MQTT with Sparkplug B for telemetry and versioned JSON for business events. Birth and death certificates mark source liveness. |
| P3 | **Vibration Feature Extractor** | L3 | Takes kHz-rate sensor streams from the ~300 critical assets and computes features (RMS, peak, kurtosis, band energies) once per second. Keeps a 7-day ring buffer of raw waveforms locally. | Publishes `FeatureVector` to the UNS. On an anomaly, the raw waveform snapshot (±60 s) is attached to the outbound anomaly event. |
| P4 | **Edge Anomaly Detector** | L3 | Runs threshold rules plus the currently *active* deployed model on features and state, and raises local alerts within NFR-5's 10 seconds. Has no path to Levels 0–2. | Consumes `FeatureVector` and telemetry. Emits `AnomalyDetected` to the UNS and to **Plant Alerting** (maintenance tablets, plant alert display, on-call paging). |
| P5 | **Genealogy Recorder** | L3 | Assembles each serial's genealogy record: part number + serial, asset, tooling ID, material lot, process-parameter snapshot, inspection results. Writes it to the Local Genealogy Journal **before** confirming the serial ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)). | Synchronous request/ack with the station or MES (`RecordSerial` → `SerialRecorded` / `SerialHeld`). Emits `GenealogyRecorded` to the UNS. |
| P6 | **Local Genealogy Journal** | L3 | Append-only, hash-chained journal of genealogy records. Replicated synchronously to the second edge node before acknowledging. | Write-once by the recorder. Read by the Edge Outbox and by local lookup during an outage. Holds at least 90 days locally. |
| P7 | **Edge Outbox (store-and-forward)** | L3 | Durably queues everything bound for the cloud in **four priority lanes** ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)). Holds ≥ 72 hours (NFR-1). At about 250 GB per node it actually holds roughly 4 weeks at an average plant's rate, leaving headroom for tag growth and high-rate plants. Replicated across both edge nodes. | Dequeued by the Cloud Bridge only. A message is removed only after the **cloud** acknowledges a durable write, not when the bridge receives it. |
| P8 | **Local Time-Series Store** | L3 | 30 days of local trending for plants without a historian (07, 10), and the local source for OEE during outages. | Subscribes to the UNS. Queried by plant engineers locally. |
| P9 | **Edge Deployment Agent** | L3 | Pulls signed model and configuration artifacts from DMZ staging, verifies signatures, runs a new model in **shadow mode**, and activates it only after plant approval. Keeps the previous version for one-step rollback. | Pull-only from DMZ staging ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)). Reports version and health to Fleet Management through the outbox. |
| P10 | **Cloud Bridge** | L3.5 DMZ | The plant's only connection to the cloud: outbound-only, holding the edge node's X.509 identity. It drains the outbox lanes in priority order under a per-plant bandwidth cap, and it hosts the DMZ staging area for pulled artifacts. | One conduit inward (to the outbox) and one outbound TLS connection to Cloud Ingestion. Nothing initiates inbound. |

### Cloud tier (instantiated in a US region and an EU region; the German plants use EU only)

| # | Component | Responsibility | Interface / Contract |
|---|---|---|---|
| C1 | **Cloud Ingestion Endpoint** | Authenticates each plant bridge by certificate. Accepts batches. Acknowledges only after a durable write to the event stream. | Batch-append API. The ack carries the highest sequence number durably written per lane, which the bridge uses to release outbox entries. |
| C2 | **Event Stream** | A durable, partitioned log (partitioned by site and asset) with **separate live and backfill streams** ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)) plus a dedicated genealogy stream. | Publish/subscribe with consumer groups. At-least-once delivery, with replay from any offset for 7 days. |
| C3 | **Decoder / Normalizer** | Decodes Sparkplug B, validates schemas, and removes duplicates using `(site, source, sequence)`. | Consumes raw streams. Publishes normalized events. |
| C4 | **Hot-Path Stream Processor** | Windowed aggregation and longer-horizon predictive models (remaining useful life, degradation trends) on **live data only**. | Consumes the live stream. Emits `MaintenanceRecommendation` (with a unique recommendation ID) within NFR-5's 5 minutes. |
| C5 | **Maintenance Integration Adapter** | Creates SAP PM notifications and work orders through a supported interface. Idempotent on recommendation ID. | Consumes `MaintenanceRecommendation`. An adapter boundary lets ECC be swapped for S/4HANA without changing C4. |
| C6 | **Time-Series Store (hot)** | 90 days of raw normalized telemetry (NFR-8), indexed by asset and source timestamp. Accepts late data in the correct time position. | Written from both the live and backfill streams. Queried by engineers, data science, and C7. |
| C7 | **Analytical Store (cold)** | 1-minute downsampled telemetry for 5 years, machine-state history, OEE facts, and curated ML training datasets. | Batch and incremental loads from C6 and the event stream. |
| C8 | **Genealogy Store + Recall Query Service** | Immutable (write-once) 15-year store of genealogy records, verified against each plant's hash chain. Answers per-serial queries (≤ 5 s, NFR-7) and recall scoping by lot, tool, asset, or time window (≤ 4 h). | Consumes the genealogy stream. Idempotent insert on `(part number, serial, record version)` ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)). |
| C9 | **OEE / KPI Service** | Calculates OEE with one definition (below) per asset, line, shift, and plant. Restates affected windows when late data arrives. | Reads C7. Publishes **aggregated, non-personal** KPIs to the Global KPI Layer. |
| C10 | **Global KPI Layer** | Cross-region reporting across all 12 plants. Receives aggregates only, never raw telemetry or operator IDs (NFR-10). | Fed by C9 in both regions. |
| C11 | **ML Training + Model Registry** | Trains edge anomaly models and cloud predictive models on cross-plant data. Validates, versions, and **signs** artifacts. | Publishes signed artifacts to each plant's DMZ staging for P9 to pull. |
| C12 | **Fleet Management** | Inventory, software versions, configuration, and health of every edge node and bridge. Stages rollouts plant by plant. | Receives health and version reports via the outbox. Stages artifacts. Never initiates connections into a plant. |
| C13 | **Observability and Audit Log** | Platform telemetry, plus an append-only audit trail of model deployments, approvals, genealogy verification results, and privileged access. | Append-only consumer of the platform's control events. |

## The One OEE Definition (driver 4)

OEE = **Availability × Performance × Quality**, calculated per asset and rolled up by line, shift, plant, and network:

- **Availability** = run time ÷ planned production time. Planned production time excludes scheduled breaks and planned maintenance. Run time comes from `MachineStateChanged` events. **A data gap (Sparkplug death certificate) is recorded as "unknown", not as downtime**, and is shown separately.
- **Performance** = (ideal cycle time × total count) ÷ run time. Ideal cycle time comes from the asset master, not from each plant's spreadsheet.
- **Quality** = good count ÷ total count, from inspection results in the genealogy and quality events.

The definition lives in C9 alone. No plant calculates its own.

## End-to-End Flows

### Flow A — Telemetry to predictive maintenance (happy path)

1. The **Edge Connector** reads a spindle-motor current tag over OPC UA, maps it to `kestrel/plant01/machining/line3/cnc07/spindle_current`, and publishes it with its source timestamp and sequence number.
2. The **Vibration Feature Extractor** publishes the spindle's feature vector once per second.
3. The **Edge Anomaly Detector** sees band energy crossing the active model's threshold. It raises `AnomalyDetected` and pages the plant's on-call maintenance technician **within 10 seconds, with no dependency on the WAN**.
4. The anomaly event (with its waveform snapshot) enters the outbox's alert lane. Telemetry and features enter the live lane.
5. The **Cloud Bridge** forwards them. **Cloud Ingestion** writes them durably and acknowledges, and the outbox releases them.
6. The **Hot-Path Stream Processor** combines this asset's trend with fleet history for the same machine type and emits `MaintenanceRecommendation` ("bearing degradation, estimated 9–14 days to failure").
7. The **Maintenance Integration Adapter** creates an SAP PM notification within 5 minutes of data arrival. A redelivered recommendation is a no-op because the adapter is idempotent on recommendation ID.

### Flow B — WAN outage and backfill

1. The WAN drops at Ramos Arizpe. Production, local alerting (step A3), genealogy recording (Flow C), and local trending all continue unchanged.
2. The outbox accumulates data: at about 5,000 values/sec and about 20 bytes per value after compression, that is roughly **26 GB per 72 hours**. Each edge node's outbox volume is about 250 GB, roughly 4 weeks at this rate, so 72 hours is met with a wide margin.
3. The WAN returns after 19 hours. The bridge drains the lanes **in priority order** ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)):
   1. genealogy
   2. alerts
   3. current live data, so that the plant is "live" again within seconds
   4. the 19-hour backlog, rate-capped (default 20 Mbps on this 50 Mbps link, so about 7 GB drains in about 45 minutes)
4. Backfill lands on the cloud's **backfill stream**, which the hot path does not consume. So other plants' live processing is never delayed (NFR-4), and stale data does not generate "urgent" predictive alerts about conditions from 19 hours ago.
5. The Time-Series Store places late values by source timestamp. The OEE Service **restates** Ramos Arizpe's affected shifts and marks them as restated.

### Flow C — Serial produced to genealogy record (see [ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md))

1. A brake caliper finishes final inspection at Plant 02. The station (or MES) sends `RecordSerial` with part number + serial to the **Genealogy Recorder**.
2. The Recorder assembles the record from UNS context: the asset, tooling ID, material lot scanned at the line, the process-parameter snapshot for that cycle, and the inspection results.
3. The Recorder appends the record to the **Local Genealogy Journal**, including the hash of the previous record, and waits for synchronous replication to the second edge node.
4. Only then does it return `SerialRecorded`, and the station releases the part to packing. If the journal cannot be written, the station receives `SerialHeld`. The part goes to a hold-for-genealogy bin and **the line keeps running**. An untraced part is never shipped, and a recording fault never stops production.
5. The record enters the outbox's genealogy lane (the highest priority) and is inserted into the **Genealogy Store** with an idempotent insert keyed on `(part number, serial, record version)`.
6. Nightly, each plant's journal hash-chain head and record count are compared with the cloud store's. Any mismatch is a quality-system exception, never silently corrected.

### Flow D — Recall scoping

1. Quality learns that material lot `L-4471` of steel bar may be out of specification.
2. The **Recall Query Service** returns every serial whose genealogy references `L-4471`, across all plants in the region, with each part's asset, date, and inspection outcome, in minutes rather than the 19 days a 2025 containment took (NFR-7 requires ≤ 4 hours).
3. The results can be narrowed further by tool, asset, or process-parameter range (for example, "only parts machined while coolant temperature was above X"). That is what turns a 41,000-part containment into a 3,000-part one.

### Flow E — Model lifecycle (train in cloud, run at edge)

1. **ML Training** trains a bearing-anomaly model on fleet-wide data for one press type, validates it against held-out failures, and the **Model Registry** versions and signs it.
2. **Fleet Management** stages it to one pilot plant's DMZ staging area.
3. That plant's **Edge Deployment Agent** pulls it, verifies the signature, and runs it in **shadow mode** next to the active model for a set period, logging would-have-alerted events without paging anyone.
4. The plant's reliability engineer reviews the shadow results and approves activation. The approval is recorded in the Audit Log.
5. The rollout then proceeds plant by plant. Rollback is one step, because the previous version is kept on every node.

## Security and Identity (logical)

- **Device identity:** every edge node and bridge has its own X.509 certificate. Certificates are issued and rotated centrally, revoked per node, and never shared across plants.
- **Direction:** the only network connection that crosses a plant boundary is the bridge's outbound TLS session to Cloud Ingestion. Artifacts come in only by the edge **pulling** from DMZ staging.
- **Human access:** engineers and vendors reach plant systems only through brokered, MFA-enforced, session-recorded remote access that terminates in the DMZ ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)). Cloud-side users are federated to Kestrel's corporate identity provider, with role-based access by region: the EU region's raw data is not readable by US-only roles.
- **Integrity:** models and configuration are signed. Genealogy is hash-chained at the edge and verified in the cloud.

## Diagram

See [`diagrams/logical-architecture.md`](../diagrams/logical-architecture.md) for the component diagram (plant tier, DMZ, and cloud tier with numbered components) and the genealogy exactly-once sequence diagram, both in Mermaid.

## Key Decisions Made at This Step

- **[ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)**: how a genealogy record is made durable at the edge before a serial is confirmed, and carried to the cloud exactly once. The mechanism is a hash-chained local journal plus an idempotent insert, **not** MQTT QoS 2.
- **[ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)**: a four-lane priority outbox, and separate live and backfill streams in the cloud, so that a reconnecting plant cannot stall its own or anyone else's live processing.

## What Step 5 Deliberately Leaves Open

Nothing above names a message broker product, stream service, time-series database, or edge runtime. Every component is described by its responsibility and its contract. Steps 6–8 each take this exact model and answer what it looks like on Azure, AWS, and GCP, **including which edge software fills P1–P10 on each platform**. That is where the tracks will differ most, particularly on GCP, which has had no first-party managed IoT service since 2023.
