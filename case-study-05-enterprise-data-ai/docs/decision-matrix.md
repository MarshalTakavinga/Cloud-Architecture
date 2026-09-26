# Step 9: Decision Matrix (Azure / AWS / GCP)

## Purpose

[Steps 6](azure-implementation.md)–[8](gcp-implementation.md) each chose a stack within their cloud, after weighing the cloud's native services against Databricks and Snowflake:

- **Azure:** Databricks and Unity Catalog at the core, with Azure AI Search, Foundry, and API Management.
- **AWS:** AWS-native (S3 Tables, Lake Formation, Redshift, OpenSearch, Bedrock, and a custom gateway).
- **GCP:** GCP-native (BigQuery with Iceberg, Dataplex, Vertex AI, and Apigee).

This step scores those three stacks against the weighting recorded in `requirements.md` before any platform work. Unlike Case Study 4, no criterion needed adding, because the six provisional criteria covered every place where the tracks turned out to differ.

## Criteria and Weights

The weights follow `requirements.md`'s priority order, using the same weight shape as Case Study 4 for consistency across the portfolio.

| # | Criterion | Weight | Traced to |
|---|---|---|---|
| 1 | Governance and security fit (one plane, enforcement reaching retrieval, audit, perimeter) | 25% | Driver 1; NFR-3, NFR-4, NFR-6; ADR-002, ADR-003 |
| 2 | AI and RAG capability (model choice under US/ZDR terms, retrieval quality, gateway, evaluation) | 20% | Driver 2; NFR-1, NFR-2, NFR-4; ADR-004, ADR-006, ADR-007 |
| 3 | Data platform and Teradata migration fit (translation incl. BTEQ, CDC, lakehouse) | 15% | Driver 3; NFR-7, NFR-8; ADR-001, ADR-005 |
| 4 | Cost and FinOps (directional until Step 12; attribution quality) | 15% | Driver 5; NFR-11; ADR-008 |
| 5 | Operational and skills fit (a ~35-person team with SQL/SAS/some Python) | 15% | The skills assumption |
| 6 | Portability (open data, portable logic, exit cost) | 10% | NFR-12 |

## Scoring (1–5, 5 = strongest fit)

| Criterion (weight) | Azure (Databricks core) | AWS (native) | GCP (native) |
|---|---|---|---|
| 1. Governance and security (25%) | 3.5 | **4** | **4** |
| 2. AI and RAG capability (20%) | **4.5** | 3.5 | 4 |
| 3. Data platform and Teradata migration (15%) | 3.5 | 4 | **4.5** |
| 4. Cost and FinOps (15%) | 3 | **3.5** | **3.5** |
| 5. Operational and skills (15%) | 3.5 | 2.5 | **4** |
| 6. Portability (10%) | **4** | 3.5 | 3 |
| **Weighted total** | 3.68 / 5.00 (73.5%) | 3.55 / 5.00 (71.0%) | **3.90 / 5.00 (78.0%)** |

*The totals were calculated directly, not estimated. The rationale for every cell is in [ADR-027](../adr/ADR-027-cloud-platform-selection.md).*

### Scoring notes (short form)

