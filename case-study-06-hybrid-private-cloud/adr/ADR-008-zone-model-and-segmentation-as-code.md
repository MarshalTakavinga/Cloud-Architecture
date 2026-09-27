# ADR-008: Zone Model and Segmentation as Code, Identical in Both Sites

**Status:** Approved
**Date:** Step 5 of the Case Study 6 pipeline

## Context

- Microsegmentation exists **only in DC1**, where the NSX distributed firewall protects the PCI zone.
- DC2 relies on VLANs and perimeter firewalls, and it **lacked rules** that DC1 had, which is one reason the May 2026 failover failed (`current-state.md`).
- PCI DSS 4.0.1 requires the card-data environment to be segmented wherever it runs, and that includes the recovery site.
- NFR-6 applies FFIEC and PCI controls to both sites.

## Decision

1. **Eight zones:**
   - Z0 (Tier 0)
   - Z0-PCI (card-data environment)
   - Z0-DMZ (API ingress and FedLine)
   - Z1 (Tier 1)
   - Z2 (Tier 2)
   - Z-MGMT
   - Z-VAULT
   - Z-IRE

   East-west traffic is **denied by default in Z0 and Z0-PCI**, with allow lists per application tag (`logical-design.md`).
2. **Intent in Git, rendered per site.** Rules are written as application intent ("A may reach B on port P"). The policy pipeline renders them into each site's enforcement point and applies them **identically to DC1 and DC2**.
3. **A daily parity check** compares the effective rules in both sites. Differences fail DR readiness ([ADR-006](ADR-006-recovery-plan-model-and-readiness.md)).
4. **Enforcement runs locally.** It keeps working when any central or cloud plane is disconnected (the local-autonomy contract). Rule *changes* may wait until connectivity returns.
5. **A PCI scope boundary in both sites.** Z0-PCI in DC2 is in scope, assessed, and evidenced like DC1.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **VLANs and perimeter firewalls only.** Rejected. They can't do default-deny east-west within Tier 0, and they are how DC2 drifted.
2. **Hand-maintained rule bases per site.** Rejected. That is the drift mechanism that failed in May 2026.
3. **Segmenting only the PCI zone.** Rejected. Tier 0 as a whole is the ransomware blast radius the examiners care about.

## Consequences

- **Positive:** Both causes of drift (hand edits and site asymmetry) are removed, and PCI scope is correct in the recovery site.
- **Positive:** Intent-based rules are portable. If the platform changes, only the renderer changes, not the rules.
- **Negative / accepted trade-off:** Distributed firewalling across all of Tier 0 in both sites costs extra on some platforms (Steps 6–9 name it), and every Tier-0 application needs its flows documented up front.
