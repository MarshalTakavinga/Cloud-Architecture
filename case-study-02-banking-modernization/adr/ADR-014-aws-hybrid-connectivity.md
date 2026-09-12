# ADR-014: Hybrid Connectivity Between AWS and Palisade's Data Center

**Status:** Approved
**Date:** Step 7 of the Case Study 2 pipeline

## Context

As in the Azure track ([ADR-008](ADR-008-hybrid-connectivity.md)), Palisade's core banking system of record — the COBOL/CICS mainframe on DB2 for z/OS — stays on-premises by explicit constraint (`requirements.md`), while the new real-time payment services run in AWS. [ADR-001](ADR-001-mainframe-integration-approach.md) established that this architecture depends on a single synchronous hold/release call into CICS at the moment of payment authorization, and NFR-3 caps total end-to-end posting latency at 5 seconds. That call, and the CDC feed reading the DB2 transaction log, both have to cross from AWS to Palisade's data center and back, and their latency and reliability characteristics depend directly on how that connection is built.

## Decision

Palisade provisions **AWS Direct Connect** as the primary connection between its data center and the AWS Payments account/VPC ([ADR-016](ADR-016-aws-landing-zone-and-segmentation.md)), with a **Site-to-Site VPN as an automatic failover path** if Direct Connect becomes unavailable. The synchronous hold/release call and the CDC feed both traverse this private connection — neither crosses the public internet at any point.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Site-to-Site VPN only, no Direct Connect.** Rejected as the sole connectivity mechanism — same reasoning [ADR-008](ADR-008-hybrid-connectivity.md) used for Azure: VPN traffic traverses the public internet (even encrypted), with less predictable latency and throughput than a private, dedicated circuit. Given that the hold/release call's latency directly consumes part of NFR-3's 5-second total budget, and that this same connection carries the CDC feed's ongoing change-event volume, a best-effort public-internet path introduces exactly the kind of latency variance this design cannot absorb. VPN is retained only as the automatic failover, not the primary path.
2. **Replicate DB2 data into AWS and query the replica instead of calling CICS directly.** Rejected — not a real alternative to the synchronous hold call specifically, since [ADR-001](ADR-001-mainframe-integration-approach.md) already established that only a live, authoritative balance check (not a replica, which can lag) is acceptable for the fund-hold decision; a stale replica reintroduces the same double-spend race condition the hold call exists specifically to close.

## Consequences

- **Positive:** Direct Connect's private, dedicated circuit gives the hold/release call and the CDC feed predictable, low-variance latency and throughput, directly supporting NFR-3.
- **Positive:** The VPN failover path means a single Direct Connect issue does not take down real-time payment processing entirely — it degrades to VPN-path latency rather than failing outright, a defensible resiliency posture for the OCC heightened-standards obligation this case study is built around.
- **Negative / accepted trade-off:** Direct Connect carries a recurring circuit cost and a provisioning lead time (typically weeks, not days) that has to be accounted for in any migration timeline — flagged here for Step 12's migration roadmap, exactly as [ADR-008](ADR-008-hybrid-connectivity.md) flagged the equivalent for Azure.
- **Note:** This decision confirms what [ADR-008](ADR-008-hybrid-connectivity.md) predicted this step would need — a Direct Connect equivalent to ExpressRoute. The pattern is structurally identical across both tracks because it is dictated by the physics of a private circuit to a fixed data center, not by either platform's distinctive service design; the two tracks' genuinely different decisions live elsewhere (compute, database, messaging, landing zone).
