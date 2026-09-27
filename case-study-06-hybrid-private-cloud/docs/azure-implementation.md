# Step 7: Azure Local + Azure Arc Implementation

## Purpose of This Step

This is the second of four independent mappings of the 26 [Step 5](logical-design.md) components, after [VCF](vcf-implementation.md). It maps them onto **Azure Local** (formerly Azure Stack HCI: Hyper-V, Storage Spaces Direct, and SDN on validated hardware) managed through **Azure Arc**, with the public-cloud landing zone in Azure. It answers the nine questions every track must answer.

The question this track has to settle is whether a platform **managed from Azure** can meet an invariant that says **Tier 0 must be operated without any cloud control plane**.

## Findings from Current Documentation (September 2026)

1. **A 30-day sync requirement.** *"Azure Local must sync successfully with Azure once per 30 consecutive days."* If it doesn't, the instance is *"Out of policy"* and enters reduced functionality: *"all current VMs continue to run normally. However, new VMs can't be created until Azure Local can sync again."*
2. **Arc-managed VMs are operated from Azure.** For Azure Local VMs enabled by Azure Arc, Microsoft's supported-operations page says to start, restart, and stop VMs *"only via the Azure portal or the Azure CLI. Don't use the local tools."* Local tools *are* supported for node-level operations such as live migration within a cluster and checkpoints.
   - **Consequence:** with Azure unreachable, an operator has no *supported* way to start or stop an Arc-managed Tier-0 VM.
3. **Disconnected operations exist** (Azure Local 2602 and later). They provide a local Azure portal, ARM, RBAC, Azure Policy, Key Vault, and Azure Local VMs. AKS is still in preview there. They need a **dedicated management cluster**, hardware from the Premier catalog, and an **eligibility application** (a "valid business need", with approval in about 10 business days). They are priced as a separate tier.
4. **Pricing** (from 25 June 2026):

   | Tier | Host fee |
   |---|---|
   | L1 hyperconverged | **$10 per physical core per month** |
   | L2 with external SAN | $20.10 |
   | L3 disconnected | Priced separately |

   **Azure Hybrid Benefit waives the L1 host fee** for Windows Server Datacenter licences with Software Assurance, which **Alder Valley already holds** (`current-state.md` §6). AKS on Azure Local is included. There is a 60-day trial.
5. **Disaster recovery.** *"You can use [Hyper-V Replica] to replicate VMs between two separate Azure Local clusters"*, every 30 seconds, 5 minutes, or 15 minutes, with test, planned, and unplanned failover. **Caveat:** an Arc-managed VM *"fails over … as an unmanaged VM"* and must be re-registered to be managed from Azure. Veeam, Cohesity, Commvault, and Rubrik are documented partners.
6. **Horizon is not supported on Hyper-V.** Omnissa's 2026 platform statements list vSphere, Nutanix AHV, and OpenShift, not Hyper-V or Azure Local. VDI on this track means **Azure Virtual Desktop** (on Azure Local or in Azure).
7. **Migration.** Azure Migrate supports agentless migration of VMware VMs to Azure Local (announced November 2025), keeping static IPs and keeping migration traffic local.

## The Central Design Choice: How Tier 0 Is Managed ([ADR-016](../adr/ADR-016-azure-tier0-local-management-mode.md))

Findings 2 and 3 leave three ways to run Tier 0 on Azure Local:

| Option | Disconnected-week test | Assessment |
|---|---|---|
| a. **Arc-managed Azure Local VMs** (the default) | **Fails.** Start and stop are supported only through Azure | Rejected for Tier 0. Used for Tier 1 and Tier 2 |
| b. **Disconnected operations** for the Tier-0 instances | **Passes.** A local portal and ARM | Rejected *for now*. It needs a dedicated management cluster in each site, eligibility approval, and a separate price tier. It isolates Tier 0 from Azure governance entirely (by design it has *no public-cloud connectivity*). It remains the fallback |
| c. **Locally managed Hyper-V VMs** on connected Tier-0 instances. The VMs are not enrolled in Azure Local VM management. They are operated with Failover Cluster Manager, Windows Admin Center, and PowerShell, and governed through **Arc-enabled servers** in each guest | **Passes.** Lifecycle, failover (Hyper-V Replica + Data Guard), and guest patching are all local | **Selected.** The instances stay connected for platform lifecycle and governance. **No Tier-0 operation needs Azure.** The cost is giving up the Azure-portal lifecycle for 260 VMs, which is exactly the dependency the invariant forbids |

