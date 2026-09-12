# Step 13: Cost and Risk Analysis (Final Step)

## Purpose

This is the last of Case Study 2's 13 steps. It gives an illustrative steady-state run-rate for the confirmed Azure architecture ([Step 11](target-architecture.md)), states plainly what this initiative's cost case actually rests on, and consolidates every risk named across all 31 ADRs into one register.

## Steady-State Annual Run-Rate (Illustrative)

Anchored to the specific services fixed in [Step 6](azure-implementation.md)'s ADRs, not invented. All figures are illustrative list-price approximations, not vendor quotes — flagged explicitly where that matters.

| Line item | Basis | Annual (illustrative) |
|---|---|---|
| Azure Container Apps (3 services, 2 min replicas each, ~1 vCPU/2 GiB) | [ADR-005](../adr/ADR-005-azure-compute-platform.md) | ~$5,700 |
| Azure SQL Database (4 vCore GP, SQL Ledger enabled) + Blob archive | [ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md) | ~$10,200 |
| Service Bus Premium (1 messaging unit, sessions) | [ADR-007](../adr/ADR-007-azure-messaging.md) | ~$8,160 |
| ExpressRoute circuit + gateway | [ADR-008](../adr/ADR-008-hybrid-connectivity.md) | ~$9,600 |
| Landing zone governance (Policy, Defender for Cloud, Log Analytics) | [ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md) | ~$30,000 |
| ISO 20022/FedNow gateway license (bought product) | [ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md) | ~$320,000 |
| **Total steady-state run-rate** | | **~$383,600/year** |

*(Recalculated directly, not hand-estimated: see the arithmetic behind each line before treating this total as authoritative.)*

**The single largest line by a wide margin is the bought ISO 20022/FedNow gateway license — roughly 83% of the entire steady-state run-rate.** This is the direct cost consequence of [ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md)'s own build-vs-buy trade-off: buying de-risks the highest-schedule-risk component (rail certification) at the cost of a large, ongoing licensing line. The figure here is illustrative — a real vendor quote, not modeled here, is needed before this number is treated as budget-grade, and is named as an open item in the risk register below.

## What This Cost Case Actually Rests On — Stated Plainly

This is **not** a cost-reduction case study. The mainframe's own MIPS-based licensing cost continues exactly as it does today (`problem-statement.md`'s driver 3 concern) — nothing in this architecture reduces it, because the mainframe is never modified or replaced. The ~$383,600/year Azure spend is an **additive** cost, and its value case rests on two things `requirements.md` and `problem-statement.md` actually ask for, not on displacing existing spend:

1. **NFR-9's actual target** — that net-new transaction growth must not add *proportional* MIPS cost — is satisfied structurally, not financially: every unit of real-time payment volume growth runs on Azure Container Apps and Azure SQL Database, entirely off mainframe capacity. The mainframe's cost trajectory flattens because new growth stops landing on it, not because this initiative reduces what it already costs.
2. **Driver 2's regulatory bar** (OCC heightened standards) and **driver 1's competitive necessity** (two direct regional competitors already offer real-time payments) are the actual business case for this spend — a compliance and competitive-parity investment, not a savings initiative. `problem-statement.md` never claims otherwise, and this analysis doesn't manufacture a cost-reduction narrative to match a "cloud is cheaper" expectation the source documents never set.

## One-Time Rollout Cost (Phases 0–4, Months 1–16)

Separate from steady-state run-rate: an illustrative **~$650,000** in external professional-services spend, covering FedNow/ISO 20022 rail-certification support and initial build acceleration across [ADR-030](../adr/ADR-030-rollout-sequencing.md)'s Phases 0–3 — a one-time cost, not a recurring line, and itself illustrative pending actual SI/vendor quotes.

## Consolidated Risk Register

Pulled from every ADR across all 31 decisions in this case study, not re-derived from scratch:

