# ADR-021: Identity and Access Model for the GCP Implementation

**Status:** Approved
**Date:** Step 8 of the Case Study 2 pipeline

## Context

As in the Azure and AWS tracks ([ADR-009](ADR-009-azure-identity.md), [ADR-015](ADR-015-aws-identity.md)), two distinct identity problems exist: human/workforce access, and service-to-service access (the Hold/Release Adapter, Fraud Orchestration Service, and Ledger-of-Intent Service calling Cloud SQL and Pub/Sub). Palisade already operates an on-premises Active Directory for workforce identity, and no prior cloud identity federation exists anywhere at Palisade today.

## Decision

Workforce identity federates through **Workforce Identity Federation**, trusting SAML assertions directly from Palisade's existing on-premises Active Directory Federation Services (AD FS) — engineers and auditors sign in with their existing corporate credentials, and no directory data is copied or synced into Google Cloud at all. All service-to-service authentication — Cloud Run services and the Cloud Run Job calling Cloud SQL or Pub/Sub — uses a dedicated **IAM service account per service**, with Google's Workload Identity mechanism issuing short-lived, automatically rotated credentials; no downloaded service-account key file is used anywhere.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Google Cloud Directory Sync (GCDS), replicating Palisade's on-prem AD into Cloud Identity.** Rejected — GCDS creates a synced copy of directory data that has to be kept current, the same "second identity system to keep in sync" governance risk `current-state.md` already flags as the core problem with the 2021 AWS account, and the same reasoning [ADR-015](ADR-015-aws-identity.md) used to reject AWS Managed Microsoft AD. Workforce Identity Federation avoids this entirely — it federates at sign-in time against the real on-prem AD FS, and copies nothing.
2. **Downloaded IAM service-account key files for service-to-service auth**, instead of Workload Identity. Rejected — same reasoning [ADR-009](ADR-009-azure-identity.md) and [ADR-015](ADR-015-aws-identity.md) used to reject stored client secrets and long-lived access keys: a downloaded key file is a credential-management burden and leak risk that Workload Identity's automatically rotated, short-lived credentials eliminate structurally.

## Consequences

- **Positive:** One identity system for workforce access — federated to the AD Palisade already operates — with no second directory to administer, replicate, or audit separately. Of the three hyperscaler tracks, this is the only one that avoids *any* directory-sync step at all: Azure's Entra Connect and AWS's AD Connector both involve an ongoing sync or per-request proxy process, while GCP's federation trusts a SAML assertion at login time with nothing persisted or replicated in between.
- **Positive:** Workload Identity removes an entire class of credential-leak risk; there is no key file to rotate, store, or accidentally commit to source control for any of the three services' calls to Cloud SQL or Pub/Sub.
- **Negative / accepted trade-off:** Workforce Identity Federation still depends on Palisade's on-prem AD FS being reachable and correctly configured for every login — a dependency the other two tracks also carry in different forms ([ADR-009](ADR-009-azure-identity.md)'s Entra Connect sync health, [ADR-015](ADR-015-aws-identity.md)'s AD Connector live-proxy dependency) — named here for Step 10's platform comparison rather than treated as unique to GCP.
