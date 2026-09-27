# ADR-020: Azure Track — Azure Virtual Desktop on Azure Local Replaces Horizon

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

Omnissa Horizon's supported platforms (2026) are vSphere, Nutanix AHV, OpenShift, and public-cloud options, **not Hyper-V or Azure Local**. The 1,400-seat VDI estate is Tier 1. Its users are the contact center and branch back office.

## Decision

- **Azure Virtual Desktop on Azure Local** (session hosts on the VDI instances in each site, with Windows 11 multi-session). The control plane is in Azure, which is acceptable for Tier 1.
- **Horizon is retired** at the end of its Omnissa term, after a pilot with the contact center.
- **Fallback:** if AVD on Azure Local can't meet contact-center latency or peripheral needs, move those users to AVD in Azure or Windows 365.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Keep Horizon on a small vSphere island.** Rejected. It keeps a Broadcom subscription for Tier-1 desktops.
2. **Windows 365 for everyone.** Considered as the fallback. Per-user pricing is higher for shift-based contact-center use.

## Consequences

- **Positive:** One vendor for desktop and platform, Omnissa licensing retired, and Entra ID integration native.
- **Negative / accepted trade-off:** A user-facing product change for 1,400 staff, with training and a pilot.
- **Negative / accepted trade-off:** VDI depends on Azure for brokering, so a long Azure outage degrades desktops (Tier 1, accepted).
