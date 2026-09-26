# Step 8: GCP Implementation (including the plant edge)

## Purpose of This Step

This is the third independent mapping of the 23 Step 5 components, after [Azure](azure-implementation.md) and [AWS](aws-implementation.md). GCP is the track where Step 4's warning about vendor churn is most concrete. **Google Cloud IoT Core was retired on 16 August 2023**, so Google has no first-party device or IoT hub today. Its industrial answer is a partner-plus-platform combination:

- **Google Distributed Cloud (GDC) software-only for bare metal** provides Kubernetes at the edge.
- **Manufacturing Connect edge (MCe)**, which is Litmus Edge "designed by Litmus Automation and developed exclusively for Google Cloud", is sold and supported by Litmus through Google Cloud Marketplace.
- **Manufacturing Data Engine (MDE)** is Google's packaged ingestion and contextualization solution. It is deployed into Kestrel's own project on Pub/Sub, Dataflow, BigQuery, Bigtable, and Cloud Storage, with "no extra costs" beyond cloud consumption.

Findings from current documentation (September 2026) that shape this track:

1. **GDC's disconnected behavior is the most favorable of the three tracks.** When disconnected from Google Cloud, local Kubernetes operations, application deployment via kubectl, DNS, load balancing, and Config Sync (if its Git source is reachable) keep working with **no documented time limit**. What stops is cluster lifecycle work (creating, upgrading, adding nodes) and Cloud Identity sign-in. Local log and metric buffers are finite (about 4.5 h and 24 h per node). See [ADR-018](../adr/ADR-018-gcp-edge-platform.md).
2. **MCe natively supports Sparkplug B** (as a Sparkplug edge node and client), and **270+ automation protocols**. This makes GCP the only track that honors [ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)'s payload choice without a partner add-on, and it removes the separate protocol gateways for Plant 07 and the Windows 7 HMI plants. However, Google documents MCe capacity at about **10,000 tags per edge deployment**, so the larger plants need two instances.
3. **Nothing native provides ADR-005's lanes.** MCe has store-and-forward, but with no documented priorities, TTL, or rate cap. As a result the four-lane outbox is **entirely Kestrel-built** on this track, the most custom edge code of the three. See [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md).
4. **More churn:** Pub/Sub Lite was turned down on 18 March 2026. This track uses standard Pub/Sub. See [ADR-020](../adr/ADR-020-gcp-ingestion-and-hot-path.md).

## Service Mapping

### Plant tier (per plant: a 3-node GDC bare-metal cluster, edge profile, in Level 3, plus DMZ services)

| Step 5 component | GCP implementation | Decision |
|---|---|---|
| P1 Edge Connector | **Manufacturing Connect edge (Litmus Edge)** on the GDC cluster, two instances at plants above about 10K tags. OPC UA plus native drivers (so Plant 07 and the Windows 7 HMI plants need no separate gateway). Publishes **Sparkplug B** to the UNS. `MachineStateChanged` is derived in MCe flows. | [ADR-018](../adr/ADR-018-gcp-edge-platform.md) |
| P2 Plant UNS Broker | **Clustered, Kubernetes-native MQTT broker** (commercially licensed, for example HiveMQ or EMQX Enterprise) on the GDC cluster. MCe is a Sparkplug client and edge node, not a broker, so the broker is a **third edge vendor**. | [ADR-018](../adr/ADR-018-gcp-edge-platform.md) |
| P3, P4 | Kestrel-built containers (P4 runs ONNX Runtime), depending only on the local broker | [ADR-018](../adr/ADR-018-gcp-edge-platform.md) |
| P5 + P6 | Kestrel-built recorder. The journal is PostgreSQL (CloudNativePG) with a synchronous standby, as on Azure. | [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md) |
| P7 Edge Outbox | **Kestrel-built four-lane outbox service**: disk-backed queues per lane, strict priority, a 5-minute live horizon, gap-based backfill from P8, and a per-plant rate cap. It publishes to Pub/Sub with ordering keys. | [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md) |
| P8 | TimescaleDB (CloudNativePG), 30 days | [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md) |
| P9 | **Config Sync** (pull-based GitOps) from a DMZ Git mirror, images pulled from a DMZ **registry mirror** (Harbor) that syncs from Artifact Registry, signature verification at admission (Sigstore policy controller), and a Kestrel activation controller. MCe configuration and templates are managed through **Litmus Edge Manager**. | [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md) |
| P10 | DMZ **HTTPS forward proxy** with an allowlist of Google APIs (reached via Private Service Connect over the VPN), the Git mirror, and the registry mirror. Outbound only. | [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md) |

### Cloud tier (US: us-east5 Columbus, Ohio · EU: europe-west3 Frankfurt)

