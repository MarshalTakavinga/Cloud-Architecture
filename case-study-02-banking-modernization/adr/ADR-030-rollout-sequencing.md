# ADR-030: Rollout Sequencing for the Real-Time Payments Capability

**Status:** Approved
**Date:** Step 12 of the Case Study 2 pipeline

## Context

[ADR-029](ADR-029-cloud-platform-selection.md) confirmed Azure as the target platform. Unlike Case Study 1's Solstice, where production traffic already existed and had to be *migrated* from one platform to another, this case study's real-time payments capability is **entirely new-build** — the mainframe has never had a real-time posting path, so there is no existing production real-time-payments traffic to cut over. The one genuine migration in this case study is the 2021 AWS account's workloads, which need to move onto Azure. This ADR sequences both kinds of work against the board-committed 18-month deadline (driver 1).

## Decision

Rollout proceeds in five phases, sequenced so that the highest-schedule-risk item (FedNow/ISO 20022 rail certification) starts as early as possible and the lowest-risk, fully decoupled item (the 2021 account migration) is free to slip without endangering the board-committed deadline:

1. **Phase 0 — Foundation (months 1–3):** Azure Landing Zone ([ADR-010](ADR-010-azure-landing-zone-and-segmentation.md)), ExpressRoute provisioning ([ADR-008](ADR-008-hybrid-connectivity.md), started immediately given its own weeks-long lead time), Entra ID federation ([ADR-009](ADR-009-azure-identity.md)), and CI/CD/IaC tooling stood up.
2. **Phase 1 — Core real-time path (months 3–8):** Hold/Release Adapter, CDC Connector, and Ledger-of-Intent Service built and tested against the mainframe's lower (QA/UAT) LPAR, in coordination with Palisade's mainframe team on the still-open specific-CICS-transaction question ([ADR-001](ADR-001-mainframe-integration-approach.md)).
3. **Phase 2 — Fraud and reconciliation (months 6–10, overlapping Phase 1):** Fraud Orchestration Service built in coordination with Palisade's BSA/AML and fraud teams (the working assumption named in `requirements.md`), and the nightly Reconciliation Process built and validated against synthetic provisional/confirmed mismatches before any real payment ever flows through it.
4. **Phase 3 — Gateway integration and rail certification (months 8–14):** The bought ISO 20022/FedNow gateway ([ADR-002](ADR-002-payment-hub-build-vs-buy.md)) is integrated and taken through FedNow/RTP rail certification — the single longest-lead-time, least-controllable item in this plan, which is why it starts as early as the core real-time path allows rather than being sequenced last.
5. **Phase 4 — Limited pilot (months 13–16):** Real-time payments enabled for a limited transaction volume or branch/customer subset, with reconciliation-exception rate monitored closely, since the nightly Reconciliation Process has no production track record before this point.
6. **Phase 5 — Full rollout, decoupled from the 2021 account migration (months 15–18):** Real-time payments opened to full volume across all customers. **In parallel, not sequentially dependent**, the 2021 AWS account's push-notification and mobile-analytics workloads migrate into the Azure landing zone's second spoke ([ADR-010](ADR-010-azure-landing-zone-and-segmentation.md)) — a lower-risk, fully decoupled workstream that may extend past month 18 without threatening the board-committed real-time-payments deadline.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Sequence the 2021 account migration before the real-time payments build**, on the theory that closing the governance gap first is the more conservative order. Rejected — the 2021 account's workloads (push notifications, mobile analytics) carry no dependency relationship with the real-time payments path at all; sequencing them first would consume schedule against the one deadline that is actually board-committed (driver 1) for a workstream that has no such deadline. Decoupling them, not sequencing them, is what protects the critical path.
2. **Start rail certification (Phase 3) only after the core real-time path (Phase 1) is fully complete**, a strictly linear/waterfall sequencing. Rejected — rail certification's own lead time is the single largest, least-controllable schedule risk in this case study (named in [ADR-002](ADR-002-payment-hub-build-vs-buy.md)); starting it as early as the core-path dependency allows, rather than waiting for full completion, is the only way to protect the 18-month deadline against that specific risk.
3. **A single "big bang" production cutover with no limited pilot phase.** Rejected — the nightly Reconciliation Process is a brand-new operational process with no track record ([ADR-003](ADR-003-provisional-vs-confirmed-state-model.md)); a limited pilot surfaces reconciliation-exception patterns and operational readiness gaps at a volume where they're manageable, before the full customer base depends on the process working correctly every night.

## Consequences

- **Positive:** The plan's structure directly protects the one hard, board-committed deadline (driver 1) by decoupling the one workstream that has no deadline (the 2021 account migration) from it entirely, and by front-loading the single largest schedule risk (rail certification) rather than sequencing it last.
- **Positive:** The limited-pilot phase (Phase 4) gives the new Reconciliation Process a real-world proving ground before it has to be right for every customer, every night.
- **Negative / accepted trade-off:** Phases 1 and 2 overlap deliberately to compress the timeline, which means the Fraud Orchestration Service and the core real-time path are being integration-tested against each other while both are still under active development — a coordination cost accepted specifically because the 18-month deadline does not allow a strictly sequential build.
- **Carried to Step 13:** The cost of running Phase 4's limited pilot (a period of dual operational readiness — the new real-time path live but unproven, the old fully-batch path still the fallback) is a named cost-and-risk item, not folded into steady-state run-rate.
