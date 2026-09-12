### ADR-006: Azure database service for the primary relational database

**Context:**
ADR-003 already decided the data layer stays managed relational, not NoSQL. The Azure-specific question is which managed relational offering implements that decision — Azure SQL Database and Azure SQL Managed Instance are both realistic candidates with materially different compatibility profiles.

**Options considered:**
- Azure SQL Database (PaaS, logical server model)
- Azure SQL Managed Instance (PaaS, near-full SQL Server engine compatibility)
- SQL Server self-managed on Azure VMs (IaaS)

**Decision:** Azure SQL Managed Instance, Business Critical tier, zone-redundant.

**Rationale:**
Self-managed SQL Server on VMs would recreate the exact patching and end-of-support burden ADR-001 and ADR-003 were trying to eliminate — it's technically an option but works against the reason this migration exists. Azure SQL Database is the more common default for new applications, but CareLink PM is a mature, vendor-built product likely to depend on SQL Server Agent jobs, cross-database queries, linked servers, or CLR integration — features Azure SQL Database's logical-server model doesn't support but Managed Instance does. Choosing Managed Instance up front avoids discovering an incompatibility mid-migration and having to re-platform the database a second time.

**Trade-off:**
Managed Instance costs more than Azure SQL Database at equivalent compute, and has a longer provisioning time and a less granular serverless/consumption pricing model. Accepted because compatibility risk with a vendor application Meridian can't modify outweighs the cost difference — this is exactly the kind of trade-off that should be revisited during the cost/risk analysis stage with real numbers, not assumed away here.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Region (primary) | East US | Satisfies the US-only data residency requirement; full Availability Zone support (required for zone-redundant HA below); every other service in this design (APIM Premium, Front Door Premium, Service Bus Premium) is available here too, so nothing forces a second region for capability reasons |
| Region (DR/paired) | West US | Azure's documented paired region for East US — carries forward the "paired Azure region" language already used in ADR-004 and Section 8 with an actual region name |
| Deployment tier | Managed Instance | Decided above |
| Service tier | Business Critical | Decided above — also the tier that supports zone-redundant HA, which Standard/General Purpose does not |
| Instance type | Single Instance (not Instance Pool) | Instance Pools exist for hosting many small, lightweight instances together (ISV multi-tenant SaaS patterns). Meridian needs one instance hosting two related databases — CareLink PM and MeridianConnect Portal — which Single Instance supports natively; pooling adds complexity this workload doesn't need |
| Hardware generation | Standard-series (Gen5) | The right default for an OLTP scheduling/billing workload. Premium-series (higher memory-to-vCore ratio, newer CPUs) exists for latency- or memory-sensitive workloads — nothing captured in the current-state assessment indicates that profile yet. Revisit if an Azure Migrate performance baseline says otherwise |
| Compute size | 8 vCores (starting point) | The current-state assessment captured cluster-level facts (6× Dell R740 hosts, ~85% peak shared CPU/memory across the *entire* VMware cluster) but not per-VM sizing for the two SQL Server 2014 Always On nodes specifically — that granularity wasn't captured at the business/infra-summary level this case study was built from. 8 vCores is a directional starting point sized to a mid-size regional health system OLTP workload (~2.05M patient records, ~3.6M appointments/year, 1,180 providers), consistent with consolidating two AAG-node VMs into one Business Critical instance that provides equivalent HA internally. This is explicitly provisional — real right-sizing needs an Azure Migrate assessment against the actual on-prem SQL nodes before go-live, which is why exact sizing stays listed under "Explicitly Deferred" until Step 13 |
| Redundancy | **Zone Redundant** (not Locally Redundant) | Required to match the zone-redundant HA posture already stated throughout this design (service mapping table, this ADR's own Decision line, azure-implementation.md). Zone Redundant spreads Business Critical's internal replicas across Availability Zones instead of within one; it costs more than Locally Redundant, and that cost is intentionally not estimated here — see note below |
| DR topology | Auto-failover group to a matching Business Critical instance in West US | Implements ADR-004/Section 8's warm-standby design — the secondary instance is a second, equivalently-configured Managed Instance, not a smaller/cheaper stand-in, since a warm standby that can't actually take full production load on failover isn't a real warm standby |

Cost for this configuration — including the Zone Redundant premium and the West US DR secondary — is deliberately not estimated in this ADR. This ADR fixes the *configuration*; Step 13 (cost and risk analysis) fixes the *number*, once every core resource across all four applications has been sized and can be costed together instead of piecemeal.
