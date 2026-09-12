# ADR-028: Self-Managed RabbitMQ for the Event Bus

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

As in every other track, events after the synchronous hold call — `HoldPlaced`, `FraudApproved`/`FraudDeclined`, `ProvisionallyPosted`, `BatchConfirmed` — must reach four independent subscribers (Fraud Orchestration, Ledger-of-Intent, Digital Banking Integration, Audit/Compliance Log) with ordering preserved per payment. No managed messaging service exists on private infrastructure.

## Decision

**RabbitMQ**, self-managed, deployed as a **clustered, highly-available broker** mirrored across the primary and secondary data-center sites established in [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md). Each payment's end-to-end ID ([ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md)) is used as the routing key into a **Consistent Hash Exchange**, which routes all messages sharing that key to the same queue, preserving per-payment order. A dedicated queue per consumer is bound to a single fan-out exchange, with dead-letter exchanges configured per queue for poison-message isolation.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Apache Kafka.** Considered — a legitimate, widely adopted self-hosted messaging platform. Rejected narrowly, for the same reasoning every other track used to reject its platform's own high-throughput streaming product (Event Hubs, Kinesis Data Streams): Kafka is built for log-based streaming and consumer-group replay, a weaker match for this design's actual shape — a small number of purpose-built consumers processing discrete, ordered payment events — than a queue-and-exchange model. Kafka's own operational surface (partition rebalancing, consumer-offset management, a coordination layer) is also materially heavier for Palisade's team to run day-to-day than RabbitMQ, working against the same cloud-skills-gap concern already named in [ADR-024](ADR-024-private-cloud-compute-platform.md).
2. **ActiveMQ Artemis.** Considered as a closer conceptual analog to Azure Service Bus's own JMS-influenced heritage. Rejected narrowly — RabbitMQ has broader current adoption and a larger available operational knowledge base for Palisade's team to draw on, with equally mature clustering and HA support for this workload's actual needs; no capability in this design specifically favors Artemis.

## Consequences

- **Positive:** Full control over the messaging layer with no consumption-based cost tied to message volume — a genuine cost-model difference worth quantifying in Step 13 against the three managed alternatives.
- **Negative / accepted trade-off:** Palisade's own team must operate RabbitMQ's clustering, patching, and capacity planning — the same recurring finding as [ADR-024](ADR-024-private-cloud-compute-platform.md) and [ADR-025](ADR-025-private-cloud-database.md): a private-cloud platform trades every hyperscaler managed-service convenience for direct operational ownership, at every layer of this track without exception.
- **Carried to Step 13:** Cluster sizing and throughput capacity planning are cost and sizing decisions deferred to Step 13.
