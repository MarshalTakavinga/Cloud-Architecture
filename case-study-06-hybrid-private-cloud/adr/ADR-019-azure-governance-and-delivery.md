# ADR-019: Azure Track — Arc as the Single Governance Plane; Terraform, AKS on Azure Local, and an Azure Landing Zone

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

Driver 3 and [ADR-004](ADR-004-govern-centrally-operate-locally.md) want one governance plane across on-premises and cloud. Alder Valley already runs Entra ID, M365, and Microsoft Sentinel. [ADR-005](ADR-005-platform-api-and-portability.md) requires a platform API, Terraform, and a platform-run Kubernetes. AKS on Azure Local is included from release 2402.

## Decision

- **Governance:** Azure Arc over:
  - every Azure Local instance
  - every guest (Arc-enabled servers, Tier 0 included)
  - the Azure landing zone

  **Azure Policy** handles baselines and required tags. **Defender for Cloud** handles vulnerability and CIS. **Update Manager** handles patch-compliance reporting. **Resource Graph** feeds ServiceNow, and **Sentinel** remains the SIEM.
- **Delivery:** Terraform (azurerm/azapi) for Azure Local VMs, logical networks, NSGs, and AKS, with ServiceNow approvals (automatic for Tier 2 and dev/test).
- **Kubernetes:** **AKS on Azure Local** on the General instances replaces the Rancher clusters.
- **Landing zone:** **Azure**, following the enterprise-scale pattern. The 2025 AWS account is **closed** and its extracts purged. The digital team's ML work moves to the Azure landing zone.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **System Center or a third-party CMP as the governance plane.** Rejected. It would duplicate what Arc provides and not reach the landing zone.
2. **Keep Rancher.** Rejected ([ADR-005](ADR-005-platform-api-and-portability.md)).

## Consequences

- **Positive:** The strongest driver-3 outcome of any track: one plane, one identity, one SIEM.
- **Negative / accepted trade-off:** Concentration in Microsoft across identity, productivity, SIEM, cloud, *and* the private platform. It is mitigated by the tested exit ([ADR-005](ADR-005-platform-api-and-portability.md)) and it is a named risk in Step 13.
