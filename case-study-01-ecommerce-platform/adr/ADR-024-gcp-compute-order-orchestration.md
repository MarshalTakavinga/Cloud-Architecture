### ADR-024: GCP compute for Inventory & Order Orchestration

**Context:**
ADR-001 decided Inventory & Order Orchestration is Rearchitect  event-driven, asynchronous, replayable, the one place ADR-002 scoped event-driven adoption to. Its shape is a multi-step saga (reserve inventory → confirm payment → create order → hand off to fulfillment) that needs to track its own in-progress state across several asynchronous steps, retry individual steps, and compensate (release a reservation) if a later step fails  a genuinely different compute problem than Storefront & Catalog, Cart, and Checkout & Payment (ADR-021), which are synchronous and reachable from the API Gateway. Order Orchestration reacts to events on the Event Bus (ADR-025) rather than serving inbound HTTP traffic directly.

**Options considered:**
- Run Order Orchestration as another Cloud Run service (the same pattern as ADR-021), a long-running consumer process polling the event bus, scaled on message backlog.
- Cloud Functions, one function per event type, invoked directly off the event bus.
- Google Cloud Workflows, with Cloud Run/Cloud Functions as the individual saga steps, triggered by an Eventarc trigger on the `order-placed` event.

**Decision:**
Google Cloud Workflows, one workflow definition deployed independently per active region, triggered by an Eventarc trigger matching `order-placed` events (ADR-025). Each step in the workflow calls a small, single-purpose Cloud Run service  reserve inventory, confirm payment, create order, hand off to fulfillment  with Workflows' native `retry` policies handling per-step retry and `try`/`except` blocks routing to explicit compensating steps (for example, a `ReleaseInventory` call on the failure path out of the payment-confirmation step).

**Rationale:**
A same-pattern-as-ADR-021 Cloud Run consumer service was seriously considered, and it would work  but it's not chosen as the default here because doing so would import the same cost ADR-008 and ADR-016 both accepted and then deliberately avoided on the other two tracks: a saga is a workflow-orchestration shape, not a stateless function-per-event shape, and a plain consumer service still has to build and own its own saga-state tracking, per-step retry, and compensation logic inside application code running on a long-lived process. GCP has a service purpose-built to remove that cost structurally rather than just relocate it: Cloud Workflows *is* a managed, durable, serverless orchestration engine  each execution's current step, full history, and variable state is tracked by the service itself, not by application code; retries follow a declarative per-step `retry` policy (exponential backoff, maximum attempts, specific error-code matching); and failures branch to an explicit compensating step via a `try`/`except` construct  all without a single always-on process holding saga state in memory or in a database table the application team has to design and maintain. The individual Cloud Run services handling each step are simple, stateless, and scale independently with no fleet to size for peak concurrency. Plain Cloud Functions-per-event (the second option) is rejected for the identical reason ADR-008 and ADR-016 rejected their own platforms' plain-function options: without something coordinating the steps, the saga's cross-step state  what's already been reserved, what still needs compensating  has to live somewhere application code manages directly, reintroducing exactly the problem a workflow engine exists to solve.

This is the third and final case in this case study's platform comparison where the genuinely native answer is architecturally different from a mechanical restatement of the Azure pattern, and it's the same underlying discovery both other tracks made independently: Container Apps (Azure), Step Functions (AWS), and Cloud Workflows (GCP) are three platform-specific products that each remove the same saga-coordination cost structurally, rather than three names for the same idea. Worth stating plainly rather than treating GCP as the "third me-too" answer  the underlying problem (saga state, retries, compensation) is identical across all three platform tracks; GCP happens to have its own purpose-built managed product that addresses it directly, distinct from the other two.

**Trade-off:**
Cloud Workflows pricing is per internal step and per external (HTTP) call, not per compute-hour. At Solstice's peak volume (`requirements.md` §1's ~3,750 orders/minute system-wide, each saga touching roughly 4–6 steps), this needs to be modeled carefully against a fixed-capacity compute alternative before the cost-analysis stage  the same "flagged forward, not resolved here" treatment ADR-016 gave Step Functions' transition-based pricing. Cloud Workflows executions carry their own payload/variable-size and step-count limits; not a real constraint for a saga passing order/inventory/payment identifiers and small status metadata, but worth stating rather than assuming, and worth verifying explicitly once real payloads exist. Operationally, Cloud Workflows' own YAML/JSON-based workflow syntax is a genuinely different authoring and testing model than a regular application codebase  a real onboarding cost for a 22-person engineering team that doesn't currently author Workflows definitions, the same category of trade-off ADR-016 accepted for Step Functions' ASL and ADR-018/ADR-026 accepted for a newer identity product's operating model. Cold starts on the individual Cloud Run step services are a minor, not zero, latency contributor per step  acceptable for the same reason the other two tracks accepted their own equivalent lag: order processing isn't latency-critical the way a product-page load is.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Orchestration engine | Google Cloud Workflows, one workflow definition per active region |
| Trigger | Eventarc trigger matching `order-placed` events on that region's event bus (ADR-025), invoking the workflow execution directly |
| Step compute | Cloud Run, one service per saga step (reserve inventory, confirm payment, create order, hand off to fulfillment) plus compensating steps (e.g., release inventory) |
| Retry policy | Per-step `retry` policy  exponential backoff, max 3 attempts, matched on transient error types (throttling, timeout) before falling through to `except` |
| Compensation | Per-step `try`/`except` block routes to a compensating step (e.g., a failed payment-confirmation step triggers a `ReleaseInventory` call) before surfacing failure back to Checkout & Payment |
| Concurrency | No fixed floor/ceiling to manage  Workflows and its Cloud Run step services scale per-execution; regional Cloud Run concurrency monitored as a guardrail, not provisioned as a capacity number |
| Saga-state store | Workflows' own execution history and variable state, durable and managed by the service  no dedicated schema/table required, the same gap ADR-008's Azure and ADR-016's AWS equivalents avoided by not building this in the Regional Transactional Store |

**Status:** Approved

---

See [diagram](../diagrams/gcp-compute-order-orchestration.png).
