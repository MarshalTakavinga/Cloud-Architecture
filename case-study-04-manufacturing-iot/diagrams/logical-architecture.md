# Diagram: Logical Architecture (Step 5)

Source of truth for the Step 5 diagrams referenced in [`docs/logical-design.md`](../docs/logical-design.md), [ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md), and [ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md). Component numbers (P1–P10, C1–C13) match the tables in `logical-design.md`. Both diagrams are Mermaid, which renders natively on GitHub, and both are platform-neutral.

## 1. Logical component model

```mermaid
flowchart LR
    subgraph PLANT["Plant tier (×12) — every component on ≥2 edge nodes"]
        direction TB
        L2["Level 2 OPC UA servers\n(read-only source)"]
        STN["Station / MES"]
        subgraph Z3["Level 3 — site operations"]
            P1["P1 Edge Connector\nasset-model mapping · seq no."]
            P2[["P2 Plant UNS Broker"]]
            P3["P3 Vibration Feature Extractor"]
            P4["P4 Edge Anomaly Detector"]
            ALERT["Plant Alerting\n(tablets · paging)"]
            P5["P5 Genealogy Recorder"]
            P6[("P6 Local Genealogy Journal\nhash-chained")]
            P7[("P7 Edge Outbox\n4 priority lanes")]
            P8[("P8 Local Time-Series Store")]
            P9["P9 Edge Deployment Agent\nshadow → approve → active"]
        end
        subgraph Z35["Level 3.5 — DMZ"]
            P10["P10 Cloud Bridge\noutbound-only · DMZ staging"]
        end
        L2 -- "OPC UA read" --> P1
        P1 --> P2
        P3 --> P2
        P2 --> P4
        P4 --> ALERT
        STN -- "RecordSerial" --> P5
        P5 -- "SerialRecorded / SerialHeld" --> STN
        P5 --> P6
        P2 --> P8
        P2 --> P7
        P6 --> P7
        P7 -- "priority drain" --> P10
        P10 -. "signed artifacts (pulled)" .-> P9
        P9 -. "activate model" .-> P4
    end

    subgraph CLOUD["Cloud tier (US region · EU region for DE plants)"]
        direction TB
        C1["C1 Ingestion Endpoint\ncert auth · ack after durable write"]
        subgraph C2["C2 Event Stream"]
            LIVE[["live"]]
            BACK[["backfill"]]
            GENS[["genealogy"]]
        end
        C3["C3 Decoder / Normalizer\ndedupe (site, source, seq)"]
        C4["C4 Hot-Path Processor"]
        C5["C5 Maintenance Adapter"]
        C6[("C6 Time-Series Store\n90 days")]
        C7[("C7 Analytical Store\n5 years · training data")]
        C8[("C8 Genealogy Store\nimmutable · 15 years\n+ Recall Query")]
        C9["C9 OEE / KPI Service"]
        C11["C11 ML Training + Registry"]
        C12["C12 Fleet Management"]
        C1 --> LIVE
        C1 --> BACK
        C1 --> GENS
        LIVE --> C3
        BACK --> C3
        C3 -- "live only" --> C4
        C3 --> C6
        C6 --> C7
        GENS --> C8
        C4 --> C5
        C7 --> C9
        C7 --> C11
        C11 --> C12
    end

    SAP["SAP PM\n(ECC → S/4HANA)"]
    C10["C10 Global KPI Layer\naggregates only"]

    P10 -- "outbound TLS\n(lanes tagged)" --> C1
    C5 --> SAP
    C9 --> C10
    C12 -. "stage artifacts" .-> P10
```

### How to read it

- **Only one arrow crosses the plant boundary outward**, from P10 to C1. The dotted arrow from C12 to P10 is *staging*: artifacts are placed in the DMZ and P9 **pulls** them. Nothing in the cloud opens a connection into the plant ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)).
- **Alerts never leave the plant to be raised.** P4 alerts locally (≤ 10 s) whether or not the WAN is up.
- **C3 feeds C4 from the live stream only.** Backfill goes to storage and OEE, never to the hot path ([ADR-005](../adr/ADR-005-store-and-forward-and-backfill-lanes.md)).
- **Genealogy has its own path end to end:** P5 → P6 → outbox lane 1 → genealogy stream → C8 ([ADR-004](../adr/ADR-004-genealogy-exactly-once-record-path.md)).
- C13 (Observability and Audit) consumes control events from every component. It is omitted from the drawing for readability.

## 2. Genealogy exactly-once path (ADR-004)

```mermaid
sequenceDiagram
    autonumber
    participant STN as Station / MES
    participant REC as P5 Genealogy Recorder
    participant J1 as P6 Journal (node A)
    participant J2 as P6 Journal (node B)
    participant OB as P7 Outbox (lane 1)
    participant BR as P10 Cloud Bridge
    participant ING as C1 Ingestion
    participant GS as C8 Genealogy Store

    STN->>REC: RecordSerial(part no., serial)
    REC->>REC: Assemble record (asset, tool, lot, params, inspection)
    REC->>J1: Append v1 + prev-hash
    J1->>J2: Synchronous replicate
    J2-->>J1: Replicated
    J1-->>REC: Durable
    REC-->>STN: SerialRecorded (part released to packing)
    Note over STN,REC: If the journal write fails, SerialHeld is returned,<br/>the part goes to a hold bin, and the line keeps running
    REC->>OB: Enqueue GenealogyRecorded
    Note over OB,BR: WAN may be down here for hours.<br/>The record waits durably in lane 1
    BR->>OB: Dequeue (highest lane first)
    BR->>ING: Batch (lane 1)
    ING->>GS: Insert keyed (part no., serial, version)
    alt New key
        GS-->>ING: Stored
    else Same key, same hash (redelivery)
        GS-->>ING: No-op (already stored)
    else Same key, different hash
        GS-->>ING: Rejected, quality exception raised
    end
    ING-->>BR: Ack (durably written up to seq n)
    BR->>OB: Release entries up to seq n
    Note over J1,GS: Nightly: compare journal hash-chain head + count<br/>with the store's view. A mismatch becomes an exception
```
