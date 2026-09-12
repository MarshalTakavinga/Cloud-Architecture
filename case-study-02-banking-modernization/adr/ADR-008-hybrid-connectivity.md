# ADR-008: Hybrid Connectivity Between Azure and Palisade's Data Center

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

Unlike Case Study 1 (Solstice), which was already fully cloud-native, this case study's core banking system of record — the COBOL/CICS mainframe on DB2 for z/OS — stays on-premises in Palisade's own data center by explicit constraint (`requirements.md`), while the new real-time payment services run in Azure. [ADR-001](ADR-001-mainframe-integration-approach.md) already established that this architecture depends on a single synchronous hold/release call into CICS at the moment of payment authorization, and NFR-3 caps total end-to-end posting latency at 5 seconds. That synchronous call now has to cross from Azure to Palisade's data center and back, and its latency and reliability characteristics depend directly on how that connection is built.

## Decision

Palisade provisions **Azure ExpressRoute** as the primary connection between its data center and the Azure landing zone, with a **site-to-site VPN as an automatic failover path** if ExpressRoute becomes unavailable. The synchronous hold/release call and the CDC feed both traverse this private connection — neither crosses the public internet at any point.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Site-to-site VPN only, no ExpressRoute.** Rejected as the sole connectivity mechanism — VPN traffic traverses the public internet (even though encrypted), with less predictable latency and throughput than a private, dedicated circuit. Given that the hold/release call's latency directly consumes part of NFR-3's 5-second total budget, and that this same connection carries the CDC feed's ongoing change-event volume, a best-effort public-internet path introduces exactly the kind of latency variance this design cannot absorb. VPN is retained, but only as the automatic failover, not the primary path.
2. **No hybrid connectivity — replicate DB2 data into Azure and query the replica instead of calling CICS directly.** Rejected — this was never actually on the table as an alternative to the synchronous hold call specifically, since ADR-001 already established that only a live, authoritative balance check (not a replica, which can lag) is acceptable for the fund-hold decision; a stale replica reintroduces the same double-spend race condition ADR-001 designed the hold call specifically to close.

## Consequences

- **Positive:** ExpressRoute's private, dedicated circuit gives the hold/release call and the CDC feed predictable, low-variance latency and throughput, directly supporting NFR-3.
- **Positive:** The VPN failover path means a single ExpressRoute circuit issue does not take down real-time payment processing entirely — it degrades to VPN-path latency rather than failing outright, which is a defensible resiliency posture for the OCC heightened-standards obligation this case study is built around.
- **Negative / accepted trade-off:** ExpressRoute carries a recurring circuit cost and a provisioning lead time (typically weeks, not days) that has to be accounted for in any migration timeline — flagged here for Step 12's migration roadmap.
- **Note for Steps 7–9:** This is the first ADR in this case study with no Case Study 1 precedent to compare against, because Case Study 1's workload never needed hybrid connectivity at all. Steps 7 (AWS) and 8 (GCP) will need their own equivalent decisions (Direct Connect, Cloud Interconnect); Step 9 (private cloud) may not need this ADR's shape at all, since a private-cloud footprint could plausibly sit in the same data center as the mainframe.
