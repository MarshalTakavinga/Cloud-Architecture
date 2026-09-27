# ADR-031: Platform Selection — Azure Local + Azure Arc, Gated by G0

**Status:** Approved, **conditional on gate G0** (by M4, January 2027)
**Date:** Step 10 of the Case Study 6 pipeline

## Context

Four tracks were designed in Steps 6–9 and scored in [`decision-matrix.md`](../docs/decision-matrix.md) against the six weighted criteria from `requirements.md`. The VCF subscription ends on **31 March 2027 (M6)**. The hardware refresh is due by **December 2027**. The MRA requires a successful Tier-0 recovery before the **Q4 2027 examination**.

## Decision

**Azure Local + Azure Arc is selected** (3.95, against VCF 3.725, OpenStack 3.15, and GDC 2.775), as designed in [ADR-015](ADR-015-azure-local-instance-topology.md) to [ADR-020](ADR-020-azure-vdi.md).

**Scores by criterion:**

| Criterion (weight) | Azure | VCF | GDC | OpenStack |
|---|---|---|---|---|
| Resilience and disconnected (25%) | 3.5 | 4.5 | 2.5 | 3.5 |
| Workload compatibility (20%) | 4 | 5 | 2 | 2.5 |
| Cost and licensing exposure (20%) | 4.5 | 2 | 2.5 | 3.5 |
| Governance and operations (15%) | 4.5 | 3 | 3 | 2.5 |
| Developer platform (10%) | 3.5 | 4 | 5 | 4 |
| Exit, portability, and skills (10%) | 3.5 | 3.5 | 3 | 3 |

## Gate G0 (by M4)

1. **Tier-0 disconnected-week proof of concept** for locally managed Hyper-V VMs on Azure Local. It covers start/stop, Hyper-V Replica + Data Guard failover, and guest patch rollback for 7 days with Azure unreachable, with Microsoft's written confirmation that the mode is supported. **If it fails, this ADR reverses to VCF** ([ADR-009](ADR-009-vcf-platform-and-domain-design.md) to [ADR-014](ADR-014-vcf-cloud-extension.md)).
2. **Broadcom's best offer** (3-year and 1-year) with Azure Local on the table. **If the offer is below the Step 13 threshold price, this ADR reverses to VCF.**
3. **An Oracle batch proof of concept on Storage Spaces Direct.** A failure moves the Oracle instances to external SAN (L2). It is not decision-changing.
4. **An AVD contact-center pilot.** A failure moves those users to Windows 365 or AVD in Azure. It is not decision-changing.

**In every outcome,** a short VCF term is bought from 1 April 2027 to cover the migration (Step 12).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **VCF, modernized in place (3.725).** It has the lowest technical risk and wins resilience and compatibility outright. It is rejected on cost exposure and the licence stop, which removes negotiating leverage permanently. **It is the designated fallback** if G0-1 or G0-2 fires.
2. **OpenStack (RHOSO) (3.15).** The most independent option, but the certified island, the backup product change, and the skills jump outweigh it for this bank.
3. **Google Distributed Cloud (2.775).** The best developer platform, but KVM certification, Preview VM live migration, and disconnection "not the nominal mode" rule it out for a Tier-0 estate.

## Consequences

- **Positive:**
  - The largest licence line is mostly **replaced by fees waived on licences the bank already owns**.
  - One governance plane closes the examiners' inventory finding.
  - Core banking stays certified.
- **Negative / accepted trade-off:** **Concentration in Microsoft** across identity, productivity, SIEM, public cloud, and now the private platform. This is named in the Step 13 risk register, mitigated by the annual exit test ([ADR-005](ADR-005-platform-api-and-portability.md)) and portable images and plans. The interagency guidance requires it to be managed, not avoided.
- **Negative / accepted trade-off:** Tier 0 runs **outside** Azure Local's own VM management to meet the invariant. The bank owns that automation and the DR orchestrator.
- **Negative / accepted trade-off:** 1,400 VDI users change product (Horizon → AVD).

## Addendum — Step 13 Cost Check

[`docs/cost-and-risk-analysis.md`](../docs/cost-and-risk-analysis.md) modeled all three paths in [`finance/TCO-Analysis.xlsx`](../finance/TCO-Analysis.xlsx):

- **NFR-10 passes narrowly.** The Azure platform's five-year TCO is **$30.56M against $31.87M** for the status quo (4% margin). From Y3, the like-for-like run-rate is about **$1.73M a year lower**.
- **The G0-2 threshold:** on illustrative pricing, a Broadcom 3-year offer **below about $0.89M a year (−46%)** reverses this ADR to VCF.
- **The case rests on two Microsoft-side assumptions.**
  - With **0% Azure Hybrid Benefit coverage**, NFR-10 fails by $0.73M.
  - If the **2023 hosts can't be reused**, NFR-10 fails by $0.29M.
  - In a combined downside, a Broadcom discount of only 12.5% would flip the decision.

**Gate G0 therefore gains two checks, both by M4:**
- **G0-5:** Microsoft confirms in writing that Azure Hybrid Benefit (Windows Server Datacenter + SA) covers every Azure Local host core.
- **G0-6:** the 2023 hosts are confirmed on the Azure Local validated catalog.

**The G0-2 threshold is recomputed with these answers** before the Broadcom decision. Status is unchanged: Approved, conditional on G0.

