# ADR-007: Azure Service Bus for the Event Bus

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md)'s logical design routes every event after the synchronous hold call — `HoldPlaced`, `FraudApproved`/`FraudDeclined`, `ProvisionallyPosted`, `BatchConfirmed` — through a single event bus consumed by the Fraud Orchestration Service, the Ledger-of-Intent Service, the digital banking platform, and the notification path. [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md) already established that the messaging layer only needs to guarantee at-least-once delivery, since exactly-once *posting* is enforced downstream by the Ledger-of-Intent Service's uniqueness constraint — but the messaging layer does need to preserve **ordering** for events belonging to the same payment (a `FraudDeclined` arriving after a `ProvisionallyPosted` for the same payment, out of order, would be a real correctness problem, not just a cosmetic one).

## Decision

The event bus is **Azure Service Bus, Premium tier, with sessions enabled**, using each payment's end-to-end ID (from ADR-004) as the session key. Sessions guarantee strict in-order, single-consumer processing for all messages sharing that key, which gives ordering per-payment without imposing a single global order across all payments (which would be an unnecessary bottleneck).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure Event Hubs.** Rejected — Event Hubs is built for high-throughput event streaming and analytics ingestion (e.g., telemetry, clickstream), where consumers replay a log rather than receive discrete work items. This case study's flow is closer to a work-queue-with-ordering pattern per payment than a stream-analytics pattern, and Event Hubs' partition-based ordering model would require the same session-key-style discipline as Service Bus while giving up Service Bus's message-level features (dead-lettering, per-message retry policies) that this compliance-sensitive workload benefits from.
2. **Azure Event Grid.** Rejected — Event Grid is designed for reactive, fan-out notification of discrete events to multiple subscribers (closer to a pub/sub eventing backbone for service-to-service triggers), not for ordered, stateful processing of a related sequence of events for the same business entity. It doesn't offer the session-based ordering guarantee this design depends on.
3. **Service Bus Standard tier (without sessions/Premium).** Rejected — Standard tier lacks the dedicated resource isolation and higher throughput guarantees Premium provides, and sessions (required for the per-payment ordering guarantee) come with performance and reliability characteristics that Microsoft's own guidance ties to the Premium tier for production financial workloads.

## Consequences

- **Positive:** Per-payment ordering is guaranteed structurally (via sessions), not by convention or client-side sequencing logic that every consumer would otherwise have to reimplement.
- **Positive:** Dead-lettering and per-message retry policies give the Fraud Orchestration Service and Ledger-of-Intent Service a built-in way to isolate a poison message (e.g., a malformed event) without blocking the session for the next unrelated payment.
- **Negative / accepted trade-off:** Premium tier carries a materially higher baseline cost than Standard tier or Event Grid — accepted here because ordering correctness on a real-money payment flow is a compliance and correctness requirement (NFR-5), not a nice-to-have, and this cost is exactly the kind of trade-off Step 13's cost analysis exists to make explicit.
- **Carried to Step 13:** Messaging-unit sizing (Premium tier is priced/sized in messaging units, not per-message) is deferred to Step 13.
