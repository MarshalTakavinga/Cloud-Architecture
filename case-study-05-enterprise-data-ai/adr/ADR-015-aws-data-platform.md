# ADR-015: AWS-Track Data Platform — AWS-Native Iceberg Lakehouse

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

These are the same requirements the Azure track faced ([ADR-009](ADR-009-azure-data-platform.md)): an open-format medallion lakehouse (ADR-001), one governance plane (ADR-002), Teradata translation (ADR-005), per-workload attribution (ADR-008), and a SAS-replacement workbench. On AWS, the native stack includes:
- **S3 Tables** (native Apache Iceberg) in the Glue Data Catalog
- **Lake Formation** column/cell permissions and LF-tags, enforced for Athena, Redshift, EMR, and Glue
- **Redshift Serverless** and **Athena**
- **SageMaker Unified Studio**
- **SCT** (Teradata → Redshift, including BTEQ → RSQL)
- **DMS** (Oracle CDC)

## Decision

**The AWS track uses the AWS-native stack:**
- **S3 Tables (Iceberg)** is the system of record for bronze, silver, and gold.
- **Redshift Serverless** runs the translated Teradata logic and BI (C1). Its managed storage holds **only derived gold performance marts**, which can be rebuilt from Iceberg.
- **Athena** is used for ad hoc queries.
- **EMR Serverless/Glue** handle Spark work.
- **SageMaker Unified Studio** is the notebook workbench (C2).
- **Lake Formation** is the governance plane for data ([ADR-016](ADR-016-aws-governance-plane.md)).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Databricks on AWS.** It has the strongest single catalog (Unity Catalog governs data, models, and indexes), which is why it won on Azure. On AWS the native stack already provides native Iceberg, cell-level security across four engines, first-party Teradata/BTEQ translation, and first-party Oracle CDC, all with one vendor. Databricks is the **runner-up**, and its governance advantage is scored in Step 9.
2. **Snowflake on AWS.** It has SnowConvert AI, Cortex with Claude available in AWS regions, and it would absorb the 2024 account. It is rejected for the same reasons as on Azure: the SAS workbench, and the need for a separate retrieval stack and gateway for non-Snowflake applications.

## Consequences

- **Positive:** It is the most open storage story of any track so far, because Iceberg is native and several first-party engines read the same tables. One vendor, one bill, one support path.
- **Positive:** First-party tooling covers both hard migration problems: Teradata translation (SCT) and Oracle CDC (DMS).
- **Negative / accepted trade-off:** **Several engines** (Redshift, Athena, EMR, Glue) mean more to learn and operate than one unified platform, for a data team of about 35. This is scored under operational fit.
- **Negative / accepted trade-off:** AI-asset governance is not in the same plane as data governance ([ADR-016](ADR-016-aws-governance-plane.md)).
