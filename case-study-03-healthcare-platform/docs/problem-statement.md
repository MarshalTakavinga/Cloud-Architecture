# Business Problem Statement — Meridian Health Network

## 1. Problem Statement

Meridian Health Network's ability to safely, reliably, and compliantly serve roughly 2 million patients now depends on a single, aging, single-site, on-premises appointment and practice-management platform that was never designed for its current scale, its current threat environment, or its current growth trajectory. The primary data center is a converted server room with no true secondary site; a full facility loss would keep scheduling, registration, and clinical workflows down for 24–48+ hours and could lose up to a day of transactional data. The core database platform is running outside vendor support. Storage is at 91% capacity. A recent credential-compromise incident moved laterally for a day and a half before detection, and the organization's cyber insurer is now conditioning renewal on controls — organization-wide MFA, immutable/offsite backups, tested DR — that the current architecture cannot deliver without a fundamental redesign. At the same time, the business is trying to grow (a 9-clinic acquisition in progress) and modernize the patient experience (self-scheduling, real telehealth) faster than a single, capacity-constrained data center can support.

## 2. Business Drivers

- **Cyber-insurance and compliance mandate** — MFA, encryption at rest everywhere, immutable/offsite backups, and annually tested DR are now conditions of renewal, not optional hardening.
- **Availability and resilience** — a single data center with a 24–48+ hour RTO is an unacceptable risk for a system that gates patient access to care at 46 sites.
- **Scalability for growth** — the in-flight 9-clinic acquisition is projected to take 4–6 months per site to onboard under the current architecture; leadership's target is weeks, not months.
- **Technical debt and end-of-support risk** — SQL Server 2014 is out of extended support; the VMware hosts are 6.5 years old on average; SAN capacity is nearly exhausted.
- **Cost trajectory** — a like-for-like hardware and SAN refresh is due regardless, plus a rising MSP/tape-courier DR cost base that still doesn't deliver a tested recovery capability.
- **Patient and staff experience** — portal latency during peak booking and a disjointed, bolted-on telehealth experience are visible, measurable friction points for both patients and front-desk staff.
- **Interoperability and future reporting** — referral partners, labs, and future value-based-care and interoperability reporting increasingly expect modern, API-based integration rather than point-to-point HL7v2 batch feeds alone.

## 3. Stakeholders and Concerns

| Stakeholder | Primary Concern |
| --- | --- |
| CIO / CTO | Technical debt, DR risk, ability to support growth without linear headcount/hardware growth |
| CISO / Compliance Officer | HIPAA Security Rule posture, cyber-insurance conditions, audit readiness |
| VP Clinical Operations | Scheduling uptime and performance; disruption to clinical workflow during any migration |
| CFO | Capital cost of a hardware/SAN refresh vs. a migration; predictable multi-year TCO |
| Clinic directors / front-desk staff | System responsiveness at peak, minimal retraining, reliable check-in during any cutover |
| Patients | Portal reliability, a coherent (not bolted-on) telehealth experience, confidence their data is protected |
| Referring hospital partners | Continued, reliable HL7/interoperability feeds through and after any change |
| Cyber insurer / external auditors | Verifiable MFA, encryption, backup immutability, and tested recovery |

## 4. Quantified Impact (Illustrative, Within the Scenario)

- 1 full business day of scheduling/check-in downtime across all 46 sites (January 2025 ice storm), reverting staff to paper processes
- ~36 hours of undetected lateral movement in the March 2026 credential-compromise incident
- 8–12 second scheduling page loads during flu-season peak, with measurable portal-abandonment and call-center-volume impact
- 4–6 months of onboarding time per newly acquired clinic under the current architecture
- 91% SAN utilization and a 6.5-year-average compute fleet age, both forcing a near-term capital refresh decision regardless of any migration
- Cyber-insurance premium exposure: renewal at up to 3x current cost if MFA, immutable backup, and tested-DR conditions are not met

## 5. What This Problem Statement Does Not Yet Decide

This document establishes the current-state architecture and the business case for change. It deliberately does not yet select a target cloud platform, a migration pattern, or a specific architecture — that follows in later stages of this case study (architecture options and styles, vendor-neutral logical design, platform-specific implementations, a weighted decision matrix, and a migration roadmap with ADRs).
