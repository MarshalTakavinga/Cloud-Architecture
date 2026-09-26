# Step 11: Migration Roadmap and ADRs

## Purpose

[Step 10](target-architecture.md) confirmed the GCP target architecture. This step sequences how Kestrel gets there against three dates the business did not choose, and one physical constraint on when plants can be touched.

**The three dates** (Month 1 = October 2026):

| Date | Month | What is due |
|---|---|---|
| **July 2027** | M10 | Cyber-insurance full renewal, conditioned on IEC 62443 segmentation, MFA remote access, and offline OT backups at every plant (driver 1) |
| **Q4 2027** | M13–M15 | Serial-level genealogy production-ready for the OEM's model-year 2028 program (driver 3) |
| **October 2028** | M24 | Unplanned downtime down 30% (driver 2) |

**The physical constraint:** Levels 0–2 can only be changed in the **late-December** (~10 days) and **July** (~2 weeks) shutdowns. Levels 3–3.5 can use monthly weekend windows. **Only the December 2026 shutdown falls fully before the insurer deadline.**

## Why This Migration Shape Differs from Case Studies 1–3

- **Case Study 1** was a production cutover with a traffic-shift rollback.
- **Case Study 2** was a net-new capability rolled out behind a kill-switch.
- **Case Study 3** was a site-by-site cutover of a vendor application.

This case study is **neither a cutover nor a single launch**. Nothing running today is replaced: the historians, MES, PLCs, and HMIs all stay, and the new platform is a *read-only tap* beside them. What *is* disruptive is the network work. Re-segmenting 12 live plants is where production risk lives, so the roadmap is really **two tracks with different risk profiles**:

- a **security track** that touches the plant network and is paced by shutdown windows
- a **data-platform track** that only adds things at Levels 3–3.5 and is paced by tag-mapping effort

[ADR-025](../adr/ADR-025-rollout-sequencing.md) explains why the security track leads.

## The Plan

### Plant groupings used below

- **OEM program plants** build the safety-critical brake and steering components for the MY2028 program: **01, 02, 05, 06, 08, 09**.
- **Flat-network plants** (highest ransomware exposure, [`current-state.md`](current-state.md) §1): **03, 04, 05, 07, 08, 10**, plus **09**, where only an emergency firewall is in place.

### Phases

