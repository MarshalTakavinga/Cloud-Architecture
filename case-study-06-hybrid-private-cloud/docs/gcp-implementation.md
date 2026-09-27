# Step 8: Google Distributed Cloud Implementation (software only, bare metal, with VM Runtime)

## Purpose of This Step

This is the third mapping of the 26 [Step 5](logical-design.md) components, after [VCF](vcf-implementation.md) and [Azure Local + Arc](azure-implementation.md). It maps them onto **Google Distributed Cloud (GDC), software only, for bare metal**:
- GKE clusters on the bank's own Linux servers
- **VM Runtime on GDC** for virtual machines
- fleet management from Google Cloud, with a GCP landing zone

This track is the most **Kubernetes-first** of the four: VMs become Kubernetes objects. The question is whether that model can carry a VM-heavy banking estate.

## Findings from Current Documentation (September 2026)

1. **What it is.** GDC software-only *"extends Google Kubernetes Engine (GKE) to let you create clusters on your own Linux servers on your own premises"* (RHEL or Ubuntu). Clusters join a **fleet** through the Connect Agent.
2. **VM Runtime is KubeVirt.** *"VM Runtime on GDC builds on the KubeVirt open source project"* and lets you *"run VMs on top of Kubernetes in the same way that you run containers."* It supports multiple disks, VLAN-tagged Layer 2 networks, and disk import through the Containerized Data Importer (qcow2). **Live migration of VMs during cluster upgrades is documented as Preview.**
   - **The hypervisor is KVM.** The core banking vendor certifies **vSphere and Hyper-V only**.
3. **Behavior when disconnected.** Google's connectivity page states that GDC *"isn't intended to operate disconnected as nominal working mode."*

   | What | Disconnected behavior |
   |---|---|
   | Workloads, local RBAC, cluster DNS | Keep running |
   | Application management through the local Kubernetes API | Unlimited |
   | Creating or upgrading clusters | Not possible |
   | Adding nodes | Not possible (preflight checks need Google Cloud) |
   | The Connect gateway | Not available |
   | License validation | A grace period, *"after the grace period expires, components start to log errors"* |
   | Cloud Logging buffer | 4.5 hours per node |
4. **Pricing.** GDC (bare metal) is **$0.03288 per vCPU per hour**. *"If hyperthreading is enabled one CPU is equivalent to two vCPUs."* That is **about $48 per physical core per month** with hyperthreading on (about $24 with it off). *"VM Runtime on GDC … doesn't require an alternate SKU or additional pricing."* Admin-cluster and control-plane nodes are excluded. **Host OS subscriptions (RHEL) are extra.**
5. **Backup.** Veeam Kasten protects VMs on Kubernetes (KubeVirt), and Veeam Backup & Replication 13.1 added a KubeVirt proxy.
6. **Horizon** is not supported on KubeVirt or GDC. Omnissa lists vSphere, Nutanix AHV, and OpenShift.
7. **Migration.** Google documents deploying an existing VM by importing its disk image (conversion to qcow2). **There is no first-party, change-block-tracking migration from vSphere to VM Runtime.** Google's *Migrate to Virtual Machines* targets Compute Engine, not GDC.
8. **Lens: GDC air-gapped** is a separate, fully disconnected product on Google-supplied hardware, aimed at sovereign and defense customers. It would satisfy the invariant, but it is out of proportion to a regional bank, and it doesn't change the KVM certification problem.

## Consequence 1: A Certified Island for Core Banking ([ADR-022](../adr/ADR-022-gcp-certified-island.md))

The core vendor doesn't certify KVM, so **core banking (application tier + Oracle) cannot move to VM Runtime**. Under [ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md)'s exception, this track runs a **certified island** in each site. The least-cost certified option is **Windows Server 2025 Hyper-V failover clusters**:
- **licensing:** Windows Server Datacenter licences the bank already holds
- **vendor:** no extra hypervisor vendor
- **size:** about 16 hosts per site (the Oracle clusters + the core application servers)

The island also removes the Oracle licence question from this track: Oracle stays on Hyper-V (soft partitioning, 320 processor licences). The price is **two platforms to run, patch, and recover**.

