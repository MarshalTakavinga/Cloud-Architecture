# ADR-027: Identity and Access Model for the Private-Cloud Implementation

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

As in every other track, two identity problems exist: workforce access, and service-to-service access between the Hold/Release Adapter, Fraud Orchestration Service, and Ledger-of-Intent Service and the PostgreSQL cluster and messaging layer. Every hyperscaler track needed a federation mechanism to bridge Palisade's on-prem Active Directory into a separate cloud identity system (Entra ID, IAM Identity Center, or Workforce Identity Federation). This track's workload never leaves Palisade's own data center.

## Decision

The VMware Cloud Foundation platform, the Tanzu Kubernetes Grid cluster, and the PostgreSQL cluster all join **Palisade's existing on-premises Active Directory domain directly** — the same domain every other on-prem system already uses — via standard LDAP/Kerberos integration for platform and database administrative access, and Kubernetes RBAC bound to AD groups for workload-level access. Service-to-service authentication between the three containerized services and PostgreSQL or the messaging layer uses **mutual TLS**, with certificates issued and rotated by Palisade's existing internal PKI/certificate authority.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A cloud-based identity broker or federation service**, even though the workload itself never leaves Palisade's data center. Rejected — this would introduce exactly the external dependency and second-identity-system risk this workload is avoiding by staying private in the first place. If Palisade were going to depend on a cloud identity service regardless, that undercuts the actual rationale for choosing this track over a hyperscaler at Step 10.
2. **Static credentials (shared secrets or API keys) for service-to-service authentication**, instead of mutual TLS. Rejected — the same reasoning every other track used to reject stored secrets and long-lived keys: a static credential is a leak risk that a short-lived, rotatable mechanism avoids.

## Consequences

- **Positive:** This is the only track that requires **zero new identity infrastructure** — no federation service, no directory sync, no new identity-provider relationship — since it joins the exact Active Directory domain Palisade already runs everything else on.
- **Negative / accepted trade-off:** Without a cloud-native workload-identity mechanism (Managed Identity, IAM roles, Workload Identity), Palisade's own PKI/CA team must manage mutual-TLS certificate issuance and rotation for these services directly — genuine operational work the other three tracks get automatically from their platform. This is the same core trade-off already named in [ADR-024](ADR-024-private-cloud-compute-platform.md) and [ADR-025](ADR-025-private-cloud-database.md), recurring again at the identity layer: what a hyperscaler platform automates, private cloud requires Palisade's own team to build and run.
