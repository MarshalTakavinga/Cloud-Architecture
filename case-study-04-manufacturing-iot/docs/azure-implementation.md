# Step 6: Azure Implementation (including the plant edge)

## Purpose of This Step

[Step 5](logical-design.md) defined 10 plant-tier components (P1–P10) and 13 cloud-tier components (C1–C13) without naming a platform. This step answers, for Azure specifically:

- what each component runs on, **at the plant as well as in the cloud**
- what the network and identity model looks like
- where Azure's own product boundaries force a decision or a deviation from Steps 4–5

Steps 7 and 8 ask the same questions independently for AWS and GCP. Neither may simply copy this track's answers.

This track surfaced three findings that matter more than any individual service choice. They were checked against Microsoft's current documentation (September 2026), and each is carried into the Step 9 decision matrix:

1. **Azure IoT Operations documents a maximum of 72 hours of disconnected operation**, "degradation might occur during this period". This is exactly NFR-1's buffer floor, while NFR-1 requires production-critical functions to continue *indefinitely*. The design therefore keeps the two functions that must never degrade (local alerting and genealogy capture) out of any dependency on IoT Operations' cloud connection. See [ADR-006](../adr/ADR-006-azure-edge-platform.md).
2. **The IoT Operations connector for OPC UA publishes JSON with CloudEvents headers (including a sequence number and source timestamp), not Sparkplug B.** This is a documented deviation from [ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)'s payload choice, though not from its pattern. See [ADR-006](../adr/ADR-006-azure-edge-platform.md).
3. **IoT Operations data flows buffer through the broker's subscriber queue, oldest message first.** That is the single-FIFO behavior [ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md) rejected, so the four-lane outbox is assembled from native data flows plus two small Kestrel-built services. See [ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md).

## Service Mapping

### Plant tier (per plant: a 3-node Arc-enabled K3s cluster in the Level 3 zone, plus DMZ services)

