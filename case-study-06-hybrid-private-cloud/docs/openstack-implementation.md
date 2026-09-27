# Step 9: OpenStack Implementation (open private cloud)

## Purpose of This Step

This is the fourth and last mapping of the 26 [Step 5](logical-design.md) components, after [VCF](vcf-implementation.md), [Azure Local + Arc](azure-implementation.md), and [Google Distributed Cloud](gcp-implementation.md). It maps them onto **OpenStack**, as the open-source private-cloud alternative from a **commercially supported distribution**.

**Distribution choice: Red Hat OpenStack Services on OpenShift (RHOSO) 18.** Alder Valley already runs RHEL with Satellite and holds a Red Hat relationship. Canonical OpenStack was the alternative considered, and it is noted where it would differ.

This track is the purest test of driver 2: **how much independence can an open platform buy, and what does it cost in skills?**

## Findings from Current Documentation (September 2026)

1. **Architecture.** In RHOSO 18, the OpenStack control plane runs **as pods on an OpenShift cluster** (*"Nova runs as several pods in a highly available setup"*). The data plane is RHEL compute nodes with **KVM**.
2. **Subscription model.** RHOSO is licensed **per socket-pair**: *"a single server with up to two populated sockets."*
   - **Ceph storage** is an add-on: *"a Red Hat Ceph Storage add-on subscription is required for each OpenStack compute-node subscription."*
   - RHEL guests are subscribed separately. Windows guests are covered by the bank's existing Windows Server Datacenter licences on the host cores.
   - There is **no licence enforcement** that stops running workloads if a subscription lapses, unlike VCF ([ADR-012](../adr/ADR-012-vcf-control-plane-and-governance.md)). The customer loses support and updates, not operations.
3. **Migration tooling.** The **VMware migration kit** (os-migrate) is *Red Hat Ansible Certified Content*. It uses nbdkit with **VMware Change Block Tracking** to *"approach a zero downtime"* with warm, multi-cycle migration, and it has a virt-v2v path. **It is the strongest migration tooling of the three non-VMware tracks.**
4. **Backup.** *"Veeam Backup & Replication … does not offer agentless backup for OpenStack virtual machines"*, and support *"remains absent from their short-term plans"* (March 2026). **Trilio for OpenStack** is purpose-built and documents installation on RHOSO. This is a **backup product change**.
5. **Hypervisor = KVM.** The core banking vendor certifies vSphere and Hyper-V only, so **a certified island is needed**, as on the GDC track ([ADR-022](../adr/ADR-022-gcp-certified-island.md)).
6. **Horizon** is not supported on OpenStack. Omnissa's 2026 platform list includes *OpenShift* (that is, OpenShift Virtualization), which is a different virtualization stack from OpenStack Nova.

## Component Mapping (all 26)

