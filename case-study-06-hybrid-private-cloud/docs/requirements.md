# Steps 2–3: Capabilities Required, Requirements, and NFRs

## Step 2: Business Capabilities Required

Traced to the five ranked drivers in `problem-statement.md`:

1. **A virtualization platform** for about 2,400 VMs:
   - Windows failover clusters
   - Oracle RAC, placed with the licence count in mind
   - about 120 vendor appliances
   - a 1,400-seat VDI estate

   Each workload lands on a platform its vendor supports. (Drivers 1, 2)
2. **A Kubernetes platform** that absorbs the three shadow Rancher clusters and grows with digital banking. It should be consistent with the Kubernetes the bank would use in public cloud. (Drivers 3, 4)
3. **A hybrid management and governance plane** covering every host, VM, and cluster, on premises or in cloud:
   - inventory with owner and tier
   - configuration policy and drift detection
   - patch orchestration
   - role-based access through Entra ID
   - security posture reporting

   (Drivers 1, 3)
4. **Disaster-recovery orchestration and immutable backup:**
   - automated, dependency-ordered Tier-0 and Tier-1 failover between DC1 and DC2
   - immutable, isolated backups for Tier 0 and Tier 1, with an isolated recovery environment for ransomware
   - optionally, a public cloud as a third recovery location for Tier 1 and Tier 2

   (Driver 1)
