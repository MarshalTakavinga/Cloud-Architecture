# Step 10: Decision Matrix

## Method

The four tracks from Steps 6–9 are scored against the **six weighted criteria recorded in `requirements.md`** before any platform work began. Scores run from 1 to 5, and each is justified from the track documents. Totals and the sensitivity analysis were computed in Python. As in Case Studies 4 and 5, the criteria were not changed after the tracks were known.

| # | Criterion | Weight | Traces to |
|---|---|---|---|
| 1 | Resilience and disconnected operation | 25% | Driver 1; the invariant; NFR-1 to NFR-3, NFR-7 |
| 2 | Workload compatibility (core certification, Oracle, Horizon, appliances) | 20% | Constraints; driver 2 |
| 3 | Cost and licensing exposure (directional until Step 13) | 20% | Driver 2; NFR-10 |
| 4 | Hybrid governance and operations | 15% | Driver 3; NFR-8, NFR-12 |
| 5 | Developer platform | 10% | Driver 4; NFR-9 |
| 6 | Exit, portability, and skills | 10% | Driver 5; NFR-11, NFR-12 |

## Scores

| Criterion (weight) | VCF | Azure Local + Arc | Google Distributed Cloud | OpenStack (RHOSO) |
|---|---|---|---|---|
| 1. Resilience and disconnected (25%) | **4.5** | 3.5 | 2.5 | 3.5 |
| 2. Workload compatibility (20%) | **5** | 4 | 2 | 2.5 |
| 3. Cost and licensing exposure (20%) | 2 | **4.5** | 2.5 | 3.5 |
| 4. Hybrid governance and operations (15%) | 3 | **4.5** | 3 | 2.5 |
| 5. Developer platform (10%) | 4 | 3.5 | **5** | 4 |
| 6. Exit, portability, and skills (10%) | **3.5** | **3.5** | 3 | 3 |
| **Weighted total** | 3.725 (74.5%) | **3.95 (79.0%)** | 2.775 (55.5%) | 3.15 (63.0%) |

## Justification by Criterion

1. **Resilience and disconnected operation (25%)**
   - **VCF (4.5):** everything runs locally, including packaged DR orchestration and an on-premises clean room (Live Recovery). The deduction is for add-on dependence.
   - **Azure (3.5):** it passes only *by design choice*, running Tier 0 as locally managed Hyper-V VMs ([ADR-016](../adr/ADR-016-azure-tier0-local-management-mode.md)). Hyper-V Replica every 30 seconds gives a strong RPO, but the orchestrator is bank-built, and platform updates need Azure.
   - **OpenStack (3.5):** fully self-hosted, the strongest pure disconnection. It loses points for two platforms (the island) and bank-built DR.
   - **GDC (2.5):** VMs are operable offline, but lifecycle stops. VM live migration is Preview, and it has the most bank-built recovery.
2. **Workload compatibility (20%)**
   - **VCF (5):** everything is certified and supported, with no conversion.
   - **Azure (4):** core banking is certified on Hyper-V. Horizon is replaced by AVD, and appliances need Hyper-V images (widely available).
   - **OpenStack (2.5)** and **GDC (2):** KVM means a certified island. Horizon is out, and appliances need KVM images. GDC also has the less mature VM runtime.
3. **Cost and licensing exposure (20%, directional)**
   - **Azure (4.5):** the host fee is **waived by Azure Hybrid Benefit** on licences already owned, and microsegmentation and AKS are included.
   - **OpenStack (3.5):** socket-pair subscriptions with **no licence stop**, offset by Ceph, OpenShift, Trilio, and partner costs.
   - **GDC (2.5):** ~$48 per core per month, plus RHEL, plus an array refresh.
   - **VCF (2):** the ~$1.65M/yr renewal, plus vDefend and Live Recovery add-ons, **plus the licence stop** that removes negotiating leverage ([ADR-012](../adr/ADR-012-vcf-control-plane-and-governance.md)).
4. **Hybrid governance and operations (15%)**
   - **Azure (4.5):** Arc is one plane over the platform, every guest, and the landing zone, with the bank's Entra ID and Sentinel.
   - **VCF (3)** and **GDC (3):** strong in their own domain and split beyond it. GDC's fleet doesn't cover the island.
   - **OpenStack (2.5):** several consoles and the most components to operate.
5. **Developer platform (10%)**
   - **GDC (5):** GKE-native, with VMs as code.
   - **VCF (4):** VCF Automation + VKS, already licensed.
   - **OpenStack (4):** mature APIs and Terraform, with OpenShift.
   - **Azure (3.5):** ARM/Terraform and AKS on Azure Local, but Tier 0 sits outside the portal lifecycle.
6. **Exit, portability, and skills (10%)**
   - **VCF (3.5):** the skills are already present and the exit path is well trodden, but the licence stop makes a tested exit essential.
   - **Azure (3.5):** Hyper-V is close to the team's Windows depth, and VHDX images convert.
   - **GDC (3)** and **OpenStack (3):** the most open (KubeVirt, OpenStack) but the steepest skills jump.

