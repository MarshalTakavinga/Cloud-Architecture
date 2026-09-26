# ADR-027: Coexistence and Rollback Strategy

**Status:** Approved
**Date:** Step 11 of the Case Study 4 pipeline

## Context

Nothing in production is replaced by this initiative, since historians, MES, PLCs, and HMIs all stay ([Step 4](../docs/architecture-options-and-styles.md)). So the data-platform track has no cutover to roll back. Two things do carry production risk:

- **Segmentation changes** on live plant networks. A wrong firewall rule can stop a line.
- **Genealogy becoming authoritative.** Once the new record is the record of truth, an error in it is a quality-system event.

## Decision

1. **Data platform: read-only coexistence.** The edge platform reads Level 2 through OPC UA and native drivers and never writes to it. **Rollback means stopping the edge collection at a plant**, with no effect on production, historians, or MES. Model activation has its own one-step rollback ([ADR-023](ADR-023-gcp-network-identity-and-deployment.md)).
2. **Genealogy: parallel run, then a per-plant authority switch.**
   - The new genealogy record runs alongside the existing one (MES, or paper travelers and the lab database) for at least 30 days.
   - It becomes authoritative per plant only after gate G3 ([ADR-026](ADR-026-pilot-plant-and-wave-gates.md)), with sign-off from the plant quality manager.
   - After the switch, the previous record keeps being produced for a further 90 days as a fallback.
   - Reverting authority is a documented quality decision, not a technical rollback.
3. **Segmentation: monitor, then enforce, with a timed back-out.**
   - Every new zone and conduit rule set runs in **log-only mode for at least 2 weeks** before its shutdown window, so that legitimate flows it would block are found in advance.
   - Each shutdown change has a timed back-out: if a line cannot be validated within the agreed restart window, the **previous rule set is restored**.
   - Back-out **never** re-enables TeamViewer, vendor modems, or the flat L4↔L3 path. Those removals from Phase 0a are not reversible.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Make genealogy authoritative immediately at go-live.** Rejected. It would bet the OEM contract on day-one correctness of a new, custom path (the recorder, the journal, and the outbox).
2. **Enforce segmentation rules directly in the shutdown, with no monitor phase.** Rejected. Undocumented flows are the norm in brownfield plants (Querétaro found 31 unlisted devices), and discovering them at restart turns a security change into a production outage.
3. **Allow the security back-out to restore remote-access tools if a vendor cannot connect.** Rejected, because that is exactly how the risk returns. Vendors are onboarded to the brokered secure-remote-access service before cut-over instead.

## Consequences

- **Positive:** The only production-risking changes are paired with evidence gathered beforehand (monitor mode) and a bounded back-out.
- **Positive:** Genealogy authority moves plant by plant with a quality sign-off, which is the evidence trail an OEM supplier-quality audit expects.
- **Negative / accepted trade-off:** Running genealogy in parallel costs 30+ days of double effort at non-MES plants, and 90 more days of producing the fallback record. This effort is costed in Step 12.
