# ADR-006: Azure Edge Platform — Azure IoT Operations on 3-Node K3s

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

[ADR-001](ADR-001-edge-cloud-responsibility-split.md) places collection, the UNS broker, buffering, anomaly detection, and genealogy capture inside each plant, on HA edge nodes managed as a fleet by a team that has no edge operations experience today. [ADR-002](ADR-002-plant-data-integration-pattern.md) calls for OPC UA collection into a per-plant MQTT UNS with Sparkplug B telemetry. NFR-1 requires plants to keep working with no WAN connection, with at least 72 hours of buffer.

Microsoft's current edge direction is **Azure IoT Operations**: an Arc-enabled Kubernetes platform with an MQTT broker, a connector for OPC UA and other southbound connectors, Azure Device Registry assets, and data flows to Event Hubs, Event Grid, ADLS, Fabric, and Azure Data Explorer. The older **Azure IoT Edge** runtime is still maintained. Three facts from Microsoft's documentation shape this decision:

- Azure IoT Operations "can operate offline for a maximum of 72 hours. Degradation might occur during this period."
- AKS Edge Essentials supports **single-node** IoT Operations deployments only. Multi-node deployments are supported on K3s (Ubuntu), AKS on Azure Local, and Tanzu.
- The connector for OPC UA publishes **JSON with CloudEvents headers**, which include a per-message sequence number and source timestamps. It does not publish Sparkplug B.

## Decision

Each plant runs **Azure IoT Operations on a 3-node, Arc-enabled K3s cluster (Ubuntu)** on industrial-grade servers in the Level 3 zone.

**IoT Operations provides:**
- P1: the connector for OPC UA, with assets in Azure Device Registry and ISA-95 destination topics per dataset
- P2: the multi-node MQTT broker, with persistence enabled
- lanes 2–3 of P7: data flows (see [ADR-007](ADR-007-azure-store-and-forward-implementation.md))

**Kestrel-built containers on the same cluster provide:** P3, P4, P5, and the two outbox services. They are delivered by GitOps ([ADR-011](ADR-011-azure-network-identity-and-deployment.md)).

**Two rules keep NFR-1 true despite the 72-hour statement:**
1. **P4 (alerting) and P5/P6 (genealogy) depend only on local data-plane components**: the broker's local MQTT listener and the local PostgreSQL. They make no Azure calls at runtime, and their certificates are issued from a plant-local CA with lifetimes measured in months.
2. A **48-hour disconnection alert** and a **WAN resilience upgrade at Ramos Arizpe** (a second carrier or LTE) are part of the rollout, so the 72-hour documented limit is never approached in practice. Kestrel's worst observed outage is 19 hours.

**Accepted deviation from [ADR-002](ADR-002-plant-data-integration-pattern.md):** telemetry uses IoT Operations' native JSON/CloudEvents payload, not Sparkplug B. ADR-002's *intent*, telling a disconnected source from a real value, is met by connector and asset status, MQTT last-will messages, and a heartbeat topic per source. The UNS pattern and the ISA-95 topic hierarchy are unchanged.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure IoT Edge (modules on single devices).** It is lighter, and it offers effectively unlimited offline operation. Rejected because Kestrel would have to assemble the broker, the OPC UA collection, the asset model, and the cloud data paths from modules it selects and maintains itself. That is more building for a team with no edge experience, on the runtime that is not Microsoft's forward direction for industrial sites.
2. **IoT Operations on AKS Edge Essentials (Windows).** Rejected because it is single-node only, which fails the HA requirement in [ADR-001](ADR-001-edge-cloud-responsibility-split.md). A single node failure would stop collection and genealogy capture.
3. **IoT Operations on Azure Local (AKS on Azure Local), 2–3 nodes per plant.** Considered seriously. It could also host the plants' Level 3 Windows VMs (historian, MES) and consolidate hardware. Rejected *for now*: it needs validated hardware, has a heavier licensing and operations footprint across 12 sites without IT staff, and consolidating Level 3 VMs is outside this initiative's scope. It is the natural evolution if Kestrel later standardizes plant compute.
4. **A non-Microsoft industrial edge platform with Azure as the cloud only.** Deferred to the Step 9 comparison. Every track can pair its cloud with a third-party edge, so this does not help tell the platforms apart. What is being compared here is Azure's own edge story.

## Consequences

- **Positive:** Five of the ten plant components come from supported Microsoft products with a single management plane (Arc) across the 36 nodes, which directly addresses the "edge sprawl" risk.
- **Positive:** Assets are Azure resources (Device Registry), so the enterprise asset model is governed with Azure RBAC and Policy rather than in a spreadsheet.
- **Negative / accepted trade-off:** The platform's documented 72-hour offline ceiling sits exactly on NFR-1's floor. The mitigations above make it a monitored risk rather than a design flaw, and it is **scored as a risk in Step 9**.
- **Negative / accepted trade-off:** Moving away from Sparkplug B reduces plant-side portability. A future move off Azure would mean re-mapping payloads at the broker, though not re-instrumenting machines.
- **Negative / accepted trade-off:** IoT Operations is billed per node per hour, so 36 nodes is a real recurring cost line in Step 12. Its hardware requirements (16 GB RAM and 8 cores minimum per the published guidance, with more for multi-node) rule out small gateway-class devices.
