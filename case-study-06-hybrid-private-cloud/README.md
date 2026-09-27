# Case Study 6 of 6: Hybrid / Private-Cloud Modernization

**Scenario:** Alder Valley Bancorp (fictional, composite) is a ~$19B-asset US regional bank with 145 branches, two data centers, and about 2,400 VMs on VMware, with core banking and payments run in-house. Four pressures force the issue:
- a VMware Cloud Foundation renewal due 31 March 2027, quoted about a third higher than the subscription that already cost 2.6× the old support bill
- an examiners' Matter Requiring Attention after a failed disaster-recovery test (11 h 40 min against a 4-hour RTO)
- hardware and the primary storage array reaching end of support in December 2027
- delivery teams routing around a 12-day VM provisioning process, including an ungoverned AWS account

**Angle:** An existing data-center estate modernized in place and extended into public cloud. The central question is **modernize on VMware Cloud Foundation, move to a hyperscaler's hybrid stack (Azure Local + Azure Arc, or Google Distributed Cloud), or move to an open private cloud (OpenStack)**, while keeping Tier 0 running even when a vendor's cloud control plane is unreachable, and keeping a tested exit path from whatever is chosen.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs **four** implementation tracks:

| Step | Track | What it represents |
|---|---|---|
| 6 | **VMware Cloud Foundation** | Modernize in place: VCF 9 automation, Kubernetes, and recovery, with a VMware-based cloud extension |
| 7 | **Azure Local + Azure Arc** | Microsoft's hybrid stack, managed from Azure |
| 8 | **Google Distributed Cloud** (software-only) | GKE-based hybrid with VM Runtime, managed from Google Cloud |
| 9 | **OpenStack** | An open private cloud on KVM, from a commercially supported distribution |

**AWS's hybrid options** (Outposts, EKS Anywhere, Amazon Elastic VMware Service) are a lens where they change the comparison, not a fifth track.

Contrasts with earlier case studies:
- **The system of record doesn't move.** Unlike Case Studies 2 and 5, the core banking package stays. The question is what it runs *on*, and the vendor's supported-platform list is a hard constraint.
- **The invariant is about the control plane.** Several candidates are managed from a public cloud. NFR-3 requires Tier 0 to keep operating, failing over, and patching for at least 7 days without that control plane.
- **The decision is about leverage as much as technology.** A credible, costed alternative to the VMware renewal has value even if the bank ends up renewing.

## Status

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md); diagram not yet drawn |
| 2–3. Capabilities, requirements, and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-platform-strategy-and-workload-placement.md) to [ADR-005](adr/ADR-005-platform-api-and-portability.md), [target-style diagram (Mermaid)](diagrams/target-architecture-style.md). **Disposition by workload group:** core banking retained, rehosted only on a certified hypervisor (otherwise a certified island), and moved last; Tier 2 ~15% retired; dev/test to the landing zone; Rancher replatformed; SRM runbook replaced. **Platform strategy:** one primary private cloud in two sites plus a governed public-cloud landing zone, with placement by tier. **Recovery:** independent active/standby sites with recovery as code (Data Guard sized for batch, firewall policy as code, orchestrated plans, a 3-hour budget inside the 4-hour RTO). **Cyber recovery:** a three-layer design with a vault in a separate admin domain and a clean room in DC2. **Govern centrally, operate locally,** with a disconnected-week test for every track. **Delivery:** platform API + catalog, pipeline images, and an annual exit test. **AWS lens:** Outposts fails NFR-3 (no start/stop when disconnected); EVS/AVS/GCVE are assessed as the VCF track's cloud extension |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-006](adr/ADR-006-recovery-plan-model-and-readiness.md) to [ADR-008](adr/ADR-008-zone-model-and-segmentation-as-code.md), [logical diagrams (Mermaid)](diagrams/logical-architecture.md). 26 logical components (platform, control, delivery, resilience, observability, landing zone), each marked for whether it must work disconnected (the local-autonomy contract, including a licence-service component). Eight-zone model with default deny in Tier 0 and PCI, rendered from Git identically in both sites and parity-checked daily. Recovery plans per service in Git (groups G0–G6) with a daily DR-readiness job that can fail a change. Oracle on dedicated licence-bounded clusters (640 cores = 320 processor licences; consolidation only with batch evidence). Six end-to-end flows, including the disconnected-week drill, and nine questions every platform track must answer |
| 6. VMware Cloud Foundation implementation | Done — [`docs/vcf-implementation.md`](docs/vcf-implementation.md), [ADR-009](adr/ADR-009-vcf-platform-and-domain-design.md) to [ADR-014](adr/ADR-014-vcf-cloud-extension.md), [VCF diagram (Mermaid)](diagrams/vcf-implementation-architecture.md). VCF 9.1 (released 3 Sept 2026): one instance per site, domains by zone, vSAN ESA (the DC1 FC array is retired, subject to an Oracle batch PoC), Live Recovery with plans generated from Git plus Data Guard, NSX VPCs, and **vDefend (an add-on) required** for microsegmentation in both sites. VCF Automation + VKS (both already licensed and unused) meet driver 4. Core banking certified, Horizon and Veeam supported, and the lowest migration effort. **Passes the disconnected week,** but disconnected licensing needs a usage report every 180 days; if it is missed or the subscription lapses, *workload operations stop*. That makes the renewal an operational dependency and a tested exit mandatory. Arc-enabled vSphere supports vCenter 8 only, so governance is split (VCF Ops + guest-level Arc). No AVS/GCVE/EVS extension now |
| 7. Azure Local + Azure Arc implementation | Not started |
| 8. Google Distributed Cloud implementation | Not started |
| 9. OpenStack implementation | Not started |
| 10. Decision matrix | Not started |
| 11. Recommended platform / target architecture | Not started |
| 12. Migration roadmap and ADRs | Not started |
| 13. Cost and risk analysis | Not started |

