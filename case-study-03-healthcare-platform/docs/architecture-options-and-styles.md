# Architecture Options & Styles — Meridian Health Network

This document deliberately separates two decisions that are easy to conflate:

1. **Migration strategy** — *how* each current-state component moves
2. **Target architecture style** — *what pattern* the system evolves toward, once moved

No platform (Azure/AWS/GCP/private) is chosen here — that follows in later stages of the case study. This document narrows the option space and states a reasoned position, recorded as ADRs, so the logical design that follows has a real foundation rather than a guess.

## 1. Migration Strategy — The Six R's

A standard industry framework (AWS, Azure CAF, and Google Cloud all publish a version of it) for deciding what to do with each existing component. Applying it component-by-component, instead of picking one strategy for "the whole system," is the actual skill — real migrations are almost always mixed.

| Strategy | Definition | Use When | Avoid When |
| --- | --- | --- | --- |
| **Rehost** | Lift-and-shift, no code change | Time pressure, low app complexity, buys runway for later modernization | The current design carries forward real risk (e.g., single-AZ, unencrypted) unchanged |
| **Replatform** | Lift-and-shift plus targeted swaps (e.g., managed DB instead of self-hosted) | You can't change the app, but you can change what it runs on | The underlying platform choice materially changes app behavior the vendor won't support |
| **Repurchase** | Replace with a SaaS/COTS alternative | The current system is generic enough that a market alternative is genuinely better | Switching cost (data conversion, retraining, contracts) outweighs the benefit |
| **Refactor / Re-architect** | Rebuild using cloud-native patterns | You own the code and the current design is the actual bottleneck | You don't own the source, or the rebuild risk outweighs the problem it solves |
| **Retain** | Leave it where it is, for now | A real, time-bound reason exists (contract, dependency, low priority) | It's the actual source of the risk you're trying to remove |
| **Retire** | Decommission | Nothing depends on it and it adds attack surface or cost for no value | Still load-bearing |

### 1.1 Applied to Meridian's Current-State Inventory

| Component | Strategy | Why |
| --- | --- | --- |
| CareLink PM (app + DB) | **Replatform** | Vendor thick-client product — Meridian has no source access, so Refactor isn't on the table. Replatforming (move VMs to cloud IaaS, swap SQL Server 2014 for a supported, cloud-managed engine) fixes the unsupported-database and single-site risks that are actually driving the insurance deadline, without a multi-year application rewrite. |
| MeridianConnect Portal | **Refactor** | Built and owned in-house — the actual bottleneck (self-hosted, bolted-on) is a design problem Meridian *can* fix. Good Strangler Fig candidate: rebuild as an API-first service in front of CareLink PM rather than a tightly coupled add-on. |
| Telehealth (third-party video bolt-on) | **Repurchase** | The pain point (separate login, clunky plug-in) is a vendor integration problem, not something worth custom-building. A better-integrated cloud telehealth vendor with a real API/SSO story solves it directly. |
| LinkEngine (HL7 interface engine) | **Refactor** | Already message-based, which is exactly what makes it a strong candidate to replace with a managed, event-driven integration service — same conceptual job, far better resilience (replay, dead-lettering) than today's point-to-point batch feeds. |
| On-prem Active Directory | **Replatform** | Extend into hybrid identity (sync to a cloud directory) rather than rebuild identity from scratch — lower risk, and MFA/conditional access requirements can be layered on without a green-field identity project. |
| Veeam + tape backup/DR | **Replatform** | Same conceptual job (backup, DR), swapped onto cloud-native, immutable, geographically separate storage — directly resolves the RTO/RPO requirement in `requirements.md`. |
| Hub-and-spoke MPLS network | **Retire (phased)** | Once core systems aren't all sitting behind one HQ firewall, the case for expensive per-site MPLS circuits weakens. Realistic as a multi-year phase-out alongside cloud migration, not a day-one cutover — flagged here, not decided. |

Notice what's *not* on this list: a full **Repurchase** of CareLink PM itself (switching PM/EHR vendors). That's a real option — but it's a multi-year, org-wide change-management project orthogonal to the compliance/DR deadline driving this migration. Recorded as a deferred option in ADR-001 below, not silently dropped.

## 2. Target Architecture Style

Evaluated deliberately against each candidate style — including an explicit reason for ruling out the fashionable ones, not just the ones adopted — component by component:

| Style | Verdict for Meridian | Why |
| --- | --- | --- |
| Full microservices | **Avoid** | 16-person infra team, no Kubernetes operating experience today. Full microservices trades one kind of complexity (a legacy monolith) for another (distributed-systems operations) the team isn't staffed for. |
| Modular monolith / bounded services | **Use, selectively** | For the *new* components Meridian owns (portal, telehealth integration, notifications) — a small number of well-bounded services, not a service-per-feature explosion. |
| Event-driven architecture | **Use** | The HL7 workload is already message-based. An event-driven integration layer (pub/sub) is a natural fit, not a fashionable add-on — it directly buys replay and decoupling that today's synchronous point-to-point feeds don't have. |
| Serverless | **Use, for bursty pieces** | Patient self-scheduling API calls, appointment-reminder notifications, telehealth session orchestration — spiky, stateless, good serverless fits. **Avoid** for the core clinical database workload, which is latency-sensitive and stateful. |
| Zero Trust | **Use — as a cross-cutting overlay, not a separate system** | Directly answers the March 2026 incident: the attacker's problem was that VPN access implicitly trusted everything behind it. Zero Trust (verify identity/device/context on every request, not just at the network perimeter) is a requirement now, not a nice-to-have — ties straight back to the MFA requirement in `requirements.md`. |
| Shared-services / platform engineering | **Use** | Directly answers the "4–6 months per acquired clinic" pain point. A self-service landing-zone pattern turns onboarding a new clinic into "provision against a golden path" instead of bespoke circuit and hardware engineering. |
| Hub-and-spoke | **Carries forward, reshaped** | Meridian already thinks this way (MPLS hub-and-spoke). The *shape* is familiar and reusable as a cloud networking topology (hub VNet/VPC + spoke per environment); it's the *implementation* that changes, not the mental model. |
| Data mesh, Lakehouse, CQRS, Event sourcing, Cell-based | **Out of scope, explicitly** | None of these are pulled by an actual requirement in this case study. Data mesh/lakehouse belong to a future Enterprise Data & AI case study, not this one — reaching for them here would be a fashionable pattern with no requirement behind it. |

## 3. Where This Leaves the Target Direction

With the full reasoning recorded in [ADR-001](../adr/ADR-001-migration-strategy-carelink-pm-core.md) and [ADR-002](../adr/ADR-002-target-style-owned-components.md): **replatform the CareLink PM core to meet the compliance deadline, and wrap the parts Meridian actually owns — portal, telehealth, integration — in a Strangler Fig of small, event-driven, API-first services sitting behind a Zero Trust identity/network layer, provisioned through a shared-services landing zone.** This direction carries into the logical design that follows.

## 4. Diagrams

- [`../diagrams/Migration-Strategy-Map.xlsx`](../diagrams/Migration-Strategy-Map.xlsx) — the Section 1.1 table above, color-coded by strategy, plus a reference sheet of the six R definitions.
- [`../diagrams/target-architecture-style.png`](../diagrams/target-architecture-style.png) — rendered preview of the target-style sketch referenced in Section 3.
- [`../diagrams/target-architecture-style.drawio`](../diagrams/target-architecture-style.drawio) — editable draw.io/diagrams.net source for the same diagram.
