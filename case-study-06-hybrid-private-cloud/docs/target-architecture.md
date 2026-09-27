# Step 11: Recommended Platform and Target Architecture

## Confirmed Platform

**Azure Local + Azure Arc**, per [ADR-031](../adr/ADR-031-platform-selection.md). It scored 3.95/5.00 (79.0%) against VCF at 3.725, OpenStack at 3.15, and Google Distributed Cloud at 2.775 in [Step 10](decision-matrix.md).

The selection is **conditional on gate G0 by M4 (January 2027)**, before the VCF renewal decision. If the Tier-0 disconnected-week proof of concept fails, or if Broadcom's offer drops below the Step 13 threshold, ADR-031 reverses to the VCF track.

This step:
- states the target architecture at a glance
- builds G0 into it
- traces each forcing function and the invariant to the mechanism that closes it
- lists what is carried forward

It doesn't re-argue the choice.

## Target Architecture at a Glance

**Sites (two independent failure domains, [ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md), [ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md))**
- **DC1 (Pittsburgh) and DC2 (Columbus)** each run four **Azure Local instances**: Tier-0/PCI, Oracle, General, and VDI ([ADR-015](../adr/ADR-015-azure-local-instance-topology.md)).
- Hyperconverged Storage Spaces Direct on validated NVMe nodes (L1). The host fee is **waived through Azure Hybrid Benefit**.
- The DC1 Fibre Channel array is retired, subject to G0-3.

**Tier 0 (operate locally, [ADR-016](../adr/ADR-016-azure-tier0-local-management-mode.md))**
- Core banking, the payments gateways, card management, and the API layer run as **locally managed Hyper-V VMs**, operated with Windows Admin Center, Failover Cluster Manager, and PowerShell from the pipeline.
- Oracle runs on the dedicated Oracle instances, the licence boundary of [ADR-007](../adr/ADR-007-oracle-cluster-and-licence-boundary.md).
- Every guest carries the **Arc-enabled servers** agent for governance. Patches come from local WSUS/Configuration Manager and Satellite.

**Tier 1, Tier 2, and Kubernetes**
- **Arc-managed Azure Local VMs** are provisioned through Terraform with ServiceNow approvals. Standard VMs take under an hour ([ADR-019](../adr/ADR-019-azure-governance-and-delivery.md)).
- **AKS on Azure Local** replaces the three Rancher clusters.

**Recovery ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md), [ADR-017](../adr/ADR-017-azure-recovery.md))**
- Oracle **Data Guard**, and **Hyper-V Replica** DC1→DC2 (30 seconds for Tier 0, 5 minutes for Tier 1).
- A **bank-built orchestrator** in DC2 runs the Git recovery plans (G0–G6).
- A **daily readiness job** can fail any Tier-0 change that breaks recoverability.

**Cyber recovery ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md))**
- Veeam immutable repositories in each site.
- An isolated vault with its own administrative domain.
- A clean-room Hyper-V cluster in DC2.
- Tier-1/2 vault copies go to Azure immutable Blob storage with customer-managed keys.

**Network ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md), [ADR-018](../adr/ADR-018-azure-network-and-segmentation.md))**
- Eight zones. **Datacenter Firewall** (managed on premises) protects Tier 0 and the Oracle instances, and **NSGs** protect the General instances.
- Both are rendered from Git and identical in both sites, with a daily parity check. **PCI segmentation now covers DC2.**

**Governance ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md), [ADR-019](../adr/ADR-019-azure-governance-and-delivery.md))**
- **Azure Arc** over every instance and every guest, with Azure Policy, Defender for Cloud, Update Manager reporting, and Resource Graph feeding ServiceNow.
- **Sentinel** remains the SIEM.
- The **Azure landing zone** hosts dev/test, analytics, the digital team's ML work, and non-Tier-0 vault copies. **The 2025 AWS account is closed and its data purged.**

**Desktops ([ADR-020](../adr/ADR-020-azure-vdi.md))**
- **Azure Virtual Desktop on Azure Local** replaces Horizon after a contact-center pilot.

See [`diagrams/azure-implementation-architecture.md`](../diagrams/azure-implementation-architecture.md) for the reference diagram from which the hand-drawn target diagram will be made.

## Gate G0, Designed In

| G0 check ([ADR-031](../adr/ADR-031-platform-selection.md)) | Where it lives in the architecture | If it fails |
|---|---|---|
| **1. Tier-0 disconnected-week proof of concept** | A 4-node Tier-0 instance pair in a lab. Azure is cut off for 7 days while VMs are started and stopped, a Hyper-V Replica + Data Guard failover runs, and a patch is rolled back. Microsoft confirms the mode is supported, in writing | Azure resilience falls to 2.5, so **VCF is selected**. The VCF track design (ADR-009 to ADR-014) is ready |
| **2. Broadcom's best offer** | The commercial workstream. Azure Local is presented as a costed, tested alternative, and that leverage is the point | If the offer is below the Step 13 threshold, **VCF is selected** |
| **3. Oracle on Storage Spaces Direct** | A batch proof of concept on the Oracle instance design | The Oracle instances use external SAN (L2 host fee). The design is otherwise unchanged |
| **4. AVD contact-center pilot** | 50 seats on the VDI instance | Those users move to Windows 365 or AVD in Azure |

