# ADR-030: OpenStack Track — Partner-Operated Platform, Trilio Backup, and VDI in Azure

**Status:** Approved (OpenStack track, subject to the Step 10 platform selection)
**Date:** Step 9 of the Case Study 6 pipeline

## Context

The 24-person team's depth is VMware and Windows (driver 5). NFR-12 allows at most 4 hires. RHOSO adds OpenShift, OpenStack, and Ceph. Veeam doesn't support OpenStack VMs. **Trilio for OpenStack** does, and it documents RHOSO. Horizon isn't supported on OpenStack.

## Decision

- **Operating model:** a **managed-service partner** co-operates the OpenStack, OpenShift, and Ceph layers for the first three years, with knowledge transfer. Two of the four allowed hires are OpenStack/Ceph engineers.
- **Backup:** **Trilio** for OpenStack workloads and Veeam for the island, both feeding one vault ([ADR-003](ADR-003-cyber-recovery-vault-and-isolated-recovery.md)).
- **VDI:** **AVD or Windows 365 in Azure**. Horizon is retired.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Run the platform in-house from day one.** Rejected. That is too much skills risk against an examination deadline.
2. **Horizon on OpenShift Virtualization.** Rejected. It adds a *second* KVM virtualization stack just for desktops.

## Consequences

- **Positive:** The skills gap is closed by contract rather than hope.
- **Negative / accepted trade-off:** A partner cost line (Step 13), two backup products, and a third vendor for VDI.
- **Negative / accepted trade-off:** The independence gained from open source is partly spent on dependence on a partner.
