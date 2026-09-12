# Migration Roadmap — Meridian Health Network

Step 12: a phased plan for moving all 46 sites onto the Azure target architecture approved in `target-architecture.md`/ADR-034, plus the new decisions this stage required — ADR-035 (sequencing model), ADR-036 (rollback strategy), ADR-037 (decoupling compliance conditions from the full timeline). This document is execution planning, not design: it does not reopen anything from Steps 6–11. Where it names risks or dependencies, those are risks in *how* the approved design gets rolled out, not gaps in the design itself.

Timing throughout this document is **illustrative and relative** — "Month N" markers, not calendar-date commitments. The point is the sequencing logic and the relative pacing, not a specific start date this fictional case study was never given.

## 1. Guiding Principles

- **No all-46-site cutover weekend.** The explicit constraint in `requirements.md`. Section 2 below shows how the program breaks into waves that respect it.
- **The shared-services reality drives the sequencing model, not an assumption of per-clinic data isolation.** CareLink PM is one database, one integration bus, one portal serving all 46 sites today — ADR-035 designs around that fact rather than around a simpler but unrealistic "each wave gets its own slice of data" model.
- **Every wave gets a real, cheap way back.** ADR-036 — not a rollback plan that exists on paper only.
- **Compliance urgency doesn't have to mean a rushed platform decision or a rushed rollout.** ADR-037 — the insurer's four conditions are satisfied on their own accelerated track, decoupled from the pace of the 46-site rollout.

## 2. Program Structure

| Wave | Scope | Sites | What moves | Rollback mechanism (ADR-036) |
| --- | --- | --- | --- | --- |
| 0 — Foundation | Landing zone build-out | 0 (no clinical cutover) | Azure landing zone (network, management groups, policy), temporary hybrid ExpressRoute/VPN circuit to on-prem HQ, Entra Connect + Entra ID P2 Conditional Access, Key Vault, Bicep IaC modules, CI/CD pipeline, Microsoft Sentinel (ingesting on-prem logs from day one), MFA/encryption/backup quick-wins (ADR-037) | N/A — nothing clinical has moved yet |
| 1 — Central services | Single-event cutover (ADR-035) | 0 sites individually, all 46 depend on it | CareLink PM database (SQL Server 2014 AAG → Azure SQL Managed Instance), LinkEngine/Service Bus integration bus, MeridianConnect Portal, Telehealth — cut over once, off-peak | 30-day bake: legacy SQL AAG kept live via one-way log shipping; legacy Portal/LinkEngine paths kept warm behind DNS/Front Door |
| 2 — Pilot compute | First real per-site wave | 2 (lowest-volume outpatient clinics) | Citrix session routing for these 2 clinics redirected to the new Azure Citrix Cloud Connector fleet, authenticating against the already-migrated database | 14-day bake, routing-only rollback to legacy VDA farm |
| 3 | Expand the proven pattern | 6 clinics (8 cumulative) | Same as Wave 2 | Same |
| 4 | Scale | 8 clinics (16 cumulative) | Same | Same |
| 5 | Scale | 8 clinics (24 cumulative) | Same | Same |
| 6 | Scale | 8 clinics (32 cumulative) | Same | Same |
| 7 | Completes outpatient clinics | 10 clinics (42 cumulative — all outpatient clinics done) | Same | Same |
| 8 | Urgent care | 3 urgent care centers | Same pattern, sequenced after the model is proven at scale — highest walk-in/acute-continuity sensitivity of the non-surgical sites | Same |
| 9 | Ambulatory surgery center | 1 ASC | Same pattern, sequenced last of the existing 46 — highest clinical stakes of any single site if scheduling is disrupted | Same |
| — Acquisition (parallel) | 9 newly acquired pediatric clinics | 9 | Onboard **directly** onto the finished landing zone and already-migrated database — never touch on-prem infrastructure at all. Starts once Wave 2 validates the golden path, runs alongside Waves 3–7. | N/A — greenfield onboarding, no legacy system to roll back to |
| 10 — Decommission | Program closeout | 0 (infrastructure only) | Legacy on-prem Citrix VDA farm, SQL Server 2014 AAG, and the temporary hybrid circuit are decommissioned after a final archival backup; first full-scale **live** DR failover test run against the paired Azure region | N/A — this wave is itself the point of no return, gated on every prior wave's bake period having cleared cleanly |

Existing-site total: 42 outpatient clinics + 3 urgent care centers + 1 ambulatory surgery center = 46, matching `current-state.md` §1 exactly. The 9 acquired clinics are additive and never touch legacy infrastructure, directly delivering the "weeks, not months" onboarding target `requirements.md` calls for.

