# ADR-033: Produce the MRA Evidence on the Current Platform; Move Tier 0 after the Examination

**Status:** Approved
**Date:** Step 12 of the Case Study 6 pipeline

## Context

Examiners expect a successful full Tier-0 recovery before the **Q4 2027 examination** (M13–M15). Tier 0 should move to a new platform last, after it has proven itself ([Step 4](../docs/architecture-options-and-styles.md)). The recovery design from Steps 4–5 (Git plans, orchestrator, readiness gate, firewall parity, Data Guard sizing, vault, clean room) is platform-neutral.

## Decision

- **The resilience program runs on the current VMware estate first.**
  - Recovery plans in Git.
  - The orchestrator runs against SRM, Data Guard, and automation.
  - Zone intent is rendered to NSX in both sites (vDefend on the Tier-0 hosts for the bridge period).
  - Data Guard transport is resized.
  - The vault and clean room are built.
- **Two full Tier-0 recovery tests on VMware, at M8 and M11,** before the examination. These are the evidence.
- **Tier 0 moves to Azure Local after the examination** (M15–M19), and is re-proven there with tests at M17 and M19 and the disconnected-week drill.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Migrate Tier 0 first, and prove recovery on Azure Local before the examination.** Rejected. It puts the riskiest migration against the hardest deadline, on the least-proven platform.
2. **Delay all resilience work until the new platform is ready.** Rejected. The bank would have no evidence at the examination.

## Consequences

- **Positive:** The examination sees a remediated, tested recovery on the platform that is actually running Tier 0. Neither risk depends on the other.
- **Positive:** Plans, intent, and orchestration logic built in 2027 carry over to Azure Local unchanged. Only the executors change.
- **Negative / accepted trade-off:** Some work is done twice: SRM/NSX executors first, then Hyper-V Replica/Datacenter Firewall executors. vDefend is needed on the Tier-0 hosts in DC2 for the bridge period.
