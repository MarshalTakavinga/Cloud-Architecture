# ADR-032: A 15-Month VCF Bridge, Negotiated Alongside Gate G0

**Status:** Approved
**Date:** Step 12 of the Case Study 6 pipeline

## Context

The VCF subscription ends on **31 March 2027 (M6)**. VCF 9 stops workload operations if licences lapse ([ADR-012](ADR-012-vcf-control-plane-and-governance.md)), so running on unsupported VMware is not an option. The migration to Azure Local finishes with core banking at M19 and decommission at M20 (May 2028). Broadcom quoted about **$1.65M a year for three years**.

## Decision

- **Buy a bridge in every outcome of G0.**
  - If G0 confirms Azure Local: a **15-month term to 30 June 2028**. The fallback is a 12-month term plus a pre-negotiated 3-month extension.
  - If G0 reverses to VCF: the bridge negotiation becomes the full renewal.
- **Negotiate once, with both options priced.** The Azure Local proof of concept and its Step 13 costing are presented to Broadcom. **The Step 13 threshold price** decides whether a VCF offer wins (G0-2).
- **Size and terms to seek:**
  - a core count matching the estate as it shrinks, where Broadcom allows reductions
  - no reinstatement penalties
  - licence reporting in disconnected mode continued

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Sign the 3-year renewal "to be safe".** Rejected. It pays for about 21 months the bank would not use, and removes the leverage.
2. **Let the subscription lapse briefly.** Rejected. Workload operations stop.
3. **A 12-month bridge only.** Rejected as the target. It ends at M18, in the middle of the core banking cutover.

## Consequences

- **Positive:** The migration is paced by recovery evidence, not by Broadcom's calendar, and the bank negotiates with a tested alternative.
- **Negative / accepted trade-off:** Short terms usually carry a premium (Step 13 assumes +10%). The bridge overlaps with new platform costs (dual running).
