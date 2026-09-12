### ADR-034: Target platform selection — Microsoft Azure

**Context:**
Steps 6 through 9 produced four fully-designed, equally-rigorous implementations of the same vendor-neutral logical design (`logical-design.md`, ADR-001 through ADR-004) — Azure, AWS, GCP, and a private-cloud track on VMware Cloud Foundation — each with its own service mapping, network/identity architecture, timed DR runbook, and Well-Architected-style self-check. Step 10 (`decision-matrix.md`) scored all four against nine criteria weighted directly from `requirements.md`'s NFRs, constraints, and risks. A platform now has to actually be chosen so the migration roadmap (Step 12) and cost analysis (Step 13) have a single target to plan against — this ADR is that decision, not a restatement of Step 10's scoring.

**Options considered:**
- Microsoft Azure (`azure-implementation.md`, ADR-005 through ADR-011)
- Amazon Web Services (`aws-implementation.md`, ADR-012 through ADR-018)
- Google Cloud Platform (`gcp-implementation.md`, ADR-019 through ADR-025)
- Private cloud — VMware Cloud Foundation across two colocation facilities (`private-cloud-implementation.md`, ADR-026 through ADR-033)

**Decision:** Microsoft Azure.

**Rationale:**
The decision matrix scored Azure highest (4.50/5.00) against the other three (AWS 3.30, GCP 3.20, private cloud 2.85), and — unlike the closer ordering among the other three — Azure's lead is robust to a reasonable reweighting of the criteria (`decision-matrix.md` §4's sensitivity check). But the weighted score is corroborating evidence here, not the reason on its own; the same conclusion holds when the matrix is set aside and the two hardest constraints in `requirements.md` are checked directly:

1. **The operational-burden requirement is explicit, not implied**: "any target architecture should reduce, not increase, undifferentiated operational burden on this team," referring to Meridian's 16-person internal team plus after-hours MSP NOC. Azure is the only one of the four tracks with no self-managed tier named anywhere in its implementation — no OS-level database administration burden (unlike AWS's RDS Custom, ADR-013), no manually-rebuilt DR compute tier (unlike GCP, `gcp-implementation.md` §8), and critically nothing resembling the private-cloud track's self-managed SQL Server Always On and self-managed RabbitMQ, both named as the single most consequential and sharpest operational gaps in that entire track (ADR-028, ADR-033). A 16-person team absorbing 46 sites, ~2 million patient records, and a 9-clinic acquisition in the next 12 months cannot also absorb net-new database and message-broker administration without a corresponding staffing increase nobody has proposed.
2. **The identity requirement is explicit and tied to a realized incident**: "MFA must be enforced for all clinical and administrative access, not a subset," directly motivated by the March 2026 credential-compromise incident named in the threat model. Azure is the only platform with a native Conditional Access / Identity Protection product (Entra ID P2) — AWS, GCP, and private cloud (IAM Identity Center, Cloud Identity, and Active Directory's own native capability, respectively) each explicitly require a third-party CASB layer (Okta, Duo) to close the same gap Azure closes natively (ADR-009 vs. ADR-016/ADR-023/`private-cloud-implementation.md` §5). Choosing a platform that still needs a follow-on vendor decision to fully address the exact failure mode that already happened once is a materially weaker starting position.

Azure also has the largest real DR-runbook margin of the four tracks (180 of 240 minutes, `azure-implementation.md` §12) achieved with native tooling on every leg — not the fastest-looking number bought at real capital cost the way private cloud's 185-minute runbook is (ADR-026), and not eroded by a named gap on either the database or messaging leg the way AWS's 195 minutes and GCP's 215 minutes both are (ADR-013/ADR-018, `gcp-implementation.md` §8).

This decision is not a claim that Azure wins on every dimension — it explicitly does not. GCP's Cloud SQL native cross-region read replica is a genuine strength AWS's RDS Custom lacks (ADR-020); private cloud's direct facility ownership is the strongest form of the PHI-residency requirement (`decision-matrix.md` §3); and private cloud's fit to Meridian's existing vSphere skills is real (ADR-026). Those are accepted, named trade-offs of choosing Azure, not oversights.

**Trade-off:**
Azure does not lead on existing-skills fit (Meridian's team has documented existing vSphere experience, not documented Azure experience — a real ramp-up cost this ADR accepts rather than hides), data-services HA/DR maturity (tied with GCP, not ahead of it), regulatory fit / PHI data control (private cloud's direct facility ownership is a stronger form of control, even though Azure clears the hard US-residency/HIPAA constraint), or portability (Azure's design leans on the same degree of platform-native managed-PaaS dependency as AWS and GCP — a real, symmetric lock-in this ADR accepts as the cost of the operational-burden and identity-maturity wins above). Azure's own implementation also carries two named deferred items independent of this decision: the Service Bus Geo-DR in-flight-message gap (ADR-011, mitigated by a source-system reconciliation step rather than closed outright) and Bicep IaC modules not yet built (`azure-implementation.md` §14) — both real, both to be picked up in Step 12, not resolved by this ADR.

**Status:** Approved

---

**What this ADR approves:**

- The Azure-specific service mapping, network topology, identity/security design, and DR implementation in `azure-implementation.md` and `application-architecture.md`, and ADR-005 through ADR-011, become Meridian's approved target architecture — see `docs/target-architecture.md` for the consolidated summary and what carries forward unchanged into Step 12.
- ADR-001 through ADR-004 (platform-neutral: migration strategy, target architecture style, database technology family, DR strategy) are approved alongside this ADR — they were already inherited unchanged by all four tracks, and this decision doesn't reopen them.
- The AWS, GCP, and private-cloud tracks (ADR-012 through ADR-033) are not deleted or treated as wasted work — they remain in this repository as the audit trail this decision was actually made against, per the reference guide's own discipline (Section 8: "An ADR for every non-trivial decision, with the rejected options and why"). Each of those ADRs is marked Superseded by this one, not silently abandoned.
