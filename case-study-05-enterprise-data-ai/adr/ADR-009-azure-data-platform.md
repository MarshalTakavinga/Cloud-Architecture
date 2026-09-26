# ADR-009: Azure-Track Data Platform — Azure Databricks

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

[ADR-001](ADR-001-lakehouse-on-open-tables.md) requires a medallion lakehouse on an open table format, with a named second engine. [ADR-002](ADR-002-unified-governance-plane.md) wants one governance plane for data *and* AI assets. [ADR-005](ADR-005-teradata-migration-approach.md) needs strong Teradata translation. [ADR-008](ADR-008-finops-allocation-and-unit-cost.md) needs cost attribution per workload. SAS is replaced by notebooks (C2).

There are three candidates on Azure:
- **Microsoft Fabric** (OneLake, Delta with Iceberg virtualization, capacity billing)
- **Azure Databricks** (Delta/UniForm on ADLS, Unity Catalog, DBU billing per workload)
- **Snowflake on Azure** (Iceberg or native tables, Horizon, credits, SnowConvert AI)

## Decision

**Azure Databricks is the lakehouse and data-science platform** on the Azure track:
- Delta tables with UniForm (Iceberg-readable) on ADLS Gen2
- Unity Catalog as the governance plane ([ADR-010](ADR-010-azure-governance-plane.md))
- SQL warehouses for Tableau
- notebooks and MLflow for the actuarial and data-science workbench
- Lakebridge for Teradata translation

Azure-native services are used where they are stronger: AI Search, Foundry, API Management, and Entra ID.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Microsoft Fabric.** It is the most integrated and simplest to run for a Microsoft-standardized shop, and OneLake security reached GA in 2026. Rejected on this track for three reasons:
   - AI-asset governance is split between Foundry and Purview, which weakens ADR-002.
   - Fabric's Migration Assistant names Synapse, SQL Server, and "other SQL platforms", **not Teradata**.
   - Capacity billing makes per-use-case attribution coarse (ADR-008).
2. **Snowflake on Azure.** It has the strongest *documented* Teradata translation (SnowConvert AI, including BTEQ), it absorbs the 2024 account, and it keeps Cortex inference within `AZURE_US`. Rejected on this track because:
   - its SAS-replacement workbench is weaker than Databricks'
   - AI Search and API Management would still be needed for non-Snowflake applications

   It is recorded as the runner-up, and its migration-tool advantage is scored in Step 9.

## Consequences

- **Positive:** One platform covers ELT, SQL, notebooks, ML and evaluation, and the migration tooling, governed by one catalog. Cost is attributable per job and warehouse through system tables.
- **Positive:** Because Databricks runs on all three clouds, this choice largely **carries across tracks**. The Step 9 cloud comparison then concentrates on what differs underneath: models, retrieval, the gateway, identity, and network.
- **Negative / accepted trade-off:** There are two vendors on the critical path (Microsoft and Databricks), with two commercial relationships and two support paths.
- **Negative / accepted trade-off:** Lakebridge's Teradata coverage must be proven on Harborline's 1,800 procedures and BTEQ scripts in a Step 11 proof of concept. The 25–35% manual-rewrite assumption rides on it.
