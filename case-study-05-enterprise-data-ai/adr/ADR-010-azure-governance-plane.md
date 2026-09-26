# ADR-010: Azure-Track Governance Plane — Unity Catalog, with Purview for M365

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

[ADR-002](ADR-002-unified-governance-plane.md) requires one catalog and policy plane for data and AI assets: classification-driven masking, lineage to models, and the NAIC use-case inventory (G4). On Azure there are two credible planes:
- **Unity Catalog**, whose ABAC row filters and column masks, governed tags, and automated data classification all became GA on 13 May 2026
- **Microsoft Purview**, together with OneLake security, which became GA in 2026

Harborline already uses Purview for Microsoft 365 data protection.

## Decision

**Unity Catalog is authoritative for analytical data and AI assets** on the Azure track:
- tables, views, and volumes
- governed tags (Restricted / Confidential / Internal)
- ABAC masking and row filters
- lineage
- registered models and evaluation runs
- the use-case register

A small **entitlement service** exposes Unity Catalog–derived user entitlements (lines, states, assignments, Restricted flag) to the Retrieval Service. This makes the index filter a function of the same policy source ([ADR-011](ADR-011-azure-retrieval.md)).

**Purview stays** for Microsoft 365 information protection (email, SharePoint, endpoint DLP). It is **not** a second policy engine for analytics.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Purview + OneLake security as the plane.** It is the natural choice for a Fabric-based stack, which this track did not select ([ADR-009](ADR-009-azure-data-platform.md)).
2. **Both catalogs enforcing policy.** Rejected, because two policy engines means two answers to "who can see this".

## Consequences

- **Positive:** Masking of Restricted data follows the tag into every Databricks engine (SQL, notebooks, jobs), and the AI inventory lives beside the data it uses.
- **Negative / accepted trade-off:** The **Azure AI Search index is outside Unity Catalog's enforcement**. Its security depends on the entitlement service and the ACL attributes that UC data feeds it. This is the main governance gap on this track, and it is scored in Step 9.
- **Negative / accepted trade-off:** Enterprise users see two catalogs: Purview for M365 content and UC for analytics. The boundary is documented, not hidden.
