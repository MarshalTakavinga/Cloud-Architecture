# Step 7: AWS Implementation (native vs. Databricks vs. Snowflake on AWS)

## Purpose of This Step

This step is the second independent mapping of the 22 [Step 5](logical-design.md) components, after [Azure](azure-implementation.md). Every layer is compared three ways, then one **AWS-track stack** is chosen:

- **AWS-native**: S3 Tables, Lake Formation, Redshift, Athena, EMR, SageMaker Unified Studio, OpenSearch, and Bedrock
- **Databricks on AWS**
- **Snowflake on AWS**

The Azure track landed on Databricks at its core. This track is **not** obliged to agree, and it doesn't.

## Findings from Current Documentation (September 2026)

1. **The native open lakehouse is real on AWS.** **S3 Tables** (Apache Iceberg) register in the Glue Data Catalog. **Lake Formation** grants permissions down to "catalogs, databases, tables, **columns, and cells**", with **tag-based access control**, enforced for **Athena, Redshift, EMR, and Glue**. Iceberg is the *native* format here, not a compatibility layer.
2. **OpenSearch Service enforces document-level security natively.**
   - Fine-grained access control supports **document-level security** ("users … can see only the documents that match the query"), **field-level security**, and **field masking**.
   - Roles are mapped to users, IAM roles, or backend roles, including SAML groups.

   This is index-side enforcement, which Azure AI Search offers only in preview and not for Harborline's ECM source.
3. **Bedrock Knowledge Bases and S3 Vectors.**
   - Knowledge Bases' access control is **application-supplied metadata filtering**, with no native document ACLs.
   - **S3 Vectors** (GA 2 December 2025) scales to 2 billion vectors per index, but is vector-only, with no documented keyword or hybrid search.
4. **Bedrock data terms.**
   - Model providers "don't have access to Amazon Bedrock logs or to customer prompts and completions".
   - **Geographic (US) cross-region inference profiles** keep processing within the US on the AWS network, and CloudTrail records the processing region.
   - **Exception:** models whose provider requires human review (currently the **Claude Fable 5 and 5.1** tier) need `aws_review` retention, where prompts and completions are "retained within the AWS boundary for up to 30 days". That fails NFR-4's zero-retention term, so those models are **not admissible** without an explicit legal exception.
5. **Teradata translation is native.** The **AWS Schema Conversion Tool converts Teradata to Redshift, including BTEQ scripts to Redshift RSQL**. This is first-party tooling, unlike Azure, where Microsoft's tooling does not name Teradata.
6. **CDC.** **AWS DMS** is AWS's first-party Oracle CDC service, so no third-party CDC licence is needed. This contrasts with the Azure track ([ADR-013](../adr/ADR-013-azure-ingestion-and-teradata-migration.md)).

## Three-Way Comparison by Layer

| Layer | AWS-native | Databricks on AWS | Snowflake on AWS | AWS-track choice |
|---|---|---|---|---|
| Lakehouse (D1–D4) | **S3 Tables (Iceberg)** + Glue Catalog; Athena, Redshift Serverless, EMR/Glue | Delta/UniForm on S3 + Unity Catalog | Iceberg or native tables, warehouses | **AWS-native** ([ADR-015](../adr/ADR-015-aws-data-platform.md)) |
| Governance (G1–G3) | **Lake Formation** (LF-tags, column/cell) + Macie + SageMaker Catalog | Unity Catalog (single plane for data + AI assets) | Horizon | **Lake Formation** ([ADR-016](../adr/ADR-016-aws-governance-plane.md)) |
| Retrieval (A2–A3) | **OpenSearch Service**: hybrid (BM25 + k-NN), **native DLS/FLS** | Mosaic AI Vector Search (metadata filters) | Cortex Search | **OpenSearch Service** ([ADR-017](../adr/ADR-017-aws-retrieval.md)) |
| Models (A5) | **Bedrock**: Claude and others, US geographic inference profiles | External models via its gateway | Cortex models | **Bedrock (US geo profiles)** ([ADR-018](../adr/ADR-018-aws-models-and-ai-gateway.md)) |
| AI gateway (A4) | No first-party enterprise LLM gateway; Bedrock Guardrails, invocation logging, application inference profiles | Mosaic AI Gateway | Limited | **Harborline gateway service + Bedrock controls** ([ADR-018](../adr/ADR-018-aws-models-and-ai-gateway.md)) |
| CDC (I1) | **DMS** (Oracle CDC) | Third-party or Lakeflow | Third-party/Openflow | **DMS** ([ADR-019](../adr/ADR-019-aws-ingestion-and-teradata-migration.md)) |
| Teradata translation | **SCT: Teradata → Redshift, BTEQ → RSQL** | Lakebridge | SnowConvert AI | **SCT** |
| Notebooks (C2) | SageMaker Unified Studio (EMR Serverless, Athena, Redshift) | Databricks notebooks | Snowflake Notebooks | **SageMaker Unified Studio** |
| FinOps (F1) | **CUR 2.0 + cost-allocation tags + Bedrock application inference profiles** + Redshift workgroups | System tables | Resource monitors | **AWS-native** ([ADR-020](../adr/ADR-020-aws-network-identity-finops.md)) |

