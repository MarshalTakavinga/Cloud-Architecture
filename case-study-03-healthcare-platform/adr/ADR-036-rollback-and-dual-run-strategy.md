### ADR-036: Per-wave rollback and dual-run strategy

**Context:**
`requirements.md` explicitly defers this decision to this stage: "Rollback strategy — to be defined per migration wave in the roadmap stage — no big-bang cutover of all 46 sites at once." ADR-035 splits the program into one central-services cutover (Wave 1) and a series of per-site compute waves (Waves 2 through 9) with genuinely different risk profiles, so each needs its own rollback answer rather than one generic plan applied uniformly.

**Options considered:**
- No rollback path — commit each cutover immediately and fix forward only
- Point-in-time restore from backup if a problem is discovered after the fact
- A time-boxed dual-run: keep the legacy path warm and reachable for a defined bake period after each cutover, with a rollback mechanism scoped to what that wave actually changed (data for Wave 1, routing only for every wave after it)

**Decision:** Time-boxed dual-run, scoped differently per wave type:

- **Wave 1 (central services)**: the legacy on-prem SQL Server 2014 AAG is kept live and receiving one-way log-shipped updates from the new Azure SQL Managed Instance for a 30-day bake window post-cutover, decommissioned only after a clean go/no-go review. The legacy Portal, Telehealth, and LinkEngine paths are kept warm behind DNS/Front Door routing for the same window, so traffic can be re-pointed back without a data-recovery exercise if a problem surfaces early.
- **Waves 2–9 (per-site compute)**: rollback is routing-only. A site's cutover is reversed by re-pointing that site's Citrix StoreFront/Cloud Connector session routing back to the legacy on-prem VDA farm, which continues running and continues authenticating against the same already-migrated Azure database throughout — there is no data to reconcile, because the database itself was never re-migrated per site (ADR-035). Each wave has a 14-day bake period and an explicit go/no-go smoke-test gate (authentication, scheduling read/write, HL7 feed delivery for that wave's sites) before it is declared complete.
- The legacy on-prem Citrix VDA farm itself is not decommissioned progressively — it stays fully operational as the fallback target for every wave, including the last one, until the final wave's own bake period clears.

**Rationale:**
This gives every wave a genuine, low-cost way back without requiring the organization to run two permanently diverging copies of clinical data. The one-way log-shipping approach for Wave 1 provides a real data-level fallback for the single highest-risk event in the program without building full bidirectional sync; the routing-only rollback for every later wave costs almost nothing to maintain, because the legacy farm keeps doing exactly what it does today — serving fewer active sites each wave, not being rebuilt or resynced — while still giving each wave genuine reversibility.

**Trade-off:**
The legacy on-prem VDA farm and its underlying vSphere/SAN infrastructure — already 6.5 years old on average and at 91% SAN utilization per `current-state.md` §3 — has to stay fully operational for the entire migration program, not be decommissioned incrementally as sites cut over. That is a real capacity and hardware-failure risk during the program, named explicitly in `migration-roadmap.md` rather than assumed away, with one real offsetting factor: load on that same aging infrastructure decreases wave over wave as sites move off it, so it gains headroom as the program proceeds rather than staying pinned at today's 85% peak utilization for the full duration.

**Status:** Approved