| # | Risk | Category | Likelihood | Impact | Mitigation |
|---|---|---|---|---|---|
| 1 | CDC/messaging load against the mainframe under real-time peak volume is unproven at Palisade | Technical | Medium | High | Load-test against the mainframe's lower LPAR in Phase 1 ([ADR-030](../adr/ADR-030-rollout-sequencing.md)) before any production volume |
| 2 | Rail certification is the single longest-lead-time, least-controllable schedule item in the whole plan | Schedule | High | High | Started as early as Phase 1's dependencies allow (Phase 3, month 8), not sequenced last ([ADR-002](../adr/ADR-002-payment-hub-build-vs-buy.md), [ADR-030](../adr/ADR-030-rollout-sequencing.md)) |
| 3 | Regulatory exam timing — the OCC exam cycle could land before NFR-1/NFR-2 are demonstrably met | Regulatory | Medium | High | An interim compensating-controls plan, named in `requirements.md` as a business risk to track, not resolved architecturally |
| 4 | Skills risk: COBOL/CICS expertise is scarce and aging while real-time/cloud-native skills are new to the organization | Operational | High | Medium | Fully managed Container Apps chosen specifically to minimize new operational burden ([ADR-005](../adr/ADR-005-azure-compute-platform.md)); targeted training plan for the new skill set |
| 5 | The specific CICS transaction for the hold/release call remains undecided by Palisade's mainframe team | Technical / Schedule | Medium | Medium | Prioritized as in-scope coordination work in Phase 1, not treated as a pre-condition blocking the phase from starting ([ADR-001](../adr/ADR-001-mainframe-integration-approach.md)) |
| 6 | Integration-boundary risk between the bought gateway and the in-house fraud/ledger-of-intent services | Technical | Medium | Medium | Named as a first-class Step 5 design concern; integration-tested across Phases 1–2 before certification completes |
| 7 | The nightly Reconciliation Process is a brand-new operational process with no production track record | Operational | Medium | Medium | Validated against synthetic data in Phase 2, then proven at limited volume in Phase 4's pilot before full rollout ([ADR-030](../adr/ADR-030-rollout-sequencing.md)) |
| 8 | New daily operational cost: someone must review and resolve reconciliation exceptions every business day | Operational / Financial | Medium | Low | Named explicitly in [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md) as an ongoing operational-cost line, not a one-time engineering cost |
| 9 | Customer-facing "pending" state needs careful UX and compliance-disclosure treatment | Compliance / UX | Medium | Medium | Flagged as a dependency for whichever team implements Digital Banking Integration ([ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) |
| 10 | ExpressRoute provisioning lead time (typically weeks) could compress the schedule if started late | Schedule | Low | Medium | Provisioned immediately in Phase 0, ahead of every dependent workstream ([ADR-008](../adr/ADR-008-hybrid-connectivity.md), [ADR-030](../adr/ADR-030-rollout-sequencing.md)) |
| 11 | The 2021 AWS account may have undocumented dependencies complicating a clean migration | Operational | Medium | Medium | Decoupled from the payments critical path entirely, scheduled in parallel Phase 5 so a delay here cannot threaten the board-committed deadline ([ADR-030](../adr/ADR-030-rollout-sequencing.md)) |
| 12 | Kill-switch operational runbook and decision authority are not yet defined | Operational | Low | Medium | Named as a Phase 4 operational-readiness item ([ADR-031](../adr/ADR-031-kill-switch-and-rollback-strategy.md)), to be resolved before the pilot goes live |
| 13 | The ISO 20022/FedNow gateway licensing figure above is illustrative, not a vendor quote | Financial | Medium | Medium | A real vendor quote is needed before this case's largest cost line is treated as budget-grade |
| 14 | Entra ID federation cost assumes no new licensing beyond what Palisade may already hold for M365/AD | Financial | Low | Low | A licensing-inventory check against existing Microsoft licensing is needed to confirm this is not an unbudgeted new cost |

## Case Study Status

**All 13 steps of Case Study 2 are now complete.** Problem statement through cost and risk analysis, all four implementation tracks (Azure, AWS, GCP, private cloud), a weighted decision matrix, the Azure target architecture, a phased rollout plan with a kill-switch rollback strategy, and this cost and risk analysis. 31 ADRs total (ADR-001 through ADR-031). Diagrams and IaC templates (Bicep) remain the standing deferred items across every implementation step, consistent with this case study's own convention throughout — named here rather than left implicit now that the pipeline is otherwise complete.
