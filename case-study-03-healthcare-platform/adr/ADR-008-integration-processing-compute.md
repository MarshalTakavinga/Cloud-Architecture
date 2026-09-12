### ADR-008: Compute for LinkEngine's Service Bus subscriber logic

**Context:**
ADR-002 decided LinkEngine becomes an event-driven integration service on Azure Service Bus. Something still has to run the code that subscribes to each topic, writes results into SQL Managed Instance, and archives the raw payload to Blob Storage. The Citrix VMs that host CareLink PM (ADR-005) are a candidate simply because they already exist and are already connected to the data spoke.

**Options considered:**
- Run the subscriber logic on the existing Citrix/CareLink PM VM tier, as a background Windows service
- Azure Functions, Premium plan, VNet-integrated, one function app per Service Bus topic
- Azure Container Apps running a small subscriber container

**Decision:** Azure Functions, Premium plan, one function app per topic.

**Rationale:**
The Citrix VM tier is sized and autoscaled around interactive clinical session load — providers opening charts, entering orders. Message-processing load (a burst of lab results arriving overnight, a backlog after an outage) follows a completely different pattern. Coupling the two onto the same VMs means a spike in one workload competes for capacity with the other, and autoscaling logic tuned for one makes the wrong call for the other. Splitting them lets each scale on its own signal — Citrix on session count and schedule, Functions on Service Bus queue length. Azure Functions specifically (over Container Apps) is chosen because it has first-class native Service Bus trigger bindings, and the workload here is genuinely event-driven, short-lived processing per message rather than a long-running service — exactly Functions' design point. The Premium plan (not Consumption) is used specifically for VNet integration, since the function has to reach SQL Managed Instance over a private endpoint.

**Trade-off:**
This adds a fourth compute platform to the environment (Citrix VMs, App Service, and now Functions), which is one more thing to patch, monitor, and staff for operationally — a real cost, not free modularity. Accepted because the alternative (background processing on interactive session hosts) risks clinical-facing performance during exactly the periods — a message backlog after an outage — when reliability matters most.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Plan structure | One shared Elastic Premium plan hosting all four function apps (lab results, imaging, e-prescribing, appointment events) | Each app still scales independently on its own Service Bus trigger — sharing the underlying plan doesn't change that. It does avoid provisioning four separate App Service Plan resources and, more importantly, four separate VNet-integration subnets for a workload this size. This ADR's own Trade-off already flags operational surface as a real cost ("one more thing to patch, monitor, staff for") — a shared plan keeps that surface as small as the four-topic design allows |
| Plan SKU | Elastic Premium EP1 (1 vCPU / 3.5 GB) | The subscriber workload is I/O-bound, not compute-bound — parse an HL7 message, write to SQL MI, archive to Blob, complete the message — not the kind of work that benefits from EP2/EP3's extra vCPU. Revisit if real usage shows CPU pressure during backlog catch-up |
| Always Ready instances | 1 per function app (4 total minimum reserved capacity) | Avoids cold-start latency on every topic, including the clinically time-sensitive ones (lab results, e-prescribing), without paying to keep a large fleet warm continuously |
| Max burst instance ceiling | 20 per function app (Azure Elastic Premium default) | Headroom for exactly the scenario this ADR's own rationale names as the reason to keep this tier separate from Citrix: "a burst of lab results arriving overnight, a backlog after an outage." Using the platform default here rather than inventing a custom ceiling that isn't backed by real backlog-size data |
| Concurrency | Service Bus session-aware trigger, `maxConcurrentSessions = 8` per instance (host.json) | Because LinkEngine's topics use sessions (session ID = patient ID, per ADR-011), each session is handled by one instance at a time to preserve per-patient ordering — but up to 8 *different* patients' sessions can process concurrently per instance. 8 is a moderate starting default, not a measured figure — there's no session-concurrency telemetry from the current on-prem LinkEngine to size this against |
| VNet integration | New subnet: `snet-func-linkengine`, 10.20.5.0/24, Application Spoke, delegated to `Microsoft.Web/serverFarms` | **This subnet didn't exist before this ADR.** Azure's regional VNet Integration requires a subnet not shared with another App Service Plan — `snet-appsvc` is already committed to the Portal's App Service plan (ADR-010), so the Functions Premium plan needs its own. `network-addressing.dot`/`.png` and `azure-implementation.md` §4.1 have been updated to add this subnet rather than leaving a real gap in the network plan |
| Identity | System-assigned managed identity per function app | Same pattern as every other compute tier in this design — Key Vault access for the SQL MI login and any partner API credentials, no embedded secrets |

This sizing is a directional starting point, same discipline as ADR-005/006/010/011: there's no per-message-processing telemetry from the current on-prem LinkEngine to validate concurrency or instance-count assumptions against, only the message-volume figures already used in ADR-011. Validate against real Application Insights data after cutover and adjust Always Ready instance count and session concurrency from there. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../diagrams/linkengine-functions-hosting-architecture.png`](../diagrams/linkengine-functions-hosting-architecture.png) for the full hosting diagram — plan structure, subnet placement, and the end-to-end connectivity path exactly as sized above.
