### ADR-017: AWS messaging platform for the Event Bus

**Context:**
`logical-design.md` §2 names the Event Bus as carrying order events — order placed, inventory reserved, payment confirmed, order confirmed, order cancelled, inventory released — between Checkout & Payment, Inventory & Order Orchestration (ADR-016), and the Fulfillment/Warehouse handoff. ADR-002 was explicit that event-driven adoption is scoped narrowly, to this one write path, not a platform-wide messaging fabric — this ADR is deciding infrastructure for a deliberately bounded piece of the system.

**Options considered:**
- Amazon SQS alone (standard or FIFO queues) as the sole mechanism.
- Amazon EventBridge alone, without dedicated per-consumer queues.
- Amazon EventBridge, one custom bus per region with one rule per event type, routing to a dedicated Amazon SQS FIFO queue per consumer.
- Amazon MSK (managed Apache Kafka).

**Decision:**
Amazon EventBridge, one custom event bus per active region, with one rule per event type (`order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`) routing to a dedicated Amazon SQS FIFO queue per consumer. Message group ID is set to the order ID on every queue; native SQS dead-letter queues are enabled on every subscription queue.

**Rationale:**
SQS alone is rejected as the sole mechanism because it's a queue, not a pub-sub/topic system — Fulfillment/Warehouse and Order Orchestration both need their own independent view of the same event stream, and SQS alone would mean the publisher fanning out to multiple queues itself rather than a broker doing it, re-implementing what a topic-and-subscription model already does natively. EventBridge alone (without SQS targets) is rejected because EventBridge's own delivery model, while reliable, doesn't provide FIFO ordering guarantees or a first-class dead-letter-then-inspect pattern the way an SQS FIFO queue with message group IDs does — Order Orchestration's Step Functions trigger (ADR-016) genuinely needs a single order's sequence of events processed in order, the identical requirement ADR-009 named for Service Bus sessions on the Azure track. Amazon MSK is rejected for the same reason ADR-009 rejected Event Hubs on Azure: it's built for high-volume, replayable stream ingestion (telemetry, clickstream), a different problem than transactional order events that need to be reliably processed and moved to a dead-letter queue on repeated failure, not replayed from an arbitrary offset — and even "managed," MSK still hands a 22-person team broker and partition capacity planning for a workload that doesn't need Kafka's throughput ceiling.

The chosen combination — EventBridge for topic/event-type routing, SQS FIFO for per-consumer, per-order-ordered delivery — is the direct AWS-native equivalent of Service Bus's topic-plus-session-enabled-subscription model on Azure: EventBridge's rules are the topics, each consumer's SQS FIFO queue is its subscription, and message group ID = order ID is what keeps one order's events processed in sequence even under concurrent load across many orders, the identical mechanism ADR-009 used session ID = order ID for on the Azure track.

**Trade-off:**
This is two AWS services in the event path instead of one — an extra hop, and an extra thing to configure and monitor per event type. Accepted because, as with ADR-009's Service Bus choice, no single AWS product natively provides both topic-style fan-out and FIFO per-entity ordering with dead-lettering together. SQS FIFO queues cap throughput at 3,000 messages/second with batching (300/second without) per queue — `requirements.md` §1's peak of ~3,750 orders/minute system-wide (~62/second) splits across three regional queues per event type, comfortably inside this limit, worth stating here as a checked assumption rather than an unchecked one. Each active region runs its own independent EventBridge bus and SQS queues (matching the regional-primary shape of the orders that produce these events, per ADR-003) rather than one global bus — meaning, as with ADR-009 on Azure, there is no single global view of "all order events everywhere" without a separate aggregation step, out of scope here for the same reason it was out of scope there.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Event bus | Amazon EventBridge, one custom bus per active region |
| Rules | One per event type — `order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released` |
| Subscriptions | One Amazon SQS FIFO queue per consumer per event type — e.g., Order Orchestration's EventBridge-to-Step-Functions trigger on `order-placed`; Fulfillment/Warehouse's own queue on `order-confirmed` |
| Ordering | SQS FIFO queues, message group ID = order ID |
| Dead-lettering | SQS redrive policy on every subscription queue, `maxReceiveCount` 10, with a CloudWatch alarm on dead-letter queue `ApproximateNumberOfMessagesVisible` > 0 |
| Consumer | Inventory & Order Orchestration (ADR-016), triggered via the EventBridge-to-Step-Functions target; Fulfillment/Warehouse via its own SQS FIFO subscription |

**Status:** Approved
