# ADR-002: Build vs. Buy for the Real-Time Payments Hub

**Status:** Approved
**Date:** Step 4 of the Case Study 2 pipeline

## Context

Given ADR-001's integration pattern, Palisade needs a new event-driven layer comprising: ISO 20022 message handling and FedNow/RTP rail connectivity, fraud orchestration, and a ledger-of-intent/mainframe-adapter. The 18-month timeline (driver 1) and the cost-trajectory driver (driver 3) both bear directly on how much of this layer Palisade builds versus buys.

## Decision

Palisade will **buy** a commercially available, already-certified ISO 20022/FedNow rail-connectivity gateway, and **build in-house** the fraud-orchestration service and the ledger-of-intent/mainframe-integration adapter (including the CDC consumer and the ADR-001 hold/release logic).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Build the entire layer in-house**, including rail connectivity and ISO 20022 message handling. Rejected — FedNow/RTP rail certification is a significant, ongoing compliance and testing burden with no differentiated value to Palisade's customers; building it from scratch inside an 18-month window is the single largest schedule risk in the whole initiative, for a component that is effectively a commodity across the industry.
2. **Buy a full end-to-end commercial payment-hub product**, including fraud scoring and mainframe integration, and configure rather than build. Rejected — commercial payment-hub products are built to integrate with modern, API-native cores; none are designed around a 30-year-old CICS/DB2 core with Palisade's specific batch-window constraint (driver 5) and ADR-001's hold-then-CDC pattern. Forcing a generic product to fit this exact integration shape would mean extensive customization anyway, eroding the "buy" case's main advantage (speed), while also introducing vendor lock-in on Palisade's most Palisade-specific logic (fraud rules, mainframe adapter).
3. **Split the difference as decided** — buy only the rail-connectivity/ISO 20022 gateway (the compliance-heavy, low-differentiation piece), build the fraud orchestration and ledger-of-intent/adapter in-house (the pieces that directly encode Palisade's own risk rules and its specific ADR-001 integration pattern). This is the selected option.

## Consequences

- **Positive:** The highest-risk, most schedule-sensitive component (rail certification) is de-risked by buying an already-certified product, directly protecting the 18-month deadline (driver 1).
- **Positive:** The components with the most Palisade-specific logic (fraud rules tuned to Palisade's actual risk appetite and customer base; the ADR-001 hold/CDC integration pattern) stay in-house, where they can evolve without being constrained by a vendor's release cycle or generic integration assumptions.
- **Negative / accepted trade-off:** Palisade takes on ongoing licensing cost for the rail-connectivity gateway — a cost that must be weighed in Step 13's cost analysis against the (larger, less certain) cost and schedule risk of building and certifying rail connectivity in-house.
- **Negative / accepted trade-off:** Palisade now owns integration risk at the boundary between the bought gateway and the in-house fraud/ledger-of-intent services — this boundary is a named item in the Step 13 risk register, and its design is a first-class concern for Step 5's logical design, not an afterthought.

## Open Question Carried to Step 5 / Step 10

This ADR fixes the build-vs-buy *split*, not the specific vendor for the rail-connectivity gateway — vendor selection is out of scope for this case study's architecture decisions (it is a procurement exercise) and does not change the shape of Steps 5 through 9, which treat the gateway as a bought, ISO-20022-compliant black box with a defined event-publishing contract.