| Step 5 component | GCP implementation | Decision |
|---|---|---|
| C1 + C2 | **Pub/Sub** topics `genealogy`, `alerts`, `telemetry-live`, `telemetry-backfill`, with a **message storage policy** pinning each region's topics to that region. Retention and seek give 7-day replay. | [ADR-020](../adr/ADR-020-gcp-ingestion-and-hot-path.md) |
| C3 + C6 + C7 | **Manufacturing Data Engine**: Dataflow-based mapping and contextualization (ISA-95), with sinks to **Bigtable** (C6, 90-day garbage-collection policy) and **BigQuery** (C7, 5 years, partitioned). MDE subscribes to both telemetry topics. | [ADR-021](../adr/ADR-021-gcp-time-series-and-analytics.md) |
| C4 | **Dataflow** (Apache Beam) streaming job on **`telemetry-live` + `alerts` only**, with **Vertex AI** online prediction for RUL, output to a `maintenance-recommendations` topic | [ADR-020](../adr/ADR-020-gcp-ingestion-and-hot-path.md) |
| C5 | **Cloud Run** subscriber → SAP PM OData over the Columbus VPN, with an idempotency record in Firestore | [ADR-020](../adr/ADR-020-gcp-ingestion-and-hot-path.md) |
| C8 | **Cloud SQL for PostgreSQL (Enterprise Plus, HA)**, insert-only (grants + trigger + audit), with a hash chain. Nightly digests and a daily Parquet archive go to **Cloud Storage with a locked retention policy (Bucket Lock, 15 years)**. | [ADR-022](../adr/ADR-022-gcp-genealogy-store.md) |
| C9 + C10 | OEE in **BigQuery** (scheduled and incremental queries, with restatement), dashboards in **Looker**. EU aggregate tables are copied to the US global dataset. | [ADR-021](../adr/ADR-021-gcp-time-series-and-analytics.md) |
| C11 | **Vertex AI** training + Model Registry. Models are packaged as signed ONNX containers in Artifact Registry. | [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md) |
| C12 | **GKE Enterprise fleet** (fleet management, Config Sync, Policy Controller) + **Litmus Edge Manager** for MCe | [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md) |
| C13 | **Cloud Logging and Monitoring**, plus Cloud Audit Logs. Approvals and verification go to an append-only audit table in Cloud SQL. | [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md) |

## Build Versus Buy on This Track

**Bought:**
- MCe (Litmus), for the widest protocol coverage and native Sparkplug B of the three tracks
- a commercial MQTT broker
- the GDC software licence

**Built by Kestrel:**
- P3, P4, and P5
- the **entire outbox**: all four lanes, including gap-based backfill
- the activation controller

**Google-provided in the cloud:** MDE supplies the ingestion and contextualization pipeline as a packaged reference solution, which reduces cloud-side build effort compared with AWS.

So on this track the edge is the most *assembled* of the three (three vendors plus the most Kestrel code), while the cloud side is the most *packaged* for manufacturing.

## Edge Sizing (per plant)

- **Cluster:** three industrial servers (16 cores, 64 GB, 2 × 1.92 TB NVMe) as a GDC bare-metal HA cluster (edge profile), with storage replicated across nodes. The node count and hardware are the same as on Azure, because both need a Kubernetes control-plane quorum.
- **MCe:** one instance per 10K tags, which means two instances at about four of the larger plants, about **16 MCe instances fleet-wide**, each separately licensed via Marketplace.
- **Fleet:** **36 nodes**. GDC software is licensed per vCPU. Step 12 compares this with Azure's per-node IoT Operations fee and AWS's per-gateway SiteWise charges.

## Network and Security Summary

- **Region choice:** **us-east5 is in Columbus, Ohio**, next to Kestrel's own data center and MPLS hub. That gives the lowest-latency, shortest path of the three tracks for US and Mexico plants and for SAP integration. The German plants use **europe-west3 (Frankfurt)**.
- **WAN:** Cloud **HA VPN** from Columbus to us-east5, and from each German plant to europe-west3. Cloud Interconnect was rejected for the same reason as ExpressRoute and Direct Connect ([ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md)).
- **Private access and data boundary:**
  - **Private Service Connect** gives private access to Google APIs.
  - **VPC Service Controls** perimeters, one per region, prevent data leaving the approved projects, which enforces NFR-10 at the API layer as well as by storage location.
  - Pub/Sub **message storage policies** and Organization Policy **resource location constraints** pin data to region.
- **Identity:**
  - Humans use **Workforce Identity Federation with Entra ID**, so no Google-side directory is needed.
  - GDC workloads use **fleet Workload Identity** to call Pub/Sub and other Google APIs with no stored keys.
  - Google documents that MCe itself authenticates to Pub/Sub "using a service account key". On this track MCe does **not** publish directly to the cloud. Its output goes through the Kestrel outbox, which uses Workload Identity, so no long-lived key needs to sit in a plant.
- **Guardrails:** Organization Policy, Policy Controller on every GDC cluster, and Security Command Center.

## Observability

GDC clusters export to Cloud Logging and Monitoring. During an outage, the local buffers (about 4.5 hours for logs and about 24 hours for metrics per node) mean **the platform's own telemetry for long outages is partly lost**. Kestrel's outbox and alert metrics are also written to P8, so the plant keeps its own record. The track-specific alert is **MCe tag-count headroom per instance**, because the 10K-tag ceiling is the capacity limit that will be hit first as plants add tags.

## Alignment Check against Step 5

All 23 components are mapped.

| Step 4/5 expectation | GCP reality | Treatment |
|---|---|---|
| Sparkplug B payloads ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)) | **Met natively** by MCe | No deviation. This is the only track where that is true. |
| Plant autonomy (NFR-1) | GDC local operations continue with no documented limit. Lifecycle operations need a connection. | No deviation. Upgrades are scheduled around connectivity. |
| Four-lane outbox ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)) | No native lanes | Fully Kestrel-built. This is scored as build effort and risk in Step 9. |
| Engine-enforced genealogy immutability ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)) | No ledger-table equivalent | Grants, trigger, hash chain, and Bucket Lock, the same as AWS. Weaker than Azure. |
| Single edge vendor | Three at the edge (Google GDC, Litmus, the broker vendor) | Carried as an operations and support risk. Accountability for a plant incident spans three support contracts. |

## Diagram

See [`diagrams/gcp-implementation-architecture.md`](../diagrams/gcp-implementation-architecture.md) (Mermaid reference source for the hand-drawn version).

## Known Deferred Items

- IaC (Terraform, where MDE's own deployment tooling is also used) waits for Step 9.
- MCe licensing tier, the GDC vCPU count, Bigtable nodes, and Dataflow workers are sized in Step 12.
- The broker vendor is a procurement choice.
