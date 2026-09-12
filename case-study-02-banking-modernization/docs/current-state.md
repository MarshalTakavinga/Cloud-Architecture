# Current-State Architecture

See [`diagrams/current-state-architecture.png`](../diagrams/current-state-architecture.png) for the full current-state deployment diagram, checked against this document.

## Core Banking (System of Record)

- **Platform:** IBM zSystems mainframe, single owned data center. Two logical partitions (LPARs): production and a lower environment shared across QA/UAT.
- **Application:** COBOL programs running under CICS, handling deposit accounts, loan servicing, and the general ledger. Roughly 4.2 million lines of COBOL, oldest modules dating to the original 1990s implementation with incremental additions since.
- **Data:** DB2 for z/OS is the system of record for accounts, balances, and transactions. VSAM files remain in use for a small number of legacy batch reports not yet migrated to DB2.
- **Settlement model:** Overnight batch window, approximately 5 hours (11pm–4am ET), during which the day's transactions are posted, interest accrues, and regulatory/GL reports are generated. This window is treated internally as sacred — no initiative in Palisade's recent history has been allowed to threaten it, and this case study inherits that constraint directly (see `requirements.md`).
- **Integration today:** Digital banking platform and mainframe exchange data via a nightly batch file (fixed-width, mainframe-generated), not an API or real-time feed. A transaction initiated in the mobile app today is visible to the customer client-side immediately (optimistic UI) but is not actually posted to the ledger until the next batch cycle.

## Digital Banking Channel

- **Platform:** A third-party digital banking platform (typical of the regional-bank market — vendor licensed, not built in-house), deployed on-premises on VMware vSphere, in the same data center as the mainframe.
- **Function:** Web and mobile banking UI, account aggregation view, bill pay, mobile deposit capture.
- **Coupling to core:** One-way, batch-oriented. The platform maintains its own shadow copy of balances refreshed nightly from the mainframe batch file, which is the direct cause of the same-day posting gap driving forcing function 1.

## Card Processing

- Outsourced to a third-party card processor under a standard processor agreement (as is typical for a bank of this size). Card authorization, clearing, and PCI-DSS scope for card-present/card-not-present transactions live primarily with the processor. **Out of scope** for this case study except where ACH, wire, and real-time-payments rails intersect with card-linked funding, which remains in scope.

## The 2021 AWS Account

- Stood up ad hoc by the digital-channels team in 2021 to support mobile push notifications (via a managed notification service) and a mobile-analytics pipeline.
- No formal landing zone: single AWS account, no defined network segmentation from a broader Palisade cloud estate (because none exists), no centralized identity federation to Palisade's on-prem Active Directory, and no documented data-classification review for what mobile analytics data is permitted to leave Palisade's own data center.
- Not itself a forcing function, but carried forward as a named risk in `requirements.md`: whatever platform this case study ultimately recommends, this account's governance gap needs to be resolved as part of — not separately from — the new cloud landing zone this initiative will require.

## Disaster Recovery — Current Posture

- **Topology:** Warm secondary site, async data replication for DB2, tape-based backup for older VSAM data.
- **Failover process:** Largely manual — a documented runbook exists, but full failover has historically taken approximately 36 hours in the two most recent full-scale tests, with up to 4 hours of data loss (RPO) depending on where in the replication cycle the failure occurs.
- **Why this matters here:** This posture was acceptable under Palisade's previous regulatory tier. It is not acceptable under the OCC heightened standards Palisade is now subject to for critical banking functions (deposit posting, payment processing) — see `requirements.md` for the specific RTO/RPO targets this case study must design against.

## Regulatory and Compliance Boundary (As-Is)

- **OCC** — primary prudential regulator (national bank charter); heightened operational-resilience standards apply as of the 2025 asset-threshold crossing.
- **GLBA** — customer financial information privacy and safeguarding requirements.
- **BSA/AML** — transaction monitoring and recordkeeping obligations (7-year retention baseline).
- **SOX** — financial-reporting internal controls, given the publicly traded holding company.
- **PCI-DSS** — scoped primarily to the outsourced card processor relationship today; any new architecture that touches card-linked funding for real-time payments will need its own scoping assessment (flagged as an open question for Step 4).

## Summary of What This Case Study Inherits

The current state is stable but structurally incapable of real-time posting, carries a DR posture below the new regulatory bar, and has one ungoverned cloud foothold. Nothing here is "broken" in the sense of an outage risk today — this is a capability and resilience gap, not a system in crisis, which is precisely why a full replacement is neither justified nor proportionate, and why the architecture options considered in Step 4 will center on what to add and integrate around the existing core, rather than what to replace.
