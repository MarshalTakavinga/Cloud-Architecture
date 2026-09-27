# ADR-001: Platform Strategy — One Primary Private Cloud in Two Sites, Plus a Governed Public-Cloud Landing Zone

**Status:** Approved
**Date:** Step 4 of the Case Study 6 pipeline

## Context

Alder Valley runs about 2,400 VMs on VMware in two data centers (`current-state.md`). Four facts shape the platform strategy:
- The VCF subscription ends on 31 March 2027, and the renewal is quoted at about $1.65M a year.
- 44 hosts and the DC1 array reach end of support in December 2027.
- Board policy and the invariant keep Tier 0 on premises, and the DC2 colocation contract runs to 2030.
- The core banking vendor certifies only vSphere and Hyper-V.

Driver 2 asks for lower exposure to a single vendor. NFR-12 limits the team to 24 people plus at most 4 hires.

## Decision

1. **One primary private-cloud platform, deployed in both DC1 and DC2**, runs Tier 0, Tier 1, and most of Tier 2. Which platform is decided in Steps 6–10.
2. **A governed public-cloud landing zone** hosts dev/test, analytics, ML experiments, Tier-2 workloads where cheaper, and non-Tier-0 recovery copies.
3. **Placement by tier:**
   - Tier 0 runs in the private cloud, with its recovery location in the DC2 private cloud, and **never** in public cloud.
   - Tier 1 runs in the private cloud. Public-cloud recovery is allowed by exception, for non-NPI data or data encrypted with bank-held keys.
   - Tier 2 and dev/test run wherever is cheaper.
4. **No permanent second hypervisor**, with one exception. If the chosen platform's hypervisor isn't certified by the core banking vendor, core banking runs on a **certified island**: a small, separately licensed cluster on a certified hypervisor. The track that needs it carries its cost and complexity in Steps 10 and 13.
5. **The hardware refresh due in December 2027 is spent on the chosen platform's validated hardware**, not on a like-for-like VMware refresh followed by a migration.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Renew VCF and stand still.** Rejected as a strategy: it fixes neither resilience, governance, nor delivery, and it renews without leverage. *Modernizing in place on VCF* is a different thing and remains a full candidate (Step 6).
2. **Move the estate to public cloud**, whether through VMware-in-cloud or native IaaS. Rejected for Tier 0 by board policy and the invariant. For the rest, it means paying for two retained data centers *and* the cloud. Kept for selective Tier-2 and dev/test use.
3. **Two permanent private platforms** (VMware for Tier 0, something else for the rest). Rejected as the default, because it doubles the tooling, patching, and skills a 24-person team must carry. It survives only as the certified-island exception.

## Consequences

- **Positive:** The team runs, patches, and recovers one platform. The hardware refresh is spent once.
- **Positive:** The landing zone gives the digital team a sanctioned place for the work it took to the 2025 AWS account.
- **Negative / accepted trade-off:** One primary platform is itself a concentration. It is mitigated by portability rules and an annual tested exit ([ADR-005](ADR-005-platform-api-and-portability.md)), not by running two stacks.
- **Negative / accepted trade-off:** A track that needs a certified island is materially more complex. This is the first place the core vendor's certification shows up in the scores.
