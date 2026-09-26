# Diagram: AWS-Track Implementation (Step 7)

Reference source (Mermaid) for [`docs/aws-implementation.md`](../docs/aws-implementation.md) and [ADR-015](../adr/ADR-015-aws-data-platform.md) to [ADR-020](../adr/ADR-020-aws-network-identity-finops.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph HF["Hartford DC"]
        GW["Guidewire (Oracle)"]
        ECM["ECM"]
        TD[("Teradata (dual-run)")]
    end
    subgraph AWS["AWS — us-east-1 (DR: us-east-2) · VPC endpoints only"]
        direction TB
        DMS["AWS DMS\n(Oracle CDC)"]
        subgraph LAKE["Iceberg lakehouse"]
            BR[("S3 Tables — Bronze")] --> SI[("S3 Tables — Silver")] --> GO[("S3 Tables — Gold")]
        end
        GLUE["Glue / EMR Serverless\n(MERGE, ELT)"]
        LF["Lake Formation\nLF-tags · column/cell security"]
        MAC["Macie + Glue detection\n→ LF-tags"]
        RS["Redshift Serverless\n(workgroups per workload)\n+ derived gold marts"]
        ATH["Athena"]
        SUS["SageMaker Unified Studio\n(SAS replacement)"]
        SCT["SCT: Teradata → Redshift\nBTEQ → RSQL"]
        TX["Textract\n(OCR / layout)"]
        CH["Chunker + ACL attrs"]
        EMB["Bedrock embeddings (US)"]
        subgraph OS["OpenSearch Service (FGAC)"]
            HOT[("hot — hybrid · DLS")]
            REF[("reference")]
            WARM[("warm — lexical")]
        end
        ACL["ACL Sync (Lambda)"]
        RET["Retrieval service\nuser role (DLS) + claim filter\n+ final authZ"]
        APP["Claims assistant (Fargate)"]
        GWY["Harborline AI gateway\n(Fargate) · Guardrails\napp inference profiles"]
        BED["Bedrock — US geo profiles\n(no review-retention models)"]
        REG["Model Registry +\nuse-case register (G4)"]
        AUD[("S3 Object Lock\n7-yr + legal hold")]
        FIN["CUR 2.0 · tags · Budgets"]
    end
    IDC["IAM Identity Center\n⇄ Entra ID"]
    TAB["Tableau"]

    GW -- "Direct Connect" --> DMS --> GLUE --> BR
    TD -- "Snowball + dual-run" --> BR
    SCT -. "translated SQL" .-> RS
    GO --> RS --> TAB
    GO --> ATH
    GO --> SUS
    LF -. "enforced in" .-> RS
    LF -. "enforced in" .-> ATH
    MAC --> LF
    ECM --> TX --> CH --> EMB --> HOT
    CH --> REF
    CH --> WARM
    ACL --> HOT
    APP --> RET --> HOT
    APP --> GWY --> BED
    GWY --> AUD
    REG -. "approved versions" .-> GWY
    IDC -. "groups → LF grants + OS roles" .-> LF
    IDC -. "SAML groups" .-> OS
    RET -. "live permission check" .-> ECM
    GWY --> FIN
    RS --> FIN
```

## How to read it

- **Everything is AWS-native.** Unlike the Azure track, there is no cross-cloud data platform. The system of record is native Iceberg (S3 Tables), and Redshift holds only derived gold marts ([ADR-015](../adr/ADR-015-aws-data-platform.md)).
- **Identity Center groups (from Entra) drive both Lake Formation grants and OpenSearch roles.** The planes are aligned by identity rather than by one catalog ([ADR-016](../adr/ADR-016-aws-governance-plane.md)).
- **The OpenSearch hot index enforces document-level security itself**, on line, state, and Restricted. The retrieval service adds the claim-assignment filter and the final authorization check ([ADR-017](../adr/ADR-017-aws-retrieval.md)).
- **The AI gateway is Harborline-built** (AWS has no first-party enterprise LLM gateway). It calls Bedrock US geo profiles, excludes models that require review retention, and logs to Object Lock ([ADR-018](../adr/ADR-018-aws-models-and-ai-gateway.md)).
