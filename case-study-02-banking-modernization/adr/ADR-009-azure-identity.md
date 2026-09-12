# ADR-009: Identity and Access Model for the Azure Implementation

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

Two distinct identity problems exist in this architecture: human/workforce access (engineers, operators, auditors who need to access Azure resources or query the audit log), and service-to-service access (the Hold/Release Adapter, Fraud Orchestration Service, and Ledger-of-Intent Service calling Azure SQL Database and Service Bus). Palisade already operates an on-premises Active Directory for workforce identity — the current-state documentation notes no prior cloud identity federation exists, which is itself part of the ungoverned-2021-AWS-account risk this case study's landing zone is meant to resolve.

## Decision

Workforce identity federates through **Microsoft Entra ID, connected to Palisade's existing on-premises Active Directory** (via Entra Connect), so engineers and auditors use their existing corporate credentials rather than a second identity system administered separately. All service-to-service authentication — Container Apps calling Azure SQL Database, Container Apps calling Service Bus — uses **Managed Identities**, so no connection string, key, or credential is ever stored in application configuration or code.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A separate, cloud-only identity system for Azure access, independent of the existing on-prem Active Directory.** Rejected — this would give Palisade two identity systems to keep in sync (or, more realistically, to let drift apart), which is precisely the kind of governance gap the current-state documentation already flags as a problem with the 2021 AWS account. Federating to the existing AD directly resolves that gap rather than creating a second instance of it.
2. **Service principals with stored client secrets for service-to-service auth**, instead of Managed Identities. Rejected — stored secrets are a credential-management burden (rotation, secure storage, leak risk) that Managed Identities eliminate structurally; there is no scenario in this architecture where a stored secret is necessary, since every service-to-service call in this design is between first-party Azure resources within the same tenant.

## Consequences

- **Positive:** One identity system for workforce access — federated to the AD Palisade already operates and already has processes for (onboarding, offboarding, access review) — rather than a second system to administer and audit separately.
- **Positive:** Managed Identities remove an entire class of credential-leak risk from the architecture; there is no secret to rotate, store, or accidentally commit to source control for any of the three new services' calls to SQL Database or Service Bus.
- **Negative / accepted trade-off:** Entra Connect introduces a dependency on the on-prem AD's health and connectivity for new workforce access provisioning — an existing dependency Palisade already manages today for other systems, not a new single point of failure introduced by this design.
