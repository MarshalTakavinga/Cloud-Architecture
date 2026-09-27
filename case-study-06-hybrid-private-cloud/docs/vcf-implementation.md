# Step 6: VMware Cloud Foundation Implementation (modernize in place)

## Purpose of This Step

This step maps the 26 [Step 5](logical-design.md) components onto **VMware Cloud Foundation 9.1**, the "modernize in place" track, and answers the nine questions every track must answer. It also assesses the **VMware-in-public-cloud** services (Azure VMware Solution, Google Cloud VMware Engine, and Amazon Elastic VMware Service) as this track's cloud extension, as [Step 4](architecture-options-and-styles.md)'s AWS lens planned.

The point of this track is to find what Alder Valley can get from the platform it **already pays for and mostly doesn't use**, and at what price.

## Findings from Current Documentation (September 2026)

1. **VCF 9.1 was released on 3 September 2026.** Broadcom's FAQ lists its primary components as *"vSphere, vSAN, NSX, vSphere Kubernetes Service (VKS), VCF Operations, VCF Automation, … HCX, VCF Private AI services."* Most of what Step 5 needs is therefore **in the core subscription**. Alder Valley uses only vSphere, vSAN, part of NSX, Aria Operations, and SRM today.
2. **Add-ons are separate purchases.** *"Advanced services are available for separate purchases and are not included in the core VCF offerings"*, including Advanced Security (vDefend), Load Balancing, Data Services, and vSAN Add-On Capacity.
3. **Microsegmentation needs the vDefend add-on.** Broadcom's knowledge base: firewall features remain locked without the vDefend key, and *"the vDefend add-on license strictly requires a base VCF or vSphere subscription."* Extending the distributed firewall from DC1's PCI zone to Tier 0 in **both** sites ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) is therefore an **add-on cost**, not a configuration change.
4. **VMware Live Recovery** combines disaster and cyber recovery across VCF sites. With VCF 9.0, Broadcom announced *"cyber recovery to an on-premises VCF isolated clean room"* as a validated solution, with *"RPOs as low as 1-minute with full DR orchestration"* on vSAN-to-vSAN replication. It is purchased separately.
5. **Licensing in disconnected mode.** VCF 9 licences are managed through VCF Operations. In disconnected (air-gapped) mode, usage must be reported *"at least once every 6 months (180 days)."* If that is missed, Broadcom's documentation says *"your licenses are treated as expired, your hosts are disconnected from the vCenter instance, and you cannot start any workload operations."*
6. **Azure Arc-enabled VMware vSphere** documents support for *"vCenter Server version 8"* only. **VCF 9's vCenter is not listed**, so Azure can't project a VCF 9 inventory natively. Arc-enabled *servers* (a guest agent in each VM) still works on any hypervisor.
7. **VMware in public cloud:** Amazon EVS became generally available in August 2025. It uses *"VCF subscriptions with license portability entitlements that you bring to AWS"*, with a minimum of 4 hosts (for example, 256 cores on i4i.metal). Azure VMware Solution and Google Cloud VMware Engine offer the same model on their clouds.

## Component Mapping (all 26)

