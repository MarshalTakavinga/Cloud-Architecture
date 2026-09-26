# Step 7: AWS Implementation (including the plant edge)

## Purpose of This Step

This step answers the same questions [Step 6](azure-implementation.md) answered for Azure: what each of the 23 Step 5 components runs on, at the plant and in the cloud, and where AWS's product boundaries force a decision. It is written independently. Where AWS's answer resembles Azure's, that is because the platforms genuinely converge. Where it differs, the difference is the point.

Five findings from AWS's current documentation (September 2026) shape this track more than any single service choice. Each is carried into the Step 9 matrix:

1. **AWS IoT Greengrass v2 is not natively highly available.** AWS's own HA pattern layers Pacemaker/Corosync with DRBD block replication over Greengrass for active/passive failover (sub-minute), and AWS's setup guide labels that approach "for testing and demonstration purposes only". Kestrel would own production hardening. See [ADR-012](../adr/ADR-012-aws-edge-platform.md).
2. **Greengrass stream manager natively provides most of the four-lane outbox:** file-persisted streams, per-export **priority** ("lower values are higher priority"), per-message TTL, a full-stream strategy (`RejectNewData` or `OverwriteOldestData`), and an exporter bandwidth cap. Much less of ADR-005 is custom code than on Azure. See [ADR-013](../adr/ADR-013-aws-store-and-forward-implementation.md).
3. **Amazon Timestream for LiveAnalytics closed to new customers on 20 June 2025.** AWS directs new customers to Timestream for InfluxDB. Kestrel, as a new customer, cannot use the service AWS previously positioned for IoT time series. See [ADR-015](../adr/ADR-015-aws-time-series-and-analytics.md).
4. **Amazon QLDB reached end of support on 31 July 2025**, with Aurora PostgreSQL as AWS's recommended successor. There is no engine-enforced ledger table equivalent on AWS today, so genealogy immutability is assembled from permissions, triggers, a hash chain, and S3 Object Lock. See [ADR-016](../adr/ADR-016-aws-genealogy-store.md).
5. **Ecosystem churn in the same product area:** AWS IoT Analytics was discontinued on 15 December 2025, and SageMaker Edge Manager on 26 April 2024. Edge model deployment on AWS is now done through ordinary Greengrass components.

## Service Mapping

### Plant tier (per plant: 2-node active/passive Greengrass cluster + quorum witness in Level 3, plus DMZ proxy)

