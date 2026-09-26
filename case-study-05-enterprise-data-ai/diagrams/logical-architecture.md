# Diagram: Logical Architecture (Step 5)

Reference sources (Mermaid) for [`docs/logical-design.md`](../docs/logical-design.md) and [ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md) to [ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md). Component numbers match the table in `logical-design.md`. Hand-drawn versions will be produced from these sources. Both diagrams are platform-neutral.

## 1. Logical component model

```mermaid
flowchart LR
    subgraph SRC["Sources"]
        GW["Guidewire (Oracle)"]
        CO["Coastal files"]
        ECM["ECM documents"]
    end
    subgraph ING["Ingestion"]
        I1["I1 CDC Connector"]
        I2["I2 Batch Ingest"]
        I3["I3 Document Pipeline\nextract · chunk · embed"]
        I4["I4 ACL Sync"]
    end
    subgraph LH["Lakehouse (open tables)"]
        D1[("D1 Bronze")]
        D2[("D2 Silver\nunified insurance model")]
        D3[("D3 Gold\ntriangles · regulatory · BI")]
        D4["D4 Transformation Orchestrator"]
        D5["D5 Migration Reconciler"]
    end
    subgraph GOV["Governance plane"]
        G1["G1 Catalog & Policy Engine"]
        G2["G2 Classification"]
        G3["G3 Lineage"]
        G4["G4 AI Inventory"]
    end
    subgraph AI["AI layer"]
        A1["A1 Claims Assistant"]
        A2["A2 Retrieval Service"]
        A3[("A3 Retrieval Index\nhot · reference · warm")]
        A4["A4 AI Gateway"]
        A5["A5 Model Endpoints"]
        A6[("A6 AI Audit Store")]
        A7["A7 Evaluation Harness"]
    end
    subgraph USE["Consumption & FinOps"]
        C1["C1 SQL / BI"]
        C2["C2 Notebooks"]
        C3["C3 Regulatory exports"]
        F1["F1 FinOps Metering"]
    end
    TD[("Teradata (dual-run)")]

    GW --> I1 --> D1
    CO --> I2 --> D1
    ECM --> I3 --> A3
    GW -. "assignments" .-> I4
    ECM -. "permissions" .-> I4
    I4 --> A3
    D1 --> D4 --> D2 --> D3
    D3 --> C1
    D3 --> C2
    D3 --> C3
    TD --> D5
    D3 --> D5
    A1 --> A2 --> A3
    A1 --> A4 --> A5
    A4 --> A6
    A7 --> G4
    G4 -. "approved versions" .-> A4
    G1 -. "entitlements" .-> A2
    G1 -. "policies" .-> LH
    G2 --> G1
    G3 -. "lineage" .-> LH
    A4 --> F1
    LH --> F1
```

### How to read it

- **ECM feeds only the index, never the lakehouse as content.** Documents stay in ECM, and the index holds chunks, embeddings, and ACL attributes ([ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md)).
- **I4 ACL Sync is a separate path from I3.** Permission changes update index metadata without re-embedding anything.
- **G4 gates A4:** the gateway only serves use cases, prompts, and models approved by the evaluation harness ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md)).
- **Everything that costs money reports to F1** ([ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md)).

## 2. Flow A — Adjuster asks the assistant (sequence)

```mermaid
sequenceDiagram
    autonumber
    actor U as Adjuster
    participant A1 as A1 Claims Assistant
    participant G1 as G1 Catalog / Policy
    participant A2 as A2 Retrieval Service
    participant A3 as A3 Retrieval Index
    participant A4 as A4 AI Gateway
    participant G4 as G4 AI Inventory
    participant A5 as A5 Admitted Model
    participant SRC as ClaimCenter / ECM
    participant A6 as A6 AI Audit

    U->>A1: Question (from claim in ClaimCenter)
    A1->>A2: query + user identity + claim ID
    A2->>G1: entitlements for user?
    G1-->>A2: lines, states, assigned claims, Restricted flag
    A2->>A3: hybrid search WITH entitlement filter
    A3-->>A2: authorized candidate chunks
    A2->>A2: rerank, assemble context + citation anchors
    A2-->>A1: context
    A1->>A4: prompt + context (use case, prompt version)
    A4->>G4: use case / prompt / model approved?
    G4-->>A4: approved + data-class policy
    A4->>A4: redact per policy, meter tokens
    A4->>A5: inference (US region, ZDR or in-tenancy)
    A5-->>A4: answer with cited source IDs
    A4-->>A1: answer
    A1->>A2: verify citations
    A2->>SRC: live permission check per cited doc
    SRC-->>A2: allowed / denied
    Note over A2,SRC: Denied → drop citation and its content,<br/>log security event
    A2-->>A1: verified citations
    A1-->>U: answer + clickable citations (advisory only)
    U->>A1: accept / edit / discard / feedback
    A4->>A6: audit record: user, claim, prompt, sources,<br/>model version, response, user action
```

### How to read it

- **Steps 3–6: permissions are applied before search**, so unauthorized chunks are never candidates ([ADR-003](../adr/ADR-003-permission-aware-retrieval.md)).
- **Steps 10–11: the gateway refuses anything not approved in the AI Inventory.**
- **Steps 16–19: every cited document is re-checked against the live source system** before display. This catches ACL-sync lag.
- **The last step writes the complete record to the immutable audit store**, including what the adjuster did with the answer (NFR-6).
