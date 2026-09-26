# ADR-012: AWS Edge Platform — Greengrass v2 + SiteWise Edge (MQTT-enabled) on an Active/Passive Pair

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

As on the Azure track, [ADR-001](ADR-001-edge-cloud-responsibility-split.md) needs HA edge nodes per plant, managed as a fleet, that keep working with no WAN. [ADR-002](ADR-002-plant-data-integration-pattern.md) needs OPC UA collection into a per-plant MQTT UNS. AWS's industrial edge offering is **AWS IoT SiteWise Edge**, which runs on **AWS IoT Greengrass v2** (or on Siemens Industrial Edge). Its current **MQTT-enabled (V3) gateway** uses MQTT internally, with an EMQX broker, an OPC UA collector, and real-time and buffered (S3) destinations. According to AWS, the V3 gateway "does not support the data processing pack" that the older V2 gateway had.

Three documented facts shape the decision:

- **Greengrass is not natively clustered.** AWS's HA pattern adds Pacemaker/Corosync, with DRBD block replication for active/passive operation (sub-minute failover, preserving device identity and stream manager state). AWS labels the setup "for testing and demonstration purposes only".
- **Offline operation.** SiteWise Edge "continues collecting and processing data during internet outages". No fixed maximum offline duration is documented.
- **EKS Hybrid Nodes** keep the Kubernetes control plane in the AWS Region. During a disconnection, pods keep running, but the kubelet "cannot evict pods" and workloads cannot be mutated until the connection is restored.

## Decision

Each plant runs **Greengrass v2 with the SiteWise Edge MQTT-enabled gateway** on **two industrial servers in active/passive**, with **Pacemaker/Corosync** managing failover, **DRBD (protocol C, synchronous)** replicating the Greengrass root, stream manager, and genealogy volumes, and a **quorum witness** device to prevent split-brain.

- **Native components:** the OPC UA collector (P1), the EMQX broker (P2), and stream manager (P7, see [ADR-013](ADR-013-aws-store-and-forward-implementation.md)).
- **Kestrel-built Greengrass components:** P3, P4, P5, the backfill controller, and the model-activation component.
- **HA hardening:** the HA layer is productionized with an integrator. That includes fencing, failover testing, and runbooks, and it is treated as part of the platform, not as an afterthought.
- **Payload deviation (same as Azure):** native JSON rather than Sparkplug B, with liveness from last-will messages and heartbeats. A partner Sparkplug component remains an option.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A single Greengrass node per plant.** Rejected. It fails ADR-001's HA requirement: one hardware fault stops collection, alerting, and genealogy capture.
2. **Active/active Greengrass, with independent nodes and credentials.** Rejected for the collection path. Two collectors reading the same OPC UA sources would double the load on Level 2 and the data volume, and genealogy needs one authoritative journal.
3. **EKS Hybrid Nodes running Kestrel's own containers.** Rejected. The control plane lives in the Region, so during a WAN outage (exactly when HA matters) a failed node's pods **cannot be rescheduled**. That defeats plant autonomy.
4. **EKS Anywhere (local Kubernetes control plane) with self-assembled components.** Considered. It gives real Kubernetes HA locally, but it gives up SiteWise Edge's native OPC UA collector and stream manager integration, so Kestrel would be building an edge platform. It would also add an EKS Anywhere subscription per cluster.
5. **SiteWise Edge on Siemens Industrial Edge for the two German (Siemens) plants.** Worth noting, but rejected for consistency. Two edge platforms in one fleet would split tooling and runbooks for a 2-of-12-plant benefit.

## Consequences

- **Positive:** Collection, the broker, and buffering come from AWS's industrial-specific offering, with no documented offline ceiling (compare Azure's 72 hours, [ADR-006](ADR-006-azure-edge-platform.md)).
- **Positive:** Two servers plus a witness per plant is a smaller hardware footprint than Azure's three-node Kubernetes cluster, and there is no per-node platform fee.
- **Negative / accepted trade-off:** **HA is Kestrel's responsibility.** Pacemaker/DRBD clusters in 12 plants without IT staff, built from a pattern AWS itself labels demo-grade, is the single largest operational risk on this track. It is scored heavily under "OT/edge fit" and "operational/skills fit" in Step 9.
- **Negative / accepted trade-off:** Active/passive failover takes seconds to under a minute. During that window collection pauses, but the sources, OPC UA servers, and PLCs keep their own values and nothing is written to them. Genealogy requests are answered `SerialHeld` for the failover window, which is safe.