| # | Component | VCF 9.1 implementation | Notes |
|---|---|---|---|
| P1 | Compute clusters | **One VCF instance per site**, each with its own management domain. Workload domains: **Tier-0 + PCI**, **Oracle**, **general (Tier 1/2)**, **VDI** | Separate instances keep the sites as independent failure domains ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md)) |
| P2 | Storage | **vSAN Express Storage Architecture** (ESA, NVMe) in every domain. **The DC1 Fibre Channel array is retired at refresh, not replaced** | Oracle on vSAN ESA must prove p99 ≤ 2 ms at the batch peak (proof of concept). Capacity beyond the included vSAN entitlement is an add-on |
| P3 | Oracle clusters | A dedicated Oracle workload domain in each site, with **no vMotion path out of the domain** | Soft partitioning, as today ([ADR-007](../adr/ADR-007-oracle-cluster-and-licence-boundary.md)). Consolidation at refresh is the lever |
| P4 | SDN + microsegmentation | **NSX** (VPCs for self-service networks) + **vDefend distributed firewall** on the Tier-0, PCI, Oracle, and Tier-1 hosts in **both** sites. Rules through the NSX Terraform provider | vDefend is an add-on, licensed on the hosts that enforce it |
| P5 | Site edge | Existing next-generation firewalls. NSX edges for north-south within domains | Unchanged |
| P6 | Kubernetes | **vSphere Kubernetes Service (VKS)**, included. It replaces the three Rancher clusters | Conformant Kubernetes, lifecycle-managed by the platform |
| C1 | Governance plane | **VCF Operations** (fleet inventory, compliance, capacity) for the private cloud. For the landing zone and guest level: **Arc-enabled servers** in every VM, reporting to Azure | **Two consoles.** Arc-enabled vSphere doesn't support vCenter 9 |
| C2 | Site manager | vCenter + VCF Operations **per site** | Local |
| C3 | Local identity | vCenter identity federation to Entra ID for day to day, with **local AD and SSO break-glass** held in PAM | Local |
| C4 | Local repository | An **offline depot** for VCF lifecycle updates, plus WSUS/SCCM and Red Hat Satellite for guests | Local |
| C5 | Policy pipeline | Git + Terraform (NSX, vSphere, VCF Automation providers) + Ansible | |
| C6 | CMDB sync | ServiceNow discovery + VCF Operations integration | |
| C7 | Licence service | **VCF Operations in disconnected mode**: a usage report every **180 days** | **The critical finding**, below |
| D1 | Platform API and catalog | **VCF Automation** (the "All Apps" organization model with self-service VPCs, VMs, and VKS namespaces) + its Terraform provider | Approvals in ServiceNow |
| D2 | Image pipeline | Packer builds for vSphere templates in the content library | |
| D3 | ServiceNow integration | VCF Automation ↔ ServiceNow | |
| R1 | Database replication | Oracle Data Guard, as designed ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md)) | Platform-independent |
| R2 | Platform replication | **VMware Live Recovery** vSAN-to-vSAN replication, DC1→DC2 | Replaces vSphere Replication + SRM |
| R3 | Recovery orchestrator | **Live Recovery** recovery plans, **generated from the Git plans** ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)). Data Guard and payments steps are called as automation from the plan | The DC2 instance runs with DC1 lost |
| R4 | Immutable local backup | **Veeam** with hardened repositories in each site (as today, extended to Tier 1) | Veeam's primary platform |
| R5 | Isolated vault | Veeam to an isolated repository in Z-VAULT, with a separate administrative domain | Platform-neutral |
| R6 | Clean room | **Live Recovery on-premises isolated clean room** in DC2 | Validated by Broadcom for VCF 9 |
| O1 | Telemetry | VCF Operations for Logs → Sentinel | |
| O2 | Capacity and cost | VCF Operations capacity and cost | Shows back per business service |
| O3 | Scanning | Existing vulnerability scanner + VCF Operations compliance packs (CIS, PCI) | |
| L1 | Landing zone | **Azure**, the natural pair given Entra ID, Sentinel, and M365. Not dictated by VCF | See the cloud extension section |

## The Nine Questions

| # | Question | VCF answer |
|---|---|---|
| 1 | Core banking certification | **Certified** (vSphere). No certified island is needed |
| 2 | Oracle partitioning | **Soft**, as today. 640 cores = 320 processor licences, reducible by consolidating onto fewer, faster cores at refresh, subject to the batch test |
| 3 | Horizon VDI | **Supported.** vSphere is Horizon's primary platform. Confirm the Omnissa matrix for vSphere 9 |
| 4 | Backup | **Veeam supported**, with immutability and a vault. No change of tooling |
| 5 | Disconnected-week test | **Passes** (every component runs locally), **with a 180-day licence-reporting obligation**. See below |
| 6 | Microsegmentation in both sites | **Yes, with the vDefend add-on** on the enforcing hosts |
| 7 | Kubernetes + API | **VKS** (included) + **VCF Automation** with a Terraform provider |
| 8 | Migration tooling | **Barely needed.** Upgrade vSphere 8 to VCF 9.1 in place, and move workloads onto refreshed hosts with vMotion and HCX. This is the lowest migration effort of the four tracks |
| 9 | Governance reach to public cloud | **Weak natively.** VCF Operations governs the private cloud. The landing zone is governed by its own cloud, bridged at guest level by Arc-enabled servers |

## The Disconnected-Week Test and the Licence Finding

