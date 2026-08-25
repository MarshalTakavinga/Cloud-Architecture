### ADR-025: GCP messaging platform for the Event Bus

**Context:**
`logical-design.md` §2 names the Event Bus as carrying order events  order placed, inventory reserved, payment confirmed, order confirmed, order cancelled, inventory released  between Checkout & Payment, Inventory & Order Orchestration (ADR-024), and the Fulfillment/Warehouse handoff. ADR-002 was explicit that event-driven adoption is scoped narrowly, to this one write path, not a platform-wide messaging fabric  this ADR is deciding infrastructure for a deliberately bounded piece of the system.

**Options considered:**
- Google Cloud Pub/Sub alone  topics with per-consumer subscriptions, ordering keys, and dead-letter topics.
- Cloud Pub/Sub paired with Cloud Tasks for per-consumer queueing.
- A managed Apache Kafka offering on GCP (e.g., Confluent Cloud via GCP Marketplace, or a self-managed cluster on GKE).

**Decision:**
Google Cloud Pub/Sub, one set of topics per active region (one topic per event type  `order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`), with one subscription per consumer per event type. Ordering keys are set to the order ID on every subscription that needs per-order sequencing; dead-letter topics are configured natively on every subscription.

**Rationale:**
This ADR lands on a materially different answer than ADR-009 (Azure) and ADR-017 (AWS), and the reason is worth stating plainly rather than treated as an implementation detail: **Google Cloud Pub/Sub natively provides everything both other platforms needed a second product for.** Azure needed Service Bus's topic-plus-session-enabled-subscription model as one integrated product; AWS needed EventBridge for topic-style event-type routing *and* a separate SQS FIFO queue per consumer for per-order ordering and dead-lettering  two distinct services glued together (ADR-017). Pub/Sub's topic/subscription model already provides the pub-sub fan-out Fulfillment/Warehouse and Order Orchestration both need (each gets its own independent subscription against the same topic), its ordering keys guarantee per-key (per-order) in-sequence delivery within a subscription  the same mechanism SQS FIFO's message group ID and Service Bus sessions provide, using order ID as the key  and dead-letter topics are a first-class, natively-configured subscription property, not a bolted-on second queue. Cloud Pub/Sub paired with Cloud Tasks was considered and rejected because it reintroduces the two-product shape this platform specifically doesn't need  Cloud Tasks solves a task-queueing problem Pub/Sub's subscriptions already solve here, adding a second service to configure and monitor without closing a capability gap. A managed Kafka offering is rejected for the same reason ADR-009 rejected Event Hubs and ADR-017 rejected MSK: it's built for high-volume, replayable stream ingestion (telemetry, clickstream), a different problem than transactional order events that need reliable, ordered, dead-letter-on-failure processing, not replay from an arbitrary offset  and it hands a 22-person team broker and partition capacity planning for a workload that doesn't need Kafka's throughput ceiling.

**Trade-off:**
Enabling ordering keys on a subscription carries a documented per-key throughput characteristic that should be checked against this workload's shape rather than assumed  worth stating here as a checked assumption: each order uses its own distinct key, and `requirements.md` §1's peak of ~3,750 orders/minute system-wide (~62/second) splits across per-order keys well inside Pub/Sub's per-key guidance, the same "comfortably inside the limit" framing ADR-017 gave SQS FIFO's own throughput cap. The "one product instead of two" simplification is real but not "zero operational surface"  dead-letter topics still need their own subscription and monitoring configured per event type, the same discipline ADR-009 and ADR-017 required of their own dead-letter mechanisms, just concentrated in one product's configuration surface instead of two. Each active region runs its own independent set of Pub/Sub topics and subscriptions (matching the regional-primary shape of the orders that produce these events, per ADR-003) rather than one global topic set  meaning, as with the other two tracks, there is no single global view of "all order events everywhere" without a separate aggregation step, out of scope here for the same reason it was out of scope there.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Event bus | Google Cloud Pub/Sub, one topic set per active region |
| Topics | One per event type  `order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released` |
| Subscriptions | One Pub/Sub subscription per consumer per event type  e.g., Order Orchestration's Eventarc trigger on `order-placed` (ADR-024); Fulfillment/Warehouse's own subscription on `order-confirmed` |
| Ordering | Pub/Sub ordering keys, key = order ID |
| Dead-lettering | Native dead-letter topic on every subscription, `maxDeliveryAttempts` 10, with a Cloud Monitoring alert on dead-letter topic message count > 0 |
| Consumer | Inventory & Order Orchestration (ADR-024), triggered via Eventarc; Fulfillment/Warehouse via its own Pub/Sub subscription |

**Status:** Approved
