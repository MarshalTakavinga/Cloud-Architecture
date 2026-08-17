### ADR-004: Disaster recovery strategy for the CareLink PM core

**Context:**
The current environment has no real secondary site, a documented RTO of 24–48+ hours, and an RPO of up to 24 hours — the single largest gap driving the cyber-insurance renewal risk. The target requirement is RTO ≤ 4 hours and RPO ≤ 15 minutes.

**Options considered:**
- Backup-and-restore only: rely on regular backups to a second region, rebuild infrastructure on failure
- Warm standby (pilot light): pre-provision core infrastructure in a second region at reduced scale, replicate data continuously, scale up and promote on failover
- Active-active: run production traffic in two regions simultaneously, with real-time bidirectional replication

**Decision:** Warm standby (pilot light) in a second geographic region, with asynchronous continuous replication and a manually-triggered, tooling-assisted failover.

**Rationale:**
Backup-and-restore alone cannot reliably hit a 4-hour RTO once infrastructure has to be rebuilt from scratch — it's a cheaper option that doesn't meet the actual requirement. Active-active would comfortably beat both targets but is disproportionate to them: Meridian's RTO/RPO targets are moderate, not nearly-zero, and active-active roughly doubles operational complexity and cost for headroom the requirement doesn't call for. Warm standby is the option actually sized to the stated numbers. Failover is deliberately manual-initiated rather than automatic — an unplanned automatic failover in a clinical scheduling system carries its own risk (mid-transaction state, provider workflow disruption), so a human decision point is intentional, not a gap.

**Trade-off:**
Warm standby costs more, ongoing, than backup-and-restore (idle standby capacity has to be paid for continuously), and it still requires a failover event — a period of disruption, even if bounded to 4 hours — that active-active would avoid almost entirely. That risk is accepted explicitly, not overlooked.

**Status:** Proposed
