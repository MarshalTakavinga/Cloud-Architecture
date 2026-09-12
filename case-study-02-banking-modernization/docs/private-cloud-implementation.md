# Step 9: Private-Cloud Implementation

## Purpose of This Step

[Step 5](logical-design.md) defined nine logical components without naming a single platform service. [Steps 6](azure-implementation.md)–[8](gcp-implementation.md) answered that question for Azure, AWS, and GCP. This step answers it for the fourth track: dedicated, Palisade-owned infrastructure. This case study runs all four tracks — unlike Case Study 1's three-way hyperscaler-only comparison — specifically because Palisade's mainframe investment and OCC heightened-standards scrutiny make "stay on private infrastructure for the new capability too" a live, defensible option (`README.md`'s scope note), not an afterthought.

This track has a structural advantage and a structural cost that recur across every one of its six decisions, and both are named plainly rather than glossed over: placing the workload inside Palisade's own existing data center ([ADR-023](../adr/ADR-023-private-cloud-platform-and-facility-strategy.md)) eliminates the hybrid-connectivity problem every hyperscaler track had to solve ([ADR-026](../adr/ADR-026-private-cloud-network-topology.md)); but the absence of any managed-service layer means Palisade's own team takes on operational ownership — of Kubernetes, of database HA, of messaging clustering, of certificate rotation — that every hyperscaler track gets for free from its platform ([ADR-024](../adr/ADR-024-private-cloud-compute-platform.md), [ADR-025](../adr/ADR-025-private-cloud-database.md), [ADR-027](../adr/ADR-027-private-cloud-identity.md), [ADR-028](../adr/ADR-028-private-cloud-messaging.md)).

## Service Mapping

| Logical Component (Step 5) | Private-Cloud Implementation | Decision Recorded In |
|---|---|---|
| ISO 20022/FedNow Gateway (bought, ADR-002) | Deployed as a vendor appliance, racked in the same data-center segment, reachable over the internal network | [ADR-026](../adr/ADR-026-private-cloud-network-topology.md) |
| Hold/Release Adapter | VMware Tanzu Kubernetes Grid (on VMware Cloud Foundation) | [ADR-024](../adr/ADR-024-private-cloud-compute-platform.md) |
| Fraud Orchestration Service | VMware Tanzu Kubernetes Grid | [ADR-024](../adr/ADR-024-private-cloud-compute-platform.md) |
| Ledger-of-Intent Service (application) | VMware Tanzu Kubernetes Grid | [ADR-024](../adr/ADR-024-private-cloud-compute-platform.md) |
| Ledger-of-Intent Service (data store) | Self-managed PostgreSQL, Patroni-orchestrated HA cluster (primary + secondary site) | [ADR-025](../adr/ADR-025-private-cloud-database.md) |
| Event Bus | Self-managed RabbitMQ cluster, Consistent Hash Exchange for per-payment ordering | [ADR-028](../adr/ADR-028-private-cloud-messaging.md) |
| CDC Connector / Hold-Release path to the mainframe | Internal data-center network — no WAN circuit, since the workload shares the mainframe's facility | [ADR-026](../adr/ADR-026-private-cloud-network-topology.md) |
| Reconciliation Process (nightly, [ADR-003](../adr/ADR-003-provisional-vs-confirmed-state-model.md)) | A Kubernetes CronJob in the same Tanzu cluster as the three always-on services | [ADR-024](../adr/ADR-024-private-cloud-compute-platform.md) |
| Identity (workforce + workload) | Direct join to Palisade's existing on-prem Active Directory domain; mutual TLS via Palisade's internal PKI for service-to-service auth | [ADR-027](../adr/ADR-027-private-cloud-identity.md) |
| Landing zone / network segmentation | VLANs and VMware NSX micro-segmentation within Palisade's existing data-center network | [ADR-026](../adr/ADR-026-private-cloud-network-topology.md) |
| Audit/Compliance Log | Self-managed PostgreSQL (append-only table, INSERT-only role, application-enforced checksums) | [ADR-025](../adr/ADR-025-private-cloud-database.md) |
| 2021 AWS account workloads (Replatform, Step 4) | **Not migrated onto this footprint** — explicitly out of scope for this track; disposition left open for Step 12 if this platform is selected | [ADR-026](../adr/ADR-026-private-cloud-network-topology.md) |

## Why Six Decisions, and Why They Don't Map One-for-One to the Other Tracks

Every hyperscaler track needed a hybrid-connectivity ADR and a cloud-landing-zone ADR. This track needed neither in that shape: [ADR-023](../adr/ADR-023-private-cloud-platform-and-facility-strategy.md) (platform and facility strategy) has no equivalent on the other three tracks at all — none of them had to decide *where a facility physically is*, since a hyperscaler abstracts that question away entirely — and [ADR-026](../adr/ADR-026-private-cloud-network-topology.md) does the job of both a landing zone and a hybrid-connectivity decision at once, because co-location with the mainframe collapses them into a single network-topology question. The result is still six ADRs (023–028), but the six areas they cover are not a direct one-for-one substitution for the other tracks' six.

## Network and Security Summary

- **Segmentation:** A dedicated VLAN, isolated by NSX micro-segmentation, hosts the new payment-processing workload inside Palisade's existing data-center network — structurally separate from the mainframe's own segment and from every other system in the facility.
- **Connectivity to the mainframe:** The synchronous hold/release call and the CDC feed traverse the internal data-center backbone directly — no WAN circuit, no public internet exposure at any point, and no hybrid-connectivity cost or lead time to plan for ([ADR-026](../adr/ADR-026-private-cloud-network-topology.md)).
- **Identity:** Workforce and platform administrative access uses Palisade's existing on-prem Active Directory directly; service-to-service calls use mutual TLS certificates from Palisade's own internal PKI ([ADR-027](../adr/ADR-027-private-cloud-identity.md)).
- **Governance guardrails:** NSX distributed firewall rules enforce the same segmentation boundary at the workload level that Organization Policy, Azure Policy, and Service Control Policies enforce natively on the other three tracks — here, configured and maintained directly by Palisade's own network and platform teams rather than inherited from a cloud provider's policy engine.

## Observability

Tanzu cluster logs and metrics, PostgreSQL logs, and RabbitMQ metrics feed into Palisade's own centralized logging stack (e.g., an internally operated ELK/OpenSearch deployment or equivalent) rather than a cloud-native logging service — another instance of this track's recurring theme: observability tooling here is operated by Palisade, not consumed as a managed service.

## Known Deferred Items

Consistent with this case study's convention: the specific hyperconverged infrastructure sizing (host count, CPU/memory/storage per site) and the Tanzu, PostgreSQL, and RabbitMQ cluster sizing are all deferred to Step 13's cost analysis; diagrams for this track are not yet drawn; the specific CICS transaction for the [ADR-001](../adr/ADR-001-mainframe-integration-approach.md) hold/release call remains an outstanding mainframe-team decision, unresolved here exactly as in every other track. Two items are unique to this track: the capital cost of new hyperconverged infrastructure at both sites has no hyperscaler-track equivalent to compare against directly, and must be modeled as its own line in Step 13 rather than adapted from another track's cost structure; and the 2021 AWS-equivalent workloads' disposition is explicitly left open ([ADR-026](../adr/ADR-026-private-cloud-network-topology.md)), a genuine unresolved question if this track is selected, not an oversight.
