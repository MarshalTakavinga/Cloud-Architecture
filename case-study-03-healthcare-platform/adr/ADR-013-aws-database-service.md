### ADR-013: AWS database service for the primary relational database

**Context:**
ADR-003 already decided the data layer stays managed relational, API/wire-compatible with SQL Server, not NoSQL — that decision is platform-neutral. The AWS-specific question is which managed relational offering implements it. Unlike Azure, AWS's managed-relational lineup for SQL Server workloads has three materially different compatibility/operational profiles, not two.

**Options considered:**
- Amazon RDS for SQL Server (fully-managed PaaS, no OS-level access)
- Amazon RDS Custom for SQL Server (AWS-managed automation with OS and filesystem access)
- Self-managed SQL Server on EC2 (IaaS)

**Decision:** Amazon RDS Custom for SQL Server, Multi-AZ.

**Rationale:**
Self-managed SQL Server on EC2 recreates the exact patching and end-of-support burden ADR-001/ADR-003 exist to eliminate — technically available, but works against the reason this migration exists, the same reasoning ADR-006 used to reject it for Azure. Standard Amazon RDS for SQL Server is the more common default and does support SQL Server Agent jobs, but it does not provide OS-level or filesystem access, does not support CLR integration, and constrains linked-server configurations more than a vendor product like CareLink PM — a mature, on-prem-built application — may actually depend on. This is a real, AWS-specific divergence from the Azure comparison: Azure SQL Managed Instance gives near-full instance-level compatibility *without* trading away full managed-service automation, but AWS's standard RDS tier doesn't offer that same combination — the closer-compatibility option on AWS (RDS Custom) costs some of RDS's hands-off automation to get there. RDS Custom for SQL Server closes that gap: it provides OS and filesystem access (so CareLink PM's actual dependencies can be verified and supported directly) while AWS still manages the underlying infrastructure, patching orchestration, and automated backups — a materially different trade-off shape than Azure's, worth naming explicitly rather than assuming the two platforms map cleanly onto each other.

**Trade-off:**
RDS Custom trades away some of standard RDS's fully hands-off automation (a subset of maintenance and patching operations require more deliberate coordination than they would on standard RDS) in exchange for the compatibility headroom a vendor application may need — accepted for the same reason ADR-006 accepted Managed Instance's higher cost and slower provisioning over Azure SQL Database: compatibility risk with an application Meridian doesn't control outweighs the operational cost difference. A second, AWS-specific trade-off worth flagging up front: RDS Custom's cross-region disaster-recovery tooling is materially less mature than standard RDS or Aurora's native cross-region read replicas — see Section 8 gap in `aws-implementation.md` for how this is handled and why it's a real limitation, not glossed over. This should be revisited during the cost/risk analysis stage with real numbers.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Region (primary) | us-east-1 (N. Virginia) | Satisfies the US-only data residency requirement; full 6-AZ availability (more than the 3 used, giving headroom); every other AWS service in this design is available here, so nothing forces a second region for capability reasons — same logic ADR-006 used for East US |
| Region (DR/paired) | us-west-2 (Oregon) | A standard, widely-used AWS DR pairing for US-only workloads — carries forward the "paired region" language from ADR-004 with an actual AWS region name |
| Deployment | Amazon RDS Custom for SQL Server | Decided above |
| Multi-AZ | Enabled | Zone-level HA within the primary region — direct parity with ADR-006's zone-redundant Business Critical tier |
| Instance class (starting point) | `db.m6i.2xlarge` (8 vCPU / 32 GiB) | Direct sizing parity with ADR-006's 8 vCores — same caveat applies: this is a directional starting point, not a validated figure, since (as ADR-006 notes) the current-state assessment captured cluster-level facts, not per-VM SQL Server sizing |
| Storage | Amazon EBS io2 Block Express, provisioned IOPS | The consistent low-latency, high-IOPS profile an OLTP scheduling/billing workload needs — the closest AWS storage analog to Business Critical's local SSD-backed storage tier |
| Backup | Automated backups via RDS Custom, 7-day retention (starting point) | Standard RDS-managed backup automation, retained despite the OS-level access RDS Custom grants |
| DR topology | Continuous change-data-capture replication (AWS DMS) from the primary instance to a warm-standby SQL Server instance in us-west-2 | See the gap called out below — this is *not* a native, one-click cross-region failover group the way ADR-006's Azure design has; it's a deliberately chosen mechanism to hit the same RPO target despite that gap |

**A gap worth surfacing, not glossing over — cross-region DR for RDS Custom.** Standard Amazon RDS and Aurora both offer native cross-region read replicas that make cross-region DR close to turnkey. RDS Custom for SQL Server does not have that same native cross-region replication feature at the time of this design. Closing that gap without giving up the compatibility RDS Custom was chosen for means running AWS DMS (Database Migration Service) in continuous CDC (change-data-capture) mode from the primary RDS Custom instance to a warm-standby SQL Server instance (RDS Custom or, if DMS CDC proves insufficiently low-latency in practice, a self-managed EC2 instance kept purely as a DR target) in us-west-2. This is explicitly flagged as needing validation against a real RPO measurement before go-live — DMS CDC replication lag is a function of change volume and network path, not a guaranteed sub-15-minute figure the way an Azure SQL MI auto-failover group's replication is. This is a genuinely different risk profile than ADR-006's Azure design, not a like-for-like swap, and should be weighed as such in the eventual decision matrix (Step 10).

Cost for this configuration — including the Multi-AZ premium, io2 storage, and the DMS-based DR path — is deliberately not estimated in this ADR, the same discipline ADR-006 applied. This ADR fixes the *configuration*; Step 13 fixes the *number*.

See [`../docs/application-architecture-aws.md`](../docs/application-architecture-aws.md) §1 for how CareLink PM and the Portal each connect to this instance, and [`../diagrams/sql-managed-instance-architecture-aws.png`](../diagrams/sql-managed-instance-architecture-aws.png) for the zone layout and network path, including LinkEngine's Lambda functions as the third RDS Custom consumer alongside CareLink PM and the Portal.
