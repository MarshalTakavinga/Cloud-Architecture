# ADR-006: Recovery-Plan Model and Continuous DR Readiness

**Status:** Approved
**Date:** Step 5 of the Case Study 6 pipeline

## Context

[ADR-002](ADR-002-recovery-as-code-active-standby.md) chose recovery as code across independent sites, with a 3-hour budget inside the 4-hour Tier-0 RTO. It did not say what a recovery plan *is*, or how the bank knows before a test or a disaster that the plan will work. The May 2026 failure showed that a plan can be correct on paper and wrong in reality. Rules were missing in DC2, and replication lagged.

## Decision

1. **One recovery plan per business service**, in Git, owned by the service owner and reviewed by the platform team. A plan is an ordered set of recovery groups:
   - G0: shared services, always active in DC2
   - G1: databases
   - G2: middleware
   - G3: application servers
   - G4: payments gateways
   - G5: ingress and network cutover
   - G6: business validation

   Every group has health gates and timeouts.
2. **Humans decide, automation executes.** A declaration and a switchover approval are the only manual steps. The vendor procedures for the payments gateways are wrapped as automation with the vendors' agreement.
3. **A daily readiness job** checks:
   - replication lag against RPO
   - reserved DC2 capacity
   - firewall-rule parity between the sites
   - that every VM in the plan exists and is replicated
   - that images and patches are present in DC2's repository

   It publishes **DR-ready or not DR-ready per service**. A Tier-0 change that breaks readiness **fails the change**.
4. **Evidence by default.** The orchestrator timestamps every group. Test reports compare actual times against the budget, and they are filed as MRA evidence.
5. **Cadence:** a full Tier-0 test twice a year, monthly partial tests that rotate through services, and a disconnected-week drill each year ([ADR-004](ADR-004-govern-centrally-operate-locally.md)).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **One monolithic plan for all of Tier 0.** Rejected. It can't be tested piece by piece, and one broken service blocks the rest.
2. **Plans kept in the orchestrator's own database only.** Rejected. That leaves no review, no history, and no portability if the orchestrator changes with the platform.
3. **Readiness checked only before scheduled tests.** Rejected. Drift between tests is what failed in May 2026.

## Consequences

- **Positive:** The bank knows *every day* whether each Tier-0 service can recover, not only twice a year.
- **Positive:** Plans survive a platform change, because they're in Git and the orchestrator only executes them.
- **Negative / accepted trade-off:** Service owners have new obligations: plan ownership and validation scripts. Tier-0 change lead time rises slightly, because readiness is a gate.
