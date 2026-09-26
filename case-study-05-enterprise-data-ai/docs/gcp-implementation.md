# Step 8: GCP Implementation (native vs. Databricks vs. Snowflake on GCP)

## Purpose of This Step

This step is the third independent mapping of the 22 [Step 5](logical-design.md) components, after [Azure](azure-implementation.md) (a Databricks core with Azure AI services) and [AWS](aws-implementation.md) (AWS-native). Every layer is compared three ways, then one **GCP-track stack** is chosen:

- **GCP-native**: BigQuery, BigLake/Iceberg, Dataplex Universal Catalog, Datastream, Vertex AI, and Apigee
- **Databricks on GCP**
- **Snowflake on GCP**

## Findings from Current Documentation (September 2026)

1. **Teradata translation is first-party and GA.** BigQuery's SQL translators list **"Teradata and Teradata Vantage"** with support for **SQL, Basic Teradata Query (BTEQ), and Teradata Parallel Transport (TPT)**, among the fully supported (non-preview) translations. BigQuery Data Transfer Service moves the data itself.
2. **Claude on Vertex AI has a US multi-region endpoint.** It was announced on 15 April 2026 and reached **GA on 15 May 2026**. Requests "automatically route … across multiple regions within a single geography", and data processing "remains within your preferred geography". The endpoint uses `locations/us`.
3. **Vertex AI data governance.**
   - "Google won't use your data to train or fine-tune any AI/ML models without your prior permission or instruction."
   - Gemini models **cache data in memory for 24 hours by default**. Caching can be disabled per project.
   - Prompts may be logged for abuse monitoring. Customers "can request an exception for abuse monitoring" to reach zero retention.
   - The document covers "all managed models on Vertex AI". **Partner-model (Claude) terms are separate and must be confirmed.**
4. **Vertex AI Search document ACLs are preview.** Documents carry `acl_info` readers (users and groups, with Entra supported via Workforce Identity Federation).
   - Limited to **3,000 readers per document**.
   - Access control **cannot be enabled or disabled after data-store creation**.
   - Status is **preview**.
5. **Apigee** documents LLM token policies, **Model Armor** integration, and semantic caching as AI-gateway capabilities. As on Azure, and unlike AWS, the gateway is **bought rather than built**.
6. **BigQuery-native governance.** Column-level access control (policy tags), row-level security, and dynamic masking are native. **BigQuery tables for Apache Iceberg** (BigLake) put Iceberg data under BigQuery management and security.

## Three-Way Comparison by Layer

| Layer | GCP-native | Databricks on GCP | Snowflake on GCP | GCP-track choice |
|---|---|---|---|---|
| Lakehouse (D1–D4) | **BigQuery** + **BigQuery tables for Apache Iceberg**; serverless | Delta/UniForm on GCS + Unity Catalog | Iceberg or native tables | **GCP-native** ([ADR-021](../adr/ADR-021-gcp-data-platform.md)) |
| Governance (G1–G3) | **Dataplex Universal Catalog** + BigQuery policy tags, row-level security, masking + Sensitive Data Protection | Unity Catalog | Horizon | **Dataplex + BigQuery policies** ([ADR-022](../adr/ADR-022-gcp-governance-plane.md)) |
| Retrieval (A2–A3) | **Vertex AI Vector Search** (hybrid dense + sparse, restricts); **BigQuery search indexes**; Vertex AI Search (ACLs preview) | Mosaic AI Vector Search | Cortex Search | **Vector Search (hot/reference) + BigQuery search (warm)** ([ADR-023](../adr/ADR-023-gcp-retrieval.md)) |
| Models (A5) | **Vertex AI**: Gemini (managed), **Claude US multi-region (GA)** | External models | Cortex | **Vertex AI, US** ([ADR-024](../adr/ADR-024-gcp-models-and-ai-gateway.md)) |
| AI gateway (A4) | **Apigee** LLM token policies + Model Armor | Mosaic AI Gateway | Limited | **Apigee** |
| CDC (I1) | **Datastream** (Oracle) → BigQuery | Third-party | Third-party | **Datastream** ([ADR-025](../adr/ADR-025-gcp-ingestion-and-teradata-migration.md)) |
| Teradata translation | **BigQuery translator: SQL, BTEQ, TPT (GA)** | Lakebridge | SnowConvert AI | **BigQuery Migration Service** |
| Notebooks (C2) | BigQuery Studio / Colab Enterprise (Python, SQL, Spark via serverless Spark) | Databricks | Snowflake Notebooks | **BigQuery Studio** |
| FinOps (F1) | **Billing export to BigQuery** + labels + **BigQuery reservations per workload** | System tables | Resource monitors | **GCP-native** ([ADR-026](../adr/ADR-026-gcp-network-identity-finops.md)) |

## Service Mapping (all 22 components)

