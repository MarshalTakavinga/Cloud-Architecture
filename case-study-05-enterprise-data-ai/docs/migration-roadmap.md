# Step 11: Migration Roadmap and ADRs

## Purpose

[Step 10](target-architecture.md) confirmed the GCP target, conditional on gate G0. This step sequences the work against the contract dates Harborline did not choose (M1 = October 2026):

| Date | Month | What happens |
|---|---|---|
| **Mid-December 2026** | M3 | **Gate G0** complete: Iceberg parity, model terms, translation proof of concept ([ADR-027](../adr/ADR-027-cloud-platform-selection.md)) |
| **31 December 2026** | M3 | **Teradata notice deadline** |
| **30 June 2027** | M9 | Teradata term ends |
| **30 June 2028** | M21 | End of the one-year **bridge extension**, if signed (+25%) |

## Why This Migration Shape Differs from the Earlier Case Studies

- Case Study 2 separated a net-new capability from a legacy migration.
- Case Study 4 separated network work paced by physical shutdown windows from a platform paced by tag mapping.

This case study has **three tracks with genuinely different clocks**:

1. **Governed AI** (drivers 1 and 2). This is the most visible value, and it **does not depend on Teradata at all**. The assistant needs ECM indexing, ClaimCenter CDC (for claim context and ACLs), the governance plane, and the AI gateway. None of these is the warehouse.
2. **The Teradata exit** (driver 3). Its clock is the contract, and its pace is set by about 1,800 procedures and macros, BTEQ scripts, and a dual-run per domain.
3. **SAS retirement** (driver 5's cost baseline). It depends on the reserving domain having moved, so it naturally comes last.

The roadmap's main design choice is to **decouple the assistant from the warehouse migration** ([ADR-029](../adr/ADR-029-decoupled-assistant-rollout.md)), so that the business sees value within about 8 months, while the Teradata exit proceeds at the pace its reconciliation needs.

## The Teradata Contract Decision (ADR-028)

**At M3, after G0: give notice of non-renewal, and sign the one-year bridge to 30 June 2028.**

Exiting by 30 June 2027 would leave about six months after G0 to translate, reconcile, and sign off every domain, including **two quarterly reserving closes run in parallel**. That is not credible for about 1,800 procedures and 2,400 Informatica jobs, even at the optimistic end of the 25–35% manual-rewrite estimate.

The bridge is bought as **insurance for an exit already under way**, not as a renewal. Terms Harborline seeks:
- **extended hardware support** for the ageing appliance
- the right to **reduce licensed capacity** as domains leave

See [ADR-028](../adr/ADR-028-teradata-contract-and-exit-sequencing.md).

## The Plan

| Phase | Months | Track | Scope |
|---|---|---|---|
| **0 — Gate G0 + foundation** | M1–M3 | Platform | G0 proofs of concept (Iceberg parity on the claims domain; model terms; translation of ≥ 200 BTEQ scripts and 150 procedures/macros). GCP landing zone, VPC Service Controls, Workforce Identity Federation with Entra, Dataplex and policy tags, Apigee, use-case register. **Report rationalization** begins (retire ~70%). **2024 Snowflake account:** inventory, re-land legitimate datasets, **close by M4**. FinOps role hired |
| **Teradata decision** | M3 | Exit | Notice of non-renewal + one-year bridge ([ADR-028](../adr/ADR-028-teradata-contract-and-exit-sequencing.md)). **New Teradata development frozen** |
| **1 — Assistant foundation** | M3–M6 | AI | Datastream CDC from ClaimCenter (assignments, claim context). Document pipeline and **hot tier for the pilot scope**. Golden set (~1,500 questions) built with Claims SMEs. Red-team suite. Evaluation harness |
| **2 — Assistant pilot** | M6–M8 | AI | **~300 adjusters**, personal auto, in the three Prairie Shield states (Guidewire-native, no NY or CO rules in the pilot scope). **Gate A1** before go-live, **gate A2** before scale ([ADR-029](../adr/ADR-029-decoupled-assistant-rollout.md)) |
| **3 — Assistant scale** | M9–M14 | AI | All lines and states, **~3,800 claims staff + ~600 underwriters**. Coastal claim documents indexed (M12+). NY and CO use cases reviewed against state-specific requirements before enabling |
| **4 — Claims domain** | M4–M10 | Exit | Translate → dual-run (M8–M10) → sign-off → freeze. Claims marts repointed in Tableau |
| **5 — Policy and billing domain** | M8–M13 | Exit | The same pattern. Coastal nightly files ingested into bronze (M6–M9) |
| **6 — Reserving and actuarial domain** | M11–M17 | Exit | Silver conformed model complete. **Two consecutive quarterly closes run in parallel**: the Q3 2027 close (October 2027, M13) and the Q4 2027 close (January 2028, M16). The ≤ 8-day close target (NFR-8) is measured on the second |
| **7 — Regulatory and remaining** | M14–M18 | Exit | Statistical plans, annual-statement schedules, vendor feeds (C3). **Teradata frozen at M18** |
| **Decommission** | M19–M20 | Exit | Final archive to Iceberg (history is already in bronze). **Teradata and Informatica switched off by M20 (May 2028)**, one month inside the bridge |
| **8 — SAS retirement** | M9–M24 | Actuarial | SAS reads the lakehouse from M9. Programs are ported to Python/SQL by priority. Reserving models move **after** the reserving domain sign-off. **SAS retired by M24** |

See [`diagrams/migration-roadmap.md`](../diagrams/migration-roadmap.md) for the reference Gantt chart.

## Gates

| Gate | When | Pass criteria |
|---|---|---|
| **G0** | M3 | Iceberg parity; model terms confirmed; translation proof of concept sized ([ADR-027](../adr/ADR-027-cloud-platform-selection.md)) |
| **A1: assistant pilot go-live** | M6 | Golden-set faithfulness ≥ 95%. **Zero red-team leaks**. p95 ≤ 6 s. Audit trail verified end to end. Apigee admitting only confirmed-term models. The use case approved in G4 |
| **A2: assistant scale** | M8 | Pilot adoption ≥ 60% weekly active. Measured search-time reduction. **Zero leakage incidents**. Cost per query ≤ $0.05. No regression on online quality metrics |
| **D (per domain): domain sign-off** | Per phase | **20 consecutive business days** of clean reconciliation (row counts, control totals, critical reports) plus business-owner sign-off. For reserving: **two parallel quarterly closes** reconciled |
| **T: Teradata decommission** | M19 | Every domain signed off. No consumer reads Teradata for 30 days (verified from query logs). Archive verified |

## Rollback

Explained in [ADR-030](../adr/ADR-030-domain-dual-run-and-rollback.md):

- **Assistant:** it is a new capability, so rollback means turning it off per use case at the gateway. Nothing depends on it.
- **Warehouse domains:** during a domain's dual-run, and until the Teradata freeze, rollback means **repointing that domain's consumers back to Teradata**, which is possible because Teradata keeps running under the bridge. After the freeze (M18) there is no rollback to Teradata. That is exactly why every domain must pass gate D before it.
- **Reserving:** the parallel quarterly closes mean an actuary can sign the official close from either platform until the second close reconciles.

## What This Step Carries Forward

- **[Step 12](cost-and-risk-analysis.md):**
  - the dual-run period
  - the bridge premium (about $3.9M × 1.25 for July 2027 – June 2028)
  - assistant ramp costs against the $0.05 ceiling
  - SAS licence step-down
  - run-rate against the $6.8M baseline
  - the consolidated risk register
- **Operational readiness:** golden-set ownership in Claims, the FinOps analyst, the G4 approval board (Compliance, Claims, Data), and assistant support. These are named as Phase 0–1 deliverables.