| # | Component | OpenStack (RHOSO 18) implementation | Notes |
|---|---|---|---|
| P1 | Compute clusters | **One OpenStack region per site** (independent control planes on OpenShift in each site). Host aggregates / availability zones for Z0, PCI, and General | No shared control plane across sites |
| P2 | Storage | **Ceph** per site (block through Cinder RBD, images through Glance), hyperconverged or dedicated storage nodes | The FC array is retired. Ceph operations are a new skill |
| P3 | Oracle clusters | **On the certified island** (Windows Server Hyper-V), with Data Guard | [ADR-027](../adr/ADR-027-openstack-certified-island-and-recovery.md) |
| P4 | SDN + microsegmentation | **Neutron with OVN:** stateful **security groups** enforced on every hypervisor, default-deny ingress, rules from Git through the Terraform OpenStack provider | **Included.** It covers all VMs, including those on provider (VLAN) networks |
| P5 | Site edge | Existing next-generation firewalls. Neutron routers and provider networks | |
| P6 | Kubernetes | **OpenShift on OpenStack** (installer-provisioned) for the digital team | An extra OpenShift subscription. Magnum was rejected as weaker to support |
| C1 | Governance plane | **Satellite + Ansible Automation Platform** (hosts, guest patching, compliance) + OpenStack resource inventory + **Arc-enabled servers in guests** for the Azure landing zone | **Partial.** Several consoles |
| C2 | Site manager | The OpenStack APIs and CLI, and the Horizon dashboard (OpenStack's web UI, unrelated to Omnissa Horizon), **per site** | Fully local |
| C3 | Local identity | Keystone federated to on-premises AD/LDAP. Break-glass accounts in PAM | Local |
| C4 | Local repository | Satellite (RHEL content), a local image registry mirror (for the OpenShift-hosted control plane), and Glance images | **Disconnected deployment and updates are supported through mirrored content** |
| C5 | Policy pipeline | Git + Terraform (OpenStack provider, one of the most mature) + Ansible | |
| C6 | CMDB sync | OpenStack APIs + Satellite → ServiceNow | |
| C7 | Licence service | **None that affects operations** (subscription = support and updates) | **Strongest of the tracks** |
| D1 | Platform API and catalog | **Native OpenStack APIs** (compute, network, volume, image), with Terraform and ServiceNow approvals. Projects and quotas for self-service | OpenStack's native strength |
| D2 | Image pipeline | Packer → Glance (qcow2/raw) | |
| D3 | ServiceNow | ServiceNow → Terraform/Ansible | |
| R1 | Database replication | Data Guard (on the island) | |
| R2 | Platform replication | **Ceph RBD mirroring** (snapshot-based, on a schedule, for example every 5 minutes) DC1→DC2 for stateful Tier-0/1 volumes | Asynchronous. Instances are re-created in DC2 from Terraform |
| R3 | Recovery orchestrator | **Bank-built:** Terraform/Ansible re-creates instances in the DC2 region on the mirrored volumes and runs groups G0–G6. The island uses Hyper-V Replica | **No packaged OpenStack DR orchestrator** |
| R4 | Immutable local backup | **Trilio for OpenStack** + Veeam (island) → hardened repositories | Two backup products |
| R5 | Isolated vault | Both feed Z-VAULT | |
| R6 | Clean room | A small isolated OpenStack project/region + a Hyper-V host in DC2 | Built by the bank |
| O1 | Telemetry | OpenStack and OpenShift logging → **Sentinel** | |
| O2 | Capacity and cost | Placement API + Prometheus | |
| O3 | Scanning | Satellite/Insights compliance + an in-guest scanner | |
| L1 | Landing zone | **Cloud-neutral**, paired with **Azure** by default (Entra ID, Sentinel, M365) | The AWS account is closed |
| — | VDI | **AVD or Windows 365 in Azure** | Horizon isn't supported on OpenStack |

## The Nine Questions

| # | Question | OpenStack answer |
|---|---|---|
| 1 | Core banking certification | **Not certified (KVM).** A certified Hyper-V island is required |
| 2 | Oracle partitioning | On the island: **soft**, unchanged |
| 3 | Horizon VDI | **Not supported.** VDI moves to AVD/W365 in Azure |
| 4 | Backup | **Veeam: no.** **Trilio** for OpenStack + Veeam for the island |
| 5 | Disconnected-week test | **Passes, strongly.** Everything is self-hosted, updates come from mirrored content, and nothing is licence-enforced |
| 6 | Microsegmentation | **Yes, included.** OVN security groups on every hypervisor, including VLAN-attached VMs |
| 7 | Kubernetes + API | **Mature native APIs + Terraform.** OpenShift on OpenStack for containers (extra subscription) |
| 8 | Migration tooling | **Good.** VMware migration kit with CBT and warm migration (Ansible Certified Content) |
| 9 | Governance reach | **Partial.** Satellite/AAP on premises, Arc guest agents toward the Azure landing zone |

## What This Track Gets Right, and What It Costs

**Strengths:**
- **The most independence:** open source, a distribution that could be swapped (RHOSO ↔ Canonical), and **no licence stop** (finding 2).
- **Disconnected operation:** fully self-hosted, the strongest of the tracks.
- **Microsegmentation:** included and distributed.
- **APIs and Terraform:** the most mature of the tracks.

**Weaknesses:**
- **The certified island:** two platforms.
- **Skills:** OpenStack, OpenShift (for its control plane), and Ceph together are the steepest learning curve for a VMware/Windows team (driver 5, NFR-12). A partner managed service is needed in practice.
- **Tooling changes:** the backup product changes (Trilio), VDI moves to a third vendor, and there is no packaged DR orchestrator.
- **Several subscription lines:** RHOSO, Ceph, OpenShift for applications, and Trilio.

## Alignment Check against Steps 4–5

| Expectation | OpenStack reality | Treatment |
|---|---|---|
| One primary private cloud ([ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md)) | OpenStack + a Hyper-V island | **Partial** (the island exception) |
| Recovery as code ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md), [ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)) | Ceph mirroring + Terraform re-creation + a bank-built orchestrator | **Met, with a heavy build** |
| Cyber recovery ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | Trilio + Veeam into one vault | **Met, with two products** |
| Govern centrally, operate locally ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)) | Operate locally: **strongest**. Govern centrally: **partial** | **Partial** |
| Platform API and portability ([ADR-005](../adr/ADR-005-platform-api-and-portability.md)) | Open APIs, qcow2 images, distribution-portable | **Strongest on openness** |
| Zones as code ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) | OVN security groups, included | **Met** |

## Diagram

See [`diagrams/openstack-implementation-architecture.md`](../diagrams/openstack-implementation-architecture.md) (Mermaid reference source, to be hand-drawn).

## Known Deferred Items

- The socket-pair count, the Ceph add-on count, OpenShift subscriptions, Trilio licensing, and the managed-service partner cost are Step 13 inputs.
- The KVM images for the payments appliances are to be checked vendor by vendor.
