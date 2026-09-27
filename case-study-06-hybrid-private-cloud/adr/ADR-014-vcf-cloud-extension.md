# ADR-014: VCF Track — No VMware-in-Public-Cloud Extension Now

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

Azure VMware Solution, Google Cloud VMware Engine, and **Amazon EVS** (GA August 2025, a bring-your-own portable VCF subscription with a minimum of 4 hosts, for example 256 cores) could extend this track into public cloud as a Tier-1 and Tier-2 recovery or burst location. Tier 0 can't use them (the invariant). DC2 meets the Tier-1 RTO, and its contract runs to 2030.

## Decision

**No cloud VMware extension in this program.** The landing zone (Azure, [ADR-012](ADR-012-vcf-control-plane-and-governance.md)) hosts dev/test and non-Tier-0 vault copies natively. **Re-evaluate in 2029**, ahead of the DC2 contract decision, when Azure VMware Solution or EVS could replace DC2 for Tier 1 and Tier 2.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure VMware Solution as a third recovery site for Tier 1.** Rejected now. It adds cores to the same VCF subscription and a third site to run, with no gap to fill.
2. **EVS using the 2025 AWS account.** Rejected. It would legitimize an ungoverned account and deepen the VCF dependency.

## Consequences

- **Positive:** No additional exposure to VCF core counts, and no third site.
- **Negative / accepted trade-off:** The public cloud cannot absorb VMware workloads quickly if DC2 is lost for a long time. That scenario is covered by rebuilding into DC1 capacity and the vault.
