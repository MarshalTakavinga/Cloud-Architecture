# ADR-021: GCP Track — GDC Bare-Metal Clusters per Site with VM Runtime and CSI Array Storage

**Status:** Approved (GCP track, subject to the Step 10 platform selection)
**Date:** Step 8 of the Case Study 6 pipeline

## Context

GDC software-only runs GKE on the bank's own Linux servers. **VM Runtime on GDC** (KubeVirt) runs VMs as Kubernetes objects at no extra SKU. Pricing is **$0.03288 per vCPU-hour**, and a hyperthreaded core counts as two vCPUs. Live migration of VMs during upgrades is Preview. KubeVirt VMs need shared storage through a CSI driver for HA and live migration.

## Decision

- **Per site:** one admin cluster and user clusters for **Tier 0 (non-core)**, **PCI**, and **General (Tier 1/2 VMs + containers)**, on RHEL hosts. No cluster spans sites.
- **VM Runtime** enabled on the user clusters.
- **Storage:** an **enterprise array with a GDC-qualified CSI driver** in each site. The DC1 Fibre Channel refresh is therefore **not avoided** on this track.
- **Hyperthreading on,** accepting the doubled vCPU count for pricing in exchange for capacity. Step 13 tests the alternative.
- **Maintenance:** until VM live migration is GA, Tier-0 cluster upgrades run in maintenance windows, with VMs restarted in rolling order.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **GDC software-only on VMware.** Rejected. It keeps the vSphere subscription underneath.
2. **Local volumes instead of an array.** Rejected. They give no VM HA or live migration.

## Consequences

- **Positive:** One Kubernetes platform for VMs and containers, identical to GKE in Google Cloud.
- **Negative / accepted trade-off:** Per-vCPU pricing on every managed core, plus RHEL subscriptions, plus an array refresh.
- **Negative / accepted trade-off:** NFR-2 (non-disruptive maintenance) is met only by windows until live migration is GA.