| Step 5 component | Azure implementation | Decision |
|---|---|---|
| P1 Edge Connector | IoT Operations **connector for OPC UA**. Assets and datasets are defined in **Azure Device Registry**, with each dataset's destination topic set to the ISA-95 path. Plant 07's Mitsubishi line and the Windows 7 HMI plants go through a commercial OPC UA protocol gateway. `MachineStateChanged` is derived in an IoT Operations **data flow**. | [ADR-006](../adr/ADR-006-azure-edge-platform.md) |
| P2 Plant UNS Broker | IoT Operations **MQTT broker** (multi-node, with persistence enabled) | [ADR-006](../adr/ADR-006-azure-edge-platform.md) |
| P3 Vibration Feature Extractor | Kestrel-built container on the cluster (reads sensor gateways, publishes 1/s features to the broker) | [ADR-006](../adr/ADR-006-azure-edge-platform.md) |
| P4 Edge Anomaly Detector + Plant Alerting | Kestrel-built container running ONNX Runtime. It depends **only on the local broker's data plane**. Paging goes through the plant's local notification gateway. | [ADR-006](../adr/ADR-006-azure-edge-platform.md) |
| P5 Genealogy Recorder | Kestrel-built container | [ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md) |
| P6 Local Genealogy Journal | PostgreSQL (CloudNativePG operator) with a **synchronous** standby on a second node. The hash chain is stored per row. | [ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md) |
| P7 Edge Outbox (4 lanes) | Lane 1: a journal forwarder (Kestrel-built). Lanes 2–3: IoT Operations data flows with broker persistence and `requestDiskPersistence`, with a 5-minute message expiry on lane 3. Lane 4: a gap-based **backfill uploader** (Kestrel-built) reading from P8. | [ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md) |
| P8 Local Time-Series Store | PostgreSQL + TimescaleDB (CloudNativePG, asynchronous replica), fed by a data flow. 30-day retention. | [ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md) |
| P9 Edge Deployment Agent | **Azure Arc GitOps (Flux)**, which pulls configuration, plus a Kestrel-built model-activation controller that enforces shadow → approve → active. Images are signed and verified at admission. | [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md) |
| P10 Cloud Bridge + DMZ staging | DMZ: an **Envoy explicit proxy** (the Level 3 cluster's only egress, with an allowlist of Azure endpoints), the **Azure Arc gateway**, and an **ACR connected registry** in `ReadOnly` mode as the pull-only artifact staging point | [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md) |

### Cloud tier (US: East US 2 · EU: Germany West Central for Plants 11–12)

| Step 5 component | Azure implementation | Decision |
|---|---|---|
| C1 Ingestion Endpoint + C2 Event Stream | **Azure Event Hubs Premium**, one namespace per region, with four event hubs: `genealogy`, `alerts`, `telemetry-live`, `telemetry-backfill`. Reached through private endpoints only. | [ADR-008](../adr/ADR-008-azure-ingestion-and-streaming.md) |
| C3 Decoder / Normalizer | Fabric **Eventstream** (schema validation, routing). Deduplication on `(site, source, sequence)` happens at Eventhouse ingestion. No Sparkplug decoding is needed on Azure, because payloads are already JSON. | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C4 Hot-Path Stream Processor | **Azure Stream Analytics**, consuming `telemetry-live` and `alerts` **only**, with remaining-useful-life scoring through an **Azure Machine Learning** online endpoint | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C5 Maintenance Integration Adapter | **Azure Service Bus** queue feeding a **Logic Apps Standard** workflow with the SAP connector (idempotent on recommendation ID) | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C6 Time-Series Store (90 days) | Fabric Real-Time Intelligence **Eventhouse** (KQL database) | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C7 Analytical Store (5 years) | Fabric **Lakehouse** (OneLake, Delta tables) | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C8 Genealogy Store + Recall Query | **Azure SQL Database Hyperscale** with **append-only ledger tables**. Database digests go to immutable Blob storage, and a daily export goes to an immutable (WORM) Blob container for the 15-year portability archive. | [ADR-010](../adr/ADR-010-azure-genealogy-store.md) |
| C9 OEE/KPI Service + C10 Global KPI Layer | Fabric (KQL + SQL) with **Power BI**. EU aggregates are *copied* to the US global workspace. Raw EU data is never shortcut across regions. | [ADR-009](../adr/ADR-009-azure-time-series-analytics-and-hot-path.md) |
| C11 ML Training + Registry | **Azure Machine Learning** (training, registry). Models are packaged as ONNX containers in **Azure Container Registry** and signed with Notation. | [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md) |
| C12 Fleet Management | **Azure Arc** (cluster inventory, extensions, GitOps configuration), **Azure Device Registry** (assets), and Azure Policy for Arc-enabled Kubernetes | [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md) |
| C13 Observability + Audit | **Azure Monitor** (Log Analytics, managed Prometheus) for cloud and Arc clusters. Model-activation approvals and genealogy verification results are written to an append-only audit table in the C8 database. | [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md) |

## Why Six Decisions

Case Study 2's Azure track had five platform decisions, for a small, uniform set of services. This track needs six because it answers a question the earlier case studies never faced: **what runs in the plant**. The edge platform ([ADR-006](../adr/ADR-006-azure-edge-platform.md)) and how the outbox is assembled on it ([ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md)) are where Azure's product boundaries show up most. The four cloud-side decisions ([ADR-008](../adr/ADR-008-azure-ingestion-and-streaming.md) to [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md)) are closer to conventional platform mapping.

## Build Versus Buy on This Track

Azure provides P1, P2, the southbound connectors, the asset registry, GitOps delivery, and the cloud-bound data flows **natively**. Kestrel must **build** six small edge services:

- the feature extractor (P3)
- the anomaly detector (P4)
- the genealogy recorder (P5)
- the journal forwarder (lane 1 of P7)
- the backfill uploader (lane 4 of P7)
- the model-activation controller (part of P9)

These are the Kestrel-specific parts of the design. The two outbox services exist only because the native buffering is FIFO. How much Kestrel must build at the edge is compared across tracks in Step 9.

## Edge Sizing (per plant)

- **Cluster:** three industrial-grade servers (16 cores, 64 GB RAM, 2 × 1.92 TB NVMe each) running Ubuntu + K3s, Arc-enabled. There are three nodes rather than [ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md)'s minimum of two because a Kubernetes control plane needs three nodes for quorum. Microsoft's published multi-node reference sustained about 50,000 data points per second on five 16-core nodes. Kestrel's largest plants peak at around 15,000 values per second, so three nodes leave headroom for one node to fail.
- **Storage:** about 250 GB per node for P8, which also serves as the lane 4 source, plus 50 GB for the P6 journal. Broker persistence is sized for lanes 2–3 at the 5-minute live horizon plus the alert backlog.
- **Fleet:** 12 plants × 3 nodes = **36 edge nodes**. IoT Operations is billed per node per hour, so node count is a direct cost driver in Step 12.

## Network and Security Summary

- **Plant side (ADR-003 made concrete):**
  - The Level 3 cluster has **no direct route out**. All of its egress goes through the DMZ Envoy proxy, and the proxy's allowlist contains only the Azure endpoints the cluster needs, consolidated through the Arc gateway.
  - Images and artifacts are pulled from the DMZ connected registry.
  - Nothing in Azure can initiate a connection into a plant.
- **WAN to Azure:**
  - US and Mexico plants reach Azure over the existing MPLS through Columbus, then over an **active-active site-to-site VPN** from Columbus to the US hub VNet.
  - The German plants use a VPN from each plant to the EU hub VNet, so their traffic never crosses the Atlantic.
  - ExpressRoute was considered and rejected as out of proportion to about 60 Mbps of aggregate steady-state traffic ([ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md)). This contrasts with Case Study 2, where the bank's mainframe path justified it.
- **PaaS:** Event Hubs, SQL, Fabric (through managed private endpoints), Azure ML, and ACR are reached through private endpoints only.
- **Identity:**
  - Human access is through **Entra ID**, which Kestrel already runs for its office workforce. That is a modest onboarding advantage, noted but deliberately not over-weighted in Step 9.
  - Cluster workloads use Arc-enabled workload identity federation and managed identities. No connection strings are stored at the plant.
  - EU raw data is readable only by EU-scoped roles.
- **Guardrails:** Azure Policy pins each region's resources to that region (NFR-10), enforces private endpoints, and audits the Arc clusters' configuration. Microsoft also offers first-party OT network monitoring (Defender for IoT). Under [ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md) the OT monitoring product is a separate procurement decision, but the availability of a first-party option is noted for Step 9.

## Observability

Arc cluster metrics and logs, IoT Operations broker and data-flow metrics, Event Hubs, Stream Analytics, and SQL all report to one Log Analytics workspace per region. The EU workspace is in Germany West Central.

Three plant-level signals get their own alerts, because each represents a design assumption from Step 5 failing:

- **Outbox depth per lane:** lane 4 growing while the WAN is up means the backfill cap is too low.
- **Genealogy `SerialHeld` rate:** anything above zero is investigated the same shift.
- **Hours since the cluster last connected, alerted at 48 hours.** This gives a day of warning before IoT Operations' documented 72-hour limit ([ADR-006](../adr/ADR-006-azure-edge-platform.md)).

## Alignment Check against Step 5

All 23 logical components are mapped above. Step 5's contracts hold on Azure, with two documented deviations, both carried to Step 9:

| Step 5 / Step 4 expectation | Azure reality | Treatment |
|---|---|---|
| Telemetry payload in Sparkplug B ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)) | The OPC UA connector publishes JSON + CloudEvents | Accept the native format. Liveness comes from connector/asset status plus MQTT last-will and heartbeat topics. Portability is scored down slightly in Step 9. |
| Plant autonomy "indefinitely" (NFR-1) | IoT Operations documents a 72-hour maximum offline | Critical functions (P4, P5/P6) do not depend on IoT Operations' cloud connection. A 48-hour alert, plus a WAN resilience upgrade at Ramos Arizpe, are named in the Step 11 roadmap. Scored as a risk in Step 9. |

Everything else maps without deviation: the lanes are isolated and backfill is kept out of the hot path; genealogy uses a keyed idempotent insert into an append-only store; deployments are pull-only and signed; and EU and US data stay separate.

## Diagram

See [`diagrams/azure-implementation-architecture.md`](../diagrams/azure-implementation-architecture.md) (Mermaid) for the plant cluster, the DMZ, the WAN paths, and both regional cloud deployments.

## Known Deferred Items

- Bicep or Terraform for the cloud tier, and the GitOps repository layout for the edge. This IaC is deferred until the platform is selected in Step 9, consistent with the earlier case studies.
- Exact Event Hubs processing units and Fabric capacity SKUs are sized in Step 12's cost model. This document fixes the *shape*, and Step 12 fixes the size.
- Selecting the protocol-gateway product for Plant 07 and the Windows 7 HMI plants is procurement, not platform.
