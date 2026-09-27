# ADR-024: GCP Track — NetworkPolicy for Pod-Network VMs, Rendered Firewalls for Layer-2 VMs

**Status:** Approved (GCP track, subject to the Step 10 platform selection)
**Date:** Step 8 of the Case Study 6 pipeline

## Context

VM Runtime VMs can use the pod network, where Kubernetes NetworkPolicy applies, or VLAN-tagged Layer 2 attachments. Layer 2 attachments are needed for the vendor appliances and for VMs that must keep their IP addresses. Pod-network NetworkPolicy does not govern traffic on those external Layer 2 attachments. [ADR-008](ADR-008-zone-model-and-segmentation-as-code.md) requires default deny in Z0 and PCI in both sites.

## Decision

- **Pod-network VMs:** NetworkPolicy from Git through Config Sync, default deny in the Z0 and PCI namespaces.
- **Layer 2 VMs:** placed in per-zone VLANs, and segmented by the **site firewalls**, with rules rendered from the same Git intent.
- **The island:** Hyper-V with Windows Firewall + site firewalls, rendered from Git.
- **A parity check** across all three enforcement points in both sites.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Move every VM onto the pod network.** Rejected. Appliances and IP-preserving migrations can't.

## Consequences

- **Positive:** It stays within the intent model of [ADR-008](ADR-008-zone-model-and-segmentation-as-code.md).
- **Negative / accepted trade-off:** **Three enforcement points**, with east-west control for Layer 2 VMs that is coarser than VCF's or Azure Local's distributed firewalls.
