# Step 12: Migration Roadmap and ADRs

## Purpose

[Step 11](target-architecture.md) confirmed Azure Local + Azure Arc, conditional on gate G0. This step sequences the work against dates Alder Valley did not choose (M1 = October 2026):

| Date | Month | What happens |
|---|---|---|
| **31 December 2026** | M3 | MRA remediation plan due to examiners |
| **January 2027** | M4 | **Gate G0** decides the platform ([ADR-031](../adr/ADR-031-platform-selection.md)) |
| **31 March 2027** | M6 | **VCF subscription ends.** A bridge term must be in place |
| **Q4 2027** | M13–M15 | **Examination.** A successful Tier-0 recovery must be evidenced |
| **December 2027** | M15 | **44 hosts and the DC1 Fibre Channel array reach end of support** |

## Why This Roadmap Is Shaped the Way It Is

Tier 0 should move **last**, after the new platform has proven itself with Tier 2 and Tier 1 ([Step 4](architecture-options-and-styles.md)). But the examination comes first. Planning the migration naively would put the bank in front of examiners in Q4 2027 **in the middle of moving core banking**, with its recovery evidence on a platform it is about to leave, or on one it has barely started using.

**The roadmap therefore decouples the MRA from the platform migration** ([ADR-033](../adr/ADR-033-mra-evidence-before-tier0-migration.md)), in the same way Case Study 5 decoupled the AI assistant from the Teradata exit:

1. **The resilience track** applies recovery as code, firewall parity, Data Guard transport sizing, the vault, and the clean room to **the current VMware estate** during 2027. All of it is platform-neutral ([Step 5](logical-design.md)). **Two full Tier-0 recovery tests (M8 and M11)** produce the examination evidence on the platform Tier 0 is actually running on.
2. **The platform track** moves Tier 2 and Tier 1 onto Azure Local during 2027, driven by the December 2027 hardware end of support.
3. **Tier 0 moves after the examination** (M16–M20), with two more recovery tests on the new platform before the VCF bridge ends.

## The VCF Bridge ([ADR-032](../adr/ADR-032-vcf-bridge-term.md))

Nothing can be migrated off VCF by 31 March 2027, so **a bridge is bought whatever G0 decides**:

- **Target:** a **15-month term, 1 April 2027 to 30 June 2028**, matching the Tier-0 cutover plus a margin of one month.
- **Fallback:** if Broadcom will offer only 12 months, sign to 31 March 2028 plus a pre-negotiated 3-month extension.
- **Negotiated alongside G0-2**, with the Azure Local proof of concept on the table. Broadcom's 3-year quote is the comparison point, and Step 13 computes the price at which VCF would win.

## The Plan

