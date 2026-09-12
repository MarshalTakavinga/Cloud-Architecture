### ADR-020: GCP database service for the primary relational database

**Context:**
ADR-003 already decided the data layer stays managed relational, not NoSQL — platform-neutral. The GCP-specific question is which managed relational offering implements that decision. Unlike the Azure comparison (Azure SQL Database vs. Managed Instance) and the AWS comparison (standard RDS vs. RDS Custom), GCP genuinely doesn't offer a middle tier between "fully managed, no OS access" and "you manage the whole VM" — that gap itself is the central question this ADR has to resolve, not just a side note.

**Options considered:**
- Cloud SQL for SQL Server (fully managed PaaS — provisioning, patching, backups, and HA handled by Google; no OS or filesystem access)
- SQL Server self-managed on Google Compute Engine VMs (IaaS — full OS/filesystem access, but Meridian owns patching and HA end to end)
- Google Cloud Bare Metal Solution for SQL Server (dedicated physical hardware in a Google-adjacent facility, connected via Partner Interconnect, running a fully self-managed Windows/SQL Server stack with true hardware-level access)

**Decision:** Cloud SQL for SQL Server, Enterprise Plus edition, Regional (HA) configuration.

**Rationale:**
ADR-013's reasoning for AWS was "a mature vendor product like CareLink PM is likely to depend on OS-level integrations, CLR functionality, or linked-server configurations that a fully-managed tier doesn't support" — and that pushed AWS toward RDS Custom, a tier that gives OS access *without* giving up managed automation. **GCP has no equivalent middle tier.** Cloud SQL for SQL Server does not grant OS-level or filesystem access, and there is no "Cloud SQL Custom." The realistic choice on GCP is therefore genuinely binary in a way it wasn't on AWS or Azure: accept Cloud SQL's compatibility ceiling, or self-manage SQL Server on Compute Engine (or, more extreme still, on Bare Metal Solution) and recreate exactly the patching and end-of-support burden ADR-001 and ADR-003 were trying to eliminate in the first place. Self-managing on Compute Engine is rejected for the same reason ADR-003 rejected it generically: it's technically an option, but it works directly against the reason this migration exists. Bare Metal Solution is rejected for the same reason and more — it's a colocation-adjacent product aimed at workloads with a genuine hardware-level dependency (specific storage arrays, licensing tied to physical cores), not a fit for a scheduling/billing OLTP workload with no such requirement, and it would mean Meridian re-acquiring exactly the kind of physical-infrastructure operational burden this whole case study exists to escape. Cloud SQL for SQL Server is chosen as the default, accepting its compatibility risk as a real, named trade-off rather than discovering it unplanned mid-migration — see the Trade-off section for how that risk is managed rather than ignored.

**Trade-off:**
If a pre-migration compatibility assessment surfaces a genuine blocking dependency Cloud SQL can't support — `xp_cmdshell`, unrestricted CLR (`EXTERNAL_ACCESS`/`UNSAFE` assemblies), or filesystem-level access CareLink PM's vendor confirms is load-bearing — this decision has to be revisited toward self-managed SQL Server on Compute Engine, with the patching burden that implies, or toward re-opening the Repurchase option ADR-001 deferred. That's a real, not cosmetic, platform-specific risk: the equivalent AWS and Azure ADRs (RDS Custom, Managed Instance) don't face this same binary choice, because both platforms offer a managed-with-OS-access middle tier GCP doesn't. Named here explicitly so it carries real weight in the Step 10 decision matrix, not glossed over as "the same decision, different vendor name." On the positive side of the ledger, Cloud SQL for SQL Server supports native cross-region read replicas — a genuine capability RDS Custom explicitly lacks (ADR-013's own flagged gap) — so the DR story this decision enables is, in one specific respect, stronger than the AWS equivalent; see Section 8 of `gcp-implementation.md`.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Region (primary) | `us-central1` | Satisfies the US-only data residency requirement; full multi-zone support (required for Regional/HA below); every other service in this design is available here too |
| Region (DR) | `us-west1` | A geographically separate US region from `us-central1`, carrying forward the "paired/secondary region" language already used in ADR-004 with an actual region pair |
| Edition | Enterprise Plus | The tier that supports Cloud SQL's newer HA and read-replica performance features (faster failover, cross-region replica support) — decided above |
| Availability type | Regional (HA) | Synchronous replication to a standby in a second zone within `us-central1`, with automatic failover — the direct GCP analog to ADR-006's Zone Redundant Business Critical tier and ADR-013's RDS Custom Multi-AZ |
| Machine type | `db-perf-optimized-N-8` (8 vCPU, comparable memory-to-vCPU ratio) | Direct sizing parity with ADR-006's 8-vCore starting point and ADR-013's equivalent RDS Custom instance class — same directional-starting-point caveat: no per-VM sizing was captured for the current on-prem SQL Server 2014 nodes, so this is provisional pending real telemetry |
| Storage | SSD, 500 GB starting point, automatic storage increase enabled | Matches the OLTP scheduling/billing profile; automatic growth avoids a hard-stop outage from underestimated storage, revisited with real usage data before go-live |
| Cross-region DR | Cross-region read replica in `us-west1`, promotable on failover | Implements ADR-004/Section 8's warm-standby design using a Cloud SQL-native feature — unlike RDS Custom (ADR-013), which needed a separate replication service (AWS DMS) bolted on because RDS Custom itself has no native cross-region replica support, Cloud SQL's cross-region replica is a first-class feature of the service being used, not an add-on |
| Encryption | Encrypted at rest by default (Google-managed keys), Customer-Managed Encryption Keys (CMEK) via Cloud KMS for the PHI-handling instance specifically | Matches the "no exceptions carried forward from unencrypted legacy LUNs" requirement in `requirements.md`; CMEK gives Meridian key-rotation and revocation control consistent with the compliance posture the other two platform designs assume |

Cost for this configuration — including the Regional/HA premium and the cross-region replica — is deliberately not estimated in this ADR, the same discipline ADR-006/ADR-013 applied. This ADR fixes the *configuration*; Step 13 fixes the *number*.

See [`../docs/application-architecture-gcp.md`](../docs/application-architecture-gcp.md) §1 for how CareLink PM and the Portal both connect to this instance, and [`../diagrams/sql-managed-instance-architecture-gcp.png`](../diagrams/sql-managed-instance-architecture-gcp.png) for the detailed zone/DR/network diagram matching this ADR's Proposed Configuration (Regional HA synchronous standby, cross-region read replica, Private Services Access connectivity, and CMEK) — hand-reproduced, matched this ADR on the first submission.