## Service Mapping (all 22 components)

| # | Component | AWS-track implementation |
|---|---|---|
| I1 | CDC Connector | **AWS DMS** (Oracle source, CDC) → S3 staging → **Glue streaming / EMR Serverless MERGE** into Iceberg bronze, ≤ 15 min |
| I2 | Batch Ingest | Glue jobs from S3 landing (Coastal files via Transfer Family SFTP, vendor feeds) |
| I3 | Document Pipeline | ECM change feed → **Amazon Textract** (OCR, layout) → structure-aware chunker (Glue/Lambda) → **Bedrock embedding model** (US) → OpenSearch tiers |
| I4 | ACL Sync | Lambda consuming ClaimCenter assignment changes (from bronze) and ECM permissions → partial updates of ACL fields in OpenSearch |
| D1–D3 | Bronze / Silver / Gold | **S3 Tables (Iceberg)** in the Glue Data Catalog. **Redshift Serverless managed storage only for derived gold performance marts** (rebuildable from Iceberg), so the system of record stays open (ADR-001) |
| D4 | Transformation Orchestrator | SQL transformations (dbt-style) orchestrated by **Amazon MWAA**, running on Redshift and Athena, with tests blocking gold |
| D5 | Migration Reconciler | Glue jobs comparing Teradata extracts with Iceberg and Redshift |
| G1 | Catalog and Policy Engine | **Lake Formation**: LF-tags (Restricted / Confidential / Internal, line, state), column and cell permissions. An entitlement service derives user entitlements from Identity Center groups and LF-tags for A2 |
| G2 | Classification | **Amazon Macie** (S3 sensitive-data discovery) + Glue sensitive-data detection → proposed LF-tags. Human confirmation for core entities |
| G3 | Lineage | SageMaker Catalog lineage for Glue, Redshift, and EMR jobs |
| G4 | AI Inventory | **SageMaker Model Registry** (models, evaluation metrics) + a use-case register (DynamoDB) holding approved model IDs, prompt versions, and index versions. The gateway reads it |
| A1 | Claims Assistant | App on **ECS Fargate**, Entra SSO via IAM Identity Center/SAML, launched from ClaimCenter |
| A2 | Retrieval Service | Fargate service: entitlement lookup → OpenSearch query **as the user's mapped role** (DLS) **plus** an application filter for claim assignment → rerank → final authorization check |
| A3 | Retrieval Index | **Amazon OpenSearch Service**: hot (hybrid BM25 + k-NN), reference, and warm (lexical) indices. **FGAC DLS** on line, state, and Restricted by role. Index aliases for blue/green |
| A4 | AI Gateway | **Harborline gateway service** (Fargate, open-source LLM-gateway core) behind API Gateway (private). It handles use-case identification, the G4 check, budgets, and routing. It applies **Bedrock Guardrails** (sensitive-information filters for redaction) and uses **application inference profiles** per use case for cost attribution |
| A5 | Model Endpoints | **Amazon Bedrock** with **US geographic inference profiles**. Admissible: models without mandatory review retention. **Excluded: `aws_review` models** (for example, the Claude Fable tier) unless legal grants an exception |
| A6 | AI Audit Store | Bedrock model-invocation logging + gateway logs → **S3 Object Lock (compliance mode, 7 years) with native legal hold**, plus an Iceberg copy for analysis |
| A7 | Evaluation Harness | Harborline harness on SageMaker Processing (golden set, scorer model ≠ tested model, red-team), with Bedrock Evaluations for model-graded metrics. Results go to G4 |
| C1 | SQL and BI | **Redshift Serverless** workgroups for Tableau; **Athena** for ad hoc queries |
| C2 | Notebooks | **SageMaker Unified Studio** (EMR Serverless Spark, Athena, Redshift), with SAS reading Iceberg via connectors during the transition |
| C3 | Regulatory exports | Glue/Redshift UNLOAD to governed export buckets |
| F1 | FinOps | **CUR 2.0 + cost-allocation tags** (SCP-enforced), **Bedrock application inference profiles per use case**, Redshift workgroups per workload, AWS Budgets and Cost Anomaly Detection |

