# ADR-025: Rollout Sequencing — Security First, Two Tracks, OEM Plants First

**Status:** Approved
**Date:** Step 11 of the Case Study 4 pipeline

## Context

Three fixed dates apply: the insurer renewal in July 2027 (M10), OEM genealogy readiness in Q4 2027 (M13–M15), and −30% downtime by October 2028 (M24). Levels 0–2 can only be changed in the December and July shutdowns, and only the December 2026 shutdown precedes the insurer deadline. [ADR-001](ADR-001-edge-cloud-responsibility-split.md) through [ADR-003](ADR-003-ot-segmentation-reference-architecture.md) and ADR-024 condition 3 impose three further requirements:

- the cloud connection must go into a segmented plant, never a flat one
- the Outbox Service must pass its acceptance suite before any plant after the pilot
- tag-model mapping is the pacing effort

## Decision

1. **Run two parallel tracks with different pacing.**
   - The **security track** touches the plant network and is paced by shutdown windows.
   - The **data-platform track** adds only Level 3–3.5 components and is paced by tag mapping and the wave gates.
2. **Security goes first at every plant.** No plant gets a cloud bridge until its DMZ, secure remote access, and L4↔L3 default-deny are in place (Phase 0a, all plants by M3). Full L2/L3 separation happens in the December 2026 shutdown at the five highest-exposure plants (09, 03, 08, 10, 05), and in the July 2027 shutdown at the remaining five (01, 02, 04, 07, 12). Plants 06 and 11 already have DMZ segmentation and are brought up to the reference model in weekend windows.
3. **Negotiate staged acceptance with the insurer from M1.** Kestrel presents the full plan and the Phase 0a controls (which close the actual Querétaro attack path) early, and asks for renewal on the basis of 7/12 plants segmented by M8, the remaining 5 in the renewal-month shutdown, and compensating controls until then.
4. **Order the data waves by business deadline, not geography.**
   - Pilot at **Plant 06**: it already has a DMZ, has an MES, and is an OEM steering plant.
   - Then the other **OEM program plants** (01, 02, 05, 08, 09), plus 03 for telemetry.
   - Then 04, 07, and 10, then the EU plants 11 and 12.
5. **Onboard tags in tiers.** Tier 1 (critical assets plus genealogy) goes to every plant first. Tiers 2 and 3 follow in Phase 5.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Platform first, security in parallel "as plants are onboarded".** Rejected. It would connect flat plants to a cloud platform, the exact risk named in driver 1. It would also lose the December 2026 shutdown to data work when the insurer deadline needs it for zoning.
2. **All 12 plants' full zoning in the December 2026 shutdown.** Rejected as infeasible and unsafe. It would need seven or more simultaneous integrator crews on live control networks in a 10-day window, with no chance to learn from the first plants. Five plants is the realistic limit, prioritized by exposure.
3. **Geographic waves (US, then Mexico, then Germany).** Rejected. The OEM genealogy deadline is plant-specific (01, 02, 05, 06, 08, 09 span the US and Mexico), and a geographic order would leave two OEM plants until after Q4 2027.
4. **Onboard each plant's full tag estate before moving to the next plant.** Rejected. At roughly 15,000 tags per plant, the waves would be paced by Tier 3 tags that no deadline depends on, and the OEM plants would not all be ready by Q4 2027.

## Consequences

- **Positive:** The insurer's specific concern, the IT-to-OT path that ransomware used, is closed at all 12 plants by M3. Zoning evidence then accumulates ahead of the renewal rather than arriving at it.
- **Positive:** All six OEM plants are genealogy-ready by M14 (November 2027), inside the Q4 2027 window, with a month of margin.
- **Negative / accepted trade-off:** Full renewal still depends on the insurer accepting a staged plan, since five plants are zoned *in* the renewal month. If refused, the fallback is a second interim renewal at a higher premium. This is carried to the Step 12 risk register with the M1 engagement as its mitigation.
- **Negative / accepted trade-off:** The −30% downtime target at M24 gets only about 10–14 months of fleet-wide Tier 1 data from the later-wave plants. Early gains are expected at the pilot and OEM plants (where the critical press and machining assets are concentrated). The target is at risk if Phase 4 slips, and it is tracked as such.