1. **Governance and security**
   - **AWS (4):** OpenSearch **enforces document-level security in the index**, Lake Formation provides cell-level security, and Object Lock supports native legal hold. The drawback is three planes, aligned only by identity.
   - **GCP (4):** BigQuery policies govern data *and* the warm retrieval tier in the engine, and **VPC Service Controls** give the strongest exfiltration perimeter. The hot tier relies on application-supplied restricts.
   - **Azure (3.5):** Unity Catalog is the strongest *single catalog* (data, models, evaluations). But AI Search filtering is application-only (native ACLs are preview and don't cover the ECM source).
2. **AI and RAG**
   - **Azure (4.5):** two frontier families in Data Zone US (Azure OpenAI, and Claude hosted on Azure), a mature hybrid search with a semantic ranker, and a bought gateway (API Management).
   - **GCP (4):** Gemini plus Claude's US multi-region endpoint (GA), and Apigee with Model Armor. Two retrieval engines to run.
   - **AWS (3.5):** clean Bedrock terms with no retention application needed, but the **review-retention model tier is excluded** and the gateway is **custom-built**.
   - Azure and GCP both carry contract gates.
3. **Data platform and Teradata migration**
   - **GCP (4.5):** a first-party GA translator for **SQL, BTEQ, and TPT**, plus Datastream CDC, on a serverless engine.
   - **AWS (4):** SCT, including BTEQ → RSQL, plus DMS.
   - **Azure (3.5):** Lakebridge is first-party to Databricks but not to Microsoft, and CDC needs a third-party product.
4. **Cost and FinOps** (directional)
   - **AWS (3.5):** native per-use-case token attribution through application inference profiles, and one vendor, offset by custom-gateway build cost.
   - **GCP (3.5):** reservations per workload, billing data in BigQuery, and one vendor. The Apigee licence is a real cost.
   - **Azure (3):** two platform vendors, a third-party CDC licence, and API Management.
5. **Operational and skills**
   - **GCP (4):** serverless, with no clusters to size.
   - **Azure (3.5):** one unified Databricks workbench, but two vendors.
   - **AWS (2.5):** Redshift, Athena, EMR, Glue, managed OpenSearch domains, *and* a custom gateway to run.
6. **Portability**
   - **Azure (4):** Delta with UniForm, and Databricks is cross-cloud, so even the *translated logic* runs on any cloud's Databricks.
   - **AWS (3.5):** the best *data* openness (native Iceberg), but the logic is Redshift-shaped.
   - **GCP (3):** Iceberg-managed tables with a feature-parity risk, and GoogleSQL-shaped logic.

## Result: GCP

**GCP wins at 3.90, ahead of Azure (3.68) and AWS (3.55).** It leads on three of the six criteria (Teradata migration, operations, and a share of governance) and trails on none by more than one point. Its win rests on two things this case study needs most:

- **The Teradata exit.** It has the broadest first-party GA translation, including BTEQ and TPT, which matters directly for the 31 December 2026 notice date.
- **An operating model a ~35-person team can actually run** (serverless).

## Sensitivity

| Scenario | Azure | AWS | GCP | Winner |
|---|---|---|---|---|
| Primary | 3.68 | 3.55 | **3.90** | GCP |
| Governance weight 35% | 3.65 | 3.61 | **3.91** | GCP |
| AI/RAG weight 30% | 3.78 | 3.54 | **3.91** | GCP |
| Operations weight 5% | 3.70 | 3.67 | **3.89** | GCP |
| Portability weight 20% | 3.71 | 3.54 | **3.80** | GCP |
| Azure governance → 4 (if AI Search native ACLs reached GA for this source) | 3.80 | 3.55 | **3.90** | GCP |
| **GCP risk A:** Iceberg feature parity fails (platform 4, portability 2) | 3.68 | 3.55 | **3.73** | GCP (narrowly) |
| **GCP risk B:** Gemini abuse-monitoring exception denied (AI 3) | 3.68 | 3.55 | **3.70** | GCP (narrowly) |
| **Both GCP risks materialize** | **3.68** | 3.55 | 3.53 | **Azure** |
| *Variant: Databricks on GCP* (runner-up within the GCP track) | — | — | 3.70 | *below GCP-native* |

What this means:

- **GCP's lead is robust to every re-weighting tested.** It is also robust to either of its two known risks *individually*. It is **not** robust to both together, and in that case Azure (Databricks core) is the answer.
- **The two risks can be tested before commitment.** Iceberg feature parity is a technical proof of concept. The abuse-monitoring exception is a contract request. [ADR-027](../adr/ADR-027-cloud-platform-selection.md) makes both **gate G0**, completed **before the Teradata notice date**.
- **"Databricks everywhere" was checked.** Databricks was the runner-up on every track. Scored as a GCP variant it reaches 3.70, below GCP-native, because it gives up the first-party BTEQ/TPT translation and the serverless operating model in exchange for a single catalog. It remains the principled fallback if a multi-cloud future becomes a requirement.

## What the Other Platforms Do Better (named, not hidden)

- **Azure** has the strongest **single governance catalog** (Unity Catalog over data, models, and evaluations), the richest **US-zone model choice** (two frontier families), and the most **portable logic** (Databricks SQL runs on any cloud). If the Iceberg and model-term gates both fail on GCP, Azure is the answer.
- **AWS** has the only **index-enforced document-level security** (OpenSearch DLS), the most open **data** layer (native Iceberg), **no retention application** needed for admitted models, and **native per-use-case token attribution**. If Harborline's security team weights retrieval enforcement above everything else, AWS closes the gap.
- **GCP's own weaknesses remain:**
  - hot-tier retrieval security is application-supplied (like Azure's)
  - translated logic is GoogleSQL-shaped
  - the Iceberg-parity question is unresolved until the proof of concept
  - two contract gates before go-live

## What This Matrix Deliberately Does Not Resolve

- **Dollar costs** are for Step 12. The cost criterion here is directional.
- **Timing** against the Teradata notice (31 December 2026) and term end (30 June 2027), including whether the bridge extension is needed, belongs to Steps 10–11.
