# Steps 2–3: Capabilities Required, Requirements, and NFRs

## Step 2: Business Capabilities Required

Traced to the five ranked drivers in `problem-statement.md`:

1. **AI governance and control plane:** a model and use-case inventory, pre-deployment evaluation (quality, safety, bias where relevant), approval workflow, prompt and response audit logging, and policy enforcement over which data may reach which model. (Driver 1)
2. **Governed retrieval over claims knowledge:** ingestion, text extraction, chunking, and embedding of about 40M text-bearing claim documents plus coverage forms and state handling guidelines, with **document-level access control enforced at retrieval time**. (Drivers 1, 2)
3. **A claims knowledge assistant:** a RAG application for adjusters and underwriters that answers with **citations to source documents**, summarizes claim files, and drafts routine correspondence for human review. (Driver 2)
4. **A modern analytical platform:** a lakehouse or cloud warehouse in **open table formats**, replacing Teradata, with Teradata SQL workloads migrated or rewritten and the Informatica jobs rationalized. (Driver 3)
5. **A unified insurance data model:** conformed customer, policy, claim, and loss entities across Guidewire, Coastal, and third-party data, with change-data-capture from ClaimCenter and PolicyCenter. (Driver 4)
6. **Catalog, lineage, and classification:** column-level and document-level classification (Restricted / Confidential / Internal), lineage from source to report and to model, and masking policies driven by classification. (Drivers 1, 4)
7. **FinOps:** tagging and allocation of 100% of spend, unit-cost reporting (per claim, per assistant query, per report), budgets and anomaly alerts, and commitment management. (Driver 5)
8. **A governed data-science and actuarial workbench** to replace SAS over time, with access to the same governed data. (Drivers 3, 4)

## Step 3: Non-Functional Requirements

| # | NFR | Target | Driven by |
|---|-----|--------|-----------|
| NFR-1 | Assistant response latency | p95 ≤ 6 s to the first complete answer with citations; p95 ≤ 2 s to first token (streamed) | Driver 2 (adjusters abandon slow tools) |
| NFR-2 | Assistant groundedness | 100% of factual answers carry citations. **≥ 95% faithfulness** on Harborline's curated evaluation set, re-run on every model or prompt change | Drivers 1, 2; NAIC bulletin testing expectation |
| NFR-3 | Retrieval-time authorization | A user can retrieve only documents they may open in ClaimCenter/ECM (by line, state, claim assignment, and Restricted-data entitlement). **Zero** cross-permission leakage in red-team testing | Driver 1; GLBA; state insurance data security laws |
| NFR-4 | Model data use | Customer data is never used to train or improve third-party models. **Zero-data-retention** terms, or models hosted within Harborline's cloud tenancy. All inference and data processing **in the US** | Driver 1; the invariant; NAIC third-party oversight |
| NFR-5 | Human-in-the-loop | No automated adverse decision (claim denial, reserve setting, rating) from any AI system. The assistant output is advisory and every drafted artifact requires human send or approval | The invariant; NAIC bulletin; Colorado SB21-169 |
| NFR-6 | AI audit trail | Every prompt, retrieved source set, model version, response, and user action logged immutably, **retained 7 years** (aligned to claim-file retention), and subject to legal hold | Drivers 1, 2; regulatory examination |
| NFR-7 | Operational data freshness | ClaimCenter and PolicyCenter changes available for analytics and assistant context within **≤ 15 minutes** (CDC), compared with next-day today | Drivers 2, 4 |
| NFR-8 | Reserving close | Quarterly close in **≤ 8 business days** (from 18) | Driver 4 |
| NFR-9 | Availability | Assistant 99.9% during business hours (07:00–20:00 local, all US time zones). Analytics platform 99.9%. Warehouse RPO ≤ 1 h and RTO ≤ 8 h (from nightly backup today) | Drivers 2, 3 |
| NFR-10 | Scale | About 450 TB raw today, growing ~20%/yr. About 40M documents (~8 TB text) to index, plus about 25K new claim documents a day. About 4,400 assistant users, ~110K queries/day, peak ~15 queries/s | Drivers 2, 3 |
| NFR-11 | FinOps | 100% of spend tagged and allocated. Steady-state **data-platform** run cost ≤ the $6.8M/yr legacy baseline (excluding the AI capability). **Assistant unit cost ≤ $0.05 per query** all-in (retrieval + inference + logging), reported monthly | Driver 5 |
| NFR-12 | Openness and portability | Analytical data stored in an **open table format** (Apache Iceberg or Delta Lake) readable by more than one engine. No new proprietary storage format for the system of record | Driver 3 (the Teradata lesson) |

