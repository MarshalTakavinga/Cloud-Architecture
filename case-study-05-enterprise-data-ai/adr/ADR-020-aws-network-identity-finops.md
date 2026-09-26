# ADR-020: AWS-Track Network, Identity, and FinOps Controls

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

The requirements are the same as on the Azure track ([ADR-014](ADR-014-azure-network-identity-finops.md)): US-only processing, private access, continuous CDC and document flow, about 180 TB of historical data, a dual-run period, Entra ID as the identity provider, and [ADR-008](ADR-008-finops-allocation-and-unit-cost.md)'s tagging, attribution, and budgets.

## Decision

- **Regions:** us-east-1 (primary) and us-east-2 (DR). SCPs deny non-US regions and global inference profiles.
- **Connectivity:** **redundant Direct Connect** from Hartford for CDC, documents, and dual-run traffic. **Snowball Edge** for the historical bulk load. VPC endpoints (PrivateLink) for every data and AI service, and OpenSearch in a VPC domain.
- **Identity:** **IAM Identity Center federated with Entra ID** (SAML + SCIM). The same groups drive Lake Formation grants and OpenSearch backend roles.
- **Landing zone:** Control Tower with separate accounts for Data, Analytics, AI, Security/Log-Archive, and Network. The 2024 Snowflake account is retired.
- **FinOps:**
  - SCP and tag policies **deny untagged resources**.
  - **CUR 2.0** with cost-allocation tags.
  - **Bedrock application inference profiles per use case** give token cost per use case natively.
  - **Redshift Serverless workgroups per workload** (ELT, BI, actuarial, migration dual-run).
  - AWS Budgets per use case and Cost Anomaly Detection.
  - Unit-cost dashboards (cost per query, per claim, and run-rate against the $6.8M baseline).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Site-to-Site VPN only.** Rejected, for the same dual-run reasoning as on the Azure track.
2. **Online bulk transfer of the historical data.** Rejected in favor of Snowball, which avoids saturating Direct Connect for weeks.

## Consequences

- **Positive:** Per-use-case token attribution is a **native Bedrock feature** here (application inference profiles), not a gateway-derived metric. This is the cleanest FinOps story for the AI capability so far.
- **Negative / accepted trade-off:** There is more account and engine sprawl to attribute across (Redshift, Athena, EMR, Glue, OpenSearch, Bedrock), so the allocation formula for shared costs is more involved than on a single-platform track.
