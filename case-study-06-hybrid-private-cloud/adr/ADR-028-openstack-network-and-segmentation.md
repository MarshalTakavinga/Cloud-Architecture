# ADR-028: OpenStack Track — OVN Security Groups Rendered from Git

**Status:** Approved (OpenStack track, subject to the Step 10 platform selection)
**Date:** Step 9 of the Case Study 6 pipeline

## Context

Neutron with OVN enforces stateful security groups on every hypervisor port, including VMs on provider (VLAN) networks. [ADR-008](ADR-008-zone-model-and-segmentation-as-code.md) requires default deny in Z0 and PCI, rendered from Git, in both sites.

## Decision

- **Security groups per application role**, rendered from Git intent through the Terraform OpenStack provider, identical in both regions, with a daily parity check.
- **Default-deny egress** is also configured for the Z0 and PCI projects (the default security group allows egress).
- **The island** uses Windows Firewall and site firewalls, rendered from the same intent.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A third-party SDN overlay.** Rejected. OVN is included and distributed.

## Consequences

- **Positive:** Distributed microsegmentation **included**, covering VLAN-attached VMs as well (unlike GDC's NetworkPolicy).
- **Negative / accepted trade-off:** OVN troubleshooting is a new network skill. The team's network engineers are the natural owners.
