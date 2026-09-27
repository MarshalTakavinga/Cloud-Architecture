# Step 4: Architecture Options and Styles

## Framing the Question

Every option is judged against the five ranked drivers in `problem-statement.md` and the constraints in `requirements.md`:
- Tier 0 stays on premises.
- Both data centers stay.
- The core banking vendor certifies only vSphere and Hyper-V today.
- The renewal date (31 March 2027) and the hardware end-of-support date (December 2027) are fixed.

Every option is also judged against **the invariant**: Tier 0 keeps running, failing over, and patching with no vendor cloud control plane.

Five design questions follow:

1. **What is the platform strategy, and where does each tier run?** ([ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md))
2. **How does Tier 0 recover within 4 hours and 15 minutes, reliably and in front of examiners?** ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md))
3. **How does the bank recover from a destructive cyberattack**, which a DR site alone doesn't solve? ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md))
4. **Where does governance live, and what must work locally?** ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md))
5. **How do delivery teams get infrastructure, and how does the bank keep an exit path?** ([ADR-005](../adr/ADR-005-platform-api-and-portability.md))

*Which* platform (VCF, Azure Local + Arc, Google Distributed Cloud, or OpenStack) is left to Steps 6–10. *In what order* workloads move is left to Step 12.

## 6-R Disposition per Workload Group

| Workload group | Disposition | Rationale |
|---|---|---|
| **Core banking** (application servers + Oracle 19c RAC, Tier 0) | **Retain on premises; rehost onto the new platform only on a vendor-certified hypervisor** | The vendor's supported-platform list is a hard constraint. If a track's hypervisor isn't certified, core banking stays on a **certified island** (a small, separately licensed cluster) and that track carries the cost and complexity. Moves **last**, after two successful recovery tests of other Tier-0 services on the new platform. |
| **Payments** (Fedwire/FedLine, ACH, FedNow/RTP gateway) and **card management** (PCI), Tier 0 | **Retain on premises; rehost with vendor-supplied images** | Mostly vendor appliances. Each moves when its vendor supplies a supported image for the target hypervisor. Until then it stays where it is supported. |
| **API layer** used by digital banking (Tier 0) | **Rehost now, refactor later** | Stateless services on VMs today. Rehosted in the Tier-0 zone. Moving it to the platform's Kubernetes is a later option, not part of this program. |
| **Tier-1 applications** (loan origination, treasury, fraud, identity, PKI, file transfer, SQL Server warehouse) | **Rehost** | Standard Windows and RHEL builds, converted with the target platform's migration tooling. Public cloud is allowed as a recovery location by exception (ADR-001). |
| **Tier-2 applications** (~1,620 VMs) | **Retire ~15%, rehost the rest; relocate dev/test to public cloud** | The inventory reconciliation required by the MRA will find unowned and idle VMs (assumed about 15%). Dev/test moves to the governed public-cloud landing zone, where it is cheaper to run elastically. |
| **Horizon VDI** (1,400 desktops) | **Retain on a supported hypervisor, or repurchase as cloud-hosted desktops** (decided per track) | Omnissa's supported platforms decide what's possible. A cloud desktop service is a legitimate option because VDI is Tier 1, not Tier 0. |
| **Rancher RKE2 clusters** (~40 nodes, shadow IT) | **Replatform** onto the platform team's Kubernetes | The workloads are stateless (`requirements.md` assumption). Operating them under infrastructure patching and monitoring is the point. |
| **SRM + the 140-step runbook** | **Replace** with recovery as code ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md)) | The May 2026 test failed on runbook steps, not on replication. |
| **Veeam backup** | **Retain and extend** (immutability for Tier 1, isolated vault, isolated recovery environment) ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | Whether Veeam supports each target hypervisor is checked per track. Where it doesn't, the track names its backup product. |
| **NSX** (DC1 PCI zone only) | **Replace or extend** so microsegmentation covers Tier 0 and the card-data environment in **both** DCs | Today DC2 has no equivalent, which is one reason the failover broke. |
| **Aria Operations, vCenter-per-site management** | **Replace** with the chosen control plane ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)) | One inventory, policy, and patch plane is driver 3. |
| **44 hosts + DC1 Fibre Channel array** (end of support December 2027) | **Refresh as the new platform's validated hardware** | The refresh is spent once. Buying like-for-like VMware hardware and then changing platform would pay for it twice. |
| **2025 AWS proof-of-concept account** | **Absorb or close** (decided with the landing zone) | If the governed landing zone is on AWS, the account is re-enrolled under it. Otherwise it is closed. **Either way the re-identifiable extracts are purged**, and the digital team's ML work moves to the landing zone. |

