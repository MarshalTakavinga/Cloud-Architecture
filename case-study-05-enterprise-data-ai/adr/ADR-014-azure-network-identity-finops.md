# ADR-014: Azure-Track Network, Identity, and FinOps Controls

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

These requirements apply:
- US-only processing (NFR-4)
- private access to every data and AI service
- continuous CDC plus ECM document flow from Hartford
- a one-time historical load of about 180 TB compressed from Teradata
- a dual-run period (ADR-005)
- Entra ID as the existing identity provider
- [ADR-008](ADR-008-finops-allocation-and-unit-cost.md)'s mandatory tags, per-workload attribution, and budgets

## Decision

- **Regions:** East US 2 (primary), Central US (DR). Azure Policy denies non-US regions and non–Data Zone US model deployments.
- **Connectivity:**
  - **Redundant ExpressRoute circuits** from Hartford carry CDC, document flow, and dual-run traffic.
  - **Azure Data Box** handles the historical Teradata bulk load. At 1 Gbps, 180 TB would take more than two weeks of saturated transfer. Data Box avoids competing with production traffic.
  - Private Link and private endpoints for ADLS, Databricks (VNet injection), AI Search, Foundry, APIM (internal), and Key Vault. No public endpoints.
- **Identity:**
  - Entra ID for all users, with SCIM provisioning into Databricks.
  - Group-based entitlements feed Unity Catalog ABAC.
  - Managed identities for services.
  - The user's token is propagated to the retrieval service so entitlements are always the user's.
- **FinOps:**
  - Azure Policy **denies untagged resources**.
  - Databricks **cluster and warehouse policies enforce tags** and auto-termination.
  - Separate SQL warehouses and job clusters per workload class (ELT, BI, actuarial, data science, migration dual-run).
  - **Databricks system billing tables** + **APIM token metrics** + **Azure Cost Management** feed the unit-cost dashboards (cost per query, cost per claim, run-rate against the $6.8M baseline).
  - Budgets and anomaly alerts per use case.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Site-to-site VPN only.** It is fine for the steady state, but inadequate for the multi-month dual-run with continuous CDC and large ECM flows. This deliberately contrasts with Case Study 4, where about 60 Mbps did not justify a dedicated circuit.
2. **Online transfer of the historical data over ExpressRoute.** Possible, but it would saturate the circuit for weeks during the dual-run. Data Box is cheaper and isolates the risk.

## Consequences

- **Positive:** All data and AI traffic is private and US-bound by policy, and cost attribution is enforced at creation time rather than reconstructed later.
- **Negative / accepted trade-off:** ExpressRoute and dual-run networking are material costs that fall mostly in the migration years. They are modeled in Step 12.
