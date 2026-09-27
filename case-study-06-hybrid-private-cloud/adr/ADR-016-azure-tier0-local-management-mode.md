# ADR-016: Azure Track — Tier 0 Runs as Locally Managed Hyper-V VMs, Governed through Arc-Enabled Servers

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

The invariant and NFR-3 require Tier 0 to be started, stopped, failed over, and patched for at least 7 days with no cloud control plane ([ADR-004](ADR-004-govern-centrally-operate-locally.md)). Microsoft documents that Azure Local VMs enabled by Arc are started, restarted, and stopped *"only via the Azure portal or the Azure CLI. Don't use the local tools."* Disconnected operations provide a local control plane, but they need a dedicated management cluster in each site, eligibility approval, and a separate price tier. By design they have no public-cloud connectivity.

## Decision

- **Tier-0 and Oracle instances run locally managed Hyper-V VMs.** These VMs are *not* enrolled in Azure Local VM management. They are operated with Failover Cluster Manager, Windows Admin Center, and PowerShell, run from the pipeline.
- **The instances themselves stay connected** (Arc-registered) for platform health, solution updates, and governance.
- **Every Tier-0 guest runs the Arc-enabled servers agent**, for inventory, Azure Policy guest configuration, Defender, and patch-compliance *reporting*. Patches come from the **local** WSUS/Configuration Manager and Satellite.
- **Tier 1 and Tier 2 use Arc-managed Azure Local VMs**, the default, with the full portal and Terraform lifecycle.
- **The disconnected-operations mode is the named fallback.** It is re-evaluated if Microsoft makes it available without a dedicated management cluster, or if examiners require a local control plane for the platform itself.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Arc-managed VMs for Tier 0.** Rejected. This fails the disconnected-week test, because start and stop are supported only through Azure.
2. **Disconnected operations for the Tier-0 instances.** Rejected for now. It needs extra management clusters and approval, and it removes Tier 0 from central governance.

## Consequences

- **Positive:** Tier 0 passes the invariant, and it is still governed centrally at guest level.
- **Negative / accepted trade-off:** The 260 most important VMs don't get Azure Local's portal lifecycle. Their automation is PowerShell and Ansible owned by the bank.
- **Negative / accepted trade-off:** Two VM management models run on one platform, which must be clear in runbooks and in RBAC.
