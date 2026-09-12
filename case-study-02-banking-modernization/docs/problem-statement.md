# Step 1: Business Problem

## Organization

**Palisade Financial Group** (fictional, composite) is a super-regional bank holding company with approximately $21B in assets, 84 branches across the Mid-Atlantic, and a growing digital-only deposit product launched in 2022. Palisade is chartered as a national bank, placing the OCC as its primary prudential regulator, alongside standard federal obligations under GLBA (customer financial privacy), BSA/AML recordkeeping, and SOX (public-company financial reporting controls, since Palisade's holding company is publicly traded).

Deposits and loan servicing run on a 30-year-old COBOL/CICS core banking application on IBM zSystems hardware, batch-settled overnight against a DB2 for z/OS system of record. Digital banking (web and mobile) is delivered through a third-party digital banking platform running on-premises VMware, which talks to the mainframe through a nightly batch file interface rather than any real-time channel. A separate, ad hoc AWS account — stood up by the digital-channels team in 2021 without a formal cloud landing zone — hosts push-notification and mobile-analytics workloads.

## Forcing Functions

Four converging pressures are forcing this initiative now, rather than at a time of Palisade's choosing:

1. **Real-time payments has moved from roadmap item to competitive necessity.** The Federal Reserve's FedNow Service and the industry-wide migration to ISO 20022 messaging require settlement and posting capability the overnight-batch mainframe core cannot provide today — a payment initiated at 2pm on a Tuesday currently posts in the next overnight batch window, not in seconds. Two of Palisade's direct regional competitors already offer real-time push-to-card and account-to-account transfers. The board has set an 18-month target to reach parity.
2. **Mainframe cost is rising faster than the workload it serves.** MIPS-based software licensing on the mainframe has increased for four consecutive years at a rate that outpaces transaction-volume growth — Palisade is paying more to do the same amount of work, not more work. Compounding this, the average age of Palisade's COBOL/CICS engineering staff is 54, with no realistic internal hiring pipeline behind them; the mainframe isn't going away in this initiative's timeframe, but the cost and staffing trajectory make "do nothing" untenable.
3. **A new regulatory resiliency bar the current DR posture cannot meet.** Palisade crossed an asset threshold in early 2025 that subjected its critical banking functions — deposit posting and payment processing specifically — to OCC heightened standards for operational resilience. Palisade's current disaster-recovery posture is a warm secondary site with a largely manual failover runbook: roughly 36 hours to recover, with up to 4 hours of data loss. The new regulatory expectation for critical banking functions is materially tighter, and Palisade's next scheduled exam cycle will test against it directly.
4. **Real-time payments fraud has arrived ahead of real-time payments defenses.** A 2025 industry-wide wave of authorized-push-payment fraud made real-time fraud scoring a prerequisite for any real-time payments rollout, not a nice-to-have added later. Palisade's current fraud stack scores transactions in batch, hours after settlement — a real-time payment rail without a real-time fraud control is, in practical terms, an open door.

## Ranked Business Drivers

These forcing functions translate into five ranked drivers that every subsequent architecture decision in this case study must trace back to:

1. Reach real-time payments parity (FedNow / ISO 20022) within 18 months — without attempting a full core-banking replacement, which is both too slow and too risky given the mainframe's role as system of record.
2. Meet OCC heightened-standards RTO/RPO expectations for deposit posting and payment processing.
3. Flatten the mainframe cost trajectory by moving net-new workload growth off MIPS-billed capacity wherever it does not require the ledger-of-record itself to move.
4. Stand up real-time fraud detection ahead of, or alongside, the real-time payments launch.
5. Do all of the above without ever disrupting nightly batch settlement correctness — the one property of the current system that must not regress during transition.

## What This Case Study Is — and Is Not

This is a **core-adjacent modernization**, not a core replacement. The central design question, carried through every later step, is Palisade's version of the mainframe workload-placement question: which functions must move to a real-time, cloud-capable architecture to satisfy drivers 1, 2, and 4 — and which must stay exactly where they are, integrated via change-data-capture and messaging rather than rewritten, to protect driver 5 and avoid the risk profile of a full core migration. A secondary, explicitly named risk carried forward from the current-state review is the ungoverned 2021 AWS account, which represents unmanaged blast radius regardless of which platform is ultimately chosen for the new real-time capability.