See [`../diagrams/migration-roadmap.png`](../diagrams/migration-roadmap.png) for the wave timeline.

## 3. Why Urgent Care and the Surgery Center Go Last

Wave sequencing is risk-based, not alphabetical or geographic: the two lowest-volume outpatient clinics go first specifically to prove the pattern with the smallest possible blast radius, then batches scale up once Waves 2 and 3 validate that the golden path actually delivers the fast onboarding the business case depends on. Urgent care centers and the ambulatory surgery center are deliberately held to Waves 8 and 9 — after the pattern has already been proven across 42 sites — because a walk-in acute-care setting and a surgical-scheduling environment carry materially higher consequences from a botched cutover than a scheduled outpatient clinic does. This is the same discipline `decision-matrix.md` and every implementation doc already applied: name the reasoning, don't just assert an order.

## 4. Compliance Quick-Wins Timeline

Per ADR-037, the insurer's four renewal conditions are decoupled from the full 46-site schedule:

| Condition | Satisfied by | Timing |
| --- | --- | --- |
| Organization-wide MFA | Entra Connect + Entra ID P2 Conditional Access + NPS Extension for Azure MFA in front of the existing on-prem VPN/Citrix auth path | Wave 0 — weeks, not the full program |
| Encryption at rest, no exceptions | Dell EMC Unity SAN native at-rest encryption enabled on remaining unencrypted LUNs, including the patient-imaging archive volumes named in `current-state.md` §5 | Wave 0 |
| Immutable, geographically separate backups | Existing Veeam jobs re-pointed at immutable, retention-locked Azure Blob Storage — for current on-prem data, not just future Azure-hosted data | Wave 0 |
| Annually tested DR | First live (not tabletop) DR failover test against the paired Azure region | Shortly after Wave 1's bake period closes — months ahead of full-program completion |

This means all four insurer conditions have a credible path to being satisfied well before the 46-site rollout finishes, removing the forcing function that could otherwise pressure a rushed rollout — the same risk `requirements.md` named for the platform decision, now addressed for the rollout pace too.

## 5. Legacy Infrastructure Survival Risk

ADR-036 keeps the legacy on-prem Citrix VDA farm, its vSphere cluster, and the SQL Server 2014 AAG fully operational for the entire program, as the fallback target for every wave including the last. That infrastructure is already flagged in `current-state.md` §3 as 6.5 years old on average, running at ~85% peak utilization, with the SAN at 91% capacity — real hardware that has to keep functioning for the better part of a year without the capital refresh `requirements.md` notes is otherwise "due in the current on-prem model regardless." This is named as a real program risk, not assumed away: an unplanned hardware failure on infrastructure this old, mid-program, would remove the rollback safety net for whichever sites haven't cut over yet.

The mitigating factor, not a guarantee: load on the legacy environment decreases wave over wave as sites move off it, so the fleet gains headroom as the program proceeds rather than staying pinned at today's peak utilization — by the time the highest-stakes remaining sites (urgent care, the ASC) reach their own wave, the legacy farm is serving a small fraction of its original load. This is a real, structural improvement in the risk profile over time, not a promise that the aging hardware can't fail — if a critical on-prem component fails before Wave 10, it becomes a Step-12-adjacent capital decision (targeted component replacement, not a full refresh) rather than something this roadmap can resolve in advance.

## 6. Explicitly Deferred

- Specific calendar dates and maintenance-window scheduling per wave — this roadmap sets relative sequencing and pacing logic, not a contractually committed calendar; that belongs to program management once Wave 0 actually kicks off.
- Detailed clinician/front-desk communications and training plan per wave — a real workstream, not designed here.
- SIEM alert-tuning runbook for the Wave-0-deployed Sentinel instance — deployed early per ADR-037, but tuning it against real on-prem log volume is operational work for whoever owns it once it's live.
- Final hardware disposal / data-destruction certification process for the decommissioned legacy environment (Wave 10) — a compliance and vendor-management task, not an architecture decision.
- Cost and staffing plan for the program itself — Step 13 by design, the same boundary held throughout this case study.

## 7. Diagrams

- [`../diagrams/migration-roadmap.png`](../diagrams/migration-roadmap.png) / [`.mmd`](../diagrams/migration-roadmap.mmd) — wave timeline: Foundation → Central Services → Pilot → scaled compute waves → Urgent Care → Ambulatory Surgery Center → Decommission, with the parallel acquired-clinic onboarding workstream shown against the same timeline.