## Requirement / Constraint / Assumption / Risk (Section 7.1 framework)

**Requirements**
- Access control must be expressed **once**, in the catalog and governance layer, and enforced consistently in SQL, notebooks, BI, *and* retrieval. It must not be re-implemented separately in the assistant.
- Classification must drive masking automatically. A new Restricted column should be masked by default, not exposed until someone notices.
- The assistant must show *why* it answered: the retrieved sources, with links into ClaimCenter/ECM, so that an adjuster can verify an answer in one click.

**Constraints**
- **Guidewire stays.** Integration is through CDC and supported APIs, not changes to its data model. Coastal's legacy system is decommissioned in a separate program, so this initiative ingests it but does not migrate it.
- **Teradata dates are fixed.** Notice is due by **31 December 2026** and the term ends on **30 June 2027**. The one-year bridge extension (at +25%) is available and is treated as the latest acceptable exit, not a target.
- **US-only data residency** for all customer data, embeddings, logs, and inference.
- The assistant is **retrieval and summarization with citations**. Autonomous agents that take actions in ClaimCenter are out of scope for this initiative.

**Assumptions**
- Most Teradata workloads can be migrated with automated SQL translation plus rewrite of the stored procedures and macros. The share needing manual rewrite (estimated 25–35%) is validated in Step 4, not assumed.
- About 70% of the 14,000 reports are retired rather than migrated (based on the 2025 usage scan).
- Frontier-class models are available under zero-data-retention terms, or as models hosted within the tenancy, on every candidate platform. Which models, where, and on what terms is exactly what Steps 6–8 must verify, because it differs by platform.
- SAS is replaced gradually (Python/SQL on the new platform). SAS is out of the critical path for the Teradata exit but in scope for the FinOps baseline.

**Risks (carried forward to the consolidated risk register in Step 12)**
- **Teradata migration effort:** 1,800 stored procedures and macros plus BTEQ scripts are the long pole. An underestimate forces the bridge extension, or worse.
- **Retrieval-time authorization gaps:** RAG systems commonly leak across permission boundaries when the index is built by a service account and filtered after retrieval. The design must enforce permissions *in* retrieval.
- **Model and platform churn:** GenAI model versions and platform AI services change faster than any other layer in this portfolio. Evaluation and prompt assets must survive a model swap.
- **Cost unpredictability:** consumption-priced warehouses and token-priced inference are both easy to overrun. FinOps is a design requirement, not a later report.
- **The 2024 Snowflake account** holds unmanaged copies of claims data. It is a governance risk regardless of platform choice, and is retired or absorbed under the chosen platform's governance.
- **Change adoption:** adjusters who were told "no AI" in March 2026 must trust a sanctioned tool enough to stop using personal devices.

## Priority Weighting (feeds the Step 9 decision matrix)

Provisional weights, to be refined once options are on the table in Step 4 (from highest to lowest):

1. **Governance and security fit:** unified catalog and policy enforcement across SQL, BI, and retrieval; model-data-use terms; audit.
2. **AI and RAG capability:** model choice and access terms, retrieval quality and authorization, evaluation tooling.
3. **Data platform and Teradata migration fit:** SQL translation tooling, performance, and open-format support.
4. **Cost and FinOps:** run-rate against the $6.8M baseline, unit-cost transparency, and controls.
5. **Operational and skills fit:** Harborline's data team of about 35, with SQL, SAS, and some Python skills.
6. **Portability:** open formats, and the exit cost from the chosen platform and from any cross-cloud data platform layered on it.

Each platform track (Azure, AWS, GCP) also evaluates **Databricks and Snowflake running on that cloud** against the cloud's native stack, because for data and AI that is the real decision, not just which hyperscaler to use. These weights are recorded here so that Step 9 traces back to this document rather than being invented at decision time.