## Decision 1: Platform Strategy and Workload Placement (feeds [ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md))

| Option | Assessment |
|---|---|
| 1. **Renew and stand still:** renew VCF on the quoted terms and keep operating as today | **Rejected as a strategy.** It fixes none of drivers 1, 3, or 4 on its own, and it renews with no leverage. It is different from *modernizing in place on VCF*, which uses the capabilities the bank already pays for and remains a full candidate track (Step 6). |
| 2. **Move the estate to public cloud** (VMware-in-cloud services such as Azure VMware Solution, Google Cloud VMware Engine, or Amazon EVS, or native IaaS) | **Rejected for Tier 0** (board policy, the invariant). For the rest, the bank would pay for two data centers it is keeping (the DC2 contract runs to 2030) *and* cloud capacity. It is allowed selectively for Tier 2, dev/test, and recovery copies. |
| 3. **Two permanent private platforms:** VMware for Tier 0, a second platform for everything else | **Rejected as the default.** It doubles tooling, patching, skills, and support contracts for a 24-person team (NFR-12). It is kept **only as a certified island** where a track's hypervisor isn't certified for core banking, and that track is scored for it. |
| 4. **One primary private-cloud platform in both DCs, plus a governed public-cloud landing zone, with workloads placed by tier** | **Selected.** One platform to run, patch, and recover. Placement rules below. The exit path comes from portability and a tested exit ([ADR-005](../adr/ADR-005-platform-api-and-portability.md), NFR-11), not from running two stacks forever. |

**Placement rules:**

| Workload class | Where it runs | Recovery location |
|---|---|---|
| Tier 0 | Private cloud, DC1 primary | Private cloud, DC2 (never public cloud) |
| Tier 1 | Private cloud | DC2, or public cloud by exception (non-NPI or encrypted with bank-held keys) |
| Tier 2 | Private cloud or public cloud, by cost | Backup restore; public cloud allowed |
| Dev/test, analytics, ML experiments | Public-cloud landing zone | Not applicable (rebuildable) |
| New cloud-native services | Private Kubernetes or public cloud, by data class | Per tier |

## Decision 2: Recovery Architecture (feeds [ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md))

The May 2026 test failed for three identifiable reasons:
- the dependency order in a 140-step manual runbook
- firewall rules that existed in DC1 but not in DC2
- Oracle redo transport lagging under batch load

The options are judged against those failures.

| Option | Assessment |
|---|---|
| 1. **Fix the runbook** and rehearse it more | **Rejected.** It keeps a human sequencing 140 steps under pressure. It might pass one test, but it cannot be relied on twice a year. |
| 2. **Stretched cluster across DC1 and DC2** (synchronous storage, automatic restart) | **Rejected for Tier 0.** The ~4 ms round trip is inside the limit for a stretched vSAN cluster (under 5 ms), so it is technically possible, but a stretched cluster is **one** failure domain. A configuration error, a bad upgrade, or ransomware reaches both sites at once, and examiners expect an *independent* recovery site. Extending Oracle RAC across 290 km is not a supported design. |
| 3. **Active-active Tier 0** across both DCs | **Rejected.** The core banking package runs one active database. The payments gateways are also active/standby by design. |
| 4. **Independent active/standby sites with recovery as code** | **Selected.** Database-native replication (Oracle Data Guard, with transport sized for the batch peak and a lag alert). Platform replication or rebuild-from-image for application tiers. **Network and firewall policy as code**, applied identically to both sites. **Recovery plans as versioned code** executed by an orchestrator in dependency order. Humans *decide* (declare the disaster, approve the switchover); automation *executes*. |

