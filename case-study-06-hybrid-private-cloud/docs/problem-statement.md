# Step 1: Business Problem

## Organization

**Alder Valley Bancorp** (fictional, composite) is a US regional bank headquartered in Pittsburgh, Pennsylvania, with **about $19B in assets**, **145 branches** across Pennsylvania, Ohio, West Virginia, and Maryland, and about 3,900 employees. The bank is state-chartered and a member of the Federal Reserve, so it is examined jointly by the Federal Reserve Bank of Cleveland and the Pennsylvania Department of Banking and Securities. It operates under the FFIEC IT Examination Handbook, the GLBA Safeguards Rule, PCI DSS for its card-management systems, and the 2023 interagency guidance on third-party risk management.

Alder Valley runs its **core banking system in-house**: a major US vendor's package on Windows application servers with Oracle databases. It also runs its payments stack in-house: Fedwire through FedLine Advantage, ACH, a FedNow and RTP gateway, and debit-card management. Digital banking is a vendor SaaS product that integrates through the bank's on-premises API layer.

All of this sits on **two data centers**: an owned facility near Pittsburgh (DC1) and a colocation facility in Columbus, Ohio (DC2), about 290 km apart. Both run **VMware**: about **2,400 virtual machines on 76 hosts**, including a 1,400-seat VDI estate for the contact center and branch back office. The bank's public-cloud footprint is Microsoft 365, Entra ID, and Microsoft Sentinel. There is also one ungoverned AWS account, described below.

## Forcing Functions

Four pressures are forcing this initiative now:

1. **The VMware subscription ends on 31 March 2027, and the renewal quote is up another third.**
   - In March 2024, when Broadcom ended perpetual licences and support-and-subscription renewals, Alder Valley signed a **three-year VMware Cloud Foundation (VCF) subscription** at about **$1.25M a year**. Its previous perpetual support cost was about $480K a year, so that was 2.6× the old bill.
   - In August 2026, the bank received the renewal quote: **about $1.65M a year for a further three years**, before any true-up of core counts. VCF is licensed per physical core, with a 16-core minimum per CPU.
   - Letting the subscription lapse is not an option. Partners report reinstatement penalties for late renewal, and the bank cannot run unsupported hypervisors under its own policy or examiner expectations.
   - The board's question is not "renew or not". It is: **"Why are we renewing without a credible alternative, and what would it take to have one?"**
2. **Examiners issued a Matter Requiring Attention on operational resilience.**
   - In the May 2026 disaster-recovery test, failing core banking over to DC2 took **11 hours 40 minutes** against a **4-hour recovery time objective**. Oracle data loss was **35 minutes** against a 15-minute recovery point objective.
   - The August 2026 examination turned this into an **MRA**. It also cited an incomplete asset and configuration inventory, and backups that were not immutable for every critical tier.
   - A remediation plan is due by **31 December 2026**. Examiners expect to see a **successful full recovery of the critical tier (Tier 0)** before the **2027 examination (Q4 2027)**.
3. **About 60% of the compute hardware and the primary storage array reach end of vendor support in December 2027.** 44 of the 76 hosts (bought in 2020) and the DC1 Fibre Channel array that carries the Oracle databases go out of support at the end of 2027. A like-for-like refresh is estimated at about **$4.2M**. This refresh is the natural moment to change the hypervisor *without* a separate hardware cycle, and it becomes a sunk cost if the choice is made after it.
4. **Delivery teams are routing around the data center.**
   - The average time to provision a VM is **12 business days**, all through tickets. There is no self-service and no API.
   - The digital-lending team runs three Rancher Kubernetes clusters (about 40 nodes) on VMs that it built itself, outside the infrastructure team's patching and monitoring.
   - In 2025 the same team opened an **AWS account** on a departmental card for a proof of concept. It still holds "masked" copies of customer records that a 2026 internal review found could be re-identified.

## Ranked Business Drivers

1. **Operational resilience first.** Tier 0 must recover within **4 hours with no more than 15 minutes of data loss**, proven by test, and the MRA must be closed at the 2027 examination. Resilience ranks first because it is the examiners' finding and the board's first question, the same logic Case Study 4 applied to OT security and Case Study 5 to AI governance.
2. **End the single-hypervisor dependency on cost and on risk.**
   - **Cost:** the five-year infrastructure cost must be no higher than simply renewing VCF and refreshing the hardware like for like.
   - **Risk:** whatever the bank runs on, it must have a **documented and tested exit path**, as the interagency third-party guidance expects for critical services.
3. **One operating and governance model across on-premises and public cloud:** asset inventory, patching, configuration policy, identity, and observability, with the same controls wherever a workload runs.
4. **Self-service delivery:** standard VMs in hours rather than 12 days, Kubernetes namespaces in minutes, both through an API. The digital team's clusters and the AWS account come back under governance.
5. **A skills transition the team can absorb:** a 24-person infrastructure team whose depth is almost entirely VMware and Windows.

## The Invariant

**Tier-0 systems (core banking, payments, and card management) and customer non-public personal information stay in bank-controlled facilities, and they keep running, can fail over, and can be patched even if the connection to any vendor's cloud control plane is lost.**

This is the property that must not regress. It is Case Study 6's equivalent of Case Study 2's batch-settlement invariant, Case Study 4's control-loop isolation, and Case Study 5's human-in-the-loop rule. It matters here because several hybrid platforms are *managed from* a public cloud. The invariant makes that dependency something to test in each platform track, rather than something to discover in an outage.

## What This Case Study Is — and Is Not

This is a **modernization of an existing private estate, extended into public cloud where it makes sense**. It is not a data-center exit: both data centers stay, and board policy keeps Tier 0 on premises. It is not a core-banking replacement either. The core vendor's package stays, and its supported-platform list is a hard constraint.

The central design question, carried through every later step, is the one most regulated enterprises with a VMware estate face in 2026: **modernize in place on VMware Cloud Foundation, move to a hyperscaler's hybrid stack (Azure Local with Azure Arc, or Google Distributed Cloud), or move to an open private cloud (OpenStack), and in each case how to keep an exit path so this is the last time a single vendor's renewal sets the bank's infrastructure budget.**

Four tracks are evaluated:
- **VCF** (modernize in place)
- **Azure Local + Azure Arc**
- **Google Distributed Cloud**
- **OpenStack**

**AWS's hybrid options** (Outposts, EKS Anywhere, and Amazon Elastic VMware Service) are assessed as a **lens** where they change the comparison.

As in Case Studies 2, 4, and 5, the **2025 AWS proof-of-concept account** is carried as a named governance risk. It is **not** a vote for AWS, and the evaluation treats it neutrally.
