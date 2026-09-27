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
| 4. Architecture options and styles | Not started |
| 5. Vendor-neutral logical design | Not started |
| 6. VMware Cloud Foundation implementation | Not started |
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
└── docs/
    ├── problem-statement.md   # organization, 4 forcing functions, 5 ranked drivers, the invariant (done)
    ├── current-state.md       # two DCs, 76 hosts / 4,160 cores, tiers and the failed DR test, $5.05M/yr baseline (done)
    └── requirements.md        # 8 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
```
