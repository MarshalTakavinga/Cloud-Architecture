# Requirements — Solstice Retail Group

Requirement, constraint, assumption, and risk are kept explicitly separate here, not blended into one list — the same discipline this portfolio applied in Case Study 3, because conflating "what we need" with "what we're assuming" is exactly how a rushed re-architecture quietly bakes in an unstated bet.

## 1. Scale, Stated Concretely

Numbers grounded in `current-state.md`, not invented for this document:

| Metric | Baseline | Named peak events |
| --- | --- | --- |
| Orders/minute | ~150 | ~3,750 (25x — Black Friday/Cyber Monday and two additional flash-sale days/year) |
| Page views/minute | ~9,000 | ~180,000 (20x) |
| Ramp time to peak | N/A | As fast as ~4 minutes from a marketing-triggered flash sale |
| Active customer accounts | 2.4M today | Growing ~15–20%/year, plus new EU/APAC acquisition |

## 2. Functional / Capability Requirements

- Serve the storefront, cart, and checkout experience to customers in the US, Canada, UK, Germany, France, Australia, and Singapore at launch.
- Process payments through the existing PCI Level 1 gateway relationship, using its hosted-tokenization capability rather than building new payment infrastructure.
- Preserve the existing order-to-fulfillment handoff (SCE's fulfillment/warehouse integration is out of scope for this re-architecture — `problem-statement.md` §5).

## 3. Non-Functional Requirements

| Requirement | Target |
| --- | --- |
| Availability, named peak events | 99.95% (Black Friday/Cyber Monday, 2 additional flash-sale days/year) |
| Availability, baseline | 99.9% |
| Elasticity | Sustain a 25x baseline throughput ramp within 5 minutes of demand onset, without manual intervention |
| Latency, US/Canada | p95 page load ≤ 100ms |
| Latency, UK/Germany/France/Australia/Singapore | p95 page load ≤ 150ms (down from ~2.1s measured today) |
| PCI-DSS scope | Cardholder data must never transit or be stored within the general application environment — target SAQ A-EP or better |
| Data residency (EU) | EU customer PII processed and stored within an EU region, consistent with GDPR |
| Cost | ≥ 30% reduction in infrastructure cost per order within 18 months, without breaching the availability or elasticity targets above |
| Engineering bandwidth | No more than one additional major replatforming initiative may run in parallel with the EU launch program |

## 4. Constraints

- **Solstice owns 100% of the SCE source code.** Unlike a vendor product, Refactor/Rearchitect strategies are genuinely available for every internally-built component — this constraint is the mirror image of Case Study 3's "no source access" constraint, not a repeat of it, and it changes which of the 6 R's are even worth discussing in Step 4.
- The third-party payment gateway relationship is fixed for the duration of this initiative — not being re-procured or replaced, only integrated with differently (via its existing hosted-tokenization capability).
- No more than one additional major replatforming project may run in parallel with the EU launch program (from NFR table above) — a real bound on how much can change at once, the same kind of bandwidth constraint that shaped Case Study 3's wave sequencing.
- The existing catalog/cart/order/customer data model is not being redesigned — `current-state.md` §5 already named it sound; this case study re-architects topology and elasticity, not schema.

## 5. Assumptions

- The EU launch timeline (approved by the board, ~9–12 months out) is fixed and not adjustable by this initiative.
- The next PCI-DSS assessment cycle is approximately 12 months out.
- Order volume grows 15–20% year-over-year on the existing US/Canada base, before adding any EU/APAC contribution.
- The payment gateway's hosted-tokenization/hosted-fields capability, already available today per `current-state.md` §3, is sufficient to achieve SAQ A-EP scope without a payments rebuild.

## 6. Risks

| Risk | Likelihood | Impact | Notes |
| --- | --- | --- | --- |
| A compressed EU launch timeline forces a partial rollout that doesn't fully meet the latency or data-residency targets | Medium | High | The board-committed date doesn't move; the architecture has to be ready before it, not the reverse |
| 2025 peak traffic exceeds the 25x planning figure, repeating a Black Friday 2024-style outage on a larger scale | Medium | High | The single largest reason this case study exists at all |
| The 30% cost-per-order target tempts under-provisioning peak capacity if not modeled carefully against the elasticity requirement | Medium | Medium | Named explicitly here so Step 12's cost model has to show its work against this exact target, not just assert it was hit |
| The one-parallel-initiative bandwidth constraint is exceeded if the EU launch program and this re-architecture aren't sequenced carefully | Low–Medium | Medium | A planning risk for Step 11's rollout sequencing, not an architecture risk |