| # | Component | GCP-track implementation |
|---|---|---|
| I1 | CDC Connector | **Datastream** (Oracle, log-based) → BigQuery bronze. Merged into Iceberg-managed tables, ≤ 15 min |
| I2 | Batch Ingest | Cloud Storage landing → BigQuery loads / Dataflow for files and vendor feeds |
| I3 | Document Pipeline | ECM change feed → **Document AI** (OCR, layout) → Harborline chunker (Dataflow) → **Vertex AI embeddings (US)** → Vector Search; warm-tier text → BigQuery table with a **search index** |
| I4 | ACL Sync | Dataflow/Cloud Run job updating Vector Search restricts and the warm-tier BigQuery ACL columns |
| D1–D3 | Bronze / Silver / Gold | **BigQuery tables for Apache Iceberg** as the system of record. Native BigQuery storage only for derived gold performance marts |
| D4 | Transformation Orchestrator | **Dataform** (SQL transformations in Git, assertions blocking gold) |
| D5 | Migration Reconciler | BigQuery jobs comparing Teradata extracts (via Data Transfer Service) with migrated tables |
| G1 | Catalog and Policy Engine | **Dataplex Universal Catalog** (business catalog and aspects) + **BigQuery policy tags** (column), **row-level access policies**, dynamic masking. Entitlement service from Entra groups (via Workforce Identity Federation) |
| G2 | Classification | **Sensitive Data Protection** discovery profiles → proposed policy tags. Human confirmation for core entities |
| G3 | Lineage | Dataplex data lineage (BigQuery, Dataform, Dataflow) |
| G4 | AI Inventory | **Vertex AI Model Registry** + Vertex AI evaluation results + a use-case register (BigQuery table). Apigee reads approvals |
| A1 | Claims Assistant | **Cloud Run** app with Entra SSO via Workforce Identity Federation, launched from ClaimCenter |
| A2 | Retrieval Service | Cloud Run: entitlement lookup → Vector Search query with **restricts** (line, state, claim/unit, Restricted) → rerank (Vertex ranking) → warm-tier fallback via BigQuery `SEARCH` under the user's row policies → final authorization check |
| A3 | Retrieval Index | **Vertex AI Vector Search** (hot hybrid dense + sparse; reference) + **BigQuery search index** (warm, lexical, governed by row-level security) |
| A4 | AI Gateway | **Apigee**: LLM token policies (quota and budgets per use case), **Model Armor** (prompt and response screening, sensitive-data filters), semantic caching where safe, G4 check, logging |
| A5 | Model Endpoints | **Vertex AI, US**: Gemini (with **in-memory caching disabled** and the **abuse-monitoring exception** approved) and **Claude via the US multi-region endpoint** (partner terms confirmed by legal) |
| A6 | AI Audit Store | Apigee and application logs → **Cloud Storage with Bucket Lock** (locked 7-year retention, object holds for legal hold) + BigQuery copy |
| A7 | Evaluation Harness | **Vertex AI Gen AI evaluation** + Harborline harness (golden set, a different scorer model, red-team); results to G4 |
| C1 | SQL and BI | BigQuery with **BI Engine** for Tableau |
| C2 | Notebooks | **BigQuery Studio / Colab Enterprise** (Python, SQL, serverless Spark), with SAS via connectors during the transition |
| C3 | Regulatory exports | BigQuery EXPORT to governed buckets |
| F1 | FinOps | **Cloud Billing export to BigQuery**, labels and tags, **BigQuery reservations assigned per workload project**, Apigee token analytics per use case, budgets and anomaly alerts |

## Why Not Databricks or Snowflake on This Track

- **Databricks on GCP** again offers Unity Catalog's single plane. On GCP the native stack answers the migration questions *first-party* and GA: BTEQ and TPT translation, Datastream CDC, and serverless BigQuery with no clusters to size. It adds a bought gateway (Apigee) and GA US-geography Claude. Databricks is the **runner-up**.
- **Snowflake on GCP** is rejected for the same reasons as on the other tracks.

## Network, Identity, and Security

- **Regions:** **us-east4** (N. Virginia, primary) and **us-central1** (DR). These match the regions the Claude US multi-region endpoint routes across. Organization Policy restricts resource locations to the US.
- **Hartford to GCP:** **Dedicated Interconnect** (redundant) for CDC, documents, and dual-run traffic. **Transfer Appliance** for the historical bulk load.
- **Perimeter:** **VPC Service Controls** around the data and AI projects (BigQuery, Vertex AI, Cloud Storage) block exfiltration at the API layer. **Private Service Connect** gives private access to Google APIs.
- **Identity:** **Workforce Identity Federation with Entra ID** for people. Service accounts with workload identity for services.
- **The 2024 Snowflake account** is retired on this track.

## Observability

Cloud Logging and Monitoring, BigQuery `INFORMATION_SCHEMA` job statistics, and Apigee analytics. The same four key alerts as the other tracks: ACL-sync lag, final-authorization denials, faithfulness drift, and cost per query.

## Alignment Check against Steps 4–5

| Expectation | GCP-track reality | Treatment |
|---|---|---|
| One governance plane reaches retrieval ([ADR-002](../adr/ADR-002-unified-governance-plane.md)) | BigQuery policies (via Dataplex) govern data **and the warm tier** (the BigQuery search index runs under row-level security). The **hot tier (Vector Search) uses application-supplied restricts**. Models are in the Vertex Registry | **Partial.** Between Azure and AWS: engine-enforced for warm, app-enforced for hot |
| Open format ([ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md)) | BigQuery tables for Apache Iceberg as the system of record, with native storage for derived marts only | Met. Some BigQuery features differ on Iceberg tables, to be checked in the pilot |
| ZDR models in the US ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)) | Gemini: no training, caching disabled, abuse-monitoring **exception required**. Claude: US multi-region GA, **partner terms to confirm** | Met, subject to contract gates (similar to Azure) |
| AI gateway | **Apigee** (bought) | Met, like Azure |
| Teradata translation ([ADR-005](../adr/ADR-005-teradata-migration-approach.md)) | **First-party GA: SQL, BTEQ, TPT** | Met natively, the broadest documented first-party coverage |

## Diagram

See [`diagrams/gcp-implementation-architecture.md`](../diagrams/gcp-implementation-architecture.md) (Mermaid reference source).

## Known Deferred Items

- BigQuery edition and reservation slots per workload, Vector Search index shards and replicas, Apigee tier, Vertex throughput, and Datastream volumes go into the Step 12 cost model.
- IaC waits for platform selection.
