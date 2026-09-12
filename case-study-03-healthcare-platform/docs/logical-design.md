# Vendor-Neutral Logical Design — Meridian Health Network

This document turns the target style direction into a concrete logical architecture: real components, real responsibilities, real data flow — but no cloud platform yet. Every component below is named by capability, not by product, so the same design can be evaluated fairly against Azure, AWS, GCP, and a private-cloud alternative in the next stage of this case study.

## 1. Logical Components

| Component | Responsibility | Why it's here |
| --- | --- | --- |
| Identity Provider (hybrid) | Authenticates users and devices, issues tokens, enforces MFA and conditional access | Closes the MFA gap that let the March 2026 credential compromise happen |
| API Gateway | Single ingress point; validates a token on every call before routing | Makes Zero Trust real rather than aspirational; the seam that lets Portal, Telehealth, and CareLink PM evolve independently |
| Portal Service | Patient self-scheduling and account management, rebuilt API-first | Refactor decision (ADR-002) |
| Telehealth Service | Video visits, integrated SSO | Repurchase decision (ADR-002) |
| Core PM Service (CareLink PM) | System of record for scheduling, registration, and billing | Replatform decision (ADR-001) — behavior unchanged, infrastructure modernized |
| Event/Integration Bus | Publish-subscribe messaging; replaces LinkEngine; carries HL7 and API events with replay and dead-lettering | Refactor decision (ADR-002); directly fixes "a lost message during an outage is just lost" |
| Primary Relational Database | Transactional store behind Core PM — ACID, relational, supports the same query patterns CareLink PM already relies on | Replaces the unsupported SQL Server 2014 instance; keeps behavior compatible with a vendor app Meridian doesn't control |
| Object / Blob Storage | Immutable backup storage and imaging archive | Satisfies the immutable, geographically-separate backup requirement; closes the "unencrypted archive LUN" gap |
| Secrets Manager | Centralized storage for credentials and service identities | Eliminates the shared/generic service accounts still used by legacy integrations today |
| Centralized Logging | Aggregates logs and audit events from every component into one place | Closes the "no SIEM, manual multi-system forensic review" gap named in the current-state assessment |
| Secondary Region (DR) | Warm-standby copy of Core PM, its database, and the event bus in a second geography | Meets the RTO ≤ 4h / RPO ≤ 15 min requirement — see Section 3 |
| Shared-Services / Landing Zone | Identity, policy, and network foundation new clinics provision against | Answers the "4–6 months per acquired clinic" driver |
| Hub-and-Spoke Network | Hub (shared security/identity/egress) with a spoke per environment | Reshapes Meridian's existing MPLS hub-and-spoke mental model into a segmented cloud network — fixes the flat-network gap in the current state |

## 2. Data Flow — Two Worked Scenarios

**A patient books an appointment through the portal:** Patient authenticates via the Identity Provider (MFA enforced) → request hits the API Gateway, which validates the token on this call, not just at login → Gateway routes to the Portal Service → Portal Service calls the Core PM Service for availability and books the slot → Core PM Service writes to the Primary Relational Database → a "booking created" event is published to the Integration Bus so downstream systems (reminders, reporting) can react without the Portal Service knowing who's listening.

**A lab result arrives from LabCorp:** LabCorp sends an HL7 message → received by the Integration Bus, not directly by Core PM — this is the decoupling point. The Bus normalizes and routes the event to the Core PM Service, which updates the patient record in the Primary Relational Database. If Core PM is temporarily unavailable (a deployment, a failover), the message waits on the Bus and replays once it's back — the exact resilience the current point-to-point LinkEngine feed does not have today.

## 3. HA/DR Logical View

| Element | Value | Mechanism |
| --- | --- | --- |
| Topology | Warm standby (pilot light) in a second geographic region | Core infrastructure pre-provisioned but scaled down in the secondary region; scales up on failover |
| Replication | Asynchronous, continuous | Primary Relational Database and Object Storage replicate to the secondary region on an ongoing basis |
| RTO | ≤ 4 hours | Automated failover runbook promotes the secondary region; DNS-based traffic cutover |
| RPO | ≤ 15 minutes | Bounded by the asynchronous replication interval |
| Failover trigger | Manual-initiated, tooling-assisted | A deliberate decision (not automatic) given clinical-safety implications of an unplanned failover — see ADR-004 |

See [ADR-004](../adr/ADR-004-dr-strategy.md) for why warm standby was chosen over both a cheaper backup-and-restore approach and a more expensive active-active design.

## 4. Cross-Cutting Concerns

- **Zero Trust** is not a separate box — it's the Identity Provider and API Gateway working together to verify identity, device, and context on every call, not just at the network edge.
- **Secrets Manager** and **Centralized Logging** attach to every component above, not just one — every service authenticates through the same secrets store and logs to the same place, which is what makes a forensic review after an incident a single query instead of a multi-system scavenger hunt.
- **Shared-Services / Landing Zone** is the foundation the other components are provisioned onto — it's why onboarding a new clinic becomes a repeatable pattern instead of bespoke engineering.

## 5. Explicitly Deferred to Later Stages

- Which platform (Azure, AWS, GCP, private) implements each component above
- Specific managed-service selection, SKUs, and sizing
- Exact network addressing, subnetting, and firewall rules
- IAM role and policy definitions
- Cost modeling and 3–5 year TCO

## 6. Diagrams

- [`../diagrams/logical-architecture-detail.png`](../diagrams/logical-architecture-detail.png) — the primary diagram for this stage: logical components (Section 1), the full request/event flow through the primary region, both worked data-flow scenarios (Section 2), the secondary-region warm-standby layout and HA/DR table (Section 3), cross-cutting concerns (Section 4), and what's explicitly deferred (Section 5) — all in one hand-reproduced, conflict-checked diagram. Went through several review rounds to get right, including a genuine correctness fix: the Event/Integration Bus never talks to the Primary Relational Database directly — all reads/writes happen through the Core PM Service, called out explicitly on the diagram itself.
- [`../diagrams/logical-architecture.png`](../diagrams/logical-architecture.png) / [`.drawio`](../diagrams/logical-architecture.drawio) — earlier, simpler component-view sketch. Superseded by the diagram above; kept for history.
- [`../diagrams/ha-dr-logical-view.png`](../diagrams/ha-dr-logical-view.png) / [`.drawio`](../diagrams/ha-dr-logical-view.drawio) — earlier, simpler region/replication sketch. The HA/DR table and secondary-region layout are now also covered by the diagram above; a dedicated, more detailed DR diagram is planned to fully replace this one.
