# Diagram: GCP-Track Implementation (Step 8)

Reference source (Mermaid) for [`docs/gcp-implementation.md`](../docs/gcp-implementation.md) and [ADR-021](../adr/ADR-021-gcp-data-platform.md) to [ADR-026](../adr/ADR-026-gcp-network-identity-finops.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph HF["Hartford DC"]
        GW["Guidewire (Oracle)"]
        ECM["ECM"]
        TD[("Teradata (dual-run)")]
    end
    subgraph GCP["GCP — us-east4 (DR: us-central1) · VPC Service Controls perimeter"]
        direction TB
        DS["Datastream\n(Oracle CDC)"]
        subgraph BQ["BigQuery (serverless)"]
            BR[("Bronze — Iceberg")] --> SI[("Silver — Iceberg")] --> GO[("Gold — Iceberg\n+ derived native marts")]
            WARM[("Warm tier text\n+ search index · RLS")]
            REGT[("Use-case register\n+ billing export")]
        end
        DF["Dataform\n(ELT + assertions)"]
        DPX["Dataplex Universal Catalog\npolicy tags · row policies · lineage"]
        SDP["Sensitive Data Protection\n→ policy tags"]
        BMS["BigQuery Migration Service\nTeradata SQL · BTEQ · TPT"]
        STU["BigQuery Studio / Colab\n(SAS replacement)"]
        DAI["Document AI\n(OCR / layout)"]
        CHK["Chunker (Dataflow)\n+ ACL restricts"]
        EMB["Vertex embeddings (US)"]
        VS[("Vertex AI Vector Search\nhot + reference · hybrid · restricts")]
        RET["Retrieval service (Cloud Run)\nrestricts · warm via SEARCH · final authZ"]
        APP["Claims assistant (Cloud Run)"]
        APG["Apigee\nLLM token policies · Model Armor"]
        subgraph VX["Vertex AI — US"]
            GEM["Gemini\n(caching off · abuse-monitoring exception)"]
            CLA["Claude — US multi-region endpoint"]
        end
        MR["Vertex Model Registry\n+ Gen AI evaluation"]
        AUD[("Cloud Storage Bucket Lock\n7-yr + object holds")]
    end
    WIF["Workforce Identity Federation\n⇄ Entra ID"]
    TAB["Tableau (BI Engine)"]

    GW -- "Interconnect" --> DS --> BR
    TD -- "Transfer Appliance + DTS" --> BR
    BMS -. "translated GoogleSQL" .-> DF
    DF --> SI
    GO --> TAB
    GO --> STU
    SDP --> DPX
    DPX -. "enforced in" .-> BQ
    ECM --> DAI --> CHK --> EMB --> VS
    CHK --> WARM
    APP --> RET --> VS
    RET --> WARM
    APP --> APG --> GEM
    APG --> CLA
    APG --> AUD
    MR -. "approvals" .-> REGT
    REGT -. "approved versions" .-> APG
    WIF -. "groups → row policies + restricts" .-> DPX
    RET -. "live permission check" .-> ECM
```

## How to read it

- **BigQuery is the single serverless engine** for ELT, SQL, BI, notebooks, **and the warm retrieval tier**. The system of record is Iceberg-managed tables ([ADR-021](../adr/ADR-021-gcp-data-platform.md)).
- **The warm tier sits inside BigQuery**, so row-level security enforces permissions there. The hot tier (Vector Search) uses application-supplied restricts ([ADR-023](../adr/ADR-023-gcp-retrieval.md)).
- **Apigee is the bought AI gateway**, with Model Armor screening. Models are Gemini (caching disabled) and Claude on the US multi-region endpoint ([ADR-024](../adr/ADR-024-gcp-models-and-ai-gateway.md)).
- **The whole data and AI estate sits inside a VPC Service Controls perimeter** ([ADR-022](../adr/ADR-022-gcp-governance-plane.md)).
