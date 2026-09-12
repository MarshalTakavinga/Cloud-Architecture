# ADR-015: Identity and Access Model for the AWS Implementation

**Status:** Approved
**Date:** Step 7 of the Case Study 2 pipeline

## Context

As in the Azure track ([ADR-009](ADR-009-azure-identity.md)), two distinct identity problems exist: human/workforce access (engineers, operators, auditors who need to access AWS resources or query the audit log), and service-to-service access (the Hold/Release Adapter, Fraud Orchestration Service, and Ledger-of-Intent Service calling Aurora, SNS, and SQS). Palisade already operates an on-premises Active Directory for workforce identity, and the current-state documentation notes no prior cloud identity federation exists anywhere at Palisade — itself part of the ungoverned-2021-AWS-account risk this case study's landing zone is meant to resolve.

## Decision

Workforce identity federates through **AWS IAM Identity Center**, connected to Palisade's existing on-premises Active Directory via **AWS Directory Service (AD Connector)** — a lightweight proxy that forwards authentication requests to the real on-prem AD rather than replicating directory data into AWS. Engineers and auditors use their existing corporate credentials; no second directory needs to be created or kept in sync. All service-to-service authentication — ECS tasks calling Aurora, SNS, or SQS — uses **IAM roles attached to each ECS task**, so temporary, automatically rotated credentials are issued via the task's own execution role and no access key is ever stored in application configuration or code.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **AWS Managed Microsoft AD** (a full, standalone Active Directory Domain Services deployment in AWS, optionally trust-connected to the on-prem AD). Rejected — this stands up a second Active Directory forest requiring its own domain controllers, replication, and trust management, which is precisely the "second identity system to keep in sync" governance risk `current-state.md` already flags as the core problem with the 2021 AWS account. AD Connector avoids this entirely because it doesn't replicate directory data at all — it proxies authentication requests to the existing on-prem AD directly, over the same private connection from [ADR-014](ADR-014-aws-hybrid-connectivity.md).
2. **IAM users with long-lived access keys for service-to-service auth**, instead of IAM roles. Rejected — same reasoning [ADR-009](ADR-009-azure-identity.md) used to reject stored client secrets for Azure: long-lived keys are a credential-management burden (rotation, secure storage, leak risk) that IAM roles eliminate structurally, since every service-to-service call in this design is between first-party AWS resources within the same account.

## Consequences

- **Positive:** One identity system for workforce access — federated to the AD Palisade already operates and already has processes for (onboarding, offboarding, access review) — rather than a second system to administer and audit separately.
- **Positive:** IAM roles for ECS tasks remove an entire class of credential-leak risk from the architecture; there is no secret to rotate, store, or accidentally commit to source control for any of the three services' calls to Aurora, SNS, or SQS.
- **Negative / accepted trade-off:** AD Connector requires live, reliable connectivity from AWS back to the on-prem domain controllers for *every* authentication request — it is a proxy, not a cached or replicated directory, so a connectivity gap on the Direct Connect/VPN path from [ADR-014](ADR-014-aws-hybrid-connectivity.md) blocks new authentications, not just directory sync. This is a subtly different risk shape than Azure's Entra Connect (a periodic sync process, not a per-request live dependency), and is named here for Step 10's platform comparison rather than treated as equivalent to Azure's.