**Neither outcome wastes Phase 0 work.** The platform-neutral work runs before G0 and survives either platform:
- recovery plans in Git
- the zone intent model
- inventory reconciliation
- vault and clean-room design
- Oracle Data Guard transport sizing
- closing the AWS account

## Tracing Each Forcing Function to the Mechanism That Closes It

1. **The VMware renewal (31 March 2027).**
   - **Mechanism:** a tested, costed Azure Local alternative *before* the renewal (G0). A **short VCF term** covers the migration. **Azure Hybrid Benefit** waives the new platform's host fee on licences already owned.
   - **Result:** the bank either leaves VCF on its own timeline or renews at a price set with a credible alternative on the table. Either way it no longer negotiates without leverage.
2. **The resilience MRA.**
   - **Mechanism:** recovery as code, which takes each cause of the May 2026 failure in turn:
     - the orchestrator enforces dependency order
     - firewall policy rendered identically to both sites prevents DC2 drift
     - Data Guard transport sized for the batch peak, with a lag alert, prevents redo lag
   - **Plus:** Hyper-V Replica every 30 seconds, a daily readiness gate, **evidence reports timed against a 3-hour budget**, and an isolated vault with a clean room for the backup finding.
   - **Result:** a successful, evidenced Tier-0 recovery before the Q4 2027 examination (Step 12 schedules at least two).
3. **Hardware end of support (December 2027).**
   - **Mechanism:** the refresh is spent **once**, on Azure Local validated nodes. The Fibre Channel array is retired, subject to G0-3.
   - **Result:** no like-for-like VMware refresh followed by a second migration.
4. **Delivery teams routing around the data center.**
   - **Mechanism:** Terraform and a ServiceNow catalog (a VM in under an hour, a namespace in under an hour), **AKS on Azure Local** replacing the shadow Rancher clusters, and a governed Azure landing zone replacing the AWS account.
   - **Result:** the incentive to route around the platform disappears, and so does the re-identifiable data.
5. **The invariant (Tier 0 operates, fails over, and patches without any vendor cloud).**
   - **Mechanism:**
     - Tier 0 is locally managed Hyper-V ([ADR-016](../adr/ADR-016-azure-tier0-local-management-mode.md)) with local identity and repositories.
     - The orchestrator runs in DC2.
     - Datacenter Firewall is managed on premises.
     - Azure Local's 30-day sync only blocks *new* VMs, never running ones.
   - **Proof:** the disconnected-week drill runs **before** the decision (G0-1) and **every year after** ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)).

## NFR Coverage Summary

| NFR | Met by |
|---|---|
| NFR-1 Recovery objectives | Data Guard + Hyper-V Replica (30 s), recovery as code, a 3-hour budget, tests twice a year + monthly partial tests |
| NFR-2 Availability 99.95% | Live migration within instances, rolling solution updates per instance, Tier 0 isolated in its own instances |
| NFR-3 Disconnected operation (≥ 7 days) | Locally managed Tier 0, local identity and repositories, DC2 orchestrator. Proven by G0-1 and an annual drill |
| NFR-4 Batch performance | Storage Spaces Direct NVMe for Oracle, subject to G0-3 (external SAN fallback) |
| NFR-5 Scale | Instances of up to 16 nodes per role and site, sized in Step 13 |
| NFR-6 Security and compliance | Datacenter Firewall/NSGs in both sites, PCI scope in DC2, Defender for Cloud (CIS), PAM with no unmanaged local accounts |
| NFR-7 Backup and cyber recovery | Veeam immutable repositories, an isolated vault, a clean room, quarterly restore tests |
| NFR-8 Inventory and configuration | Arc on every instance and guest, Azure Policy, Resource Graph → ServiceNow daily |
| NFR-9 Provisioning | Terraform + a ServiceNow catalog (under 1 hour for a VM or namespace) |
| NFR-10 Cost | Host fee waived through Azure Hybrid Benefit, microsegmentation and AKS included. **Tested in [Step 13](cost-and-risk-analysis.md)** |
| NFR-11 Exit and portability | VHDX images, Git plans, Terraform modules, and an annual exit test (a Tier-1 service moved off the platform) |
| NFR-12 Operability | Hyper-V close to the team's Windows depth. Up to 4 hires (Azure Local and automation) |

## What This Step Carries Forward, Not Resolves

- **[Step 12](migration-roadmap.md):**
  - the VCF bridge term and size from 1 April 2027
  - G0 timing (M1–M4)
  - the migration waves (Tier 2 first, Tier 0 last, after two successful recovery tests)
  - the Q4 2027 examination evidence plan
  - the AVD rollout
  - closing the AWS account
  - hardware delivery against December 2027
- **[Step 13](cost-and-risk-analysis.md):**
  - the five-year TCO against the status-quo path (VCF renewal + like-for-like refresh)
  - the **Broadcom threshold price** for G0-2
  - the Oracle consolidation lever
  - the consolidated risk register, including Microsoft concentration
