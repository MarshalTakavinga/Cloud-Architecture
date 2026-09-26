# ADR-002: Plant Data Integration Pattern — Unified Namespace

**Status:** Approved
**Date:** Step 4 of the Case Study 4 pipeline

## Context

Each plant has several data producers: PLCs through Level 2 OPC UA servers, MES, genealogy capture, and new vibration sensors. It also has several consumers: the existing historian, MES, edge analytics, and the cloud bridge. Today every consumer connects directly to every source it needs.

About 180,000 tags follow no common naming convention (see `requirements.md`, "tag-model debt"). [ADR-003](ADR-003-ot-segmentation-reference-architecture.md) needs as few conduits through the zone boundaries as possible. `requirements.md` also asks for portability if a cloud-side IoT service is ever retired.

## Decision

Each plant runs a **Unified Namespace (UNS)**: one MQTT broker (HA pair) in the Level 3 site-operations zone.

- **Collection:** OPC UA remains the collection protocol at Level 2. Edge connectors read OPC UA, or native drivers through protocol gateways for Plant 07's Mitsubishi line and the Windows 7 HMI plants. They map each source tag to the enterprise asset model once, and publish.
- **Topic structure:** topics follow an ISA-95 hierarchy: `kestrel/<site>/<area>/<line>/<asset>/<signal>`.
- **Payloads:** machine telemetry uses the **Sparkplug B** payload specification. Business events (work-order start/complete, serial produced, quality result) use a versioned JSON schema on a parallel `kestrel/<site>/events/...` branch.
- **Consumers:** every consumer, including the historian, MES, edge analytics, and the cloud bridge in the DMZ, subscribes to the broker. None connects to the machines.

Genealogy events are published to the UNS for local visibility, but their **system-of-record write** is not the MQTT publish itself. Its exactly-once durable path is defined in Step 5.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Point-to-point connectors (the status quo).** Rejected. Connections and firewall rules grow with every new consumer, adding load on Level 2 OPC UA servers and multiplying the conduits that [ADR-003](ADR-003-ot-segmentation-reference-architecture.md) is trying to minimize.
2. **Historian federation.** All consumers read through historian APIs. Rejected. It inherits five historian products and two plants with no historian, and it makes the historian vendor's data model and licensing the enterprise backbone (see [ADR-001](ADR-001-edge-cloud-responsibility-split.md), alternative 2).
3. **Plain MQTT with free-form JSON, without Sparkplug B.** Considered seriously. It is simpler, and every cloud handles JSON natively. It was rejected for machine telemetry only, because it has no standard way to signal that a data source has gone offline. Sparkplug B's birth/death certificates let the edge and the cloud tell a genuine zero apart from a disconnected sensor. Without that, anomaly detection raises false alarms and OEE counts a lost connection as machine downtime. Free-form versioned JSON is still used for business events, where Sparkplug's metric model is a poor fit.

## Consequences

- **Positive:** Each data source is collected once. Adding a consumer means adding a subscription, with no new PLC or OPC UA connection and no new firewall rule into Level 2.
- **Positive:** The topic hierarchy *is* the enterprise asset model, so the tag-naming debt is paid once, at the connector, per plant. This effort then paces the rollout plant by plant in Step 11.
- **Positive:** The plant side is built on open standards (OPC UA, MQTT, Sparkplug B). Changing the cloud platform, or losing a managed IoT service, changes only the bridge's cloud-side endpoint. No plant is re-instrumented.
- **Negative / accepted trade-off:** The plant broker becomes a critical local component. If it fails, collection and local alerting stop. It must therefore run as an HA pair with local persistence, and its health is a first-class monitoring signal.
- **Negative / accepted trade-off:** Sparkplug B's binary (protobuf) payloads are less human-readable than JSON, and not every cloud IoT service decodes them natively. Where one does not, decoding happens at the cloud bridge or in the first stream-processing stage. This is compared across tracks in Steps 6–8.

## Open Question Carried to Step 5

Broker product (open-source or commercial) and whether the broker and the edge compute share the same HA nodes are platform-track decisions for Steps 6–8. This ADR fixes the **pattern and the naming standard**.