| Step 5 component | AWS implementation | Decision |
|---|---|---|
| P1 Edge Connector | **AWS IoT SiteWise Edge, MQTT-enabled (V3) gateway** on Greengrass v2. The **IoT SiteWise OPC UA collector** publishes into the gateway's local MQTT broker. Protocol gateways serve Plant 07 and the Windows 7 HMI plants. `MachineStateChanged` is derived by a Kestrel-built component. | [ADR-012](../adr/ADR-012-aws-edge-platform.md) |
| P2 Plant UNS Broker | The **EMQX broker** bundled with the MQTT-enabled SiteWise Edge gateway, with ISA-95 topics. Sparkplug B is **not** native in the AWS documentation reviewed. It is available through partner components (for example, Cirrus Link's Sparkplug SiteWise Bridge). | [ADR-012](../adr/ADR-012-aws-edge-platform.md) |
| P3, P4 | Kestrel-built **Greengrass components** (P4 runs ONNX Runtime). P4 depends only on the local broker. | [ADR-012](../adr/ADR-012-aws-edge-platform.md) |
| P5 Genealogy Recorder + P6 Journal | A Kestrel-built component writes to a **stream manager stream** (`File` persistence, `flush_on_write`, `RejectNewData`) plus a local SQLite serial index. Both sit on the **DRBD-replicated volume (protocol C, synchronous)**, so a record is on both nodes before `SerialRecorded` is returned. | [ADR-013](../adr/ADR-013-aws-store-and-forward-implementation.md) |
| P7 Edge Outbox (4 lanes) | **Greengrass stream manager**, one stream per lane, exported to Kinesis with priorities 1 / 2 / 3 / 10. The live stream has a 5-minute TTL. A `history` stream (7-day size cap) has its export **disabled in normal running** and is enabled from the first unacknowledged sequence number by a small Kestrel **backfill controller** after an outage. The exporter bandwidth cap is set per plant. | [ADR-013](../adr/ADR-013-aws-store-and-forward-implementation.md) |
| P8 Local Time-Series Store | TimescaleDB as a Greengrass Docker component (30 days). The V3 gateway has no local storage or processing pack. | [ADR-013](../adr/ADR-013-aws-store-and-forward-implementation.md) |
| P9 Edge Deployment Agent | **Greengrass deployments** to per-plant thing groups. The nucleus is notified over its outbound MQTT session and **downloads** signed artifacts from S3 through the proxy. A Kestrel-built activation component enforces shadow → approve → active. | [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md) |
| P10 Cloud Bridge | A DMZ **HTTPS forward proxy** (Squid or Envoy) with an allowlist of AWS IoT, S3, and Kinesis endpoints. Greengrass, stream manager, and the collector all support proxy configuration. Outbound only. | [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md) |

### Cloud tier (US: us-east-2 Ohio · EU: eu-central-1 Frankfurt)

| Step 5 component | AWS implementation | Decision |
|---|---|---|
| C1 + C2 | **Amazon Kinesis Data Streams** (on-demand), four streams per region: `genealogy`, `alerts`, `telemetry-live`, `telemetry-backfill`. Stream manager exports to them natively. Reached through interface VPC endpoints. | [ADR-014](../adr/ADR-014-aws-ingestion-and-hot-path.md) |
| C3 + C4 | **Amazon Managed Service for Apache Flink**. A normalizer job deduplicates on `(site, source, sequence)` with event-time semantics. The hot-path job consumes **`telemetry-live` + `alerts` only** and scores RUL through an **Amazon SageMaker AI** real-time endpoint. | [ADR-014](../adr/ADR-014-aws-ingestion-and-hot-path.md) |
| C5 | **Amazon SQS FIFO** → **AWS Lambda** → SAP PM OData over the Columbus VPN, idempotent on recommendation ID. | [ADR-014](../adr/ADR-014-aws-ingestion-and-hot-path.md) |
| C6 (90 days) | **Amazon Timestream for InfluxDB** (Multi-AZ), fed by the Flink normalizer from both the live and backfill streams | [ADR-015](../adr/ADR-015-aws-time-series-and-analytics.md) |
| C7 (5 years) | **Amazon S3 Tables (Apache Iceberg)**, queried with **Amazon Athena** | [ADR-015](../adr/ADR-015-aws-time-series-and-analytics.md) |
| C9 + C10 | OEE jobs (Athena/Glue) with **Amazon QuickSight** for business reporting and **Amazon Managed Grafana** for plant dashboards. EU aggregates are copied to the US global bucket. | [ADR-015](../adr/ADR-015-aws-time-series-and-analytics.md) |
| C8 | **Aurora PostgreSQL** with insert-only enforcement (privileges + trigger), a unique key, and a hash chain. Daily Parquet export goes to **S3 Object Lock (compliance mode, 15 years)**. | [ADR-016](../adr/ADR-016-aws-genealogy-store.md) |
| C11 | **SageMaker AI** training + Model Registry. Models are packaged as ONNX Greengrass components and signed with AWS Signer. | [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md) |
| C12 | **Greengrass fleet** (thing groups, deployments), **AWS IoT Device Management**, and **AWS Systems Manager** for host OS patching | [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md) |
| C13 | **Amazon CloudWatch** and **AWS CloudTrail**. Approvals and verification results go to an append-only audit table in Aurora. | [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md) |

## Build Versus Buy on This Track

AWS supplies P1, P2, and almost all of P7's lane mechanics (stream manager) natively. Kestrel builds:

- P3, P4, and P5 (as on Azure)
- a small **backfill controller**: control-plane logic only, with the data path native
- the model-activation component
- **the HA layer itself** (Pacemaker/Corosync/DRBD configuration and runbooks)

That last item is what tips the balance. On Azure, Kubernetes and IoT Operations provide HA. On AWS, it is Kestrel's (or an integrator's) responsibility, in 12 plants without IT staff.

## Edge Sizing (per plant)

