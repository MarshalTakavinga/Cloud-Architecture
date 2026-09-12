# ADR-019: Google Cloud Pub/Sub for the Event Bus

**Status:** Approved
**Date:** Step 8 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md)'s logical design routes every event after the synchronous hold call — `HoldPlaced`, `FraudApproved`/`FraudDeclined`, `ProvisionallyPosted`, `BatchConfirmed` — through a single event bus consumed independently by the Fraud Orchestration Service, the Ledger-of-Intent Service, the Digital Banking Integration path, and the Audit/Compliance Log. [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md) already established that the messaging layer only needs at-least-once delivery, but it still needs to preserve **ordering** for events belonging to the same payment, and needs **four independent subscribers** to see the same event stream.

## Decision

The event bus is a single **Google Cloud Pub/Sub topic**, with **four independent subscriptions** (one each for Fraud Orchestration, Ledger-of-Intent, Digital Banking Integration, and Audit/Compliance Log). Each payment's end-to-end ID (from [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md)) is set as the message's **ordering key**, which guarantees in-order delivery within each subscription for messages sharing that key, without imposing a single global order across all payments. Each subscription has its own dead-letter topic for poison-message isolation.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Eventarc.** Rejected — Eventarc is built for routing discrete events from GCP services to triggers (a reactive, fan-out router), the same role Azure Event Grid and AWS EventBridge play, and neither of those was chosen as the primary event bus for the same reason: it offers no native ordering-key/session guarantee for a related sequence of events belonging to one business entity.
2. **Cloud Tasks.** Rejected — Cloud Tasks is a managed task queue built for dispatching work to a single handler per task, not for fanning the same event out to multiple independent subscribers; it does not fit Step 5's requirement that four separate components each maintain their own view of the same event stream.
3. **A single Pub/Sub subscription shared by all four consumers.** Rejected — a shared subscription splits messages across whichever subscribers are pulling from it (competing-consumer semantics), so any one message would reach only one of the four components, not all of them. Four separate subscriptions on the same topic is the mechanism Pub/Sub itself provides specifically for this fan-out-to-independent-subscribers pattern.

## Consequences

- **Positive:** Per-payment ordering is guaranteed structurally (via the ordering key), not by convention or client-side sequencing logic every consumer would otherwise have to reimplement.
- **Positive:** Pub/Sub combines topic/subscription fan-out, per-key ordering, and dead-lettering in a single product — where Azure needed one integrated product (Service Bus) and AWS needed two ([ADR-013](ADR-013-aws-messaging.md), SNS + SQS FIFO), GCP needs exactly one. This is the same structural characteristic this portfolio's other GCP tracks have already found for Pub/Sub — a genuine, repeatable platform fact, not a coincidence of restating the same answer.
- **Negative / accepted trade-off:** None specific to this workload — the main trade-off named elsewhere in this portfolio (ordering keys apply per-region, not globally, for very high-throughput multi-region topics) doesn't bind here, since NFR-6 already confines this workload to a single US region.
- **Carried to Step 13:** Pub/Sub throughput provisioning and per-subscription acknowledgment-deadline tuning are cost and sizing decisions deferred to Step 13.
