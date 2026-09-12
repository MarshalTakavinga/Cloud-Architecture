# Preliminary Requirements & NFRs — Meridian Health Network

Captured before any platform or architecture-style decision. These will be refined once target-state design begins, but should not materially change based on which cloud platform is ultimately chosen.

## 1. Non-Functional Requirements — First Pass

| Question | Preliminary Answer |
| --- | --- |
| SLA target | 99.9% for scheduling/registration during business hours (7am–8pm local, 7 days) as a starting target, pending stakeholder sign-off |
| RTO | ≤ 4 hours for the core scheduling/PM platform (down from 24–48+ hours today) |
| RPO | ≤ 15 minutes for transactional data (down from ~24 hours today) |
| Concurrent users / peak TPS | ~1,800 concurrent Citrix/PM sessions at Monday-morning peak today; design for 2–3x headroom given growth and acquisition plans |
| Data residency / compliance | Patient data (PHI) must remain within the United States; architecture must support HIPAA Security Rule technical safeguards |
| Growth (12/24/36 months) | +9 clinics in-flight; historical organic growth of 2–4 clinics/year; telehealth and portal usage growing faster than physical visit volume |
| Budget | Capital refresh (compute + SAN) is due in the current on-prem model regardless; migration business case should be evaluated against that baseline cost, not against $0 |
| Threat model | Credential compromise / phishing (realized in March 2026), ransomware against backups, insider misuse of shared service accounts, regional facility loss (realized in January 2025) |
| Operations model | 16-person internal team plus after-hours MSP NOC; any target architecture should reduce, not increase, undifferentiated operational burden on this team |
| Rollback strategy | To be defined per migration wave in the roadmap stage — no big-bang cutover of all 46 sites at once |

## 2. Requirement / Constraint / Assumption / Decision / Risk — Kept Explicitly Separate

No architecture **decisions** are made yet — that intentionally waits for the design stages that follow.

| Concept | Statement |
| --- | --- |
| Requirement | RTO for core scheduling/PM must be ≤ 4 hours; RPO ≤ 15 minutes. |
| Requirement | MFA must be enforced for all clinical and administrative access, not a subset. |
| Requirement | All PHI at rest must be encrypted, with no exceptions carried forward from the legacy unencrypted LUNs. |
| Requirement | Backups must be immutable and geographically separate from the primary environment. |
| Constraint | PHI must remain within the United States. |
| Constraint | Migration cannot require a single all-46-site cutover weekend — clinical operations cannot tolerate that blast radius. |
| Constraint | Existing HL7v2 interfaces to LabCorp, Quest, hospital PACS feeds, and Surescripts must keep working throughout any transition. |
| Assumption | Peak concurrent scheduling/PM sessions will not exceed roughly 5,000 within the 36-month planning horizon. |
| Assumption | The 9-clinic acquisition closes within the next 12 months and its onboarding timeline is a real near-term forcing function, not a hypothetical. |
| Risk | A rushed, compliance-driven timeline (cyber-insurance renewal) could push toward a platform choice that isn't fully evaluated. |
| Risk | Legacy CareLink PM thick-client/Citrix delivery model may constrain which target architectures are realistic without an application-layer change. |
| Mitigation (planned) | Run a full vendor-neutral decision matrix before committing to a platform, even under time pressure. |

## 3. Explicitly Out of Scope for This Document

- Target cloud architecture (Azure / AWS / GCP / private) — later stage
- Migration pattern selection (e.g., rehost vs. replatform vs. Strangler Fig on CareLink PM) — later stage
- Weighted decision matrix and platform recommendation — later stage
- Cost modeling and 3–5 year TCO comparison — later stage
- ADRs — these begin once real decisions are made, not before
