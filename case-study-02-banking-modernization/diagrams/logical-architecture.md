# Diagram: Logical Architecture — Real-Time Payment Sequence (Step 5)

Source of truth for the Step 5 logical-design sequence diagram referenced in [`docs/logical-design.md`](../docs/logical-design.md), [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md), and [ADR-004](../adr/ADR-004-idempotency-and-exactly-once-delivery.md). Where [`diagrams/target-architecture-style.md`](target-architecture-style.md) (Step 4) shows the *structure* of the components, this diagram shows their *behavior* over time — the actual sequence of events for one real-time payment, including both decline branches. Rendered as Mermaid (diagrams-as-code, renders natively on GitHub). A companion numbered swim-lane version matching the visual style of Case Studies 1 and 3 is also available: [`diagrams/logical-architecture.png`](logical-architecture.png) — it lays out the same event sequence, decision points, and the nightly reconciliation path across explicit component lanes, and was checked against this file, `docs/logical-design.md`, ADR-003, and ADR-004 event-by-event and NFR-by-NFR.

```mermaid
sequenceDiagram
    participant Gateway as ISO 20022/FedNow Gateway
    participant Hold as Hold/Release Adapter
    participant CICS as CICS (mainframe, retained)
    participant Bus as Event Bus
    participant Fraud as Fraud Orchestration
    participant LOI as Ledger-of-Intent
    participant Digital as Digital Banking Platform
    participant CDC as CDC Connector
    participant Recon as Reconciliation (nightly)
    participant Audit as Audit/Compliance Log

    Gateway->>Bus: PaymentReceived (end-to-end ID)
    Bus->>Hold: PaymentReceived
    Hold->>CICS: balance check + hold (sync, ADR-001)
    CICS-->>Hold: hold result

    alt insufficient funds
        Hold->>Bus: HoldRejected
        Bus->>Digital: payment declined
    else hold placed
        Hold->>Bus: HoldPlaced
        Bus->>Fraud: HoldPlaced
        Fraud->>Bus: FraudApproved / FraudDeclined
        alt fraud declined
            Bus->>Hold: release hold
            Hold->>CICS: release (sync)
            Bus->>Digital: payment declined
        else fraud approved
            Bus->>LOI: record Provisionally Posted (idempotency key, ADR-004)
            LOI->>Bus: ProvisionallyPosted
            Bus->>Digital: payment posted (pending, ADR-003)
        end
    end

    Note over CICS: Overnight batch settlement runs independently — unmodified (driver 5)
    CICS->>CDC: DB2 transaction log (read-only)
    CDC->>Bus: BatchConfirmed (same idempotency key)
    Bus->>Recon: BatchConfirmed
    Recon->>LOI: match against Provisionally Posted (ADR-003)
    alt match found
        Recon->>LOI: promote to Confirmed
    else no match by next business day
        Recon->>Recon: raise reconciliation exception
    end

    Note over Audit: every event above is captured verbatim, append-only (NFR-7)
```

## How to read this diagram

- **The two `alt` blocks in the top half** are the two ways a real-time payment can be declined — insufficient funds (caught by the single synchronous CICS hold) and fraud (caught by the Fraud Orchestration Service). Both complete in well under the NFR-3 5-second budget.
- **Everything below the first "Note over CICS"** happens hours later, asynchronously, and is not on the customer-facing critical path at all — this is the reconciliation loop that closes the gap ADR-001 accepted as a trade-off.
- **The bottom `alt` block** is the one exception path that matters most for correctness: an unmatched provisional posting is never silently resolved either way — it becomes a tracked exception, per ADR-003.
