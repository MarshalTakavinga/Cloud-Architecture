# ADR-018: Azure Track — Datacenter Firewall for Tier 0, NSGs for Tier 1/2, Both Rendered from Git

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

[ADR-008](ADR-008-zone-model-and-segmentation-as-code.md) requires default-deny east-west traffic in Z0 and Z0-PCI in both sites, rendered from Git, with enforcement that works disconnected. Azure Local offers two SDN management modes per instance:
- **SDN managed with on-premises tools** (Network Controller and Datacenter Firewall ACLs)
- **SDN enabled by Arc** (network security groups managed from Azure)

Both are included in the platform.

## Decision

- **Tier-0/PCI and Oracle instances:** SDN managed with on-premises tools. **Datacenter Firewall** ACLs are rendered from Git by the pipeline through PowerShell. Enforcement and changes are both local.
- **General instances:** SDN enabled by Arc, with **NSGs** rendered from the same Git intent through Terraform.
- **Parity check** each day between DC1 and DC2 for each mode.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Arc-managed NSGs everywhere.** Rejected for Tier 0. Rule *changes* would depend on Azure, although enforcement wouldn't.
2. **Perimeter firewalls only.** Rejected ([ADR-008](ADR-008-zone-model-and-segmentation-as-code.md)).

## Consequences

- **Positive:** Microsegmentation in both sites **at no add-on cost**, where VCF needs vDefend.
- **Negative / accepted trade-off:** Two renderers and two management modes. Datacenter Firewall is less widely skilled in the market than NSX.
