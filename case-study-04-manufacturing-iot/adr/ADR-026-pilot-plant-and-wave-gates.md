# ADR-026: Pilot Plant Selection and Wave Gates

**Status:** Approved
**Date:** Step 11 of the Case Study 4 pipeline

## Context

[ADR-025](ADR-025-rollout-sequencing.md) calls for one pilot plant, followed by waves. ADR-024 condition 3 makes the Outbox Service's acceptance suite a hard gate before any plant after the pilot. The pilot must prove the parts of the design that are **new to Kestrel and specific to the GCP track**:

- GDC in a plant
- MCe collection publishing Sparkplug B
- the Kestrel-built outbox under real outages
- genealogy exactly-once behavior
- the MSP operating model

## Decision

**The pilot is Plant 06 (Kokomo).**
- It is the only plant that already has a **designed, firewalled DMZ (2024)**, so the pilot tests the data platform without waiting on segmentation.
- It has the homegrown **MES**, so genealogy can be parallel-run against an existing electronic record rather than paper.
- It builds **steering racks for the OEM program**, so pilot results count directly toward driver 3.

**Wave gates.** Each must be met at the pilot before Phase 3, and at each wave's first plant before the rest of that wave.

| Gate | Pass criterion |
|---|---|
| G1 Outbox acceptance | The full suite passes on plant hardware: outage injection, backfill under the rate cap, lane-starvation tests, and replay idempotency |
| G2 Autonomy drill | The WAN is deliberately cut for **72 hours**. Production, local alerts, and genealogy continue. On reconnect the plant is live in under 60 seconds, the backlog drains under the cap, and cloud-side completeness is at least 99.99% (NFR-6) |
| G3 Genealogy parallel run | At least 30 days with **zero** reconciliation mismatches against the MES or paper record. A `SerialHeld` rate above zero is explained and resolved. Hash-chain verification is clean. |
| G4 Node-failure drill | One GDC node is powered off mid-shift. Collection, the broker, and genealogy continue on the remaining nodes |
| G5 Segmentation complete | The plant's ADR-003 zoning is in enforce mode, with the DMZ as the only crossing point |
| G6 Operations handover | MSP runbooks are exercised, the plant approval-gate roles are staffed, and alerts are routed and acknowledged within SLA |

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Plant 01 (Columbus).** It has an MES, sits next to the data center, and is the source of the 2024 SageMaker PoC data. It is a strong candidate. Rejected *as the pilot* because its network is only partially segmented (VLAN only), so the pilot would wait for its July 2027 zoning. It leads the Phase 3 wave instead.
2. **Plant 03 (Fort Wayne).** It had the highest-profile failure, but it is a flat network (zoned in December 2026), has no MES, and is not an OEM genealogy plant. Its pilot would prove predictive maintenance but not genealogy. Its telemetry joins Phase 3.
3. **Plant 11 (Stuttgart).** It has a DMZ and a commercial MES. Rejected because an EU pilot would add residency and works-council dependencies to the first deployment.

## Consequences

- **Positive:** The pilot starts in M5 without waiting for any shutdown, and it proves genealogy against an electronic system of record.
- **Positive:** The gates turn ADR-024's conditions and NFR-1/NFR-6 into pass/fail evidence rather than assumptions.
- **Negative / accepted trade-off:** Plant 06 is the *best-prepared* plant, so the pilot under-tests segmentation-dependent issues. G5 at the first plant of each later wave covers that.
