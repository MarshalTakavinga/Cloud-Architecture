### ADR-005: Azure compute and hosting model for the CareLink PM core

**Context:**
ADR-001 decided to Replatform CareLink PM, not rebuild it. CareLink PM is currently a Windows thick-client application published via Citrix Virtual Apps 7. An Azure implementation still has to choose a specific hosting mechanism.

**Options considered:**
- Continue with Citrix Virtual Apps and Desktops, hosted on Azure VMs (Citrix has native Azure support)
- Migrate the delivery mechanism to Azure Virtual Desktop, Microsoft's native equivalent
- Rebuild the client experience as a web application on Azure App Service

**Decision:** Keep Citrix Virtual Apps and Desktops, moving only the underlying VM infrastructure to Azure, spread across Availability Zones.

**Rationale:**
Rebuilding the client experience on App Service would be a Refactor, which ADR-001 already ruled out — Meridian doesn't own CareLink PM's source and can't change how it's delivered. Migrating to Azure Virtual Desktop would remove a real pain point in the long run (Citrix licensing, an additional vendor relationship) but introduces a second unrelated change — a new delivery platform and staff retraining — on top of the cloud migration itself, at exactly the moment Meridian is trying to reduce risk, not add it. Keeping Citrix and only moving its VM infrastructure is the smallest change that satisfies the replatform strategy: same user experience, same admin tooling, infrastructure that's finally zone-redundant instead of a single converted server room.

**Trade-off:**
This carries Citrix licensing cost and a second vendor relationship into the target state, and defers a real modernization opportunity (Azure Virtual Desktop) rather than capturing it now. Flagged as a candidate for a future, separate initiative once the migration itself is stable — not silently dropped.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| VM series | Dsv5-series, `Standard_D8s_v5` (8 vCPU / 32 GB) | Already named directionally in `azure-implementation.md`; general-purpose compute/memory ratio fits an interactive session-host workload — no GPU, no storage-optimized profile needed for a scheduling/billing thick client |
| OS | Windows Server 2022 Datacenter, Citrix multi-session | Standard OS for Citrix-published multi-session delivery — this is Citrix's own multi-user driver on Windows Server, not the separate Windows 10/11 Enterprise multi-session SKU that's specific to Azure Virtual Desktop |
| Session density (planning assumption) | ~5 concurrent sessions per vCPU → ~40 sessions per `Standard_D8s_v5` VM | A mid-range planning figure for a medium-weight interactive LOB app (scheduling/registration/billing screens — not heavy graphics or reporting). This is explicitly provisional: there's no per-VM production telemetry for CareLink PM's actual session footprint today, only cluster-level utilization (see below). Needs a real Citrix Capacity assessment or pilot load test before go-live |
| Target design capacity | 5,000 concurrent sessions | This is `requirements.md`'s own captured 36-month-horizon assumption ("peak concurrent scheduling/PM sessions will not exceed roughly 5,000"), which already reflects the "2–3x headroom over today's peak" the NFR table separately calls for. Sizing straight to this figure avoids stacking a second, redundant headroom multiplier on top of one that's already built into the requirement |
| Peak Machine Catalog size | ~125 VMs (5,000 ÷ 40 sessions/VM), spread across 3 AZs (~42 per zone) | This is the *ceiling* Citrix autoscale can grow the catalog to at target-state peak load — not a static fleet running continuously |
| Day-one Machine Catalog size | ~45 VMs (1,800 ÷ 40 sessions/VM), ~15 per zone | Sized to today's actual Monday-morning peak captured in `current-state.md`/`requirements.md` (~1,800 concurrent sessions), not the 36-month target — this is what the catalog needs to scale to on day one of cutover |
| Off-peak autoscale floor | ~6–9 VMs total (2–3 per zone) | Citrix autoscale powers the catalog down outside business hours and off-peak days, consistent with `current-state.md`'s own observation that peak is specifically "Monday mornings, flu season," not a flat load. (This also happens to land close to the "two VMs per zone" figure used earlier as an illustrative placeholder — now it's grounded in an actual off-peak assumption instead of an arbitrary starting point) |
| Cloud Connectors | 4 (one per zone + one spare), not the earlier-stated minimum of 2 | 2 is Citrix's documented HA minimum for a resource location, but that's a floor sized for small deployments. At a target of 5,000 concurrent sessions, the connector tier itself shouldn't become a bottleneck or share a single zone's failure domain — provisional pending Citrix Cloud's own capacity guidance for a resource location this size |
| Redundancy | Machine Catalog spread across 3 Availability Zones | Losing one zone removes roughly a third of capacity, not all of it — unchanged from the original design, now sized with real numbers behind it |
| OS disk | Ephemeral OS disk | Citrix VDA session hosts in this catalog are non-persistent/stateless (user profiles and data live in SQL MI and FSLogix-style profile storage, not on the VM) — ephemeral OS disks are the standard fit for that pattern. Cost/performance implications are a Step 13 concern, not decided here |

Compute sizing here is a directional starting point derived from real inputs already captured in this case study (`current-state.md`'s ~1,800-session Monday peak, `requirements.md`'s 5,000-session 36-month assumption) — not a Citrix-specific load test or Azure Migrate assessment. Real right-sizing, and the Citrix licensing implications of a fleet this size, should be validated with an actual Citrix Capacity assessment before go-live; cost for this configuration is deliberately not estimated here and stays with Step 13, same as ADR-006.

See [`../diagrams/carelink-pm-hosting-architecture.png`](../diagrams/carelink-pm-hosting-architecture.png) for the full hosting diagram — VM counts and subnets exactly as sized above, Cloud Connectors in their own `snet-cloud-connectors` (10.20.6.0/24) subnet, VDA direct connection to SQL MI (subnet-injected, not a Private Endpoint).
