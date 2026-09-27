# ADR-002: Recovery Architecture — Independent Active/Standby Sites with Recovery as Code

**Status:** Approved
**Date:** Step 4 of the Case Study 6 pipeline

## Context

The May 2026 DR test took **11 h 40 min against a 4-hour RTO** and lost **35 minutes of data against a 15-minute RPO**. Examiners issued an MRA and expect a successful full Tier-0 recovery before the Q4 2027 examination (NFR-1). The failure had three causes (`current-state.md` §4):
1. the dependency order in a 140-step manual runbook
2. firewall rules missing in DC2
3. Oracle redo transport lagging under the batch load

DC1 and DC2 are about 290 km apart, with a round trip of about 4 ms.

## Decision

- **Two independent sites, active/standby for Tier 0.** DC2 is a separate failure domain, with its own clusters, control-plane instance, and administration boundary.
- **Database-native replication** for Oracle: Data Guard in asynchronous mode, with:
  - redo transport bandwidth sized for the month-end batch peak
  - a lag alert at 10 minutes
  - a switchover rehearsed monthly
- **Application tiers** are replicated at the platform level, or rebuilt from pipeline images where they are stateless.
- **Network and firewall policy as code**, applied from one source to both sites. DC2's rules can't drift from DC1's, because both are generated from the same definitions.
- **Recovery plans as versioned code**, executed by an orchestrator in dependency order: database, then middleware, then applications, then network cutover, then validation hooks. **Humans decide** (declare the disaster, approve the switchover). **Automation executes.**
- **The recovery-time budget** is 3 hours of planned stages, leaving 1 hour of margin (`architecture-options-and-styles.md`).
- **Test cadence:** a full Tier-0 failover **twice a year**, and a partial test **every month** that rotates through services. Results are recorded as evidence for examiners.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Fix and rehearse the runbook.** Rejected. It still depends on a human sequencing 140 steps under pressure.
2. **A stretched cluster across the two sites.** Rejected for Tier 0. The ~4 ms round trip is within a stretched vSAN cluster's limit (under 5 ms), but the result is one failure domain for configuration errors, upgrades, and ransomware. Examiners expect an independent recovery site, and Oracle RAC stretched over 290 km isn't a supported design.
3. **Active-active Tier 0.** Rejected. The core package and the payment gateways are active/standby by design.

## Consequences

- **Positive:** Each cause of the May 2026 failure has a specific mechanism against it:
  - dependency order is handled by the orchestrator
  - firewall drift is handled by policy as code
  - redo lag is handled by transport sizing and the lag alert
- **Positive:** Frequent partial tests turn DR from an annual event into routine operations.
- **Negative / accepted trade-off:** DC2 holds standby capacity for Tier 0 that sits mostly idle. It is used for Tier-2 workloads that can be shed during a failover.
- **Negative / accepted trade-off:** Recovery plans are code the team must maintain. Every Tier-0 change now includes a change to the recovery plan, enforced in the change process.
