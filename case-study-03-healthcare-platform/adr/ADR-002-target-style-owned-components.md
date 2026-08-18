### ADR-002: Target architecture style for the components Meridian owns

**Context:**
Unlike CareLink PM, the patient portal (MeridianConnect), the telehealth integration, and the HL7 interface engine (LinkEngine) are within Meridian's control to redesign. Each has a clear, named pain point from the Step 2/3 problem statement: portal latency at peak, a disjointed bolted-on telehealth login, and brittle point-to-point HL7 batch feeds with no centralized audit trail.

**Options considered:**
- Leave all three as rehosted bolt-ons, unchanged in design
- Full microservices decomposition across all owned components
- A small number of bounded, event-driven services introduced incrementally behind the existing CareLink PM core (Strangler Fig), with Zero Trust identity/network principles applied as a cross-cutting overlay
- A single rewritten monolith replacing all three bolt-ons at once

**Decision:** Strangler Fig — incrementally replace the three bolt-ons with a small number of bounded, event-driven, API-first services, introduced one at a time behind the still-in-place CareLink PM core, with Zero Trust applied across all of them rather than treated as a separate initiative.

**Rationale:**
Full microservices is a poor match for a 16-person infrastructure team with no current Kubernetes/distributed-systems operating experience — it would trade a legacy-monolith problem for a distributed-operations problem the team isn't staffed for. A single big-bang rewrite of all three bolt-ons at once concentrates risk exactly where the business can least tolerate it (clinical operations across 46 sites). An incremental, event-driven approach lets each piece move independently, fits the message-based nature of the HL7 workload directly (LinkEngine is already message-passing), and Zero Trust directly answers the March 2026 credential-compromise incident, where implicit trust behind the VPN — not a missing product — was the actual failure.

**Trade-off:**
Event-driven integration introduces eventual consistency and message-ordering considerations CareLink PM's synchronous point-to-point calls didn't have, and requires operational skills (event-broker monitoring, dead-letter handling) the team doesn't currently hold — a real training/staffing cost that has to be planned for, not assumed away.

**Status:** Proposed

See [`../diagrams/target-architecture-style-detail.png`](../diagrams/target-architecture-style-detail.png) for the detailed target-style diagram — Strangler Fig services, the Zero Trust cross-cutting overlay, and Telehealth's Repurchase treatment (distinct from Portal/LinkEngine's Refactor treatment — see `application-architecture.md` §3).
