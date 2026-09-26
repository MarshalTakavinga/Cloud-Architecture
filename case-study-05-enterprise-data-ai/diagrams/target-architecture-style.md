# Diagram: Target Architecture Style (Step 4)

Reference source (Mermaid) for the Step 4 diagram in [`docs/architecture-options-and-styles.md`](../docs/architecture-options-and-styles.md) and [ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md) to [ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph SRC["Sources (retained)"]
        GW["Guidewire Policy/Claim/Billing\n(Oracle)"]
        CO["Coastal IBM i\n(nightly files)"]
        ECM["ECM — 95M claim documents\n(system of record)"]
        EXT["Third-party data"]
    end

    subgraph ING["Ingestion"]
        CDC["Log-based CDC\n(≤ 15 min)"]
        FILES["Batch file ingest"]
        DOCP["Document pipeline\nextract · chunk · embed · ACL sync"]
    end

    subgraph LH["Lakehouse on open tables (Iceberg / Delta)"]
        BR[("Bronze\nraw")]
        SI[("Silver\nconformed customer · policy · claim · loss")]
        GO[("Gold\nreserving · regulatory · BI marts")]
        BR --> SI --> GO
    end

    subgraph GOV["Unified governance plane"]
        CAT["Catalog · classification · policies\nlineage · model & use-case inventory"]
    end

    subgraph AI["AI layer"]
        IDX[("Retrieval index\nchunks + embeddings + ACL metadata")]
        RET["Retrieval service\n(pre-filtered by entitlements)"]
        APP["Claims assistant\n(citations · human-in-the-loop)"]
        GWY["AI gateway\npolicy · redaction · routing · metering"]
        MOD["Admitted models\n(ZDR hosted · or in-tenancy)"]
        AUD[("Immutable AI audit\n7 years + legal hold")]
        EVAL["Evaluation harness"]
    end

    subgraph USE["Consumption"]
        BI["BI (Tableau)"]
        NB["Actuarial / DS notebooks\n(SAS replacement)"]
        REG["Regulatory exports"]
    end

    GW --> CDC --> BR
    CO --> FILES --> BR
    EXT --> FILES
    ECM --> DOCP --> IDX
    GO --> BI
    GO --> NB
    GO --> REG
    SI -. "claim context" .-> RET
    APP --> RET --> IDX
    APP --> GWY --> MOD
    GWY --> AUD
    EVAL -. "gates every change" .-> GWY
    CAT -. "policies enforced" .-> LH
    CAT -. "entitlements → filters" .-> RET
    CAT -. "admitted models" .-> GWY
```

## How to read it

- **One copy of analytical data**, in open tables with a bronze → silver → gold layout ([ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md)). The conformed insurance model lives in silver.
- **The governance plane's dotted lines reach everything**: the lakehouse, the retrieval service, and the AI gateway. Access rules are defined once ([ADR-002](../adr/ADR-002-unified-governance-plane.md)).
- **ECM stays the system of record for documents.** The index holds chunks, embeddings, and ACL metadata, and retrieval is filtered *before* search by the user's entitlements ([ADR-003](../adr/ADR-003-permission-aware-retrieval.md)).
- **Every model call goes through the AI gateway**, which writes the immutable audit trail and meters cost. The evaluation harness gates every change ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)).
- **Platform-neutral on purpose:** Steps 6–8 fill each box with native, Databricks, or Snowflake components on Azure, AWS, and GCP.