5. **Self-service infrastructure** through an API and a catalog: Terraform or an equivalent, integrated with ServiceNow for approvals, with standard VM, network, and namespace products. (Driver 4)
6. **Network segmentation and zero-trust controls:** microsegmentation for the PCI card-data environment and for Tier 0 in *both* data centers (NSX exists only in DC1 today), and firewall policy as code. (Drivers 1, 3)
7. **Observability and security integration:** platform telemetry to Microsoft Sentinel (the existing SIEM), discovery-fed CMDB completeness, and capacity and cost reporting per business service. (Drivers 2, 3)
8. **A governed public-cloud landing zone** for non-Tier-0 workloads (dev/test, analytics, burst, the digital team's ML work). The 2025 AWS account is either absorbed into it or closed. (Drivers 3, 4)

## Step 3: Non-Functional Requirements

| # | NFR | Target | Driven by |
|---|-----|--------|-----------|
| NFR-1 | Recovery objectives | **Tier 0: RTO ≤ 4 h, RPO ≤ 15 min.** Tier 1: RTO ≤ 8 h, RPO ≤ 1 h. Tier 2: RTO ≤ 24 h, RPO ≤ 24 h. **Proven by a full Tier-0 failover test at least twice a year**, with the first before the Q4 2027 examination | Driver 1; the MRA |
| NFR-2 | Availability | Tier-0 platform 99.95% monthly. Host and platform maintenance is non-disruptive (rolling, with no Tier-0 outage) | Driver 1 |
| NFR-3 | **Disconnected operation** | With the vendor's cloud control plane unreachable for **at least 7 days**, Tier-0 workloads keep running, and operators can still start and stop VMs, fail over between DC1 and DC2, and roll back a patch. Degraded *management* features (portal views, cloud policy updates) are acceptable. Degraded *operations* are not | The invariant |
| NFR-4 | Performance | Core nightly batch finishes in the 23:00–02:00 window at month-end peak, with **≥ 30 minutes of headroom**. Oracle storage write latency p99 ≤ 2 ms | Driver 1 |
| NFR-5 | Scale | About 2,400 VMs, 4,160 licensed cores, about 1.4 PB usable across arrays and vSAN, growing about 8% a year. Kubernetes from about 40 to about 150 nodes by 2029 | Drivers 2, 4 |
| NFR-6 | Security and compliance | FFIEC IT Handbook (Architecture, Infrastructure, and Operations), GLBA Safeguards Rule, **PCI DSS 4.0.1** for the card-data environment, and CIS benchmarks for hosts and guests. Critical patches within **14 days**, high within 30. All privileged access through PAM with MFA, and **no unmanaged local or break-glass accounts** | Drivers 1, 3 |
| NFR-7 | Backup and cyber recovery | **100% of Tier-0 and Tier-1 data** with an immutable copy and a logically isolated copy. An isolated recovery environment for Tier 0. Quarterly restore tests | Driver 1; the MRA |
| NFR-8 | Inventory and configuration | **100% of hosts, VMs, and clusters** inventoried with owner, tier, and data classification, reconciled daily to the CMDB. Configuration drift detected within 24 hours | Drivers 1, 3; the MRA |
| NFR-9 | Provisioning | A standard VM in **≤ 4 hours** (goal: under 1 hour). A Kubernetes namespace in **≤ 1 hour**. All through an API, with approvals in ServiceNow | Driver 4 |
| NFR-10 | Cost | **Five-year infrastructure platform TCO ≤ the status-quo path**: VCF renewal plus a like-for-like hardware refresh, from the `current-state.md` §6 baseline. Every platform cost is allocated to a business service | Driver 2 |
| NFR-11 | Exit and portability | A **documented exit plan** for the chosen platform, **tested** by moving a representative workload set (including one Tier-1 service) off the platform. VM images, automation, and Kubernetes manifests in portable formats | Driver 2; interagency third-party guidance (2023) |
| NFR-12 | Operability | Run by the current 24-person team **plus at most 4 hires**. 24×7 vendor support with severity-1 response in ≤ 1 hour | Driver 5 |

## Requirement / Constraint / Assumption / Risk (Section 7.1 framework)

**Requirements**
- Recovery must be **orchestrated, not written down**. The Tier-0 failover is executed by automation that encodes dependency order, network and firewall changes, and database switchover, and the runbook is reduced to decisions.
- Governance is expressed **once** (policy, inventory, patch baselines, and role-based access) and applied to on-premises and cloud resources alike. It is not re-implemented per platform or per site.
- Every platform choice must show *how the bank would leave it*: formats, tools, effort, and licence implications.

**Constraints**
- **Dates are fixed:**
  - The VCF subscription ends **31 March 2027 (M6)**, and some continuity of VMware support past that date is required, because nothing can be migrated off it by then.
  - Hardware and the DC1 array reach end of support in **December 2027 (M15)**.
  - The MRA remediation plan is due **31 December 2026 (M3)**.
  - The **examination is in Q4 2027 (M13–M15)**.
- **Both data centers stay** (DC2's colocation contract runs to 2030). A data-center exit is out of scope.
- **Tier 0 stays on premises** (board policy and the invariant). Public cloud is allowed for Tier 1 and Tier 2 and for recovery copies of non-Tier-0 data, under the landing-zone controls.
- **The core banking vendor's supported platforms:** today, vSphere and Hyper-V (including Hyper-V-based Azure Local). KVM is "on the roadmap". **Any track that moves core banking to KVM must show a vendor certification, or keep core banking on a supported hypervisor.**
- **Oracle's partitioning policy** governs the Oracle licence count on any hypervisor. The Oracle clusters' design is part of each track, not a detail.
- **Omnissa Horizon's supported platforms** decide where the VDI estate can run.
- **Capital envelope:** about **$6M** for 2027–2028, covering the hardware refresh, new hardware for any target platform, and migration services.

**Assumptions**
- About **60% of VMs are standard Windows and RHEL builds** that migrate with automated conversion tools. The vendor appliances (about 120 VMs) need vendor-supplied images for the target platform, or they stay where they are supported.
- Broadcom will offer a **renewal term shorter than three years** (for example one year, or a reduced core count) at some premium. This is to be confirmed in negotiation, and it is exactly the leverage a credible alternative creates.
- Every candidate platform can integrate with Entra ID, Sentinel, ServiceNow, and Veeam or an equivalent backup tool. **How well** each does is for Steps 6–9 to verify.
- The digital team's Rancher workloads are ordinary stateless services that can move to any conformant Kubernetes.

**Risks (carried forward to the consolidated risk register in Step 13)**
- **Renewal leverage:** without a credible, costed alternative by the start of 2027, the bank renews on Broadcom's terms again.
- **Migration effort and sequencing:** 2,400 VMs, 120 appliances, and a Tier-0 estate that cannot tolerate a second failed recovery test in front of examiners.
- **Vendor certification:** the core banking vendor's KVM support is not yet available. A track that depends on it depends on the vendor's roadmap.
- **Oracle licence exposure:** a cluster redesign that accidentally widens the soft-partitioned core count could cost more than the whole hypervisor saving.
- **Control-plane dependency:** hybrid platforms managed from a public cloud must meet NFR-3, and whether they do is platform-specific.
- **Skills:** the team's depth is VMware and Windows. Every non-VCF track is a retraining program.
- **The 2025 AWS account** holds re-identifiable customer data. It is a governance risk regardless of platform choice, and is absorbed or closed under the new landing zone.

## Priority Weighting (feeds the Step 10 decision matrix)

Provisional weights, to be refined once options are on the table in Step 4 (from highest to lowest):

1. **Resilience and disconnected operation** (NFR-1 to NFR-3, NFR-7): orchestrated recovery, immutable backup integration, behavior when the control plane is unreachable.
2. **Workload compatibility:** core-banking vendor certification, Oracle licensing, Horizon support, appliance images.
3. **Cost and licensing exposure:** five-year TCO against the status quo, and how exposed the bank is to one vendor's next renewal.
4. **Hybrid governance and operations:** one inventory, policy, and patch plane across on-premises and cloud, integrated with Entra ID, Sentinel, and ServiceNow.
5. **Developer platform:** Kubernetes, self-service, API and infrastructure as code.
6. **Exit, portability, and skills:** how the bank would leave, and how far the team must travel to run it.

The platform tracks are:
- **Step 6: VMware Cloud Foundation** (modernize in place)
- **Step 7: Azure Local + Azure Arc**
- **Step 8: Google Distributed Cloud**
- **Step 9: OpenStack**, as an open private cloud (a commercially supported distribution)

**AWS's hybrid options** (Outposts, EKS Anywhere, Amazon Elastic VMware Service) are assessed as a lens in Step 4 and wherever they change a comparison. These weights are recorded here so that Step 10 traces back to this document rather than being invented at decision time.
