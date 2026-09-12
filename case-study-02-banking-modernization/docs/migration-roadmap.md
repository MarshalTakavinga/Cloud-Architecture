# Step 12: Migration Roadmap and ADRs

## Purpose

[Step 11](target-architecture.md) confirmed the Azure target architecture. This step sequences how Palisade actually gets there within the board-committed 18-month window (driver 1), and how the one genuine migration in this case study — the 2021 AWS account — fits into that sequence without endangering it.

## Why This Case Study's Migration Shape Differs From Case Study 1's

Case Study 1's Solstice had existing production traffic running on AWS that had to be *migrated* to a newly selected platform — a genuine cutover problem, with a strangler-fig traffic-shift mechanism and a matching rollback. This case study has no equivalent: the mainframe has never had a real-time posting capability, so there is nothing running today that the new Azure architecture replaces. This is a **rollout of a net-new capability**, integrated around an unmodified system of record, plus one genuinely separate, decoupled migration (the 2021 AWS account). [ADR-030](../adr/ADR-030-rollout-sequencing.md) and [ADR-031](../adr/ADR-031-kill-switch-and-rollback-strategy.md) are shaped accordingly — sequencing and a kill-switch, not a cutover and a traffic-weight revert.

## The Five-Phase Plan

See [ADR-030](../adr/ADR-030-rollout-sequencing.md) for the full rationale. In brief:

| Phase | Months | Focus |
|---|---|---|
| 0 — Foundation | 1–3 | Azure Landing Zone, ExpressRoute provisioning, Entra ID federation, CI/CD and IaC tooling |
| 1 — Core real-time path | 3–8 | Hold/Release Adapter, CDC Connector, Ledger-of-Intent Service, tested against the mainframe's lower LPAR |
| 2 — Fraud and reconciliation | 6–10 (overlapping Phase 1) | Fraud Orchestration Service, nightly Reconciliation Process, validated against synthetic data first |
| 3 — Gateway integration and rail certification | 8–14 | ISO 20022/FedNow gateway integration and certification — the single longest-lead-time item, started as early as the core path allows |
| 4 — Limited pilot | 13–16 | Real-time payments live for a limited volume/segment; reconciliation-exception rate monitored closely |
| 5 — Full rollout + 2021 account migration (decoupled) | 15–18 | Full-volume real-time payments; the 2021 AWS account's workloads migrate into Azure in parallel, free to extend past month 18 without risk to the payments deadline |

## Rollback: A Kill-Switch, Not a Traffic-Weight Revert

[ADR-031](../adr/ADR-031-kill-switch-and-rollback-strategy.md) establishes a feature-flag kill-switch at the gateway/Hold-Release-Adapter boundary — disabling new real-time submissions instantly while letting in-flight payments complete normally, with the mainframe's batch settlement never affected either way. Because there is no pre-existing real-time path to "revert to," rollback simply returns customers to the batch-only experience they had before this initiative, with zero data-migration risk: nothing about the mainframe's own ledger ever changes as part of turning the new capability on or off.

## The 2021 AWS Account Migration

Now confirmed as in-scope ([ADR-010](../adr/ADR-010-azure-landing-zone-and-segmentation.md), [ADR-029](../adr/ADR-029-cloud-platform-selection.md)): the account's push-notification and mobile-analytics workloads (Step 4's 6-R disposition: Replatform) move into the Azure landing zone's second, separately governed spoke as Azure Container Apps and Azure Notification Hubs. This work is deliberately sequenced as decoupled, parallel work in Phase 5 (per [ADR-030](../adr/ADR-030-rollout-sequencing.md)'s alternative-1 rejection) — it carries no dependency relationship with the real-time payments path and no deadline of its own, so it is scheduled where it cannot put the board-committed deadline at risk, not because it is unimportant.

## What This Step Carries Forward

The specific CICS transaction for [ADR-001](../adr/ADR-001-mainframe-integration-approach.md)'s hold/release call remains a mainframe-team decision, unresolved since Step 4 and still open here — Phase 1 explicitly names coordinating on it as in-scope work, not a blocker to be resolved before the phase starts. The operational runbook and decision authority for exercising [ADR-031](../adr/ADR-031-kill-switch-and-rollback-strategy.md)'s kill-switch is named as a Phase 4 operational-readiness item, not resolved at the architecture level. Detailed cost modeling for this plan — including the cost of Phase 4's limited-pilot period — is [Step 13](cost-and-risk-analysis.md)'s job.
