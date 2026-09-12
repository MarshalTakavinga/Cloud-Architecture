### ADR-027: Private-cloud compute and hosting model for the CareLink PM core

**Context:**
ADR-001 decided to Replatform CareLink PM, not rebuild it — platform-neutral, carries forward unchanged. ADR-026 decided the platform (VMware Cloud Foundation) and facility (two colocation sites) this hosting model actually runs on. CareLink PM is a Windows thick-client application currently published via Citrix Virtual Apps 7. This ADR answers the same narrow question ADR-005 (Azure), ADR-012 (AWS), and ADR-019 (GCP) each answered for their platform: what specifically hosts the delivery infrastructure.

**Options considered:**
- Continue with Citrix Virtual Apps and Desktops, moving only the VM infrastructure onto VCF-managed vSphere VMs
- Migrate the delivery mechanism to VMware Horizon — VMware's own VDI/app-publishing product, natively integrated with the vSphere/VCF stack this design has already chosen
- Rebuild the client experience as a web application (Refactor — already ruled out by ADR-001)

**Decision:** Keep Citrix Virtual Apps and Desktops, moving only the underlying VM infrastructure onto VCF-managed vSphere VMs, spread across ESXi hosts in the Production VI Workload Domain.

**Rationale:**
Rebuilding as a web application is a Refactor, already ruled out by ADR-001 for the same reason on every platform: Meridian doesn't own CareLink PM's source and can't change how it's delivered. The real, platform-specific decision here is Citrix versus Horizon, and **this is the one point in the entire case study where a genuinely native, first-party alternative exists that none of Azure Virtual Desktop, Amazon AppStream 2.0, or (per ADR-019) any GCP product could offer** — Horizon runs directly on the same vSphere layer VCF already provides, with no separate cloud subscription. It is a real option, not a straw man, and it deserves to be weighed as one. It is rejected anyway: switching VDI platforms is itself a nontrivial project — re-publishing every application entitlement, retraining help-desk staff on a new console, and re-validating printer/scanner/peripheral redirection behavior across 46 clinical sites — a real migration cost layered on top of the platform migration this ADR is already making, and ADR-001's Replatform strategy was explicitly chosen to avoid exactly this kind of compounding change. Citrix Virtual Apps and Desktops runs as an ordinary guest workload on VCF-managed vSphere VMs without any special integration — VCF does not require Horizon, Horizon is simply VMware's own optional product on the same hypervisor — so keeping Citrix and moving only the VM infrastructure is the smallest change that satisfies Replatform on this platform too, reaching the identical conclusion ADR-019 reached for GCP, but for a different reason: GCP had no real alternative to weigh; here there is one, and it's set aside deliberately.

**Trade-off:**
This carries Citrix licensing cost and a second vendor relationship into the private-cloud target state, the same trade-off ADR-005/ADR-012/ADR-019 accepted on every other platform. Here it also means forgoing the deeper single-vendor integration and potentially simpler unified support Horizon-on-VCF could offer — a genuine trade-off unique to this track, since it's the only one of the four where that alternative actually exists. Revisit only if Meridian undertakes a dedicated, from-scratch VDI re-platforming initiative independent of this migration; there is no forcing function to do so here.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| VM spec | 8 vCPU / 32 GB, Windows Server 2022 Datacenter, Citrix multi-session | Direct sizing parity with ADR-005/ADR-012/ADR-019's identical VM shape — the workload profile doesn't change with the underlying platform |
| Session density (planning assumption) | ~5 concurrent sessions per vCPU → ~40 sessions per VM | Same planning figure reused across every platform track — still provisional pending a real Citrix Capacity assessment |
| Target design capacity | 5,000 concurrent sessions | Same source as every sibling ADR: `requirements.md`'s 36-month-horizon assumption |
| Peak Machine Catalog size | ~125 VMs (5,000 ÷ 40 sessions/VM) | Same math as the sibling ADRs |
| Day-one Machine Catalog size | ~45 VMs (1,800 ÷ 40 sessions/VM) | Sized to today's actual Monday-morning peak (`current-state.md`) |
| **Physical host math (private-cloud-specific)** | At ~3:1 vCPU overcommit on 64-physical-core hosts, one ESXi host comfortably carries ~24 of these 8-vCPU VMs before contention risk — day-one's 45 VMs need roughly 2 hosts' worth of Citrix capacity alone; the 125-VM target needs roughly 5-6 hosts' worth, out of ADR-026's 8-host day-one / 20-host target Production Workload Domain | **The genuine platform difference this ADR has to surface that none of the Azure/AWS/GCP compute ADRs did**: on every other platform, "how many instances" is the whole sizing question. Here, instance count is only half of it — Meridian also has to size, purchase, rack, and power the *physical hosts* those VMs run on, sharing that same physical capacity with the SQL Server VMs (ADR-028), the Tanzu cluster (ADR-030), and NSX appliances (ADR-029). This host-math row exists specifically to make that shared-capacity reality visible, not hide it behind a VM count the way the hyperscaler ADRs reasonably could |
| Cloud Connectors | 4 (one per availability zone-equivalent within the Workload Domain, plus a spare), on small VMs in the Application network segment | Same reasoning as every sibling ADR — 2 is Citrix's documented HA minimum, but at 5,000 target sessions the connector tier shouldn't be a bottleneck or share one failure domain |
| Redundancy | Machine Catalog spread across ESXi hosts within the Production VI Workload Domain, with vSphere DRS anti-affinity rules keeping session-host VMs off the same physical host where possible | The private-cloud analog to "spread across zones" — vSphere DRS anti-affinity is the mechanism that prevents one host failure from being a bigger blast radius than intended, since a private-cloud facility has no built-in "zone" abstraction the way a hyperscaler region does |
| Networking | Application network segment (see ADR-029), one NSX Tier-1 segment, not per-host subnetting | Matches Azure's and GCP's regional-subnet simplicity — an NSX segment spans every host in the Workload Domain automatically, the same property that made per-zone subnetting unnecessary on Azure/GCP |
| Storage | vSAN, performance-tier storage policy (FTT=1, RAID-1) | VDA session hosts are non-persistent/stateless (user profiles live in the database and file-share-backed profile storage, not on the instance) — FTT=1 balances resilience against vSAN capacity consumption for a tier that doesn't need FTT=2's stronger protection |

Compute sizing here reuses the exact same real inputs (`current-state.md`'s ~1,800-session Monday peak, `requirements.md`'s 5,000-session 36-month assumption) that every platform track uses — deliberately, since the demand-side numbers are platform-independent; only the hosting mechanics and the physical-host math changed. Real right-sizing still needs an actual Citrix Capacity assessment before go-live. Cost for this configuration — including hardware purchase, VCF licensing, and Citrix licensing — is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-private-cloud.md`](../docs/application-architecture-private-cloud.md) §1 for the full hosting architecture narrative. No detail diagram exists yet for this ADR — hand-drawn diagrams are added incrementally and checked against this document once available, the same standard applied to every diagram in the Azure/AWS/GCP sections of this repository.
