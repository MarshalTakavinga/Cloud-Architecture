# ADR-011: VCF Track — NSX VPCs and vDefend Distributed Firewall in Both Sites

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

[ADR-008](ADR-008-zone-model-and-segmentation-as-code.md) requires default-deny east-west traffic in Z0 and Z0-PCI in **both** sites, with rules rendered from Git and parity checked daily. In VCF 9, the distributed firewall needs the **vDefend** add-on. Without it, *"firewall features remain locked"* (Broadcom knowledge base). Today vDefend and NSX firewalling cover only DC1's PCI zone.

## Decision

- **NSX** in both VCF instances, with **VPCs** as the self-service network construct for Z1 and Z2 (driver 4).
- **vDefend distributed firewall licensed only on the hosts that enforce Z0, Z0-PCI, Oracle, and Z1 policy** in both sites. Z2 and VDI use VPC and gateway firewalling without vDefend, so fewer cores carry the add-on.
- **Rules from Git** through the NSX Terraform provider, rendered from application intent, with a daily parity check between the NSX managers of DC1 and DC2.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **License vDefend on every core.** Rejected on cost. Z2 doesn't need east-west default deny.
2. **Physical firewalls for east-west inside Tier 0.** Rejected. Traffic would hairpin through appliances, and firewalls can't follow a VM as it moves.

## Consequences

- **Positive:** PCI scope is correct in DC2 for the first time.
- **Negative / accepted trade-off:** vDefend is a second Broadcom subscription line that rises with the Tier-0 footprint (Step 13).
