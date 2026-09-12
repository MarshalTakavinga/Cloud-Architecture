# ADR-026: Private-Cloud Network Topology and Segmentation

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

Every hyperscaler track in this case study needed both a hybrid-connectivity decision (a WAN circuit back to Palisade's data center — [ADR-008](ADR-008-hybrid-connectivity.md), [ADR-014](ADR-014-aws-hybrid-connectivity.md), [ADR-020](ADR-020-gcp-hybrid-connectivity.md)) and a landing-zone/segmentation decision. [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md) places this track's entire footprint inside Palisade's own existing data center(s) — the same facility the mainframe already runs in — which changes the shape of both problems at once.

## Decision

Network segmentation for the new payment-processing workload is achieved with **VLANs and VMware NSX micro-segmentation**, giving the workload its own dedicated, firewalled network segment inside Palisade's existing data-center network — isolated at the network layer from every other system in that data center, including the mainframe's own network segment. The synchronous hold/release call and the CDC feed reach the mainframe over the **existing internal data-center backbone** — there is no WAN hop to cross, so **no hybrid-connectivity circuit of any kind is provisioned for this track**.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Provision a dedicated WAN/leased-line connection to the mainframe**, mirroring the other three tracks' hybrid-connectivity ADRs. Rejected — this is the exact possibility [ADR-008](ADR-008-hybrid-connectivity.md) flagged as potentially moot for this track, and it is confirmed moot here: since [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md) places this workload in the same physical facility as the mainframe, there is no WAN hop to provision a circuit for. Adding one anyway would introduce cost and a failure point with no corresponding benefit.
2. **A flat, unsegmented network shared with the rest of the data center.** Rejected — same reasoning [ADR-010](ADR-010-azure-landing-zone-and-segmentation.md), [ADR-016](ADR-016-aws-landing-zone-and-segmentation.md), and [ADR-022](ADR-022-gcp-landing-zone-and-segmentation.md) used to reject their equivalent flat topologies: an OCC-scrutinized payment-processing workload needs a real structural network boundary, not just a shared LAN segment.
3. **Migrate the 2021 AWS-equivalent workloads (mobile push notifications, mobile analytics) onto this private-cloud footprint too**, mirroring what every hyperscaler track did in its own landing zone. Rejected as out of scope for this decision — those workloads are consumer-facing, mobile-adjacent capabilities that gain little from private infrastructure and were never a natural fit for on-premises hosting. If this track is ultimately selected in Step 10, their disposition is a genuinely open question for Step 12, not something this ADR silently resolves by omission.

## Consequences

- **Positive:** This is the only one of the four tracks with zero hybrid-connectivity cost, provisioning lead time, or latency budget to manage at all — the mainframe call happens at data-center-LAN speed, not across a metro-area private circuit. This is a genuine structural advantage worth carrying prominently into Step 10 against NFR-3's 5-second latency budget specifically.
- **Negative / accepted trade-off:** NSX micro-segmentation, VLAN design, and firewall-rule management for this new segment are new day-2 operational work for Palisade's network team, on top of what they already manage for the mainframe's own network segment and the rest of the data center.
- **Carried to Step 12:** The disposition of the 2021 AWS-equivalent workloads, if this track is selected, is an explicitly open question, not resolved here.