## Why Not Databricks or Snowflake on This Track

- **Databricks on AWS** would bring the same benefit as on Azure: one catalog (Unity Catalog) spanning data, models, and indexes, which is the strongest ADR-002 fit. It loses on AWS because the native stack here closes most of the gaps that pushed Azure toward Databricks:
  - Iceberg is the native format.
  - Lake Formation enforces column and cell security across four engines.
  - SCT natively translates Teradata, including BTEQ.
  - DMS removes the third-party CDC licence.

  All of that comes with one vendor and one bill. Databricks on AWS is the **runner-up**, and its single-plane governance advantage is scored in Step 9.
- **Snowflake on AWS** (Cortex with Claude available in AWS regions, SnowConvert AI, and absorbing the 2024 account) is again credible. It loses for the same reasons as on Azure: a weaker SAS-replacement workbench, and it would still need OpenSearch and a gateway for non-Snowflake applications.

## Network, Identity, and Security

- **Regions:** us-east-1 (primary, the nearest large region to Hartford) and us-east-2 (DR). SCPs deny non-US regions and **global** (non-US) inference profiles.
- **Hartford to AWS:** **redundant Direct Connect** for CDC, the document flow, and dual-run traffic. **AWS Snowball Edge** for the ~180 TB historical bulk load (the same reasoning as Data Box on Azure).
- **Private networking:** VPC endpoints for S3, Glue, Bedrock (PrivateLink), OpenSearch (VPC domain), Redshift, and DMS. No public endpoints.
- **Identity:** **IAM Identity Center federated with Entra ID** (SAML + SCIM), using the same groups as the rest of Harborline. OpenSearch backend roles are mapped from the SAML groups.
- **Landing zone:** Control Tower with Data, Analytics, AI, Security/Log-Archive, and Network accounts.
- **The 2024 Snowflake account** is retired on this track.

## Observability

CloudWatch (application, OpenSearch, Bedrock metrics), CloudTrail (including the `inferenceRegion` field on cross-region inference), and Redshift and Glue job metrics. The key alerts are the same four as on the Azure track:
- ACL-sync lag
- a final-authorization-check denial
- faithfulness drift
- cost per query above budget

## Alignment Check against Steps 4–5

| Expectation | AWS-track reality | Treatment |
|---|---|---|
| One governance plane reaches retrieval ([ADR-002](../adr/ADR-002-unified-governance-plane.md)) | Lake Formation governs data. **OpenSearch enforces DLS itself**, and its roles derive from the same Entra groups. Models and the inventory are separate (SageMaker Registry + register) | **Split planes, but index-side enforcement.** Stronger at retrieval than Azure, weaker as a single catalog than Unity Catalog. Scored in Step 9 |
| Open format ([ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md)) | **Native Iceberg** (S3 Tables), read by Athena, Redshift, EMR, Glue, and any Iceberg engine. Redshift managed storage only for derived gold marts | **Met, strongest of the tracks so far** |
| ZDR models in the US ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)) | US geo profiles. Providers have no access to prompts. **The review-retention tier is excluded** | Met for admitted models. The frontier tier is constrained. Scored |
| AI gateway ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)) | **No first-party enterprise LLM gateway.** Harborline builds a thin service using Bedrock Guardrails, logging, and inference profiles | Deviation: more build than Azure's API Management |
| Teradata translation ([ADR-005](../adr/ADR-005-teradata-migration-approach.md)) | **First-party SCT, including BTEQ → RSQL** | Met natively |

## Diagram

See [`diagrams/aws-implementation-architecture.md`](../diagrams/aws-implementation-architecture.md) (Mermaid reference source).

## Known Deferred Items

- Redshift Serverless RPU bases, OpenSearch instance sizing (hot tier ~2 TB of text plus vectors), Bedrock throughput (on-demand vs. provisioned), and DMS instance sizing go into the Step 12 cost model.
- IaC (CDK or Terraform) waits for platform selection.