**Every operational component is local**: vCenter, NSX Manager, VCF Operations, VCF Automation, the Live Recovery appliances, the offline depot, Veeam, and local AD. None depends on a public cloud. **For a 7-day disconnect, VCF is the strongest of the four tracks.**

The licence service is different, and it matters for driver 2. In disconnected mode, the platform must report usage every 180 days, or **"you cannot start any workload operations."** The same applies to a subscription that has expired.

- **Operationally:** a 180-day reporting task is easy to schedule, and it is added to the operations calendar with an alert at day 150.
- **Commercially:** it means **the platform stops working operationally if the subscription is not renewed**. Unlike the perpetual licences Alder Valley had before 2024, there is no "keep running unsupported" option. The renewal is not a choice between paying and running unsupported: **it is a choice between paying and being unable to operate.** This is exactly the leverage driver 2 is about, and it is why this track needs a **tested exit** (NFR-11) more than any other.

## Cloud Extension: VMware in Public Cloud

| Service | Fit | Assessment |
|---|---|---|
| **Azure VMware Solution** | VCF on Azure hosts. Pairs with the Azure landing zone and Entra ID | A possible **Tier-1 and Tier-2 recovery location** without refactoring. Not for Tier 0 (the invariant) |
| **Google Cloud VMware Engine** | The same model on Google Cloud | Equivalent, but pairs less naturally with Alder Valley's Microsoft estate |
| **Amazon EVS** (GA August 2025) | VCF in the bank's own VPC, with its **own portable VCF subscription**. Minimum 4 hosts | Equivalent. Would make use of the 2025 AWS account only if the landing zone were AWS |

**Decision for this track: no cloud VMware extension now** ([ADR-014](../adr/ADR-014-vcf-cloud-extension.md)). All three **deepen** the VCF dependency (more cores on the same subscription) rather than reducing it. They also add a third site to run, and DC2 already meets the Tier-1 RTO. The option stays open for Tier-1 DR if the DC2 contract isn't renewed in 2030.

## What the Bank Gets for the Renewal It Is Already Paying

The honest strength of this track is that **most of the Step 5 design is already licensed**:
- VCF Automation for self-service
- VKS for Kubernetes
- NSX VPCs for self-service networks
- VCF Operations for inventory and compliance
- HCX for workload moves

Adopting them closes driver 4 and most of driver 3 **without a migration**, which is the lowest-risk path to the Q4 2027 examination.

The honest weaknesses:
1. **Cost exposure:** the renewal at ~$1.65M a year, plus the **vDefend** and **Live Recovery** add-ons, with no competitive pressure unless an exit is credible.
2. **The licence stop:** operations stop if the subscription lapses.
3. **Governance is split** between VCF Operations and the cloud landing zone.

## Alignment Check against Steps 4–5

| Expectation | VCF reality | Treatment |
|---|---|---|
| One primary private cloud in two independent sites ([ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md)) | One VCF instance per site | **Met** |
| Recovery as code ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md), [ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)) | Live Recovery plans generated from Git, with Data Guard and payments automation called from them | **Met**, with the source of truth kept in Git rather than in Live Recovery's database |
| Cyber recovery ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | Veeam immutable + vault. Live Recovery on-premises clean room | **Met** |
| Govern centrally, operate locally ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)) | Operate locally: **strongest of the tracks**. Govern centrally: **split** (VCF Operations + cloud, bridged by Arc-enabled servers) | **Partial** |
| Platform API and portability ([ADR-005](../adr/ADR-005-platform-api-and-portability.md)) | VCF Automation + Terraform. VMDK images and exit tooling to every other platform are the best understood in the industry | **Met.** The exit path is well trodden, but the licence stop makes testing it essential |
| Zones as code in both sites ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) | NSX + vDefend in both sites | **Met, at add-on cost** |

## Diagram

See [`diagrams/vcf-implementation-architecture.md`](../diagrams/vcf-implementation-architecture.md) (Mermaid reference source, to be hand-drawn).

## Known Deferred Items

- The core count after consolidation, the vSAN capacity beyond entitlement, the vDefend and Live Recovery quantities, and a renewal **term** (one year versus three) are inputs to the Step 13 model.
- The Horizon and Veeam version matrices for vSphere 9.1 are to be confirmed before the design is frozen.
- An Oracle-on-vSAN-ESA batch proof of concept is needed before the Fibre Channel array is retired.
