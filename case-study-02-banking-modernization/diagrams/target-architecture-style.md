# Diagram: Target Architecture Style (Step 4)

Source of truth for the Step 4 target-style diagram referenced in `docs/architecture-options-and-styles.md`, ADR-001, and ADR-002. Rendered as Mermaid (diagrams-as-code, renders natively on GitHub) rather than a static image, so it stays in sync with the ADRs as they evolve. A hand-drawn version matching the visual style of Case Studies 1 and 3's PNG diagrams can be added alongside this later without replacing it as the source.

```mermaid
flowchart LR
    subgraph Core["Mainframe (Retained)"]
        CICS["COBOL / CICS core banking"]
        DB2["DB2 for z/OS (ledger of record)"]
        CICS --- DB2
    end

    subgraph RT["New Real-Time Integration Layer (Refactor / greenfield)"]
        HOLD["Sync hold/release adapter\n(ADR-001, single narrow call)"]
        CDC["CDC connector\n(reads DB2 log)"]
        BUS[["Event bus / message broker"]]
        LOI["Ledger-of-intent service\n(build)"]
        FRAUD["Fraud orchestration service\n(build)"]
        GATEWAY["ISO 20022 / FedNow gateway\n(buy, ADR-002)"]
    end

    subgraph Channels["Existing Channels"]
        DIGITAL["Digital banking platform\n(retain, integration extended)"]
        NOTIFY["Notifications / mobile analytics\n(replatformed from 2021 AWS account)"]
    end

    GATEWAY -- "ISO 20022 payment" --> HOLD
    HOLD -- "balance check + hold" --> CICS
    HOLD -- "hold result" --> BUS
    DB2 -- "change events" --> CDC
    CDC --> BUS
    BUS <--> LOI
    BUS --> FRAUD
    FRAUD -- "score / decision" --> BUS
    BUS -- "provisional post + status" --> DIGITAL
    BUS -- "confirmation" --> NOTIFY
```

## How to read this diagram

- **Solid boxes inside "Mainframe"** are untouched, existing systems — nothing here changes.
- **The hold/release adapter** is the *only* synchronous path into the mainframe (ADR-001) — it exists purely to prevent a double-spend race condition at authorization time.
- **The CDC connector** is a one-way, read-only tap on the DB2 transaction log — it cannot write back to the mainframe, which is what makes it safe to run without touching COBOL logic.
- **The event bus** is the backbone of the new layer — every other new component talks through it, not directly to each other, which is what will let Steps 6–9 swap in different platform-specific messaging services (Azure Service Bus / Event Hubs, AWS EventBridge/Kinesis, GCP Pub/Sub, or an on-prem equivalent) without changing this shape.
- **The gateway is bought (ADR-002)**; the ledger-of-intent and fraud services are built in-house (ADR-002) — that distinction is why they're labeled separately even though they sit in the same layer.
