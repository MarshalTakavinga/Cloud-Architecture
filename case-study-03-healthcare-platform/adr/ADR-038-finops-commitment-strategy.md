### ADR-038: FinOps commitment strategy — defer Reserved Capacity until post-cutover telemetry validates sizing

**Context:**
[`cost-and-risk-analysis.md`](../docs/cost-and-risk-analysis.md) models Meridian's steady-state Azure spend using Pay-As-You-Go rates. Every core resource's sizing in ADR-005, ADR-006, ADR-008, and ADR-010 is explicitly named as a directional starting point, not a validated figure — each of those ADRs says outright that real right-sizing needs actual telemetry (Azure Migrate assessment, Application Insights data, Citrix Capacity assessment) in the first 90 days after cutover, and that sizing may move. Azure Reserved Instances and Savings Plans offer real discounts (commonly 20–40%+ for 1–3 year terms) on compute and database capacity in exchange for a committed spend — but that commitment has to be sized against something, and today's sizing is a starting point, not a validated number.

**Options considered:**
- Purchase 1- or 3-year Reserved Capacity at go-live, sized to the day-one ADR-005/006/008/010 figures
- Stay on Pay-As-You-Go indefinitely, never committing to reserved capacity
- Run on Pay-As-You-Go through each wave's post-cutover validation window, then purchase 1-year Reserved Instances / Savings Plans once real utilization data confirms the actual steady-state footprint

**Decision:** Pay-As-You-Go through validation, then 1-year Reserved Capacity/Savings Plans on confirmed sizing — not committed at go-live, and not deferred indefinitely.

**Rationale:**
Committing 3-year Reserved Capacity against ADR-005's explicitly-flagged-provisional Citrix session-density assumption, or ADR-006's explicitly-flagged-provisional 8-vCore SQL MI starting point, would lock in a discount against a number every sizing ADR in this case study already says might be wrong. A 1-year term (not 3-year) is deliberately chosen even after validation: Meridian's own growth trajectory (9-clinic acquisition, 2–4 clinics/year organic growth, `requirements.md`) means the resource footprint this time next year is expected to be larger than today's, and a 3-year commitment sized too small becomes a second, avoidable right-sizing problem instead of a savings mechanism. Staying on Pay-As-You-Go indefinitely, by contrast, leaves real, quantified savings on the table once sizing is known — [`cost-and-risk-analysis.md`](../docs/cost-and-risk-analysis.md)'s TCO model shows this specifically on the reservable compute/database lines (CareLink PM Citrix compute, both SQL Managed Instances, App Service, Functions), not the full run-rate, since consumption-billed and per-user-licensed services (Entra ID, Sentinel, Service Bus, storage) aren't Reserved-Capacity-eligible in the same way.

**Trade-off:**
This defers real savings for the first several months after each wave's cutover — Year 1 of the TCO model runs entirely on Pay-As-You-Go rates, with no reserved-capacity discount applied until Year 2, a deliberate and quantified cost of waiting for real data rather than guessing. It also creates ongoing FinOps operational work (reviewing utilization, renewing or resizing commitments annually) that doesn't exist under a "buy once and forget" 3-year-term approach — accepted because the alternative (a 3-year commitment against unvalidated sizing) has already gone wrong in a documented, named way for other resources in this case study (e.g., ADR-010's own admission that its 3–10 instance autoscale range is "more provisional... a real gap, worth being explicit about rather than papering over with false precision").

**Status:** Approved
