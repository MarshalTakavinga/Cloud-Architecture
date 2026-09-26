# ADR-021: GCP-Track Data Platform — BigQuery with Iceberg-Managed Tables

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

The requirements are the same as on the other tracks ([ADR-009](ADR-009-azure-data-platform.md), [ADR-015](ADR-015-aws-data-platform.md)). GCP's native stack offers:
- **BigQuery** (serverless) and **BigQuery tables for Apache Iceberg**, which are Iceberg data under BigQuery management and security
- **Dataplex Universal Catalog**
- **Datastream** (Oracle CDC)
- a **first-party GA translator for Teradata SQL, BTEQ, and TPT**
- **BigQuery Studio / Colab Enterprise** notebooks

## Decision

**The GCP track uses the GCP-native stack:**
- **BigQuery tables for Apache Iceberg** are the system of record for bronze, silver, and gold.
- Native BigQuery storage is used **only for derived gold performance marts**.
- **Dataform** handles transformations.
- **BigQuery Studio** is the notebook workbench.
- The same serverless engine serves SQL, BI (via BI Engine), and notebooks.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Databricks on GCP.** It has the Unity Catalog single plane. It is the **runner-up**, because GCP's first-party answers to Teradata (including BTEQ and TPT) and CDC, plus serverless operation, remove most of the reasons to add a second platform vendor.
2. **Snowflake on GCP.** Rejected for the same reasons as on the other tracks.

## Consequences

- **Positive:** It is the **least infrastructure to operate** of the three tracks. There are no clusters or warehouses to size, only reservations per workload. That suits a data team of about 35.
- **Positive:** One engine serves ELT, SQL, BI, notebooks, and warm-tier retrieval ([ADR-023](ADR-023-gcp-retrieval.md)).
- **Negative / accepted trade-off:** **Feature parity on Iceberg-managed tables** versus native BigQuery storage must be validated in the pilot (for example, streaming CDC merges and some performance features). If parity is lacking, more of silver may be kept in native storage, which weakens NFR-12. That would be a scored risk.
- **Negative / accepted trade-off:** Translated logic becomes GoogleSQL, which is BigQuery-shaped, the same portability price as Redshift SQL on AWS.
