### ADR-033: Private-cloud messaging platform for the Integration Bus (LinkEngine)

**Context:**
ADR-002 already decided the Integration Bus is event-driven, replacing LinkEngine's point-to-point HL7v2 feeds — platform-neutral. ADR-030 already decided what *processes* messages once they arrive (Tanzu-hosted subscriber Deployments). Neither decided which messaging product those workloads actually subscribe to — mirroring ADR-011 (Azure Service Bus), ADR-018 (AWS SNS/SQS), and ADR-025 (Google Cloud Pub/Sub). Unlike every one of those three, there is no managed messaging service to choose a tier of here — this ADR is choosing, standing up, and operating the messaging product itself.

**Options considered:**
- Self-managed Apache Kafka, on the Tanzu platform or dedicated VMs
- Self-managed RabbitMQ (clustered, quorum queues), on the Tanzu platform
- A commercial, licensed on-premises enterprise service bus product

**Decision:** RabbitMQ, self-managed, deployed on the Tanzu platform (ADR-030), clustered with quorum queues — one exchange per message category, each routing to a queue with a configured dead-letter exchange, using a patient-ID-based routing key to preserve per-patient message ordering.

**Rationale:**
Kafka is rejected for the identical reason ADR-011/ADR-018/ADR-025 rejected it on every other platform: LinkEngine's actual requirement is reliable, ordered, retryable per-patient delivery, not high-volume log-based streaming, and Kafka has no native per-message dead-lettering — that reliability would have to be built on top of it, real engineering effort this design avoids by picking a tool built for the job, the same reasoning that holds regardless of who operates the cluster. A commercial on-premises ESB product is rejected because it adds a new commercial licensing relationship and vendor lock-in for a capability RabbitMQ's exchange/queue/routing-key model already provides — RabbitMQ maps directly onto the identical fan-out-plus-durable-per-consumer-queue pattern already established for every sibling platform (Service Bus topics/subscriptions, SNS+SQS, Pub/Sub topics/subscriptions), is mature and widely understood open-source infrastructure, and — unlike VCF, NSX, and Tanzu themselves — is a genuinely optional new vendor relationship this design chooses not to take on when a strong open-source option already fits the exact required pattern. Native dead-letter exchanges and quorum queues' cluster-wide replication provide both the durability and the retry semantics every sibling ADR required.

**Trade-off:**
**The sharpest, most consequential gap in this entire track, worth stating with full weight, not softened alongside the sizing details.** Unlike Service Bus, SNS/SQS, and Pub/Sub — every one a fully-managed service where Meridian pays for capacity and reliability but operates nothing — RabbitMQ here is infrastructure Meridian's own team stands up, patches, monitors, and keeps highly available, including its own clustering and quorum-queue replication configuration, upgrade cadence, and capacity planning. This is the single component in the private-cloud track with the least available managed analog anywhere in this design, and it sits directly in the platform's core resilience path: the entire reason LinkEngine was refactored to event-driven in the first place (ADR-002) was to fix "a lost message during an outage is just lost." If the team under-invests in operating this component well, the private-cloud track risks reproducing exactly the failure mode this migration exists to eliminate, on the one component meant to prevent it. This should carry very heavy weight in Step 10 — not be treated as equivalent to a vendor-name swap the way some of this track's other trade-offs reasonably can be.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Topology | RabbitMQ cluster, minimum 3 nodes, on Tanzu (ADR-030), spread across ESXi hosts via anti-affinity | Odd node count for quorum-queue consensus; anti-affinity keeps the cluster from losing quorum to a single host failure |
| Exchanges/queues | 4 topic exchanges (lab results, imaging, e-prescribing, appointment events), one durable quorum queue per exchange, one dead-letter exchange + queue per category | Direct parity with every sibling ADR's 4-category structure |
| Ordering | Routing key = patient ID, single active consumer per queue partition where strict ordering is required | Direct parity with Service Bus sessions (ADR-011), SNS/SQS FIFO `MessageGroupId` (ADR-018), and Pub/Sub ordering keys (ADR-025) — keeps multiple messages for the same patient processed in order |
| Dead-letter handling | Dead-letter exchange per queue, `x-delivery-limit` = 10 attempts, alerting on dead-letter queue depth via Aria Operations/the SIEM layer (`private-cloud-implementation.md` §7) | Direct parity with every sibling ADR's "10 attempts before dead-letter" |
| Durability | Quorum queues (not classic mirrored queues), publisher confirms enabled | Quorum queues are RabbitMQ's modern, Raft-consensus-based replication mechanism — the durability and consistency guarantee this design needs, publisher confirms ensure the Publish Function/service knows a message actually persisted before acknowledging upstream |
| DR | No native cross-facility replication — matching exchanges/queues pre-provisioned in the Dallas facility via the same configuration-management tooling used for Columbus (see `private-cloud-implementation.md` §9), with the identical source-system reconciliation strategy (LabCorp/Quest/Surescripts queried for messages sent during the failover window) every sibling ADR already establishes | RabbitMQ's federation/shovel plugins can bridge messages between clusters but require deliberate configuration and operational trust in a WAN link staying healthy during exactly the kind of event that triggers a DR failover — this design treats that as unproven rather than a safe default, the same honest posture ADR-018/ADR-025 took for SNS/SQS and Pub/Sub's identical native-replication gap |
| Message size | Up to 128 MB per message (RabbitMQ's practical, configuration-dependent ceiling) | HL7v2 text messages are a few KB each — comfortably within limit. Large binary content (imaging) doesn't travel through the bus — archived directly to object-equivalent storage, mirroring every sibling ADR's approach |

**Where the throughput comfort margin comes from.** The identical figures reused unchanged across every platform's messaging ADR: `current-state.md`'s ~1.1M HL7 messages/month, ~0.42 messages/second sustained, roughly 5-10 messages/second at planning-assumption peak. A 3-node RabbitMQ cluster's throughput ceiling is, like every sibling platform's messaging tier, orders of magnitude above this workload — there's no unit-sizing decision to make here either, only an operational-maturity one.

Cost for this configuration is deliberately not estimated here and stays with Step 13 — though unlike every sibling messaging ADR, the "cost" here is disproportionately staff time and operational risk rather than a metered service charge, worth flagging for the Step 13 framing itself.

See [`../docs/application-architecture-private-cloud.md`](../docs/application-architecture-private-cloud.md) §4 for the full messaging architecture narrative. No detail diagram exists yet for this ADR — hand-drawn diagrams are added incrementally and checked against this document once available.
