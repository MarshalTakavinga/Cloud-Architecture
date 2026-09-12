### ADR-011: Azure messaging platform for the Integration Bus (LinkEngine)

**Context:**
ADR-002 already decided the Integration Bus is event-driven, replacing LinkEngine's point-to-point HL7v2 feeds. ADR-008 already decided what *processes* messages once they arrive (Azure Functions, one function app per topic). Neither ADR decided which Azure messaging service those Functions actually subscribe to — that's what this ADR settles, since "event-driven" is a style, not a specific product.

**Options considered:**
- Azure Service Bus (brokered messaging — queues/topics, subscriptions, sessions, dead-lettering)
- Azure Event Grid (push-based pub/sub for discrete, reactive events)
- Azure Event Hubs (high-throughput, log-based event streaming/ingestion)

**Decision:** Azure Service Bus, Premium tier.

**Rationale:**
LinkEngine's actual requirement is reliable, ordered, retryable delivery of HL7v2 messages per patient — not high-volume telemetry ingestion and not simple "something happened, notify subscribers" fan-out. Event Hubs is built for millions of events per second in an append-only log (think IoT telemetry or clickstreams); it has no native per-message dead-lettering or lock/complete semantics, so building HL7-grade reliability on top of it means reimplementing what a broker already provides. Event Grid is built for lightweight, discrete event routing (a blob was created, a resource changed) rather than sustained per-entity message processing with retry and dead-letter handling. Critically, neither Event Hubs nor Event Grid has a direct equivalent of Service Bus **sessions** — the feature that keeps multiple HL7 messages for the *same patient* processed in order, which `application-architecture.md` already documents as the mechanism for exactly this requirement (APIM publishes using the patient ID as the session ID). Service Bus is the only one of the three built around that requirement natively. Premium tier, not Standard, for the same reason SQL MI is Business Critical and App Service is Premium v3 in this design: Premium is what provides VNet integration (private endpoints into the data spoke, required by the Zero Trust posture already established) and dedicated, isolated throughput instead of shared multi-tenant capacity.

**Trade-off:**
Event Hubs would handle far higher raw throughput than this workload needs, and Event Grid has a lower per-message cost profile — but both would require building ordered-per-patient delivery and dead-lettering on top of a primitive that doesn't offer it, which is real engineering effort this design avoids by picking the tool built for the job. Premium tier also has a fixed Messaging-Unit cost floor even at the current low message volume, unlike Standard's pay-per-operation model. Accepted because the VNet integration requirement rules Standard out regardless of throughput; cost is a Step 13 concern, not decided here.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Tier | Premium | Decided above — VNet integration and dedicated throughput, not available on Standard |
| Messaging Units | 1 MU (starting point) | See throughput estimate below — current and reasonably-projected load is well under a single MU's published capacity |
| Topics | 4 — lab results, imaging, e-prescribing, appointment events | Already established in `application-architecture.md` — one topic per HL7 message category |
| Subscriptions | 1 per topic, each read by its own Function App (ADR-008) | Matches the "one function app per topic" decision already made — nothing here needs a fan-out to multiple independent consumers yet |
| Sessions | Enabled, session ID = patient ID | Already established — this is what keeps multiple messages for one patient in delivery order |
| Max delivery count | 10 attempts before dead-letter | A configurable retry ceiling — high enough to absorb a transient downstream fault (e.g., SQL MI briefly unavailable during a failover), low enough that a genuinely bad message (unmatched patient ID) reaches the dead-letter queue and on-call alert within a reasonable window, not after days of silent retries |
| Max message size | 1 MB (Premium default) | HL7v2 text messages are a few KB each — comfortably within this. Large binary content (imaging) doesn't travel through the bus at all; per the existing message-flow description, the raw payload is archived to Blob Storage and the bus carries the reference/event, not the binary itself |
| Availability Zones | Enabled | Premium tier supports zone redundancy in East US — matches the zone-redundant posture used everywhere else in this design |
| DR | Native Geo-Disaster Recovery pairing to a secondary Premium namespace in West US | See the caveat below — this is topology replication, not message replication |

**Where the 1 MU starting point comes from.** `current-state.md` captures LinkEngine's actual current volume: ~1.1M HL7 messages/month across LabCorp, Quest, three hospital-affiliated PACS feeds, and Surescripts. That's roughly 0.42 messages/second sustained across a 30-day month. There's no captured peak-message-rate figure for LinkEngine specifically (the current architecture doesn't expose one), so as a planning assumption — not a captured fact — this estimate applies a generous 10–20x peak-to-average burst multiplier for a batch lab-result delivery window, landing around 5–10 messages/second at peak. That's well under Service Bus Premium's commonly-cited throughput guidance of roughly up to 1,000 messages/second per Messaging Unit for messages this size. One MU is proposed as the starting point, with the same real-telemetry validation discipline used in ADR-005/006/010: monitor actual utilization after cutover and scale to 2+ MUs only if sustained load approaches capacity, which isn't expected given today's volume even accounting for the growth already captured elsewhere in this case study (the 9-clinic acquisition, general organic growth).

**A gap worth surfacing, not glossing over.** Service Bus Premium's Geo-Disaster Recovery replicates namespace *topology* (queues, topics, subscriptions, rules) to the paired region — it does **not** replicate in-flight message content. If East US goes down with messages still sitting unprocessed in a topic, those specific messages are not automatically available in the West US namespace after failover. The realistic recovery path for that narrow window is source-system resend/reconciliation (LabCorp, Quest, and Surescripts all support querying for results/messages already sent, since HL7 interface engines losing a feed mid-transit is a known failure mode these partners already handle operationally) — not an assumption that Service Bus itself carries messages across the regional failover. `diagrams/dr-failover-runbook.mmd` now carries this explicitly as its own Step 2b (Service Bus Geo-DR alias failover, called out as topology-only) plus a Step 3 reconciliation action against LabCorp/Quest/Surescripts for the failover window — this is no longer a silently-implied gap. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../diagrams/servicebus-linkengine-messaging-architecture.png`](../diagrams/servicebus-linkengine-messaging-architecture.png) for the full messaging architecture — topics, subscriptions, dead-letter queues, Geo-DR, and this exact gap called out again on the diagram itself — and [`../diagrams/dr-failover-runbook.png`](../diagrams/dr-failover-runbook.png) for the runbook step that now accounts for it end to end.
