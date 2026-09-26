# ADR-026: GCP-Track Network, Identity, and FinOps Controls

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

The requirements are the same as on the other tracks ([ADR-014](ADR-014-azure-network-identity-finops.md), [ADR-020](ADR-020-aws-network-identity-finops.md)). The Claude US multi-region endpoint routes across US regions, including us-central1 and us-east4.

## Decision

- **Regions:** us-east4 (primary) and us-central1 (DR). The Organization Policy resource-location constraint limits resources to the US.
- **Connectivity:** redundant **Dedicated Interconnect** from Hartford, plus **Transfer Appliance** for the historical bulk load. **Private Service Connect** for Google APIs. **VPC Service Controls** perimeters around the data and AI projects.
- **Identity:** **Workforce Identity Federation with Entra ID** for people (the same groups drive BigQuery row policies, restricts entitlements, and Apigee use-case access). Service-account workload identity for services.
- **FinOps:**
  - **Cloud Billing export to BigQuery**, with labels required through custom organization-policy constraints and IaC checks.
  - **BigQuery reservations assigned per workload project** (ELT, BI, actuarial, data science, migration dual-run), so compute attribution is structural.
  - **Apigee token analytics per use case**.
  - Budgets and anomaly alerts.
  - Unit-cost dashboards built in BigQuery itself.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cloud VPN only.** Rejected for the dual-run period, as on the other tracks.
2. **On-demand BigQuery pricing for everything.** Rejected for production workloads, because reservations per workload give predictable cost and clean attribution. On-demand is kept for low-volume ad hoc projects.

## Consequences

- **Positive:** **Billing data lands in BigQuery**, so unit-cost analytics use the same platform and skills as everything else, which makes this the most self-contained FinOps loop of the three tracks.
- **Negative / accepted trade-off:** Label enforcement on GCP relies on custom constraints and IaC checks rather than a single built-in "deny untagged" control.
