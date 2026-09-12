### ADR-001: Migration strategy for the CareLink PM core

**Context:**
Meridian must move off a single-site, out-of-support on-premises platform inside a compliance-driven timeline (cyber-insurance renewal conditions: MFA, encryption, immutable/offsite backup, tested DR). CareLink PM is a third-party vendor product — Meridian does not own or have access to its source code.

**Options considered:**
- Rehost the CareLink PM VMs as-is into cloud IaaS, no other change
- Replatform: move the app tier and swap the unsupported SQL Server 2014 for a supported, cloud-managed database engine, with minimal application change
- Repurchase: replace CareLink PM entirely with a cloud-native SaaS practice-management/EHR platform
- Refactor / re-architect the core application
- Retain on-premises

**Decision:** Replatform the CareLink PM application and database core.

**Rationale:**
Refactor is not viable — Meridian doesn't own the source. Repurchase (a full PM/EHR vendor switch) is a legitimate long-term option but is a multi-year, org-wide change-management and data-conversion project across 46 sites and ~1,180 providers; it doesn't fit the compliance-driven timeline and shouldn't be forced into it. Rehost alone doesn't resolve the unsupported-database risk that's a recurring finding in Meridian's security assessments. Replatforming — moving the infrastructure and swapping the database engine while leaving the application layer materially unchanged — directly resolves the RTO/RPO, encryption, and unsupported-software risks identified in the Step 3 requirements, on a timeline that can realistically meet the insurance renewal.

**Trade-off:**
Replatforming does not reduce Meridian's long-term dependency on CareLink PM as a vendor, and it doesn't modernize the thick-client/Citrix delivery model users interact with today. That risk is deliberately deferred, not resolved — flagged here as a candidate for a future ADR once the immediate DR/compliance risk is closed out.

**Status:** Proposed
