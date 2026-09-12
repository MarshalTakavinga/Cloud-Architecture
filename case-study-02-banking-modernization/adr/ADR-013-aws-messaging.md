# ADR-013: Amazon SNS FIFO + SQS FIFO for the Event Bus

**Status:** Approved
**Date:** Step 7 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md)'s logical design routes every event after the synchronous hold call — `HoldPlaced`, `FraudApproved`/`FraudDeclined`, `ProvisionallyPosted`, `BatchConfirmed` — through a single event bus consumed independently by the Fraud Orchestration Service, the Ledger-of-Intent Service, the Digital Banking Integration path, and the Audit/Compliance Log. [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md) already established that the messaging layer only needs at-least-once delivery, since exactly-once *posting* is enforced downstream by the Ledger-of-Intent Service's uniqueness constraint — but the messaging layer still needs to preserve **ordering** for events belonging to the same payment, and needs **four independent subscribers** to see the same event stream, not one queue with competing consumers.

## Decision

The event bus is an **Amazon SNS FIFO topic**, fanning out to **four per-consumer Amazon SQS FIFO queues** (one each for Fraud Orchestration, Ledger-of-Intent, Digital Banking Integration, and Audit/Compliance Log), using each payment's end-to-end ID (from [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md)) as the **Message Group ID**. FIFO ordering guarantees strict in-order delivery within a message group, giving per-payment ordering without imposing a single global order across all payments. Each queue has its own Dead-Letter Queue for poison-message isolation, and SQS FIFO's own deduplication is used as a defense-in-depth layer, not a replacement for the Ledger-of-Intent Service's enforced uniqueness constraint.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Amazon EventBridge as the primary event bus.** Rejected — same reasoning [ADR-007](ADR-007-azure-messaging.md) used to reject Azure Event Grid: EventBridge is a rules-based router built for reactive fan-out to many possible targets, not for guaranteed same-key ordering of a related event sequence, and it has no native FIFO/message-group ordering semantics. (EventBridge Scheduler is still used narrowly, per [ADR-011](ADR-011-aws-compute-platform.md), to trigger the nightly Reconciliation task — a different job than serving as the event bus itself.)
2. **Amazon Kinesis Data Streams.** Rejected — same reasoning [ADR-007](ADR-007-azure-messaging.md) used to reject Azure Event Hubs: Kinesis is built for high-throughput streaming and analytics replay, not discrete work-item delivery with per-message dead-lettering and retry policies. Achieving per-payment ordering would require shard-key discipline equivalent to a Message Group ID, while giving up the per-message DLQ/redrive semantics this compliance-sensitive workload benefits from.
3. **A single SQS FIFO queue polled by all four consumers.** Rejected — SQS queues (FIFO or standard) deliver each message to only one consumer in a competing-consumers model; every message would reach only one of the four subscribers, not all of them, which directly breaks Step 5's requirement that Fraud Orchestration, Ledger-of-Intent, Digital Banking Integration, and the Audit/Compliance Log each maintain their own independent view of the same event stream. The topic-plus-per-consumer-queue pattern exists specifically to give each subscriber its own queue.

## Consequences

- **Positive:** Per-payment ordering is guaranteed structurally (via the Message Group ID), not by convention or client-side sequencing logic every consumer would otherwise have to reimplement.
- **Positive:** Each subscriber's own Dead-Letter Queue isolates a poison message for that consumer without blocking the same session for the next unrelated payment or affecting the other three subscribers.
- **Negative / accepted trade-off:** This is AWS's second product for the event bus — a topic (SNS) plus per-consumer queues (SQS) — rather than one integrated broker the way Azure's Service Bus (topics + subscriptions + sessions, one product) provides. This is the same platform-shape difference [ADR-007](ADR-007-azure-messaging.md) named for Azure's own AWS-track comparison, confirmed here as accurate now that AWS's actual implementation is worked out, and carried forward honestly into Step 10 rather than minimized.
- **Carried to Step 13:** SNS/SQS throughput provisioning and per-queue visibility-timeout tuning are cost and sizing decisions deferred to Step 13.
