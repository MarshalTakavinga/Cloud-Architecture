# Diagram: Migration Roadmap (Step 11)

Reference Gantt chart (Mermaid) for [`docs/migration-roadmap.md`](../docs/migration-roadmap.md) and [ADR-025](../adr/ADR-025-rollout-sequencing.md) to [ADR-027](../adr/ADR-027-coexistence-and-rollback.md). M1 = October 2026. The two shutdown bars are marked critical because they are the only windows for Level 0–2 changes. A hand-drawn version will be produced from this source.

```mermaid
gantt
    title Kestrel IT/OT platform rollout (M1 = Oct 2026)
    dateFormat YYYY-MM-DD
    axisFormat %b %y
    section Security track
    0a Perimeter, SRA+MFA, backups, monitoring (all 12)   :s0a, 2026-10-01, 2026-12-31
    0b Dec shutdown - zoning 09,03,08,10,05                :crit, s0b, 2026-12-20, 10d
    06 and 11 gap remediation (weekend windows)            :s06, 2027-01-01, 2027-04-30
    Insurer staged-acceptance engagement                   :ins, 2026-10-01, 2027-06-30
    Insurer evidence package                               :milestone, m1, 2027-05-15, 0d
    0c July shutdown - zoning 01,02,04,07,12 + cell zoning :crit, s0c, 2027-07-01, 14d
    Insurer renewal                                        :milestone, m2, 2027-07-31, 0d
    section Data platform track
    1 Foundation, MSP, Outbox build, SageMaker closure     :d1, 2026-10-01, 2027-03-31
    Ramos Arizpe 2nd WAN circuit                           :d1b, 2026-10-01, 2027-06-30
    2 Pilot Plant 06 (gates G1-G6)                         :d2, 2027-02-01, 2027-06-30
    3 OEM wave 01,02,05,08,09 (+03 telemetry)              :d3, 2027-06-01, 2027-11-30
    Station integration 05,08,09 (July shutdown)           :d3b, 2027-07-01, 14d
    OEM genealogy production-ready                         :milestone, m3, 2027-11-30, 0d
    4 Remaining 04,07,10 then EU 11,12                     :d4, 2027-11-01, 2028-05-31
    5 Tier 2/3 tags, fleet models, retirements             :d5, 2027-09-01, 2028-09-30
    Downtime -30% measured                                 :milestone, m4, 2028-09-30, 0d
```

## How to read it

- **The security track ends before the data platform reaches most plants.** No plant gets a cloud bridge before its DMZ and secure remote access (Phase 0a, done by December 2026).
- **The two red bars are the whole budget for control-network change** before the insurer renewal and the OEM deadline. That is why the December 2026 bar is used for the five highest-exposure plants and nothing else.
- **The OEM genealogy milestone (November 2027)** lands inside the Q4 2027 window with a month of margin. Phase 3 relies on the July 2027 shutdown for station integration at the non-MES OEM plants.
