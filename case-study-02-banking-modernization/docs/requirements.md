# Steps 2–3: Capabilities Required, Requirements, and NFRs

## Step 2: Business Capabilities Required

Traced directly to the five ranked drivers in `problem-statement.md`:

1. **Real-time payment initiation and posting** — accept and post FedNow/RTP-rail payments in real time, in ISO 20022 format, without waiting for the overnight batch window.
2. **Real-time fraud scoring** — score every real-time payment for fraud risk within the authorization window, before funds are released, not after.
3. **Resilient deposit and payment posting** — meet the new OCC heightened-standards RTO/RPO for the specific functions of deposit posting and payment processing (not necessarily every mainframe function equally).
4. **Governed cloud landing zone** — a real identity-federated, network-segmented cloud foundation that both hosts the new real-time capability and formally absorbs the ungoverned 2021 AWS account's workloads.
5. **Preserved batch settlement correctness** — the nightly mainframe batch window continues to run, unmodified in its core logic, throughout and after this initiative.
6. **Regulatory auditability** — every real-time payment and every fraud decision must be reconstructable after the fact for OCC exam and BSA/AML purposes.

## Step 3: Non-Functional Requirements

| # | NFR | Target | Driven by |
|---|-----|--------|-----------|
| NFR-1 | Recovery Time Objective, critical banking functions (deposit posting, payment processing) | ≤ 2 hours | OCC heightened standards (driver 2) |
| NFR-2 | Recovery Point Objective, critical banking functions | ≤ 15 minutes | OCC heightened standards (driver 2) |
| NFR-3 | Real-time payment posting latency (initiation to posted-and-confirmed) | ≤ 5 seconds end-to-end | FedNow/RTP participation rules (driver 1) |
| NFR-4 | Fraud-scoring latency, per transaction | ≤ 300 ms | Must fit inside the payment authorization window (driver 4) |
| NFR-5 | Payment posting correctness | Exactly-once / idempotent under retry | A duplicated or dropped real-time payment is a regulatory incident, not just a bug |
| NFR-6 | Data residency | US-only for all payment and account data | OCC / Federal Reserve regulatory boundary |
| NFR-7 | Audit log retention | 7 years, immutable | BSA/AML recordkeeping requirement |
| NFR-8 | Batch settlement window | No increase from current ~5-hour window | Driver 5 — must not regress |
| NFR-9 | New workload cost trajectory | Net-new transaction growth must not add proportional MIPS cost | Driver 3 |

## Requirement / Constraint / Assumption / Risk (Section 7.1 framework)

**Requirements**
- Real-time payment posting must be visible to both the customer-facing digital banking platform and the mainframe system of record without waiting for batch.
- Fraud scoring must have access to enough transaction and account context (velocity, recent activity, device/behavioral signals where available) to make a real-time risk decision, not just the payment message itself.
- The new landing zone must support centralized identity (federated to Palisade's existing on-prem Active Directory), network segmentation, and logging/audit — and must be able to absorb the 2021 AWS account's workloads under that same governance model.

**Constraints**
- The core ledger-of-record (DB2 for z/OS, COBOL/CICS application logic) is **not** in scope to be replaced or rewritten in this initiative. Integration must happen around it — via change-data-capture, messaging, or API facade — not through modification of core COBOL programs, except where a narrowly scoped, well-tested change is unavoidable (e.g., exposing a new CDC-friendly log or a callable interface).
- The 18-month timeline for real-time payments parity is board-committed and is treated as fixed; architecture options that cannot plausibly deliver within that window are considered but explicitly scored down in Step 4/Step 10, not silently dropped.
- The outsourced card-processor relationship is out of scope to renegotiate or replace as part of this initiative.

**Assumptions**
- The digital banking platform vendor supports (or can be configured to support) a real-time API integration in addition to its existing batch file interface; this is treated as a working assumption to be validated in Step 4, not a confirmed fact.
- Existing mainframe compute capacity is sufficient for current batch and transactional load; the cost pressure in driver 3 is about the *trajectory* of net-new growth, not a present-day capacity shortfall.
- Palisade's BSA/AML and fraud teams can define fraud-scoring rules/models for a real-time system, even though the organization's operational experience today is entirely batch-based.

**Risks (carried forward to the consolidated risk register in Step 13)**
- Change-data-capture or messaging load against the mainframe under real-time, peak-hour volume is unproven at Palisade and could introduce latency or stability risk to the very core system this initiative is designed not to disrupt.
- The 2021 AWS account's current workloads (push notifications, mobile analytics) may have undocumented dependencies that complicate a clean migration into a new governed landing zone.
- Regulatory exam timing: if the OCC exam cycle lands before NFR-1/NFR-2 are met, Palisade may need an interim compensating-controls plan, which is noted here as a business risk even though it is not an architecture decision per se.
- Skills risk on both ends: COBOL/CICS expertise is scarce and aging (per `problem-statement.md`), while the real-time, cloud-native, event-driven skills this initiative needs are largely new to Palisade's engineering organization.

## Priority Weighting (feeds the Step 10 decision matrix)

Provisional weights, to be refined once architecture options are on the table in Step 4: regulatory/resiliency fit (highest), real-time payments delivery within 18 months, fraud-detection latency fit, cost trajectory impact, operational/skills fit, data residency and portability. Recorded here so that Step 10's weighted criteria can be traced back to this document rather than invented fresh at decision time.