## Component Mapping (all 26)

| # | Component | Azure Local + Arc implementation | Notes |
|---|---|---|---|
| P1 | Compute clusters | **Separate Azure Local instances per site:** Tier-0/PCI, Oracle, General (Tier 1/2 + AKS), and VDI | Independent sites. Each instance has up to 16 nodes |
| P2 | Storage | **Storage Spaces Direct** (hyperconverged, L1 pricing). **The DC1 Fibre Channel array is retired**, subject to an Oracle batch proof of concept | External SAN would move the host fee to L2 ($20.10) |
| P3 | Oracle clusters | A dedicated Oracle instance in each site, running **locally managed Hyper-V VMs** | **Soft partitioning**, as on VMware. The count is unchanged unless consolidated |
| P4 | SDN + microsegmentation | **Tier-0 and Oracle instances:** SDN managed with on-premises tools (Network Controller, **Datacenter Firewall** ACLs through PowerShell). **General instances:** SDN enabled by Arc with **network security groups**. Both are rendered from Git | Included in the platform. **No add-on fee**, unlike vDefend |
| P5 | Site edge | Existing next-generation firewalls | |
| P6 | Kubernetes | **AKS on Azure Local** (included), on the General instances | AKS lifecycle needs Azure. Tier-2 only, which is acceptable |
| C1 | Governance plane | **Azure Arc + Azure Policy + Defender for Cloud + Update Manager (reporting) + Resource Graph** across the Azure Local instances, **every guest (Arc-enabled servers)**, and the Azure landing zone | **The strongest central governance of the tracks**: one plane |
| C2 | Site manager | **Tier 0:** Windows Admin Center, Failover Cluster Manager, PowerShell. **Tier 1/2:** Azure portal/CLI | Local for Tier 0 by design (ADR-016) |
| C3 | Local identity | On-premises AD (the Azure Local nodes are domain-joined). Break-glass accounts vaulted in PAM | Local |
| C4 | Local repository | WSUS/Configuration Manager + Satellite for guests. **Azure Local solution updates come through Azure** | Platform updates are deferred during a disconnect. Guest patching is local |
| C5 | Policy pipeline | Git + Terraform (azurerm/azapi for Azure Local VMs, NSGs, and AKS) + PowerShell DSC/Ansible for the Tier-0 SDN | |
| C6 | CMDB sync | Azure Resource Graph → ServiceNow (Service Graph Connector) | |
| C7 | Licence service | **A 30-day Azure sync** (existing VMs keep running if it's missed) | **Passes 7 days.** Failure mode: no new VMs, not a stop to operations |
| D1 | Platform API and catalog | ARM/Terraform for Azure Local VMs, logical networks, and AKS. ServiceNow approvals | Tier-0 changes go through the change pipeline with PowerShell |
| D2 | Image pipeline | Packer → Azure Local VM images (and a VHDX library for Tier 0) | |
| D3 | ServiceNow | Azure ↔ ServiceNow | |
| R1 | Database replication | Oracle Data Guard | Unchanged |
| R2 | Platform replication | **Hyper-V Replica** DC1→DC2 (every 30 seconds for Tier 0, 5 minutes for Tier 1) | For Tier 1, re-registration after failover is automated in the plan |
| R3 | Recovery orchestrator | **Bank-built**: Ansible + PowerShell executing the Git plans ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)) from DC2 | **No on-premises SRM equivalent.** Azure Site Recovery targets Azure, not a second on-premises site |
| R4 | Immutable local backup | **Veeam** for Hyper-V/Azure Local (a documented partner), with hardened repositories | Same product as today |
| R5 | Isolated vault | Veeam → Z-VAULT. Tier 1/2 copies to **Azure Blob immutable storage** with customer-managed keys | |
| R6 | Clean room | A small, isolated Azure Local or Hyper-V cluster in DC2 (Z-IRE) | Built by the bank. There is no packaged clean-room workflow like VCF's Live Recovery |
| O1 | Telemetry | Azure Monitor Agent → Log Analytics → **Sentinel** (the bank's existing SIEM). The agent buffers locally | Native pairing |
| O2 | Capacity and cost | Azure Monitor insights + Cost Management (for the landing zone) | |
| O3 | Scanning | Defender for Servers (vulnerability and CIS) through Arc | |
| L1 | Landing zone | **Azure** (Enterprise-Scale), the natural pair | The 2025 AWS account is closed and its data purged |
| — | VDI | **Azure Virtual Desktop on Azure Local** for the contact center and back office. Omnissa Horizon is retired | [ADR-020](../adr/ADR-020-azure-vdi.md) |

## The Nine Questions

| # | Question | Azure Local answer |
|---|---|---|
| 1 | Core banking certification | **Certified** (Hyper-V, including Azure Local). No island needed |
| 2 | Oracle partitioning | **Soft**, as on VMware. 320 processor licences unless consolidated |
| 3 | Horizon VDI | **Not supported.** It is replaced by **Azure Virtual Desktop** on Azure Local. VDI is Tier 1, and the AVD control plane is in Azure |
| 4 | Backup | **Veeam supported** (a documented partner) |
| 5 | Disconnected-week test | **Passes for Tier 0 by design choice** (locally managed Hyper-V VMs). Tier 1/2 Arc VMs keep running, but lifecycle operations wait. Solution updates wait. The 30-day sync never stops operations |
| 6 | Microsegmentation in both sites | **Yes, included** (Datacenter Firewall and NSGs). There are two management modes, both rendered from Git |
| 7 | Kubernetes + API | **AKS on Azure Local** (included) + ARM/Terraform |
| 8 | Migration tooling | **Azure Migrate** (VMware → Azure Local, agentless), or Veeam restore to Hyper-V. Tier 0 moves as locally managed VMs |
| 9 | Governance reach | **Strongest.** Arc + Policy + Defender over the platform, all guests, and the Azure landing zone, with Sentinel already in place |

## What This Track Gets Right, and What It Costs

**Strengths:**
- **Licensing economics:** Azure Hybrid Benefit **waives the host fee** on licences the bank already owns (Windows Server Datacenter with SA). Microsegmentation and AKS are included.
- **Governance:** one plane, integrated with the bank's existing Entra ID, Sentinel, and M365.
- **Certification:** core banking is certified on Hyper-V.

**Weaknesses:**
- **Tier 0 must be run outside Azure Local's own VM management** to meet the invariant. That is a supported but second-class mode, and it gives up the portal lifecycle for exactly the most important VMs.
- **No packaged DR orchestrator** between two on-premises sites. The bank builds and owns the orchestrator ([ADR-017](../adr/ADR-017-azure-recovery.md)).
- **VDI changes product** (from Horizon to AVD), which is a user-facing change for 1,400 staff.
- **Platform updates depend on Azure.** Security patches for the hosts can't be applied during a long disconnect.

## Alignment Check against Steps 4–5

| Expectation | Azure Local reality | Treatment |
|---|---|---|
| One private cloud in two independent sites ([ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md)) | Instances per site and role | **Met** |
| Recovery as code ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md), [ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)) | Hyper-V Replica + Data Guard + a bank-built orchestrator | **Met, with more build effort** than VCF |
| Cyber recovery ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | Veeam + vault + a bank-built clean room | **Met** |
| Govern centrally, operate locally ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)) | Govern centrally: **strongest**. Operate locally: **only by running Tier 0 outside Arc VM management** | **Met by design choice** |
| Platform API and portability ([ADR-005](../adr/ADR-005-platform-api-and-portability.md)) | ARM/Terraform. VHDX images are convertible | **Met** |
| Zones as code in both sites ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) | Datacenter Firewall + NSGs, included | **Met, with two renderers** |

## Diagram

See [`diagrams/azure-implementation-architecture.md`](../diagrams/azure-implementation-architecture.md) (Mermaid reference source, to be hand-drawn).

## Known Deferred Items

- Node counts per instance, the AVD session-host sizing, whether disconnected operations should be re-evaluated for Tier 0 at GA pricing, and Azure Hybrid Benefit eligibility for every core are Step 13 inputs.
- The Oracle-on-Storage-Spaces-Direct batch proof of concept is needed before the Fibre Channel array is retired.
