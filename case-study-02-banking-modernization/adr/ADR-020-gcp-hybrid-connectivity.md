# ADR-020: Hybrid Connectivity Between GCP and Palisade's Data Center

**Status:** Approved
**Date:** Step 8 of the Case Study 2 pipeline

## Context

As in the Azure and AWS tracks ([ADR-008](ADR-008-hybrid-connectivity.md), [ADR-014](ADR-014-aws-hybrid-connectivity.md)), Palisade's core banking system of record stays on-premises by explicit constraint (`requirements.md`), while the new real-time payment services run in GCP. [ADR-001](ADR-001-mainframe-integration-approach.md) established that this architecture depends on a single synchronous hold/release call into CICS at the moment of payment authorization, and NFR-3 caps total end-to-end posting latency at 5 seconds. That call, and the CDC feed reading the DB2 transaction log, both have to cross from GCP to Palisade's data center and back.

## Decision

Palisade provisions **Dedicated Interconnect** as the primary connection between its data center and the GCP Payments project ([ADR-022](ADR-022-gcp-landing-zone-and-segmentation.md)), with **Cloud VPN as an automatic failover path** if Interconnect becomes unavailable. The synchronous hold/release call and the CDC feed both traverse this private connection — neither crosses the public internet at any point.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cloud VPN only, no Dedicated Interconnect.** Rejected as the sole connectivity mechanism — same reasoning [ADR-008](ADR-008-hybrid-connectivity.md) and [ADR-014](ADR-014-aws-hybrid-connectivity.md) used for Azure and AWS: VPN traffic traverses the public internet (even encrypted), with less predictable latency and throughput than a private, dedicated circuit, and the hold/release call's latency directly consumes part of NFR-3's 5-second total budget. VPN is retained only as the automatic failover.
2. **Partner Interconnect instead of Dedicated Interconnect.** Considered — Partner Interconnect is a legitimate lower-commitment option where a supported service provider carries the connection rather than a direct physical link to a Google point of presence. Rejected here specifically because Palisade's own data center is treated the same way across all three hyperscaler tracks in this case study — a dedicated, direct private circuit — for a fair, consistent comparison at Step 10; Partner Interconnect remains a legitimate lower-cost fallback if Palisade's data center turns out not to be near a Google PoP, a detail to confirm in Step 12.
3. **Replicate DB2 data into GCP and query the replica instead of calling CICS directly.** Rejected — not a real alternative to the synchronous hold call specifically; [ADR-001](ADR-001-mainframe-integration-approach.md) already established that only a live, authoritative balance check is acceptable for the fund-hold decision, and a replica reintroduces the double-spend race condition the hold call exists to close.

## Consequences

- **Positive:** Dedicated Interconnect's private circuit gives the hold/release call and the CDC feed predictable, low-variance latency and throughput, directly supporting NFR-3.
- **Positive:** The Cloud VPN failover path means a single Interconnect issue degrades to VPN-path latency rather than failing real-time payment processing outright — a defensible resiliency posture for the OCC heightened-standards obligation this case study is built around.
- **Negative / accepted trade-off:** Dedicated Interconnect carries a recurring circuit cost and a provisioning lead time (typically weeks) — flagged here for Step 12's migration roadmap, exactly as the equivalent was flagged for Azure and AWS.
- **Note:** As with [ADR-014](ADR-014-aws-hybrid-connectivity.md), this decision confirms what [ADR-008](ADR-008-hybrid-connectivity.md) predicted this step would need. The pattern is structurally identical across all three hyperscaler tracks because it is dictated by the physics of a private circuit to a fixed data center, not by any platform's distinctive service design.