**Recovery-time budget for Tier 0 (≤ 4 h):**

| Stage | Budget |
|---|---|
| Detect and declare | 30 min |
| Database switchover | 15 min |
| Application tiers started in dependency order | 60 min |
| Network and DNS cutover | 15 min |
| Business validation | 60 min |
| **Total** | **3 h** (1 h margin) |

**RPO (≤ 15 min):** Data Guard asynchronous transport with an alert at 10 minutes of lag, and redo transport bandwidth sized for the batch peak (the May 2026 failure). Full Tier-0 tests run twice a year, with partial service-rotation tests monthly (NFR-1).

## Decision 3: Cyber Recovery (feeds [ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md))

A DR site protects against losing a site. It doesn't protect against an attacker who has administrator rights in both sites, so destructive attacks need their own answer.

| Option | Assessment |
|---|---|
| 1. **Extend today's immutable repositories to Tier 1** | **Rejected as sufficient.** It's necessary but not enough: the repositories share the production administrative domain. |
| 2. **Rely on offsite tape** | **Rejected as primary.** Weekly tapes mean up to a week of data loss and days to restore. Tape is kept as a last layer. |
| 3. **Three layers: immutable local copies + an isolated vault + an isolated recovery environment** | **Selected.** |

The three layers are:
1. **Immutable copies in each DC** for fast operational restores.
2. **A logically isolated vault** with its **own administrative identity domain** (not production AD or Entra), MFA, and time-locked retention that no administrator can shorten.
3. **An isolated recovery environment (clean room) in DC2**, where Tier 0 is restored and scanned before being released.

Tier-0 vault copies stay **on premises**, because they hold NPI. Tier-1 and Tier-2 vault copies may use public-cloud object storage in compliance mode, encrypted with bank-held keys.

The bank also evaluates **Sheltered Harbor** participation, the US banking industry's standard for a daily immutable archive of customer account data, as part of this decision.

## Decision 4: Where Governance Lives and What Must Work Locally (feeds [ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md))

| Option | Assessment |
|---|---|
| 1. **Per-site, per-tool management plus CMDB reconciliation** (today) | **Rejected.** This is how 9% of VMs fell out of patching and inventory, which is the finding the examiners cited. |
| 2. **A cloud-hosted hybrid control plane for everything** (the model several hybrid platforms use) | **Accepted for governance, not for Tier-0 operations.** Inventory, policy, patch compliance, and role-based access from one plane is exactly driver 3. But if *operating* Tier 0 depends on reaching a public cloud, the invariant fails. |
| 3. **A self-hosted control plane only** | **Accepted for operations, weaker for governance.** Full local autonomy, but the public-cloud landing zone would be governed separately, which splits driver 3. |
| 4. **Govern centrally, operate locally** | **Selected.** |

Option 4 means:
- **One authoritative plane** for inventory, policy as code, patch compliance, and role-based access through Entra ID, covering the private cloud *and* the landing zone.
- **A local operations path** that works for **at least 7 days disconnected** (NFR-3): VM lifecycle, DC1→DC2 failover, and patch rollback. This path includes:
  - local identity (on-premises AD, with break-glass through PAM)
  - a local console
  - a local image repository and update source

**Each platform track is scored on whether its control plane passes this "disconnected week" test.** This is the test that separates the tracks most sharply.

## Decision 5: Self-Service and Portability (feeds [ADR-005](../adr/ADR-005-platform-api-and-portability.md))

| Option | Assessment |
|---|---|
| 1. **Faster tickets** (better templates, more staff) | **Rejected.** It shortens 12 days to perhaps 5, and the digital team will still route around it. |
| 2. **A self-service portal** (click-ops) | **Rejected as sufficient.** Faster, but not code: changes are not reviewable, repeatable, or portable. |
| 3. **A platform API with a product catalog** | **Selected.** |

Option 3 comprises:
- **Terraform** (or an equivalent) against the platform API
- **ServiceNow** as the approval and record system, with policy-based automatic approval for standard products
- **golden images built by a pipeline**
- a **platform-team-run, CNCF-conformant Kubernetes** that replaces the three Rancher clusters

