# Current-State Architecture

A current-state diagram is still to be drawn. Sections 1–4 below map directly onto the usual source → integration → storage → consumption layers.

## 1. Source Systems

| System | Scope | Hosting | Data-access pattern today |
|---|---|---|---|
| Guidewire PolicyCenter / ClaimCenter / BillingCenter | Harborline + migrated Prairie Shield book (about 85% of premium) | Self-managed, Hartford data center (Oracle databases) | Nightly Informatica extracts from the operational databases. Some near-real-time messaging from ClaimCenter to downstream vendors |
| Coastal Assurance legacy policy/claims | The Coastal book (about 15% of premium), in decommissioning (separate program, 2028 target) | IBM i (AS/400), Jacksonville data center | Nightly flat-file extracts |
| Enterprise content management (ECM) | About **95M claim documents, ~600 TB** (photos and scanned PDFs are most of the volume; about 40M documents carry extractable text, ~8 TB of text) | On-prem, Hartford | Retrieval by claim number only. There is no full-text search across claims |
| Third-party data | Motor vehicle reports, property characteristics, weather/catastrophe feeds, credit-based insurance scores (where permitted) | Vendor APIs and SFTP | Ad hoc loads into Teradata and SAS |

## 2. Integration

- **Informatica PowerCenter** (on-prem): about **2,400 nightly jobs**, with a batch window of 01:00–06:00 ET. About 30% of jobs have no identifiable consumer. That estimate comes from a 2025 lineage review, which could trace only about half of the job estate.
- No change-data-capture and no streaming. Every analytical view is at least a day old.
- Point-to-point file feeds to about 40 downstream vendors and regulators.

## 3. Storage and Compute

- **Teradata EDW**: about **180 TB compressed (~450 TB raw)**, a 12-year-old integrated model built by a consultancy in 2014 and extended by four internal teams since. There is heavy use of Teradata-specific SQL (BTEQ scripts, stored procedures, macros, QUALIFY-heavy analytics) and about **1,800 stored procedures and macros**. The appliance is near end of hardware support.
- **Coastal SQL Server warehouse**: about 12 TB, separate, and loaded only partly into Teradata.
- **SAS 9.4** (on-prem grid): actuarial reserving, pricing, and loss-cost models. About 40 actuaries and 12 data scientists use it, with about 900 production SAS programs.
- **The 2024 Snowflake account** (actuarial): opened on a departmental credit card for faster ad hoc work. It holds copies of claims and policy extracts, has no SSO, and has no data-classification review. It is not a forcing function, but it is carried as a named governance risk, exactly like the ad hoc cloud accounts in Case Studies 2 and 4. It is **not** a vote for Snowflake, and the evaluation treats it neutrally.

## 4. Consumption

- About **14,000 reports** across Tableau (about 60%) and SSRS, used by about 1,100 BI users. A 2025 usage scan found that **about 70% had not been opened in 12 months**.
- Regulatory reporting (statistical plans, annual statement schedules) is assembled in SAS and Excel.
- There are **no governed AI capabilities**. Generative AI tools are blocked after the March 2026 incident (`problem-statement.md`).

## 5. Identity, Security, and Governance (As-Is)

- **Identity:** Microsoft Entra ID for the workforce (Microsoft 365 is standard). Teradata and SAS use AD-synchronized accounts. Snowflake uses local accounts.
- **Classification:** a written policy exists (Public / Internal / Confidential / Restricted, where Restricted covers PII, medical, and financial account data). It is **not applied at the column or document level** anywhere. Teradata access is granted by schema, so most analysts can see PII columns they do not need.
- **Governance:** there is no data catalog, no lineage beyond the partial 2025 Informatica review, and no model inventory. The CISO's office runs an NYDFS Part 500-aligned security program (Harborline writes business in New York).
- **Retention and legal hold:** claims are retained for 7 years after closure, and longer under litigation hold. Hold is applied manually in ECM.

## 6. Cost Baseline (legacy data platform, annual)

| Item | Annual cost |
|---|---|
| Teradata licence and support | ~$3.9M |
| Teradata appliance refresh (if renewed) | ~$6.0M one-time |
| SAS licences (grid + desktop) | ~$1.4M |
| Informatica PowerCenter licence and support | ~$0.9M |
| Data-center hosting share (power, space, backup) for the above | ~$0.6M |
| **Recurring legacy data-platform run cost** | **~$6.8M / yr** |

This baseline is the reference for driver 5's FinOps target.

## 7. What This Case Study Inherits

The estate *works*. Reserving closes, reports run, and regulators get their filings. What it cannot do is serve AI safely:
- Unstructured claims knowledge is locked in ECM.
- PII is broadly visible in the warehouse.
- Nothing is cataloged or lineage-tracked.
- The only cloud foothold is ungoverned.

As in Case Studies 2 and 4, this is a capability and governance gap rather than a system in crisis. **The Teradata notice date (31 December 2026) is what turns it into a deadline.**
