# ADR-010: Azure Landing Zone Topology and Network Segmentation

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

This is the first cloud footprint Palisade will operate under actual governance — the current-state documentation notes the 2021 AWS account has no landing zone, no network segmentation, and no centralized policy enforcement, and `requirements.md` carries that account's governance gap forward as a named risk to be resolved by whatever platform this case study builds, not worked around. This ADR also has to place the ISO 20022/FedNow gateway (bought per [ADR-002](ADR-002-payment-hub-build-vs-buy.md)) and decide where the 2021 AWS-equivalent workloads (Replatformed per Step 4's 6-R disposition) land once migrated.

## Decision

Azure resources for this case study are organized under an **Azure Landing Zone in a hub-spoke topology**: a central hub VNet carries shared services (the ExpressRoute gateway from [ADR-008](ADR-008-hybrid-connectivity.md), shared DNS, centralized firewall/inspection), with two spokes — one for the new real-time payment-processing workloads (Container Apps, Azure SQL Database, Service Bus, and the ISO 20022/FedNow gateway's private connection point), and a second, separately governed spoke for the Replatformed 2021 AWS-equivalent workloads (notification and mobile-analytics services) once migrated. **Azure Policy** enforces private-endpoint-only access to PaaS services, the approved region (US-only, per NFR-6), and mandatory diagnostic logging across both spokes; **Microsoft Defender for Cloud** provides continuous security posture monitoring across the whole landing zone.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A single flat VNet for all workloads, with no hub-spoke separation.** Rejected — this would put the highly regulated, real-time payment-processing workload in the same network segment as the lower-sensitivity notification/analytics workload, with no structural boundary between them. Given the OCC heightened-standards scrutiny this entire initiative is responding to, that flat topology would itself likely be flagged as a control weakness in any examination.
2. **Migrate the 2021 AWS-equivalent workloads into the same spoke as the payment-processing services**, rather than a separate one. Rejected — these workloads have a materially different risk and compliance profile (mobile push notifications and analytics vs. real-time payment processing under BSA/AML and OCC scrutiny); keeping them in a segmented, separately governed spoke lets policy and monitoring be scoped appropriately to each workload's actual sensitivity, rather than applying the payment-processing spoke's stricter controls everywhere by default (which would be safe but needlessly costly and operationally heavier) or the lighter controls everywhere (which would be a genuine gap).
3. **No formal landing zone at all — replicate the 2021 account's ad hoc pattern for this new workload too, just in a new subscription.** Rejected outright — this is the exact governance failure mode `requirements.md` names as a risk to resolve, not repeat.

## Consequences

- **Positive:** The 2021 AWS account's ungoverned-cloud-foothold risk is resolved by this ADR, not left as a separate, unaddressed problem — its equivalent workloads land inside the same governance model this case study establishes.
- **Positive:** Policy-enforced private-endpoint-only access and mandatory diagnostic logging give Palisade a defensible, demonstrable control set to present to an OCC examiner, directly responsive to driver 3 (regulatory resiliency mandate).
- **Negative / accepted trade-off:** A hub-spoke topology with policy enforcement is more setup effort up front than a flat, unmanaged VNet — accepted deliberately, since the entire point of this initiative includes closing the governance gap the current state carries, not merely adding compute capacity.
- **Carried to Step 12:** The actual migration of the 2021 AWS-equivalent workloads into this landing zone's second spoke is a migration-roadmap action item, not a Step 6 implementation detail — recorded here so Step 12 does not have to rediscover it.
