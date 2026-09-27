# ADR-004: Govern Centrally, Operate Locally

**Status:** Approved
**Date:** Step 4 of the Case Study 6 pipeline

## Context

About 9% of VMs are missing from both patching tools, and the CMDB is incomplete. The examiners cited this (`current-state.md` §4). Driver 3 wants one inventory, policy, patch, and identity model across on premises and public cloud. The invariant and NFR-3 require Tier 0 to keep running, failing over, and patching for at least 7 days with any vendor's cloud control plane unreachable. Several candidate platforms are *managed from* a public cloud.

## Decision

1. **Govern centrally.** One authoritative plane for:
   - **inventory** of hosts, VMs, and clusters, with owner, tier, and data class, reconciled daily to ServiceNow (NFR-8)
   - **policy as code** (configuration baselines, required tags, allowed images, network rules) held in Git
   - **patch compliance** reporting
   - **role-based access** through Entra ID

   It covers both data centers **and** the public-cloud landing zone.
2. **Operate locally.** In each site, a **local operations path** must work with the central plane unreachable for **at least 7 days**. It covers:
   - **VM lifecycle:** create, start, stop, and migrate between hosts
   - **DC1→DC2 failover:** the recovery orchestrator from [ADR-002](ADR-002-recovery-as-code-active-standby.md) runs locally
   - **Patch apply and roll back:** from a local repository and update source
   - **Local identity:** on-premises AD, with break-glass accounts vaulted in PAM
   - **A local console** and local logs, forwarded to Sentinel when connectivity returns
3. **The disconnected-week test.** Each platform track (Steps 6–9) is evaluated against this list with current documentation. If a track can't pass it, it can still govern Tier 1 and Tier 2, but **not Tier 0**.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Per-site, per-tool management with CMDB reconciliation.** Rejected, because it is how the inventory gap arose.
2. **A cloud-hosted control plane for everything, including Tier-0 operations.** Rejected. It makes operating Tier 0 depend on a public cloud, which fails the invariant.
3. **A self-hosted control plane only.** Rejected as the whole answer. Governing the landing zone separately would split driver 3.

## Consequences

- **Positive:** The invariant becomes a concrete test that every track must pass, not a phrase.
- **Positive:** The examiners' inventory finding is closed by construction, because anything not enrolled in the plane is non-compliant by definition.
- **Negative / accepted trade-off:** Local operation needs local infrastructure (identity, repositories, consoles) that a purely cloud-managed design would not. It must be tested, not assumed. The disconnected-week drill is added to the DR test calendar.
