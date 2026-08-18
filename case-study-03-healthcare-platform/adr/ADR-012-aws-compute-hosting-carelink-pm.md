### ADR-012: AWS compute and hosting model for the CareLink PM core

**Context:**
ADR-001 decided to Replatform CareLink PM, not rebuild it — that decision is platform-neutral and carries forward unchanged into the AWS implementation. CareLink PM is currently a Windows thick-client application published via Citrix Virtual Apps 7. An AWS implementation still has to choose a specific hosting mechanism, exactly as ADR-005 did for Azure.

**Options considered:**
- Continue with Citrix Virtual Apps and Desktops, hosted on Amazon EC2 (Citrix has native AWS support, the same way it has native Azure support)
- Migrate the delivery mechanism to Amazon AppStream 2.0, AWS's native application-streaming service
- Rebuild the client experience as a web application on AWS (ECS Fargate / App Runner)

**Decision:** Keep Citrix Virtual Apps and Desktops, moving only the underlying VM infrastructure to Amazon EC2, spread across Availability Zones — the same decision ADR-005 made for Azure, for the same reason.

**Rationale:**
Rebuilding the client experience as a web application would be a Refactor, which ADR-001 already ruled out — Meridian doesn't own CareLink PM's source and can't change how it's delivered. Amazon AppStream 2.0 is a genuinely closer AWS-native analog to Citrix's published-app model than Azure Virtual Desktop is to Citrix on Azure (AppStream streams individual applications, not just full desktops), and it would remove a real pain point in the long run — Citrix licensing, a second vendor relationship. But it introduces the exact same problem ADR-005 flagged for Azure Virtual Desktop: a second, unrelated delivery-platform change and staff retraining exercise stacked on top of the cloud migration itself, at the moment Meridian is trying to reduce risk, not add it. Keeping Citrix and only moving its VM infrastructure is the smallest change that satisfies the replatform strategy on AWS too: same user experience, same admin tooling, infrastructure that's finally zone-redundant instead of a single converted server room.

**Trade-off:**
This carries Citrix licensing cost and a second vendor relationship into the AWS target state, and defers a real modernization opportunity (AppStream 2.0) rather than capturing it now. Flagged as a candidate for a future, separate initiative once the migration itself is stable — not silently dropped, the same posture ADR-005 took on Azure Virtual Desktop.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Instance family | General purpose, `m6i.2xlarge` (8 vCPU / 32 GiB) | Direct sizing parity with ADR-005's `Standard_D8s_v5` — same vCPU/memory ratio, current-generation general-purpose instance family. No GPU, no storage-optimized profile needed for a scheduling/billing thick client |
| OS | Windows Server 2022 Datacenter, Citrix multi-session | Same OS/driver combination as ADR-005 — Citrix's own multi-user driver on Windows Server, platform-independent of the underlying hypervisor |
| Session density (planning assumption) | ~5 concurrent sessions per vCPU → ~40 sessions per `m6i.2xlarge` instance | Same planning figure as ADR-005 — the workload profile (medium-weight interactive LOB screens) doesn't change with the underlying cloud platform. Still provisional pending a real Citrix Capacity assessment or pilot load test before go-live |
| Target design capacity | 5,000 concurrent sessions | Same source as ADR-005: `requirements.md`'s captured 36-month-horizon assumption, which already includes the "2-3x headroom" the NFR table calls for |
| Peak Machine Catalog size | ~125 instances (5,000 ÷ 40 sessions/instance), spread across 3 AZs (~42 per zone) | Same math as ADR-005 — the ceiling Citrix autoscale can grow the catalog to at target-state peak, not a static fleet |
| Day-one Machine Catalog size | ~45 instances (1,800 ÷ 40 sessions/instance), ~15 per zone | Sized to today's actual Monday-morning peak (`current-state.md`, ~1,800 concurrent sessions) — identical to ADR-005's day-one figure, since the underlying demand hasn't changed, only the platform |
| Off-peak autoscale floor | ~6-9 instances total (2-3 per zone) | Same off-peak assumption as ADR-005, consistent with `current-state.md`'s "Monday mornings, flu season" peak pattern |
| Cloud Connectors | 4 (one per AZ + one spare), on small EC2 instances | Same reasoning as ADR-005 — 2 is Citrix's documented HA minimum for a resource location, but that floor is sized for small deployments; at 5,000 target concurrent sessions the connector tier shouldn't become a bottleneck or share one AZ's failure domain |
| Redundancy | Machine Catalog spread across 3 Availability Zones | `us-east-1` (see ADR-014/`aws-implementation.md` for region selection) has 6 AZs available; 3 are used, matching ADR-005's zone count and failure-domain math (losing one zone removes roughly a third of capacity, not all of it) |
| Storage | EBS gp3 root volumes, no persistent instance store | VDA session hosts in this catalog are non-persistent/stateless (user profiles and data live in RDS and FSx/S3-backed profile storage, not on the instance) — gp3 is the standard, cost-predictable fit; this is functionally the AWS equivalent of ADR-005's ephemeral OS disk choice, though EC2 doesn't offer a true ephemeral-disk option identical to Azure's for Windows boot volumes, so gp3 with automated teardown/rebuild on catalog refresh is the closest match |

Compute sizing here reuses the exact same real inputs ADR-005 used (`current-state.md`'s ~1,800-session Monday peak, `requirements.md`'s 5,000-session 36-month assumption) — deliberately, since the demand-side numbers are platform-independent; only the instance family and hosting mechanics changed. Real right-sizing, and the Citrix licensing implications of a fleet this size, still need an actual Citrix Capacity assessment before go-live, same caveat as ADR-005. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-aws.md`](../docs/application-architecture-aws.md) §1 for the full hosting architecture narrative, [`../diagrams/carelink-pm-architecture-aws.png`](../diagrams/carelink-pm-architecture-aws.png) for the component view, and [`../diagrams/carelink-pm-hosting-architecture-aws.png`](../diagrams/carelink-pm-hosting-architecture-aws.png) for the detailed sizing/hosting diagram matching this ADR's Proposed Configuration (Machine Catalog counts per AZ, Cloud Connector subnets, Citrix Cloud control-plane connectivity).
