# ADR-012: VCF Track — Local Control Planes, a 180-Day Licence Obligation, and Guest-Level Arc for Governance

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

[ADR-004](ADR-004-govern-centrally-operate-locally.md) requires a local operations path that works for 7 days disconnected, and one governance plane across the private cloud and the landing zone. Current documentation shows:
- VCF 9 in **disconnected mode** must report licence usage **every 180 days**. Otherwise *"your licenses are treated as expired, your hosts are disconnected from the vCenter instance, and you cannot start any workload operations."*
- **Azure Arc-enabled VMware vSphere** supports *"vCenter Server version 8"* only, not VCF 9's vCenter.

## Decision

- **Operate locally:**
  - vCenter, NSX Manager, VCF Operations, VCF Automation, and Live Recovery run **in each site**.
  - Lifecycle updates come from an **offline depot**.
  - Local AD and SSO break-glass accounts are held in PAM.

  This track passes the disconnected-week test on every operational component.
- **The licence obligation is an operational control:**
  - VCF Operations runs in **disconnected mode** (no outbound dependency).
  - The 180-day usage report is a calendar task with an alert at day 150.
  - **The subscription term is tracked as a Tier-0 dependency**, because a lapse stops workload operations.
- **Govern centrally, in two layers:**
  - **VCF Operations** is authoritative for the private cloud's inventory, compliance (CIS and PCI packs), and capacity.
  - **Arc-enabled servers** (a guest agent) in every Windows and RHEL VM give Azure-side inventory, policy, and patch-compliance *reporting*. Patches still come from local WSUS/SCCM and Satellite.
  - The landing zone is governed by Azure Policy.
  - The two views reconcile into ServiceNow daily.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **VCF Operations in connected mode.** Rejected for Tier 0. It adds an outbound dependency the invariant doesn't need.
2. **Arc-enabled vSphere for native VCF inventory in Azure.** Not available: Arc supports vCenter 8 only. It is re-checked when Microsoft adds vCenter 9 support.
3. **VCF Operations only, with the landing zone governed separately.** Rejected, because it splits driver 3 more than guest-level Arc does.

## Consequences

- **Positive:** This is the strongest local autonomy of any track.
- **Negative / accepted trade-off:** **The platform stops operating if the subscription lapses.** This turns the renewal into an operational dependency, and it is why NFR-11's tested exit is mandatory on this track.
- **Negative / accepted trade-off:** Governance lives in two consoles joined by reconciliation, so it is scored as partial in Step 10.
