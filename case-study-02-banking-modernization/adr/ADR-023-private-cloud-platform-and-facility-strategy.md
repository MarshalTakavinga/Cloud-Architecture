# ADR-023: Private-Cloud Platform and Facility Strategy

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

This track evaluates whether the new real-time payment layer should run on dedicated, Palisade-owned infrastructure rather than a public hyperscaler — a live, defensible option specifically because of Palisade's mainframe investment and the OCC heightened-standards scrutiny driving this initiative (`README.md`'s scope note). Unlike Case Study 3's Meridian, which had to decide a facility strategy from a weaker starting position, `current-state.md` establishes that Palisade already owns and operates a primary data center (where the mainframe itself runs) and a warm secondary/DR site. This ADR decides both the private-cloud platform itself and where it physically runs.

## Decision

Palisade deploys the new real-time payment layer on **VMware Cloud Foundation (VCF)**, built on new hyperconverged infrastructure racked in Palisade's **existing primary data center** — the same facility the mainframe already runs in — with a matching VCF footprint in Palisade's **existing secondary/DR site**, upgrading that site's role from a warm-standby target for mainframe replication into an active participant in this new workload's own HA/DR posture. No new leased colocation facility is provisioned.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Lease new colocation space** instead of using Palisade's own data center. Rejected — Palisade already owns and physically secures a data center suitable for a regulated workload (it already hosts the mainframe under the physical-security controls that come with that), so a new leased facility would add vendor and facility risk with no corresponding benefit. This differs from Case Study 3's Meridian, which didn't already have a suitable owned facility to build on.
2. **A non-VMware private-cloud stack** (e.g., Red Hat OpenShift Virtualization / OpenStack). Considered — technically viable, but `current-state.md` already establishes that Palisade's digital banking platform runs on-premises on **VMware vSphere** today; adopting VCF extends an operating model the team already knows, directly addressing the same cloud-skills-gap constraint `requirements.md` names, the same reasoning the other three tracks used to prefer their platform's simplest managed option. Introducing a second, unfamiliar virtualization stack purely for this new workload would work against that constraint, not with it.
3. **Bare-metal, with no private-cloud abstraction layer at all.** Rejected — this would forfeit the elastic scaling, self-service provisioning, and workload mobility (live migration for maintenance, DR failover) every hyperscaler track gets natively from its platform. A private-cloud platform exists specifically to recover some of that same elasticity on owned infrastructure; going bare-metal abandons that goal entirely.

## Consequences

- **Positive:** Reuses existing facility investment and existing VMware operational skill, directly responsive to driver 3 (flattening the cost trajectory) and the skills-gap constraint.
- **Positive:** Placing the new workload in the *same facility* as the mainframe removes the entire hybrid-connectivity problem every hyperscaler track had to solve (ExpressRoute, Direct Connect, Dedicated Interconnect) — see [ADR-026](ADR-026-private-cloud-network-topology.md), which confirms what [ADR-008](ADR-008-hybrid-connectivity.md) itself predicted might be the case for this track.
- **Negative / accepted trade-off:** This is a capital-expenditure model (buy servers, storage, and licensing up front) rather than the hyperscalers' consumption-based operating expense — a genuine trade-off against driver 3 in one direction (upfront capex) while potentially flattening the *trajectory* in another (no ongoing egress or consumption growth tied to transaction volume). Not resolved here; quantified honestly in Step 13.
- **Negative / accepted trade-off:** Palisade now owns the full operational burden — patching, capacity planning, hardware lifecycle — for a second infrastructure footprint, alongside the mainframe it already operates, rather than transferring that burden to a hyperscaler. This is the first instance of a trade-off that recurs at every layer of this track (see [ADR-024](ADR-024-private-cloud-compute-platform.md) and [ADR-025](ADR-025-private-cloud-database.md)).
- **Carried to Step 13:** Capital cost of the new hyperconverged infrastructure at both sites, versus the three hyperscaler tracks' consumption-based cost models, is a first-class Step 13 comparison, not assumed favorable or unfavorable here.
