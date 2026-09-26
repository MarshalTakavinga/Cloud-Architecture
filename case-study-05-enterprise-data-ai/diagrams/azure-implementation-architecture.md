# Diagram: Azure-Track Implementation (Step 6)

Reference source (Mermaid) for [`docs/azure-implementation.md`](../docs/azure-implementation.md) and [ADR-009](../adr/ADR-009-azure-data-platform.md) to [ADR-014](../adr/ADR-014-azure-network-identity-finops.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph HF["Hartford DC"]
        GW["Guidewire (Oracle)"]
        ECM["ECM"]
        TD[("Teradata (dual-run)")]
    end
    subgraph AZ["Azure — East US 2 (DR: Central US) · private endpoints only"]
        direction TB
        subgraph DBX["Azure Databricks + Unity Catalog"]
            CDC["Oracle CDC tool → bronze"]
            DOC["Doc pipeline jobs\nchunk · ACL attrs"]
            ACL["ACL Sync job"]
            BR[("Bronze")] --> SI[("Silver")] --> GO[("Gold")]
            UC["Unity Catalog\nABAC · tags · lineage\nmodels · eval runs · use-case register"]
            EVAL["MLflow GenAI eval\n+ red-team"]
            LB["Lakebridge\n(Teradata translation)"]
            SQLW["SQL warehouses\n(per workload)"]
            NB["Notebooks\n(SAS replacement)"]
        end
        DI["AI Document Intelligence\n(OCR / layout)"]
        EMB["Azure OpenAI embeddings\n(Data Zone US)"]
        subgraph SRCH["Azure AI Search"]
            HOT[("hot — hybrid + semantic")]
            REF[("reference")]
            WARM[("warm — lexical")]
        end
        ENT["Entitlement service\n(from UC)"]
        RET["Retrieval service\nsecurity filter · final authZ"]
        APP["Claims assistant\n(App Service)"]
        APIM["API Management\nAI gateway"]
        subgraph FDY["Foundry — Data Zone US (ZDR approved)"]
            AOAI["Azure OpenAI models"]
            CL["Claude hosted on Azure"]
        end
        AUD[("Immutable Blob\n7-yr audit + legal hold")]
        FIN["FinOps: system tables\n+ APIM tokens + Cost Mgmt"]
    end
    TAB["Tableau"]

    GW -- "ExpressRoute" --> CDC --> BR
    ECM --> DOC
    DOC --> DI --> DOC
    DOC --> EMB --> HOT
    DOC --> REF
    DOC --> WARM
    ACL --> HOT
    TD -- "Data Box + dual-run" --> BR
    LB -. "translated SQL" .-> SI
    GO --> SQLW --> TAB
    GO --> NB
    UC -. "entitlements" .-> ENT --> RET
    APP --> RET --> HOT
    APP --> APIM --> AOAI
    APIM --> CL
    APIM --> AUD
    EVAL -. "approvals" .-> UC
    UC -. "approved versions" .-> APIM
    RET -. "live permission check" .-> ECM
    APIM --> FIN
    SQLW --> FIN
```

## How to read it

- **Databricks and Unity Catalog are the data core.** Azure-native services surround it where they are stronger: AI Search, Foundry, API Management, and Document Intelligence ([ADR-009](../adr/ADR-009-azure-data-platform.md)).
- **Unity Catalog feeds the entitlement service**, so the AI Search security filter is derived from the same policy source as SQL masking. The index itself sits outside UC, which is the track's governance gap ([ADR-010](../adr/ADR-010-azure-governance-plane.md), [ADR-011](../adr/ADR-011-azure-retrieval.md)).
- **Every model call goes through API Management** to Foundry Data Zone US deployments. Claude is Azure-hosted, not Anthropic-hosted, and every call is logged to immutable storage ([ADR-012](../adr/ADR-012-azure-models-and-ai-gateway.md)).
- **Historical Teradata data arrives by Data Box**, while CDC and dual-run traffic use ExpressRoute ([ADR-014](../adr/ADR-014-azure-network-identity-finops.md)).