## Repository Structure

```
case-study-06-hybrid-private-cloud/
├── README.md
├── docs/
│   ├── problem-statement.md   # organization, 4 forcing functions, 5 ranked drivers, the invariant (done)
│   ├── current-state.md       # two DCs, 76 hosts / 4,160 cores, tiers and the failed DR test, $5.05M/yr baseline (done)
│   ├── requirements.md        # 8 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
│   ├── architecture-options-and-styles.md   # (Step 4) 6-R by workload group, 5 decisions, AWS lens, target style (done)
│   ├── logical-design.md                    # (Step 5) 26 components, local-autonomy contract, zones, recovery plans, Oracle pattern (done)
│   └── vcf-implementation.md                # (Step 6) VCF 9.1 mapping, nine questions, licence finding, cloud extension (done)
├── adr/
│   ├── ADR-001-platform-strategy-and-workload-placement.md   # one private cloud in 2 sites + landing zone, placement by tier (done)
│   ├── ADR-002-recovery-as-code-active-standby.md            # independent sites, Data Guard, policy as code, orchestrated recovery (done)
│   ├── ADR-003-cyber-recovery-vault-and-isolated-recovery.md # immutable copies, isolated vault, clean room (done)
│   ├── ADR-004-govern-centrally-operate-locally.md           # one governance plane, local ops path, disconnected-week test (done)
│   ├── ADR-005-platform-api-and-portability.md               # platform API + catalog, portability rules, annual exit test (done)
│   ├── ADR-006-recovery-plan-model-and-readiness.md          # plans G0-G6 in Git, daily DR-readiness gate (done)
│   ├── ADR-007-oracle-cluster-and-licence-boundary.md        # dedicated licence-bounded Oracle clusters (done)
│   ├── ADR-008-zone-model-and-segmentation-as-code.md        # 8 zones, intent in Git, parity in both sites (done)
│   ├── ADR-009-vcf-platform-and-domain-design.md             # VCF: instance per site, domains by zone, vSAN ESA (done)
│   ├── ADR-010-vcf-recovery-live-recovery-and-data-guard.md  # VCF: Live Recovery from Git plans + Data Guard (done)
│   ├── ADR-011-vcf-network-and-microsegmentation.md          # VCF: NSX VPCs + vDefend on Z0/PCI/Oracle/Z1 hosts (done)
│   ├── ADR-012-vcf-control-plane-and-governance.md           # VCF: local control planes, 180-day licence duty, guest Arc (done)
│   ├── ADR-013-vcf-developer-platform.md                     # VCF: VCF Automation + VKS (done)
│   └── ADR-014-vcf-cloud-extension.md                        # VCF: no AVS/GCVE/EVS now; revisit 2029 (done)
└── diagrams/
    ├── target-architecture-style.md                          # (Step 4) Mermaid reference (done)
    ├── logical-architecture.md                               # (Step 5) component model + Tier-0 recovery sequence (done)
    └── vcf-implementation-architecture.md                    # (Step 6) Mermaid VCF track (done)
```
