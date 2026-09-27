# ADR-026: OpenStack Track — RHOSO 18, One Region per Site, Ceph Storage

**Status:** Approved (OpenStack track, subject to the Step 10 platform selection)
**Date:** Step 9 of the Case Study 6 pipeline

## Context

A commercially supported distribution is required (NFR-12: 24×7 support). Alder Valley already runs RHEL with Satellite. In Red Hat OpenStack Services on OpenShift (RHOSO) 18, the control plane runs as pods on OpenShift and the compute nodes run RHEL/KVM. It is licensed **per socket-pair**, with a **Ceph add-on per compute subscription**. A lapsed subscription removes support and updates, not operations.

## Decision

- **RHOSO 18**, with **one independent region per site** (its own OpenShift-hosted control plane, Keystone, and Ceph cluster). No stretched control plane.
- **Availability zones and host aggregates** for Z0, Z0-PCI, and General.
- **Ceph** (RBD for Cinder and Glance) per site. **The DC1 Fibre Channel array is retired.**
- **A disconnected-capable installation:** content mirrored through Satellite and a local registry, so updates can be applied without internet access.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Canonical OpenStack.** A credible alternative, probably cheaper, and Ubuntu-based. Rejected because the bank's Linux estate, Satellite, and skills are RHEL. It stays the named fallback, which is itself exit leverage.
2. **Upstream OpenStack without a vendor.** Rejected (NFR-12).
3. **A single multi-site region.** Rejected ([ADR-002](ADR-002-recovery-as-code-active-standby.md)).

## Consequences

- **Positive:** No licence stop. Distribution portability. The strongest local autonomy.
- **Negative / accepted trade-off:** Three technologies to master (OpenShift for the control plane, OpenStack, and Ceph).