## Component Mapping (all 26)

| # | Component | GDC implementation | Notes |
|---|---|---|---|
| P1 | Compute clusters | **Per site:** an admin cluster, plus user clusters for Tier 0 (non-core), PCI, and General (Tier 1/2 VMs + containers). There is no VDI cluster (see the VDI row). RHEL hosts | Non-core Tier 0 (payments gateways, API layer) runs on VM Runtime **if each vendor supports KVM images** |
| P2 | Storage | **An enterprise array through a CSI driver** (a GDC-qualified storage partner) | **The Fibre Channel array is refreshed, not retired**. KubeVirt VMs need shared CSI storage for HA and live migration |
| P3 | Oracle clusters | **On the certified island** (Hyper-V), with Data Guard | [ADR-022](../adr/ADR-022-gcp-certified-island.md) |
| P4 | SDN + microsegmentation | **Pod-network VMs:** Kubernetes NetworkPolicy. **VMs on VLAN (Layer 2) attachments** (needed to keep IPs and for appliances) are **not** subject to pod NetworkPolicy, so they are segmented by **network firewalls rendered from Git** | Two enforcement points. [ADR-024](../adr/ADR-024-gcp-network-and-segmentation.md) |
| P5 | Site edge | Existing next-generation firewalls. This track leans on them more heavily | |
| P6 | Kubernetes | **Native.** GKE on bare metal, the same API and tooling as GKE in Google Cloud | **The strongest developer platform of the tracks** |
| C1 | Governance plane | **Fleet** + **Config Sync** (GitOps) + **Policy Controller** (admission policy) across GDC and GKE in Google Cloud. **The certified island is outside the fleet**, governed separately (Arc-enabled servers or System Center) | **Partial.** Strong for everything that is a Kubernetes object, weak for the island |
| C2 | Site manager | The local Kubernetes API (`kubectl`/`virtctl`) and `bmctl` for each site | Local |
| C3 | Local identity | Local Kubernetes RBAC with an OIDC provider on premises (AD FS or Entra with a local fallback). Break-glass kubeconfigs in PAM | Local |
| C4 | Local repository | A local container registry mirror, a local VM image store, and RHEL Satellite | **Cluster upgrades need Google Cloud** |
| C5 | Policy pipeline | Git → Config Sync (VM definitions, NetworkPolicy, quotas) + firewall rendering for Layer 2 VMs | VMs as code, natively |
| C6 | CMDB sync | Fleet inventory API + Kubernetes → ServiceNow | |
| C7 | Licence service | **A grace period**, after which *"components start to log errors"* | Passes 7 days (with documented limits). Duration to be confirmed with Google |
| D1 | Platform API and catalog | **The Kubernetes API itself** (VM, namespace, and network objects), with Terraform for the fleet and ServiceNow approvals | |
| D2 | Image pipeline | Packer → qcow2 golden images in the local image store | |
| D3 | ServiceNow | ServiceNow → GitOps pull requests | |
| R1 | Database replication | Data Guard (on the island) | |
| R2 | Platform replication | **Storage-array replication** through the CSI vendor for stateful Tier-0/1 VMs, and **rebuild from Git + image** for stateless VMs | **No first-party VM replication** between GDC clusters |
| R3 | Recovery orchestrator | **Bank-built:** apply the Git manifests to the DC2 clusters, promote the array replicas, run groups G0–G6. The island is covered by the same orchestrator (Hyper-V Replica) | GitOps makes "recovery = apply" natural, but the wrapper is bank code |
| R4 | Immutable local backup | **Veeam Kasten** (KubeVirt VMs) + **Veeam B&R** (island) → hardened repositories | Two backup products |
| R5 | Isolated vault | Both feed Z-VAULT. Tier 1/2 copies go to Cloud Storage with Bucket Lock | |
| R6 | Clean room | A small isolated GDC cluster + a Hyper-V host in DC2 | Built by the bank |
| O1 | Telemetry | Cloud Logging/Monitoring (buffers are short: 4.5 hours for logs) **and** a local Loki/Prometheus stack forwarding to **Sentinel** | Sentinel stays the SIEM, so there is a cross-vendor pipeline |
| O2 | Capacity and cost | Fleet metrics + a local stack | |
| O3 | Scanning | Policy Controller constraints + an in-guest scanner | |
| L1 | Landing zone | **Google Cloud** (the natural pair for fleet), with Entra ID through Workforce Identity Federation | The AWS account is closed and its data purged |
| — | VDI | **Azure Virtual Desktop or Windows 365 in Azure** | Horizon isn't supported on KubeVirt. This adds a *third* vendor |

