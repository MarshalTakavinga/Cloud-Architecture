# ADR-008: Azure Cloud Ingestion and Event Streaming — Event Hubs Premium

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

Step 5 requires the following of C1 and C2:
- authenticated ingestion that acknowledges only after a durable write
- separate live, backfill, and genealogy streams with independent consumers
- partitioning by site and asset
- replay for 7 days
- 60,000 values/sec sustained, scaling to 150,000 (NFR-3), with 300,000/sec backfill bursts (NFR-4)
- an EU instance for the German plants (NFR-10)

IoT Operations data flows can send natively to Azure Event Hubs, to Kafka-compatible endpoints, and to the Azure Event Grid MQTT broker. Each plant's "device" is an Arc-enabled cluster rather than thousands of individual devices.

## Decision

Use **Azure Event Hubs Premium**, one namespace per region: **East US 2** for the US and Mexico plants and **Germany West Central** for Plants 11–12. Each namespace has four event hubs:

| Event hub | Producers | Consumers | Partition key |
|---|---|---|---|
| `genealogy` | lane 1 journal forwarders | C8 loader | site + part number |
| `alerts` | lane 2 data flows | C4 hot path, C6 | site + asset |
| `telemetry-live` | lane 3 data flows | C4 hot path, C6 (Eventstream) | site + asset |
| `telemetry-backfill` | lane 4 backfill uploaders | C6/C7 **only** | site + asset |

- **Durable acknowledgement:** Event Hubs acknowledges a send only after the event is committed, which gives C1's "ack after durable write" contract directly.
- **Isolation:** the backfill hub is physically separate, so the hot path structurally cannot consume backfill (ADR-005).
- **Replay:** retention is set to 7 days, and Event Hubs Capture writes an Avro copy to ADLS for reprocessing.
- **Access:** private endpoints only. Producers authenticate with Entra workload identities (Arc-enabled workload identity federation for the plant clusters), not shared-access keys.
- **Resilience:** Premium is zone-redundant within the region.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure IoT Hub.** Rejected. Its strengths are per-device identity, device twins, and cloud-to-device messaging for large fleets of individual devices. Here there are 12 plant clusters, and device management is done by Arc and Device Registry. IoT Hub would add a hop, per-message pricing, and a second device-identity system with no benefit. IoT Operations' own documentation routes data flows to Event Hubs or Event Grid rather than through IoT Hub.
2. **The Azure Event Grid MQTT broker as the cloud landing point.** Considered seriously. It would extend the plant UNS into the cloud over MQTT, and it supports Sparkplug B-style workloads, which would partly undo the payload deviation in [ADR-006](ADR-006-azure-edge-platform.md). Rejected as the *primary* stream because Step 5's cloud design depends on a **partitioned, replayable log with independent consumer groups** feeding the hot path, time-series store, and genealogy loader. Event Hubs provides that natively, and Event Grid would need to route into Event Hubs anyway. It remains an option if Kestrel later wants cloud-side MQTT subscribers.
3. **Event Hubs Standard.** Rejected. Its limits on retention and throughput isolation are tighter than a sustained stream plus multi-hour backfill bursts justify, and Premium's dedicated resources prevent another tenant's load from affecting NFR-4.

## Consequences

- **Positive:** It is a Kafka-compatible, partitioned log. Consumers could move to Kafka-ecosystem tools with little change, which helps portability.
- **Positive:** The live, backfill, and genealogy separation from Step 5 maps one-to-one onto event hubs, which is easy to reason about and audit.
- **Negative / accepted trade-off:** Premium processing units are a fixed monthly cost whatever the actual load. Sizing (about 2 PUs in the US and 1 in the EU, as a first estimate) is refined in Step 12.
- **Negative / accepted trade-off:** Two regional namespaces mean two sets of consumers and deployments. That is intentional for residency, but it doubles operational surface.
