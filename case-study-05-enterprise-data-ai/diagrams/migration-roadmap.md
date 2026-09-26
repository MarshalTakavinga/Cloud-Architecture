# Diagram: Migration Roadmap (Step 11)

Reference Gantt chart (Mermaid) for [`docs/migration-roadmap.md`](../docs/migration-roadmap.md) and [ADR-028](../adr/ADR-028-teradata-contract-and-exit-sequencing.md) to [ADR-030](../adr/ADR-030-domain-dual-run-and-rollback.md). M1 = October 2026. Red items mark the dates that cannot move: the Teradata notice, the two parallel reserving closes, and the freeze after which there is no rollback to Teradata. A hand-drawn version will be produced from this source.

```mermaid
gantt
    title Harborline data and AI platform rollout (M1 = Oct 2026)
    dateFormat YYYY-MM-DD
    axisFormat %b %y
    section Platform
    0 G0 PoCs, landing zone, VPC-SC, Dataplex, Apigee   :p0, 2026-10-01, 2026-12-31
    Gate G0 passed                                        :milestone, g0, 2026-12-15, 0d
    Teradata notice + bridge signed, TD dev frozen        :crit, milestone, nt, 2026-12-31, 0d
    2024 Snowflake account closed                         :sf, 2026-10-01, 2027-01-31
    Report rationalization (retire ~70%)                  :rr, 2026-10-01, 2027-03-31
    section Governed AI track
    1 Assistant foundation (CDC, hot tier, golden set)    :a1, 2026-12-01, 2027-03-31
    Gate A1 pilot go-live                                 :milestone, ga1, 2027-03-01, 0d
    2 Pilot ~300 adjusters, personal auto, 3 states       :a2, 2027-03-01, 2027-05-31
    Gate A2 scale                                         :milestone, ga2, 2027-05-31, 0d
    3 Scale ~3,800 claims + ~600 underwriters             :a3, 2027-06-01, 2027-11-30
    section Teradata exit track
    4 Claims domain (dual-run M8-M10)                     :e4, 2027-01-01, 2027-07-31
    Teradata original term ends                           :milestone, te, 2027-06-30, 0d
    5 Policy and billing domain                           :e5, 2027-05-01, 2027-10-31
    6 Reserving and actuarial (2 parallel closes)         :e6, 2027-08-01, 2028-02-29
    Q3 2027 close in parallel                             :crit, c1, 2027-10-01, 20d
    Q4 2027 close in parallel                             :crit, c2, 2028-01-01, 20d
    7 Regulatory and remaining                            :e7, 2027-11-01, 2028-03-31
    Teradata frozen, no rollback after                    :crit, milestone, fz, 2028-03-31, 0d
    Decommission, gate T                                  :dc, 2028-04-01, 2028-05-31
    Teradata and Informatica off                          :milestone, off, 2028-05-31, 0d
    Bridge extension ends                                 :milestone, br, 2028-06-30, 0d
    section SAS retirement track
    8 SAS on lakehouse, port programs, reserving last     :s8, 2027-06-01, 2028-09-30
    SAS retired                                           :milestone, sas, 2028-09-30, 0d
```

## How to read it

- **The governed AI track doesn't depend on the Teradata track.** The assistant pilot goes live in March 2027 (M6), before the claims domain has even finished its dual-run. It needs ClaimCenter CDC, the document pipeline and the governance plane, not the warehouse ([ADR-029](../adr/ADR-029-decoupled-assistant-rollout.md)).
- **The December 2026 notice sits right after G0.** The notice is given on evidence from the translation proof of concept, and the bridge is signed at the same time ([ADR-028](../adr/ADR-028-teradata-contract-and-exit-sequencing.md)).
- **The original term end (June 2027) falls in the middle of the exit.** Only the claims domain is close to sign-off by then, which is why the bridge is needed.
- **Reserving is the critical path.** Its two parallel quarterly closes (October 2027 and January 2028) can't be compressed, and they push the Teradata freeze to March 2028 (M18).
- **Switch-off in May 2028 lands one month inside the bridge**, which ends in June 2028. That month is the only schedule margin on the exit track.
- **SAS retirement runs last.** Reserving models are ported only after the reserving domain signs off, and SAS is retired by September 2028 (M24).
