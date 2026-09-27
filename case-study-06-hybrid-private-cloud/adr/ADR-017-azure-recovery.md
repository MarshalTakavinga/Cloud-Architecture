# ADR-017: Azure Track — Hyper-V Replica and Data Guard, Orchestrated by Bank-Built Automation from Git

**Status:** Approved (Azure track, subject to the Step 10 platform selection)
**Date:** Step 7 of the Case Study 6 pipeline

## Context

Microsoft documents **Hyper-V Replica** between two separate Azure Local clusters (every 30 seconds, 5 minutes, or 15 minutes, with test, planned, and unplanned failover). An Arc-managed VM *"fails over … as an unmanaged VM"* and must be re-registered. **Azure Site Recovery** replicates Azure Local VMs to *Azure*, not to a second on-premises site. There is no packaged on-premises equivalent of VCF's Live Recovery. [ADR-006](ADR-006-recovery-plan-model-and-readiness.md) requires plans in Git and an orchestrator in DC2.

## Decision

- **Tier 0:** Hyper-V Replica every **30 seconds** for application VMs, and Data Guard for Oracle. These are locally managed VMs ([ADR-016](ADR-016-azure-tier0-local-management-mode.md)), so there is no re-registration.
- **Tier 1:** Hyper-V Replica every 5 minutes. **Re-registration to Azure after failover is a scripted step in the recovery plan.**
- **Orchestrator:** **bank-built Ansible and PowerShell**, running from DC2 with local identity, executing the Git plans (groups G0–G6), with the daily readiness job ([ADR-006](ADR-006-recovery-plan-model-and-readiness.md)).
- **Clean room:** a small isolated Hyper-V cluster in DC2 (Z-IRE), restored from the Veeam vault.
- **Azure Site Recovery to Azure is not used for Tier 0** (the invariant). It is optional for selected Tier-2 services.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure Site Recovery to Azure as the DR site.** Rejected for Tier 0 (board policy) and unnecessary for Tier 1, because DC2 exists.
2. **A third-party replication and orchestration product.** Considered. It is possible, but it adds a vendor for what the Git-plan model already requires the bank to own.

## Consequences

- **Positive:** A 30-second replication interval gives ample RPO margin, and the orchestrator is portable by construction.
- **Negative / accepted trade-off:** **More build and ownership than VCF.** The orchestrator, the clean-room workflow, and re-registration are bank code, and they are scored as operational load in Step 10.