**Portability rules make the exit path real** (NFR-11):
- VM images are built by pipeline, so they can be rebuilt on another hypervisor.
- Terraform modules isolate the provider-specific layer.
- Application manifests use only conformant Kubernetes APIs, with no proprietary resource types in the application layer.
- Backups are kept in a format that can be restored to more than one hypervisor.
- An **exit test runs every year**.

## The AWS Lens

AWS's hybrid options were assessed against the invariant and the core banking constraint before deciding whether any should be a track:

| AWS option | What it is | Assessment |
|---|---|---|
| **AWS Outposts** (rack) | AWS-managed racks in the bank's DC, run from an AWS Region | AWS documents that when the link to the Region is lost, instances keep running, but *"mutating requests (like starting or stopping instances on the Outpost), control plane operations, and service telemetry … will fail."* **That fails NFR-3** for Tier 0. It also doesn't run a hypervisor the core vendor certifies. **Not a Tier-0 platform.** |
| **Amazon EKS Anywhere** | AWS's Kubernetes distribution on the bank's own infrastructure (vSphere, bare metal, and others) | Kubernetes only. It could be the container layer on a VCF or bare-metal track, but it doesn't address the VM estate. Noted as an alternative in Steps 6 and 9. |
| **Amazon Elastic VMware Service** (GA August 2025) | VCF running in the bank's own VPC on EC2 bare-metal hosts, with the **bank's own portable VCF subscription**. Minimums are four hosts, for example 256 cores on i4i.metal | A VMware-compatible **cloud recovery site for Tier 1 and Tier 2**. It **deepens** the VCF dependency rather than reducing it. Azure VMware Solution and Google Cloud VMware Engine are its equivalents, so all three are assessed together in **Step 6** as the VCF track's cloud extension. |

**AWS is therefore a lens, not a track.** None of its options can host Tier 0 under the invariant and the core vendor's certification. The 2025 AWS account is handled by the landing-zone decision above and is not a vote either way.

## Target Architecture Style

The result is **a hybrid private cloud: one platform in two independent sites, governed centrally and operated locally, with a governed public-cloud landing zone.** It has five parts:

- **Private cloud in DC1 and DC2:**
  - Tier-0, Tier-1, and Tier-2 zones with microsegmentation in both sites
  - Oracle on dedicated, licence-aware clusters
  - a platform-team Kubernetes
- **Recovery:**
  - Data Guard and platform replication from DC1 to DC2
  - network policy as code in both sites
  - an orchestrator that runs recovery plans as code
- **Cyber recovery:**
  - immutable copies in each DC
  - an isolated vault with its own administrative domain
  - a clean-room recovery environment in DC2
- **Control plane:**
  - one governance plane for inventory, policy, patch compliance, and role-based access (Entra ID), covering both sites and the landing zone
  - a **local operations path** for each site that works disconnected
- **Delivery:**
  - a platform API with a catalog (Terraform plus ServiceNow approvals)
  - pipeline-built images
  - the public-cloud landing zone for dev/test, Tier 2 by choice, analytics, and non-Tier-0 vault copies

See [`diagrams/target-architecture-style.md`](../diagrams/target-architecture-style.md) for the reference diagram (Mermaid source, to be hand-drawn).

## What This Step Carries Forward

- **[Step 5](logical-design.md):**
  - the logical components
  - the tier and zone model
  - the recovery-plan structure
  - the network segmentation design
  - the Oracle cluster pattern
  - the control-plane interfaces (what "operate locally" means component by component)
- **Steps 6–9:** each track must answer, with current documentation:
  - core banking certification
  - Oracle partitioning and licence count
  - Horizon support
  - Veeam support
  - the disconnected-week test
  - Kubernetes
  - migration tooling from vSphere
  - the matching public cloud
- **[Step 12](migration-roadmap.md):** the order of waves (Tier 2 first, Tier 0 last), and how VMware support is kept past 31 March 2027 while the move happens.