## The Nine Questions

| # | Question | GDC answer |
|---|---|---|
| 1 | Core banking certification | **Not certified (KVM).** A **certified island** on Hyper-V is required |
| 2 | Oracle partitioning | On the island: **soft**, unchanged (320 licences) |
| 3 | Horizon VDI | **Not supported.** VDI moves to AVD or Windows 365 in Azure |
| 4 | Backup | **Veeam Kasten** for VMs + Veeam B&R for the island. Two products, one vault |
| 5 | Disconnected-week test | **Passes for running and operating VMs** through the local Kubernetes API. **Fails for platform lifecycle** (no upgrades, no node adds). The licence grace period needs confirming. Google says disconnection *isn't* the nominal mode |
| 6 | Microsegmentation | **Partial.** NetworkPolicy for pod-network VMs, and network firewalls for Layer 2 VMs |
| 7 | Kubernetes + API | **Best of the tracks.** GKE-native, GitOps, and VMs as code |
| 8 | Migration tooling | **Weakest.** Disk export, qcow2 conversion, and import. No change-block tracking or warm migration |
| 9 | Governance reach | **Strong for the fleet** (GDC + GKE in cloud, GitOps and policy). **The island sits outside it** |

## What This Track Gets Right, and What It Costs

**Strengths:**
- **Developer platform:** the digital team gets the same GKE on premises and in the cloud, with VMs and containers declared in Git and reconciled by Config Sync. That is the purest form of [ADR-005](../adr/ADR-005-platform-api-and-portability.md).
- **Portability:** KubeVirt is open source, so VM definitions and images move to other KubeVirt platforms (OpenShift Virtualization, for example).

**Weaknesses:**
- **The certified island:** it brings a second platform, a second backup product, and a second recovery path.
- **VDI:** it has to move to a third vendor.
- **The weakest migration tooling** for 2,000+ VMs.
- **Live migration** for VMs is still Preview.
- **Cost:** per-vCPU pricing ($48 per core per month with hyperthreading) on every core under management, plus RHEL on every host, plus a storage array that the other tracks retire.
- **Disconnection is tolerated, not designed for.** Upgrades and node adds stop.

## Alignment Check against Steps 4–5

| Expectation | GDC reality | Treatment |
|---|---|---|
| One primary private cloud ([ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md)) | GDC + a Hyper-V island | **Partial.** The certified-island exception is used |
| Recovery as code ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md), [ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)) | GitOps apply + array replication + a bank-built orchestrator | **Met, with the most build effort** |
| Cyber recovery ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | Kasten + B&R into one vault. A bank-built clean room | **Met, with two products** |
| Govern centrally, operate locally ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)) | Operate locally: VMs yes, platform lifecycle no. Govern: fleet, but not the island | **Partial** |
| Platform API and portability ([ADR-005](../adr/ADR-005-platform-api-and-portability.md)) | Kubernetes-native, KubeVirt open source | **Strongest** |
| Zones as code ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) | NetworkPolicy + firewalls for Layer 2 VMs | **Partial.** Two enforcement points |

## Diagram

See [`diagrams/gcp-implementation-architecture.md`](../diagrams/gcp-implementation-architecture.md) (Mermaid reference source, to be hand-drawn).

## Known Deferred Items

- The vCPUs under management (hyperthreading on or off), the RHEL host count, the island size, the CSI array sizing, and the licence grace-period duration are inputs to Step 13.
- A vendor-by-vendor check of which Tier-0 appliances ship KVM images is also needed.
