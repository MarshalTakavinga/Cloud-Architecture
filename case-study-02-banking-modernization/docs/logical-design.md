# Step 5: Vendor-Neutral Logical Design

## Purpose of This Step

[Step 4](architecture-options-and-styles.md) fixed the *shape* of the solution — the integration style ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)) and the build-vs-buy split ([ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md)). This step goes one layer deeper: it defines the logical components, their responsibilities, and the contracts between them precisely enough to implement — but still without naming a single Azure, AWS, GCP, or private-cloud service. That naming happens in Steps 6–9. If this document had to be rewritten to add a platform name anywhere, it would mean this step was done too early.

## Logical Component Model

| Component | Responsibility | Interface / Contract |
|---|---|---|
| ISO 20022/FedNow Gateway (bought, [ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md)) | Terminates the FedNow/RTP rail connection; validates and normalizes incoming ISO 20022 payment messages | Publishes a `PaymentReceived` event carrying amount, account, and the message's end-to-end ID (used as the idempotency key — [ADR-004](../adr/ADR-004-idempotency-and-exactly-once-delivery.md)) |
| Hold/Release Adapter ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)) | The single synchronous call into CICS: checks balance and places a hold at authorization time; releases the hold on a downstream decline | Synchronous request/response with CICS; consumes `PaymentReceived`, emits `HoldPlaced` or `HoldRejected` |
| Fraud Orchestration Service | Scores the payment within the NFR-4 300ms budget, using account and behavioral context | Consumes `HoldPlaced`; emits `FraudApproved` or `FraudDeclined` |
| Ledger-of-Intent Service | System of record for real-time payment state (`Authorized` → `Provisionally Posted` → `Confirmed`); enforces the idempotency constraint from [ADR-004](../adr/ADR-004-idempotency-and-exactly-once-delivery.md) | Consumes fraud decisions; emits `ProvisionallyPosted`; exposes a status-query interface |
| CDC Connector | One-way, read-only tap on the DB2 for z/OS transaction log; observes the mainframe's actual overnight batch confirmation | Publishes `BatchConfirmed`, keyed by the same idempotency key |
| Reconciliation Process ([ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) | Nightly job matching `ProvisionallyPosted` entries against `BatchConfirmed` events; flags exceptions | Reads Ledger-of-Intent and the CDC event log; raises exception records for anything unmatched after the batch window closes |
| Digital Banking Integration | Surfaces payment status to the existing digital banking platform, honestly distinguishing "pending" from "posted" per [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)'s state model | Subscribes to Ledger-of-Intent status events; the existing nightly batch-file interface is retained unchanged for non-real-time functions |
| Audit/Compliance Log | Immutable, 7-year-retained record of every event (NFR-7) | Append-only consumer of all bus events; no component may delete or mutate a record once written |
| Event Bus | The backbone connecting every component above | Platform-agnostic publish/subscribe abstraction — the concrete technology is chosen independently on each of the four tracks in Steps 6–9 |

## End-to-End Data Flow (Happy Path)

1. A customer-initiated FedNow payment arrives at the **ISO 20022/FedNow Gateway** as a validated, normalized `PaymentReceived` event, carrying the message's end-to-end ID as its idempotency key.
2. The **Hold/Release Adapter** makes the one synchronous call into CICS ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)) to check the available balance and place a hold. Insufficient funds emits `HoldRejected` and the customer sees a decline in under a second — the flow stops here.
3. A successful hold emits `HoldPlaced`.
4. The **Fraud Orchestration Service** scores the transaction within the NFR-4 300ms budget and emits `FraudApproved` or `FraudDeclined`. A decline triggers the Hold/Release Adapter to release the hold back through the same synchronous channel.
5. On approval, the **Ledger-of-Intent Service** records the payment as `Provisionally Posted` — the idempotency-key uniqueness constraint ([ADR-004](../adr/ADR-004-idempotency-and-exactly-once-delivery.md)) means a duplicate or redelivered event at this point is a no-op, not a second posting.
6. **Digital Banking Integration** subscribes to that status change and shows the customer a "posted" (pending) balance update — this is the real-time experience the whole initiative exists to deliver, and it completes well inside the NFR-3 5-second budget.
7. Independently, that night, the mainframe's unmodified batch settlement process actually books the transaction into DB2, exactly as it always has (driver 5 protected).
8. The **CDC Connector** observes that booking via the DB2 transaction log and emits `BatchConfirmed`, carrying the same idempotency key.
9. The nightly **Reconciliation Process** ([ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) matches `BatchConfirmed` events against `Provisionally Posted` ledger-of-intent entries by idempotency key. A clean match promotes the entry to `Confirmed` automatically. An entry with no match by the next business day is raised as a manual-review exception — never silently dropped, and never silently auto-confirmed.
10. Every event in the sequence above is captured verbatim, append-only, in the **Audit/Compliance Log**, satisfying NFR-7's 7-year retention requirement and giving OCC/BSA-AML examiners a complete, reconstructable record of every decision.

## Diagram

See [`diagrams/logical-architecture.md`](../diagrams/logical-architecture.md) (Mermaid sequence diagram) and [`diagrams/logical-architecture.png`](../diagrams/logical-architecture.png) (swim-lane flow diagram, numbered end-to-end) for the full flow covering both the happy path and the two decline branches (insufficient funds, fraud decline), plus the nightly reconciliation path — both verified component-by-component against this document. [`diagrams/target-architecture-style.png`](../diagrams/target-architecture-style.png) (introduced in [Step 4](architecture-options-and-styles.md)) also depicts this step's component model and state machine in a single static view.

## Key Decisions Made at This Step

Two questions were left open at the end of Step 4 and are resolved here, both recorded as ADRs so the reasoning and rejected alternatives survive alongside the decision:

- **[ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)** — how "provisionally posted" and "batch-confirmed" are modeled as distinct states, and how the nightly reconciliation between them actually works.
- **[ADR-004](../adr/ADR-004-idempotency-and-exactly-once-delivery.md)** — how NFR-5's exactly-once posting requirement is met given that the event bus itself only guarantees at-least-once delivery.

## What Step 5 Deliberately Leaves Open

Nothing above names a specific message broker, database, or compute service — every component is described purely by its responsibility and its contract with its neighbors. That is intentional: Steps 6 through 9 will each take this exact logical model and answer "what does this look like built on Azure / AWS / GCP / a private-cloud footprint," and the fact that this model doesn't have to change to accommodate any of those four answers is itself the proof that this step was done correctly.
