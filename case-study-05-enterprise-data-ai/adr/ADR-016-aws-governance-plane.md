# ADR-016: AWS-Track Governance — Lake Formation for Data, with a Linked AI Inventory

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

[ADR-002](ADR-002-unified-governance-plane.md) asks for one catalog and policy plane over data and AI assets. On AWS:
- **Lake Formation** provides LF-tag–based and named-resource permissions down to columns and cells, enforced by Athena, Redshift, EMR, and Glue.
- **Macie** discovers sensitive data in S3.
- **SageMaker Catalog** provides a business catalog and lineage.
- **SageMaker Model Registry** tracks models.

There is no single AWS service that governs tables, retrieval indexes, prompts, and models together.

## Decision

- **Data:** **Lake Formation is authoritative.** LF-tags cover classification, line, and state. Column masking and row/cell filters are driven by those tags. **Macie** and Glue sensitive-data detection propose tags, and core-entity tags are confirmed by people.
- **Retrieval:** OpenSearch roles are **derived from the same Identity Center groups** that Lake Formation uses ([ADR-017](ADR-017-aws-retrieval.md)), and an entitlement service exposes the combined view to the retrieval service.
- **AI assets (G4):** the **SageMaker Model Registry** holds models and evaluation metrics, and a **use-case register** holds approved model IDs, prompt versions, index versions, risk tier, and approvals. The gateway enforces the register at runtime ([ADR-018](ADR-018-aws-models-and-ai-gateway.md)).
- **Lineage:** SageMaker Catalog lineage covers Glue, Redshift, and EMR jobs.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Unity Catalog on AWS** (with Databricks). It is the strongest single plane, but it was not selected ([ADR-015](ADR-015-aws-data-platform.md)).
2. **A third-party catalog over everything.** It would add a vendor whose enforcement still depends on each engine. The combination of Lake Formation and group-derived OpenSearch roles already enforces in the engines that matter.

## Consequences

- **Positive:** Masking of Restricted data is enforced by every native query engine from one tag set, which closes the schema-wide PII exposure described in `current-state.md`.
- **Negative / accepted trade-off:** **There are three planes:** Lake Formation for data, OpenSearch security for the index, and the register for AI assets. They are **aligned by shared identity groups rather than one catalog**. That is weaker than ADR-002's ideal, and it is scored in Step 9.
