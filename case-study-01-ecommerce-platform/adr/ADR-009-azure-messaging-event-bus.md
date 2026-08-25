### ADR-009: Azure messaging platform for the Event Bus

**Context:**
`logical-design.md` §2 names the Event Bus as carrying order events  order placed, inventory reserved, payment confirmed, order confirmed, order cancelled, inventory released  between Checkout & Payment, Inventory & Order Orchestration (ADR-008), and the Fulfillment/Warehouse handoff. ADR-002 was explicit that event-driven adoption is scoped narrowly, to this one write path  not a platform-wide messaging fabric, so this ADR is deciding infrastructure for a deliberately bounded piece of the system, not a general-purpose event backbone.

**Options considered:**
- Azure Service Bus  a managed message broker with topics/subscriptions, sessions, and dead-lettering.
- Azure Event Grid  a managed event-routing service built for reactive, fan-out event notification.
- Azure Event Hubs  a managed event-streaming platform built for high-throughput telemetry/log-style ingestion.

**Decision:**
Azure Service Bus, Premium tier, one topic per event type (`order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`), each with subscriptions per consumer, session-enabled using order ID as the session key.

**Rationale:**
Event Grid is rejected because it's built for fire-and-forget reactive notification  it doesn't provide message sessions (ordering guarantees for a related sequence of events) or a first-class retry-then-dead-letter pattern the way Service Bus does, and order orchestration's saga (ADR-008) genuinely needs ordered delivery of events belonging to the same order, not just "something happened, go react." Event Hubs is rejected because it's built for high-volume, append-only stream ingestion (telemetry, clickstream, logs) that downstream consumers replay from an offset  a different problem than transactional order events that each need to be reliably processed exactly enough times and moved to a dead-letter queue on repeated failure, not replayed from an arbitrary point in a stream. Service Bus's session support is what keeps a single order's sequence of events (placed → reserved → confirmed) processed in order even under concurrent load across many orders, using the order ID as the session key; its native dead-lettering means a malformed or unprocessable order event doesn't just vanish  it lands somewhere an operator can inspect and reprocess, directly the same reasoning Case Study 3 applied choosing Service Bus for LinkEngine (ADR-011 there), arrived at independently here because order events have the identical shape: they need ordering per logical entity and they must never silently disappear.

**Trade-off:**
Service Bus Premium's fixed messaging-unit pricing means the Event Bus carries a baseline cost even during low-traffic periods, unlike Event Grid's pure consumption pricing  accepted because Premium's dedicated resources are what deliver the predictable low-latency, high-throughput behavior the 25x peak-event requirement needs; Standard tier's shared, multi-tenant resources are a real risk of noisy-neighbor throttling during exactly the highest-traffic moments this design exists to survive. Each active region runs its own independent Service Bus Premium namespace (matching the regional-primary shape of the orders that produce these events, per ADR-003) rather than one global namespace  meaning an order placed in the EU generates events processed entirely within the EU namespace, with no cross-region event routing. This is a deliberate consequence of ADR-003's regional-primary decision, not a new trade-off invented here, but it does mean there is no single global view of "all order events everywhere" without a separate aggregation step, which  like the cross-region order-analytics gap ADR-003 already named  is out of scope for this design.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Azure Service Bus, Premium tier |
| Namespace count | One per active region (3 total)  no cross-region namespace |
| Messaging units | 1 MU baseline per region, scaling to 4 MU during named peak events (manually scheduled ahead of Black Friday/Cyber Monday and the two named flash-sale days, matching ADR-006's same planned-scaling discipline for database compute) |
| Topics | `order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`  one per region |
| Sessions | Enabled, session ID = order ID |
| Dead-lettering | Enabled on every subscription; max delivery count 10 before dead-letter, with an Azure Monitor alert on dead-letter queue depth > 0 |
| Consumer | Inventory & Order Orchestration service (ADR-008), via KEDA queue-length scaling |

**Status:** Approved

---

See [`../diagrams/azure-messaging-event-bus.png`](../diagrams/azure-messaging-event-bus.png) for the detailed diagram matching this ADR's Decision  the per-region Service Bus Premium namespace, one topic per event type with per-consumer subscriptions, session-ordering by order ID, and native dead-lettering, plus the full Proposed Configuration table. 
