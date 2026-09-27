# Diagram: Migration Roadmap (Step 12)

Reference Gantt chart (Mermaid) for [`docs/migration-roadmap.md`](../docs/migration-roadmap.md) and [ADR-032](../adr/ADR-032-vcf-bridge-term.md) to [ADR-034](../adr/ADR-034-wave-plan-and-tier0-cutover.md). M1 = October 2026. Red items are the dates that can't move. A hand-drawn version will be produced from this source.

```mermaid
gantt
    title Alder Valley hybrid platform roadmap (M1 = Oct 2026)
    dateFormat YYYY-MM-DD
    axisFormat %b %y
    section Decision and commercial
    0 G0 PoCs (8-node lab), Arc on all guests, AWS closure :g0, 2026-10-01, 2027-01-31
    MRA remediation plan due                       :milestone, mra, 2026-12-31, 0d
    Gate G0 - platform decision                    :crit, milestone, gd, 2027-01-31, 0d
    VCF bridge negotiated and signed               :br, 2027-02-01, 2027-03-31
    VCF subscription ends (bridge starts)          :crit, milestone, vcf, 2027-03-31, 0d
    section Resilience track (current VMware)
    R Git plans, orchestrator, NSX parity, DG sizing :r, 2026-11-01, 2027-08-31
    Vault and clean room build                     :vlt, 2027-02-01, 2027-06-30
    Tier-0 recovery test R1                        :crit, milestone, r1, 2027-05-15, 0d
    Tier-0 recovery test R2                        :crit, milestone, r2, 2027-08-15, 0d
    Examination (Q4 2027)                          :crit, exam, 2027-10-01, 2027-12-31
    section Platform track (Azure Local)
    1 Build General and VDI instances, both sites  :p1, 2027-03-01, 2027-06-30
    2 Tier 2 waves (~1,375 VMs), dev/test to LZ    :p2, 2027-05-01, 2027-10-31
    AKS replaces Rancher                           :aks, 2027-05-01, 2027-08-31
    AVD rollout, Horizon retired                   :avd, 2027-06-01, 2027-11-30
    3 Tier 1 waves (~520 VMs)                      :p3, 2027-07-01, 2027-12-31
    44 hosts + DC1 array end of support            :crit, milestone, eos, 2027-12-31, 0d
    Build Tier-0/PCI and Oracle instances          :t0b, 2027-09-01, 2027-12-31
    4a Tier-0 non-core cutover                     :p4a, 2027-12-15, 2028-02-28
    Recovery test on Azure Local                   :milestone, r3, 2028-02-20, 0d
    4b Core banking - Oracle via Data Guard switchover :crit, p4b, 2028-02-15, 2028-04-30
    Recovery test + disconnected-week drill        :milestone, r4, 2028-04-25, 0d
    Decommission VMware, re-image 2023 hosts       :dec, 2028-05-01, 2028-06-30
    VCF bridge ends                                :milestone, be, 2028-06-30, 0d
```

## How to read it

- **The resilience track produces the examination evidence on VMware** (R1 in May 2027, R2 in August 2027), before the examination window. It doesn't depend on the migration ([ADR-033](../adr/ADR-033-mra-evidence-before-tier0-migration.md)).
- **The platform track is paced by the December 2027 hardware end of support.** Tier 2 and Tier 1 have left the old hosts by then.
- **Tier 0 moves only after the examination**, non-core first and then core banking by Data Guard switchover, with two recovery tests on Azure Local before VMware is switched off.
- **The bridge ends in June 2028, one month after decommission.** That month is the schedule margin, and ADR-032's fallback is a 12-month term plus a 3-month extension.