- **Nodes:** two industrial servers (16 cores, 64 GB, 2 × 1.92 TB NVMe) in active/passive, plus a small quorum witness device, so that Pacemaker cannot fence both nodes into a split-brain.
- **Storage:** about 1 TB DRBD-replicated for Greengrass state, stream manager streams (including 7 days of `history`), and the genealogy stream. P8 TimescaleDB is on the same replicated volume.
- **Fleet:** 12 × 2 = **24 edge servers** plus 12 witnesses. There is no per-node platform fee as there is with Azure IoT Operations. Instead, SiteWise Edge gateway and data charges apply, which are sized in Step 12.

## Network and Security Summary

- **Plant side:**
  - The Level 3 nodes' only egress is the DMZ forward proxy.
  - Greengrass keeps one **outbound** MQTT/TLS session to AWS IoT Core. Deployments are *notified* over that session and *downloaded* by the device. No AWS component can open a connection into the plant.
- **Device identity:** each Greengrass core has its **own X.509 certificate** registered in AWS IoT Core and exchanges it for short-lived AWS credentials (token exchange role). This matches Step 5's per-node certificate model directly.
- **WAN:**
  - The US and Mexico plants reach AWS through Columbus over an **AWS Site-to-Site VPN** (two tunnels) to a **Transit Gateway** in us-east-2, the region nearest Columbus.
  - The German plants use VPNs to a Transit Gateway in eu-central-1.
  - Direct Connect was rejected for the same reason ExpressRoute was on Azure ([ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md)).
- **PaaS access:** interface VPC endpoints for IoT Core (data and credentials provider), Kinesis, SageMaker, and Aurora. An S3 gateway endpoint handles artifacts. SCPs deny public endpoints and non-approved regions.
- **Human identity:** **IAM Identity Center federated to Entra ID**, which is Kestrel's existing identity provider, so there is no second directory.
- **Landing zone:** **Control Tower** with separate OT-Data, Analytics, Genealogy, and EU accounts. The **2024 SageMaker PoC account** is enrolled into the Organization long enough to extract the model code, then its historian data copy is purged and the account is closed, as Step 4 requires on every track.

## Observability

Greengrass component logs and metrics, stream manager export metrics, and host metrics (through the CloudWatch agent over the proxy) go to CloudWatch, with a separate EU account and region for the German plants. The same three plant-level alerts as on Azure apply:

- per-stream backlog
- the genealogy `SerialHeld` rate
- **Pacemaker failover events**, which replace Azure's 48-hour disconnection alert as the edge signal that matters most on this track

## Alignment Check against Step 5

All 23 components are mapped. There are three deviations, all carried to Step 9:

| Step 4/5 expectation | AWS reality | Treatment |
|---|---|---|
| Edge HA on ≥ 2 nodes ([ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md)) | Greengrass is not natively HA. The AWS pattern is active/passive with Pacemaker/DRBD, labeled demo-grade. | Kestrel productionizes the pattern (integrator-supported). Scored as a **risk** and an operations burden. |
| Sparkplug B payloads ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)) | Not native in the reviewed AWS documentation. Partner components exist. | Use native SiteWise-format JSON and meet the liveness intent with LWT and heartbeats, as on Azure. Sparkplug B could be added through a partner at the cost of a license. |
| Engine-enforced immutability for genealogy ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)) | QLDB is retired, and Aurora has no ledger-table equivalent | Immutability is enforced by privileges, a trigger, the hash chain, and S3 Object Lock. It is weaker than Azure's engine-level guarantee, and is scored in Step 9. |

On the other hand, AWS **exceeds** Azure on lane semantics (native priorities and TTL) and on per-node device identity. No 72-hour offline ceiling appears in the AWS documentation reviewed: SiteWise Edge "continues collecting and processing data during internet outages". The practical limits are local disk and certificate validity.

## Diagram

See [`diagrams/aws-implementation-architecture.md`](../diagrams/aws-implementation-architecture.md) (Mermaid, a reference source for the hand-drawn version).

## Known Deferred Items

- IaC (CDK or Terraform) and the Greengrass deployment repository layout wait for platform selection in Step 9.
- Kinesis on-demand versus provisioned, the Timestream for InfluxDB instance class, and Flink KPUs are sized in Step 12.
- The choice of HA integrator (for productionizing Pacemaker/DRBD) is procurement.
