### ADR-019: GCP compute and hosting model for the CareLink PM core

**Context:**
ADR-001 decided to Replatform CareLink PM, not rebuild it — platform-neutral, carries forward unchanged. CareLink PM is a Windows thick-client application currently published via Citrix Virtual Apps 7. A GCP implementation still has to choose a specific hosting mechanism, exactly as ADR-005 did for Azure and ADR-012 did for AWS.

**Options considered:**
- Continue with Citrix Virtual Apps and Desktops, hosted on Google Compute Engine (Citrix Cloud supports GCP as a resource location, the same way it supports Azure and AWS)
- Migrate the delivery mechanism to a GCP-native application-streaming service
- Rebuild the client experience as a web application on GCP (Cloud Run / GKE)

**Decision:** Keep Citrix Virtual Apps and Desktops, moving only the underlying VM infrastructure to Google Compute Engine, spread across zones — the same decision ADR-005 and ADR-012 made for Azure and AWS, for the same reason.

**Rationale:**
Rebuilding the client experience as a web application would be a Refactor, which ADR-001 already ruled out — Meridian doesn't own CareLink PM's source and can't change how it's delivered. Unlike the Azure and AWS comparisons, though, the second option here isn't a real like-for-like alternative to weigh — **Google Cloud has no native published-application-streaming product comparable to Azure Virtual Desktop or Amazon AppStream 2.0.** Google Workspace's Chrome Remote Desktop is a point-to-point remote-access tool, not an enterprise session-brokering/app-publishing platform, and there is no GCP first-party equivalent that could replace Citrix's role the way AVD or AppStream at least theoretically could on their respective platforms. This is a genuine, worth-naming difference, not a gap in this document's research: ADR-005 and ADR-012 both had a real (if ultimately rejected) native modernization path to weigh against staying on Citrix; on GCP, keeping Citrix isn't just the lower-risk choice, it's the only realistic one short of the Refactor this ADR has already ruled out. Keeping Citrix and only moving its VM infrastructure is the smallest change that satisfies the replatform strategy on GCP too: same user experience, same admin tooling, infrastructure that's finally zone-redundant instead of a single converted server room.

**Trade-off:**
This carries Citrix licensing cost and a second vendor relationship into the GCP target state, the same trade-off ADR-005/ADR-012 accepted — except here there isn't even a deferred native alternative to flag as a future candidate the way AppStream 2.0 was flagged for AWS. If Meridian wants to genuinely modernize CareLink PM's delivery model on GCP one day, that realistically means either a third-party DaaS product layered on top of GCP, or the Refactor path ADR-001 already ruled out for this stage — not a native GCP service waiting in the wings. Flagged here plainly so the eventual Step 10 comparison weighs this as a real structural difference between platforms, not an oversight.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Machine family | General purpose, `n2-standard-8` (8 vCPU / 32 GB) | Direct sizing parity with ADR-005's `Standard_D8s_v5` and ADR-012's `m6i.2xlarge` — same vCPU/memory ratio, current-generation general-purpose machine family. No GPU, no storage-optimized family needed for a scheduling/billing thick client |
| OS | Windows Server 2022 Datacenter, Citrix multi-session | Same OS/driver combination as ADR-005/ADR-012 — Citrix's own multi-user driver, platform-independent of the underlying hypervisor |
| Session density (planning assumption) | ~5 concurrent sessions per vCPU → ~40 sessions per `n2-standard-8` instance | Same planning figure as ADR-005/ADR-012 — the workload profile doesn't change with the underlying cloud platform. Still provisional pending a real Citrix Capacity assessment or pilot load test before go-live |
| Target design capacity | 5,000 concurrent sessions | Same source as ADR-005/ADR-012: `requirements.md`'s captured 36-month-horizon assumption |
| Peak Machine Catalog size | ~125 instances (5,000 ÷ 40 sessions/instance), spread across 3 zones (~42 per zone) | Same math as ADR-005/ADR-012 — the ceiling Citrix autoscale can grow the catalog to at target-state peak |
| Day-one Machine Catalog size | ~45 instances (1,800 ÷ 40 sessions/instance), ~15 per zone | Sized to today's actual Monday-morning peak (`current-state.md`, ~1,800 concurrent sessions), identical to ADR-005/ADR-012's day-one figure |
| Off-peak autoscale floor | ~6-9 instances total (2-3 per zone) | Same off-peak assumption as ADR-005/ADR-012, consistent with `current-state.md`'s "Monday mornings, flu season" peak pattern |
| Cloud Connectors | 4 (one per zone + one spare), on small Compute Engine instances | Same reasoning as ADR-005/ADR-012 — 2 is Citrix's documented HA minimum for a resource location, but at 5,000 target concurrent sessions the connector tier shouldn't become a bottleneck or share one zone's failure domain |
| Redundancy | Machine Catalog spread across 3 zones | `us-central1` (see ADR-021/`gcp-implementation.md` for region selection) has multiple zones available; 3 are used, matching ADR-005/ADR-012's zone count and failure-domain math |
| Networking | Single regional subnet, not one per zone | **A genuine platform difference worth naming, not inherited wholesale from AWS.** Unlike an AWS VPC subnet, which is scoped to exactly one Availability Zone (forcing ADR-012 to provision `subnet-citrix-az1/az2/az3`), a **GCP VPC subnet is regional** — it spans every zone in the region automatically, matching Azure's model, not AWS's. The whole Machine Catalog, across all 3 zones, sits in one `subnet-citrix` allocation, not three — see `gcp-implementation.md` §4.1 |
| Storage | Persistent Disk (pd-balanced), no local SSD | VDA session hosts in this catalog are non-persistent/stateless (user profiles and data live in Cloud SQL and Filestore/Cloud Storage-backed profile storage, not on the instance) — pd-balanced is the standard, cost-predictable fit, functionally the GCP equivalent of ADR-005/ADR-012's ephemeral/gp3 disk choice |

Compute sizing here reuses the exact same real inputs ADR-005/ADR-012 used (`current-state.md`'s ~1,800-session Monday peak, `requirements.md`'s 5,000-session 36-month assumption) — deliberately, since the demand-side numbers are platform-independent; only the machine family, hosting mechanics, and (per the Networking row above) the subnet model changed. Real right-sizing, and the Citrix licensing implications of a fleet this size, still need an actual Citrix Capacity assessment before go-live. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-gcp.md`](../docs/application-architecture-gcp.md) §1 for the full hosting architecture narrative, and [`../diagrams/carelink-pm-hosting-architecture-gcp.png`](../diagrams/carelink-pm-hosting-architecture-gcp.png) for the detailed sizing/hosting diagram matching this ADR's Proposed Configuration (Machine Catalog counts per zone, Cloud Connector placement, Citrix Cloud control-plane connectivity, and the Application VPC's consolidated `subnet-app`) — hand-reproduced, went through two review rounds: the first submission placed Citrix in a `vpc-meridian (10.10.0.0/16)`/`subnet-citrix` that collided with the Inspection VPC's own reserved address space and predated the Integration VPC rework; corrected to the documented `Application VPC (10.20.0.0/16)`/`subnet-app (10.20.1.0/24)` in the second round.