| Phase | Months | Track | Scope |
|---|---|---|---|
| **0a — Plant perimeter (all 12 plants)** | M1–M3 (weekend windows) | Security | OT asset inventory and passive OT monitoring. Offline and immutable backups of every PLC program and HMI/SCADA configuration. An industrial DMZ built at each plant. **MFA-brokered secure remote access** replaces TeamViewer and vendor modems (removed, not merely disabled). Default-deny at the enterprise-to-plant (L4↔L3) boundary. None of this touches Levels 0–2. |
| **0b — December 2026 shutdown** | M3 | Security | Full L2/L3 separation, plus containment zones for Windows 7 HMIs, at the **five highest-exposure plants: 09, 03, 08, 10, 05**. Rules run in log-only (monitor) mode for at least 2 weeks beforehand ([ADR-027](../adr/ADR-027-coexistence-and-rollback.md)). |
| **1 — Platform foundation** | M1–M6 (parallel) | Data | GCP landing zone, VPC-SC perimeters, and HA VPN (Columbus → us-east5; Germany → europe-west3). Workforce Identity Federation with Entra ID. The **genealogy evidence project** (ADR-024 condition 1). The **edge managed-service provider (MSP) contract** (condition 2). The **Outbox Service build plus its acceptance harness** (condition 3). The ISA-95 naming standard and tag-mapping tooling. Hardware orders for 36 nodes. **2024 SageMaker account: model code extracted, historian data copy purged, account closed by M3.** **Ramos Arizpe second WAN circuit** ordered (lead time). **Gate G0 (by M3):** commercial confirmation with binding quotes before any platform-specific licence or hardware commitment ([Step 12](cost-and-risk-analysis.md), ADR-024 addendum). |
| **2 — Pilot: Plant 06 (Kokomo)** | M5–M9 | Data | A GDC cluster in its existing 2024 DMZ design. Critical-asset telemetry and vibration sensors. Genealogy runs in **parallel-run mode** against the existing MES. Outage drills. Exit through the pilot gate ([ADR-026](../adr/ADR-026-pilot-plant-and-wave-gates.md)). |
| **Insurer evidence** | M8 (May 2027) | Security | Evidence package: 12/12 plants with DMZ, secure remote access with MFA, offline backups, and monitoring; **7/12 segmented** (the 5 Phase 0b plants plus 06 and 11, which already had DMZ-based segmentation and receive gap remediation to the reference model in weekend windows); the remaining 5 scheduled for the July 2027 shutdown under compensating controls. The **staged-acceptance conversation with the insurer starts in M1**, not M8 ([ADR-025](../adr/ADR-025-rollout-sequencing.md)). |
| **0c — July 2027 shutdown** | M10 | Security + Data | Full L2/L3 separation at the **remaining five plants (01, 02, 04, 07, 12)**, and cell/line zoning at the Phase 0b plants and at 06 and 11. **Serial-station integration** (scanners, cycle-complete signals) at the non-MES OEM plants **05, 08, 09**. |
| **3 — OEM program wave** | M9–M14 | Data | Plants **01, 02, 05, 08, 09**, plus **03 (Fort Wayne) for telemetry only**, since it had the $2.9M press failure. Scope is **Tier 1 only**: critical assets plus genealogy-relevant tags. Genealogy parallel-run of at least 30 days, then the per-plant authority switch. **Genealogy is production-ready at all six OEM plants by M14 (November 2027).** |
| **4 — Remaining plants** | M14–M20 | Data | Plants **04, 07 (Mitsubishi via MCe drivers), and 10 (after the second WAN circuit is live)**, then the **EU plants 11 and 12** in europe-west3. The EU plants go live with non-personal data first; operator-linked events are added only after works-council agreement. |
| **5 — Scale and retire** | M12–M24 | Data | Tier 2 (OEE state tags for all lines) and Tier 3 (the remaining tag estate) across all plants. Cross-plant models by asset class. Handheld vibration routes retired on critical assets. Spreadsheet OEE retired. Retirement decision on the Plant 05 Wonderware historian. **−30% downtime measured at M24.** |

A reference Gantt chart is in [`diagrams/migration-roadmap.md`](../diagrams/migration-roadmap.md).

## Tiered Tag Scope: How the Waves Fit the Calendar

`requirements.md` names tag-model debt (180,000 tags with no naming convention) as the thing most likely to pace the program. The waves therefore onboard **by tier, not by whole plant**:

- **Tier 1:** the ~300 critical assets, plus genealogy-relevant tags (roughly 10–15% of tags)
- **Tier 2:** machine-state tags for OEE on every line
- **Tier 3:** everything else

Because only Tier 1 is needed for drivers 2 and 3, six plants can be onboarded in Phase 3 without mapping 90,000 tags first.

## Rollback and Coexistence

[ADR-027](../adr/ADR-027-coexistence-and-rollback.md) sets out the rollback approach. In short:

- **Data platform:** it is a read-only tap, so rollback means stopping the edge collection. Historians, MES, and production are unaffected.
- **Genealogy:** it runs in parallel with the existing record (MES or paper travelers) and becomes authoritative per plant only after 30 days of zero reconciliation mismatches.
- **Segmentation:** every rule runs in monitor mode first. Each shutdown change has a timed back-out plan. The rollback for *security* changes is restoring the previous rule set, **never** re-enabling TeamViewer or the vendor modems.

## What This Step Carries Forward

- **Cost ([Step 12](cost-and-risk-analysis.md)):** hardware, licences (GDC vCPU, MCe, broker), the MSP contract, the Phase 0 integrator crews, the Ramos Arizpe circuit, and the cloud run-rate. Step 12 must also test ADR-024's cost review trigger.
- **Risks to consolidate in Step 12:** the insurer accepting a staged plan; integrator crew capacity for two back-to-back shutdowns; the Outbox Service delivered on time for the pilot; MCe instance counts; the works-council timeline.
- **Operational readiness:** the MSP runbooks, the plant approval-gate roles, and the OT monitoring alert destination (a managed service, per [ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)'s consequence) are Phase 1 deliverables named here, not designed at architecture level.