| Phase | Months | Track | Scope |
|---|---|---|---|
| **0: G0 + foundation** | M1–M4 | Both | G0 proofs of concept (an 8-node Azure Local lab: the Tier-0 disconnected week, Oracle on Storage Spaces Direct, the AVD pilot). Broadcom negotiation. **Arc-enabled servers on every existing VMware guest** (this closes the inventory finding early). Inventory reconciliation, with about 15% of Tier 2 retired. **AWS account closed** (M1–M3) and the Azure landing zone built. MRA plan submitted (M3) |
| **Decision** | M4 | — | G0 result. Platform confirmed (or reversed to VCF). Hardware ordered (M5) |
| **Bridge** | M5–M6 | Commercial | VCF bridge signed before 31 March 2027 ([ADR-032](../adr/ADR-032-vcf-bridge-term.md)) |
| **R: Resilience on the current platform** | M2–M11 | Resilience | Recovery plans in Git for every Tier-0/1 service. Orchestrator running against VMware (SRM + Data Guard + automation). Zone intent rendered to NSX with a parity check. Data Guard transport resized. Vault + clean room built (M5–M9). **Full Tier-0 test #1 at M8 (May 2027), #2 at M11 (August 2027)** |
| **1: Platform build** | M6–M9 | Platform | General and VDI instances in both sites (hardware lead time about 12 weeks). Arc, Policy, Defender. Terraform catalog live. Datacenter Firewall/NSG renderers |
| **2: Tier 2 + developer platform** | M8–M13 | Platform | About 1,375 Tier-2 VMs in waves (Azure Migrate), with dev/test to the landing zone. **AKS replaces Rancher** (M8–M11). **AVD rollout** (M9–M14) and Horizon retired at M14 |
| **3: Tier 1** | M10–M15 | Platform | About 520 VMs with Hyper-V Replica protection. **The 44 end-of-support hosts are emptied by M15** |
| **Examination** | M13–M15 | Resilience | Evidence: two Tier-0 recovery reports, readiness history, inventory reconciliation, vault restore tests |
| **4a: Tier-0 non-core** | M15–M17 | Platform | Tier-0/PCI and Oracle instances built (M12–M15). Payments gateways (vendor Hyper-V images), card management, and the API layer move. **Recovery test on Azure Local (M17)** |
| **4b: Core banking** | M17–M19 | Platform | **Oracle migrated by Data Guard switchover** to the new Oracle instances ([ADR-034](../adr/ADR-034-wave-plan-and-tier0-cutover.md)). Core application servers rehosted over a planned weekend. **Recovery test (M19)** and the **disconnected-week drill (M19)** |
| **Decommission** | M20–M21 | Both | VMware switched off (May 2028). The 2023 hosts are re-imaged into Azure Local (M20–M21). Bridge ends 30 June 2028 (M21) |

See [`diagrams/migration-roadmap.md`](../diagrams/migration-roadmap.md) for the reference Gantt chart.

## Gates

| Gate | When | Pass criteria |
|---|---|---|
| **G0** | M4 | The four checks in [ADR-031](../adr/ADR-031-platform-selection.md) |
| **R1 / R2: Tier-0 recovery on the current platform** | M8 / M11 | Full Tier-0 failover within **4 h** (the 3-hour budget met or explained), RPO within **15 min** (Data Guard lag recorded), evidence report filed |
| **W: per migration wave** | Each wave | 10 business days stable on Azure Local, DR readiness green for every migrated service, source VMs kept powered off for 30 days before deletion |
| **T0a: Tier-0 non-core cutover** | M15 | R1 and R2 passed. The examination has closed or has no open resilience findings. Tier-0 instances pass a readiness dry run |
| **T0b: Core banking cutover** | M17 | The M17 recovery test on Azure Local passed. Month-end batch rehearsed on the new Oracle instances with ≥ 30 min headroom (NFR-4). Core vendor sign-off |
| **D: VMware decommission** | M20 | Every service is DR-ready on Azure Local. The M19 recovery test and disconnected-week drill passed. No VMware-hosted dependency for 30 days |

## Rollback

Explained in [ADR-034](../adr/ADR-034-wave-plan-and-tier0-cutover.md):

- **Tier 2 and Tier 1 waves:** source VMs stay on VMware, powered off, for 30 days. Rollback means powering them back on and repointing DNS.
- **Oracle:** the old VMware Oracle clusters remain a Data Guard standby after switchover. **Rollback is a switchover back**, possible until decommission (M20).
- **Core application servers:** the VMware originals are kept powered off until gate D.
- **After gate D:** there is no rollback to VMware, which is why D requires the M19 test and drill.

## What This Step Carries Forward

- **[Step 13](cost-and-risk-analysis.md):**
  - the bridge cost (15 months, with a short-term premium)
  - dual-running hardware
  - the one-time migration and resilience programs
  - the Azure Hybrid Benefit coverage check
  - **the Broadcom threshold price for G0-2**
  - the consolidated risk register
- **Operational readiness:** up to four hires (Azure Local, automation, and platform engineering), plan ownership assigned to service owners, AVD training for 1,400 users, and the annual disconnected-week drill. These are Phase 0–1 deliverables.
