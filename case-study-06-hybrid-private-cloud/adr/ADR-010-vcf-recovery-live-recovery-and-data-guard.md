# ADR-010: VCF Track — VMware Live Recovery with Plans Generated from Git, Plus Oracle Data Guard

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

[ADR-002](ADR-002-recovery-as-code-active-standby.md) and [ADR-006](ADR-006-recovery-plan-model-and-readiness.md) require recovery plans as code in Git, a DC2 orchestrator that runs with DC1 lost, daily readiness checks, and a clean room ([ADR-003](ADR-003-cyber-recovery-vault-and-isolated-recovery.md)). Today SRM protects only about 400 VMs, and the Tier-0 runbook is manual. For VCF 9, Broadcom offers **VMware Live Recovery**:
- DR orchestration
- vSAN-to-vSAN replication with RPOs *"as low as 1-minute"*
- a validated *on-premises isolated clean room*

It is sold as a separate purchase.

## Decision

- **Live Recovery** replaces SRM and vSphere Replication for all Tier-0 and Tier-1 VMs, with vSAN-to-vSAN replication from DC1 to DC2.
- **Git remains the source of truth.** A pipeline **generates Live Recovery recovery plans from the Git plan definitions** (groups G0–G6). The Data Guard, payments-gateway, and validation steps are Ansible automation called from the plan. Live Recovery's own database is treated as a rendered artifact, not the master.
- **Oracle uses Data Guard**, not platform replication, for its data: transport sized for the batch peak, and a lag alert at 10 minutes.
- **Clean room:** the Live Recovery on-premises isolated clean room in DC2 (Z-IRE), fed from the Veeam vault.
- **Readiness:** the daily job ([ADR-006](ADR-006-recovery-plan-model-and-readiness.md)) reads replication state from Live Recovery and lag from Data Guard.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Keep SRM for 400 VMs and script the rest.** Rejected. It is the current state that failed.
2. **Author plans directly in Live Recovery.** Rejected. Plans would lose review and history, and they couldn't be carried to another platform (NFR-11).
3. **Platform replication for Oracle too.** Rejected. Data Guard gives transactionally consistent standby databases and is already licensed and understood.

## Consequences

- **Positive:** Every Tier-0 and Tier-1 VM is protected under one orchestrator, and the plans stay portable.
- **Negative / accepted trade-off:** Live Recovery is an add-on cost (Step 13). The generator between Git and Live Recovery is bank-owned code.