## Result

**Azure Local + Azure Arc leads at 3.95 (79.0%), ahead of VCF at 3.725 (74.5%).** OpenStack follows at 3.15 and GDC at 2.775.

The lead rests on three things:
- **licensing economics** on licences already owned
- **one governance plane** that meets driver 3 and the examiners' inventory finding
- **core-banking certification without an island**

VCF wins criteria 1 and 2 outright, and **the margin is narrow (0.225)**.

## Sensitivity Analysis

| Scenario | VCF | Azure | GDC | OpenStack | Winner |
|---|---|---|---|---|---|
| **Primary weights** | 3.725 | **3.95** | 2.775 | 3.15 | Azure |
| Equal weights | 3.667 | **3.917** | 3.0 | 3.167 | Azure |
| Resilience at 35% | 3.795 | **3.909** | 2.75 | 3.182 | Azure |
| Developer platform at 20% | 3.75 | **3.909** | 2.977 | 3.227 | Azure |
| Microsoft concentration penalty (Azure exit score 2) | 3.725 | **3.80** | 2.775 | 3.15 | Azure |
| Core vendor certifies KVM (GDC and OpenStack compatibility +1.5) | 3.725 | **3.95** | 3.075 | 3.45 | Azure |
| VCF renewal negotiated down (VCF cost score 3) | 3.925 | **3.95** | 2.775 | 3.15 | Azure (by 0.025) |
| **VCF renewal negotiated further (VCF cost score 3.5)** | **4.025** | 3.95 | 2.775 | 3.15 | **VCF** |
| **Cost weight cut to 10%** | **3.917** | 3.889 | 2.806 | 3.111 | **VCF** |
| **Azure Tier-0 local-management PoC fails (Azure resilience 2.5)** | **3.725** | 3.70 | 2.775 | 3.15 | **VCF** |

**Reading the sensitivity:**
- **Azure's lead survives every re-weighting except a halving of cost.** It also survives a Microsoft-concentration penalty and KVM certification arriving.
- **It flips to VCF in two testable ways:**
  1. Broadcom prices the renewal well enough to move VCF's cost score from 2 to 3.5. Step 13 converts this into a price threshold.
  2. The Tier-0 locally-managed-VM design fails in practice.
- **OpenStack and GDC never lead.** Their certified island is the anchor. Even if the core vendor certified KVM, OpenStack would reach only 3.45.
- **This is an honest two-horse race.** Its result depends on facts the bank can establish **before** the 31 March 2027 renewal.

## Gate G0: Must Pass Before the VCF Renewal Decision (by M4, January 2027)

As in Case Studies 4 and 5, the flip conditions are testable, so they become a gate ([ADR-031](../adr/ADR-031-platform-selection.md)):

| Check | What must be shown | If it fails |
|---|---|---|
| **G0-1: Tier-0 disconnected-week proof of concept** on a 4-node Azure Local instance | With Azure cut off for 7 days, locally managed Hyper-V VMs are started and stopped, **failed over to a second instance by Hyper-V Replica with Data Guard**, and a guest patch is applied and rolled back. All steps are supported by Microsoft in writing | Azure resilience falls to 2.5 and **VCF is selected** |
| **G0-2: Broadcom's best offer** for a 3-year renewal *and* a 1-year bridge, with Azure Local as a costed alternative on the table | Step 13 computes the VCF price at which VCF's cost score reaches 3.5 | If Broadcom's offer is below that threshold, **VCF is selected** |
| **G0-3: Oracle on Storage Spaces Direct** batch proof of concept | Month-end batch completes with ≥ 30 min headroom, and Oracle write p99 ≤ 2 ms | Oracle uses external SAN (L2 pricing) on the Oracle instances only. Not decision-changing |
| **G0-4: AVD pilot** with the contact center (50 seats) | Peripherals, latency, and softphone acceptable | Windows 365 or AVD in Azure for those users. Not decision-changing |

**Whatever G0 decides, a VMware bridge is needed.** Nothing can be migrated off VCF by 31 March 2027, so a short VCF term (one year, sized to the shrinking estate) is part of every path. Step 12 sequences it.

## What the Others Do Better, Recorded Honestly

- **VCF:** zero migration, packaged DR and clean room, and every workload certified. It is the lowest *technical* risk to the Q4 2027 examination.
- **OpenStack:** the most independence and no licence stop. Canonical as a second distribution gives real exit leverage.
- **GDC:** the best developer platform and VMs as code. It would score much better for a bank whose core vendor certified KVM and whose estate was container-first.
- **AWS (the lens):** none of its options could host Tier 0 (Outposts fails the disconnected test). EVS remains a VMware-in-cloud option only for the VCF track.
