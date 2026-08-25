### ADR-016: AWS compute for Inventory & Order Orchestration

**Context:**
ADR-001 decided Inventory & Order Orchestration is Rearchitect  event-driven, asynchronous, replayable, the one place ADR-002 scoped event-driven adoption to. Its shape is a multi-step saga (reserve inventory → confirm payment → create order → hand off to fulfillment) that needs to track its own in-progress state across several asynchronous steps, retry individual steps, and compensate (release a reservation) if a later step fails  a genuinely different compute problem than Storefront & Catalog, Cart, and Checkout & Payment (ADR-013), which are synchronous and reachable from the API Gateway. Order Orchestration reacts to events on the Event Bus (ADR-017) rather than serving inbound HTTP traffic directly.

**Options considered:**
- Run Order Orchestration as another Amazon ECS Fargate service (the same pattern as ADR-013), a long-running consumer process polling the event bus, scaled via Application Auto Scaling target-tracking on queue depth.
- AWS Lambda, one function per event type, invoked directly off the event bus.
- AWS Step Functions (Standard Workflow type), with small single-purpose Lambda functions as the individual saga steps, triggered by an Amazon EventBridge rule on the `order-placed` event.

**Decision:**
AWS Step Functions, Standard Workflow type, one state machine deployed independently per active region, triggered by an EventBridge rule matching `order-placed` events (ADR-017). Each state in the workflow invokes a small, single-purpose Lambda function  reserve inventory, confirm payment, create order, hand off to fulfillment  with Step Functions' native `Retry` fields handling per-step retry and `Catch` fields routing to explicit compensating tasks (for example, a `ReleaseInventory` task on the failure path out of the payment-confirmation state).

**Rationale:**
A same-pattern-as-ADR-013 ECS Fargate consumer service was seriously considered, and it would work  Application Auto Scaling can target-track an ECS service's desired count against an SQS `ApproximateNumberOfMessagesVisible` CloudWatch metric, the direct AWS analog to KEDA's queue-length scaler on the Azure track. It's not chosen as the default here because doing so would import the Azure track's own stated cost from ADR-008 verbatim: a saga is a workflow-orchestration shape, not a stateless function-per-event shape, and a plain consumer service still has to build and own its own saga-state tracking, per-step retry, and compensation logic inside application code running on a long-lived process  exactly the re-invention ADR-008 accepted as the price of choosing Container Apps over Azure Functions.

AWS has a service purpose-built to remove that cost structurally rather than just relocate it: Step Functions' Standard Workflow type *is* a managed, durable state-machine engine. Each execution's current step, full history, and input/output at every stage is tracked by the service itself, not by application code; retries follow a declarative per-state policy (exponential backoff, maximum attempts, specific error-type matching); and failures branch to an explicit compensating task via a `Catch` clause  all without a single always-on process holding saga state in memory or in a database table the application team has to design and maintain. The individual Lambda functions handling each step are simple, stateless, and scale near-instantly with no fleet to size for peak concurrency. Plain Lambda-per-event (the third option) is rejected for the identical reason ADR-008 rejected plain Azure Functions on the Azure track: without something coordinating the steps, the saga's cross-step state  what's already been reserved, what still needs compensating  has to live somewhere application code manages directly, reintroducing exactly the problem a workflow engine exists to solve.

This is a case where the AWS-native answer is architecturally different from a renamed copy of the Azure decision, and that's worth stating plainly rather than defaulting to the Container-Apps-shaped pattern purely for cross-platform consistency. The underlying problem  saga state, retries, compensation  is identical across all three platform tracks; AWS happens to have a managed product that addresses it more directly than provisioning compute to run that logic yourself.

**Trade-off:**
Step Functions Standard Workflow pricing is per state transition, not per compute-hour. At Solstice's peak volume (`requirements.md` §1's ~3,750 orders/minute system-wide, each saga touching roughly 4–6 state transitions), this needs to be modeled carefully against a fixed-capacity compute alternative before the cost-analysis stage  a transition-based pricing model can land either cheaper or more expensive than reserved compute capacity depending on actual request shape, and this ADR doesn't resolve that, it flags it forward. Standard Workflow executions are durable, but each state's input/output payload is capped at 256 KB  not a real constraint for a saga passing order/inventory/payment identifiers and small status metadata, but worth stating rather than assuming. Operationally, Amazon States Language (ASL) state-machine definitions are a genuinely different authoring and testing model than a regular application codebase  a real onboarding cost for a 22-person engineering team that doesn't currently write Step Functions definitions, the same category of "newer/different operating model" trade-off ADR-010 accepted choosing Entra External ID on Azure. Lambda cold starts on the individual step functions are a minor, not zero, latency contributor per state transition  acceptable for the same reason ADR-008 accepted KEDA's 30-second polling lag on Azure: order processing isn't latency-critical the way a product-page load is.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Orchestration engine | AWS Step Functions, Standard Workflow type, one state machine per active region |
| Trigger | Amazon EventBridge rule matching `order-placed` events on that region's event bus (ADR-017), invoking the state machine via the native EventBridge-to-Step-Functions target integration |
| Step compute | AWS Lambda, one function per saga step (reserve inventory, confirm payment, create order, hand off to fulfillment) plus compensating functions (e.g., release inventory) |
| Retry policy | Per-state `Retry` field  exponential backoff, max 3 attempts, matched on transient error types (throttling, timeout) before falling through to `Catch` |
| Compensation | Per-state `Catch` field routes to a compensating task (e.g., a failed payment-confirmation state triggers a `ReleaseInventory` task) before surfacing failure back to Checkout & Payment |
| Concurrency | No fixed floor/ceiling to manage  Lambda and Step Functions scale per-execution; region-level Lambda concurrency limit monitored as a guardrail, not provisioned as a capacity number |
| Saga-state store | Step Functions' own execution history and state, durable and managed by the service  no dedicated schema/table required the way ADR-008's Azure equivalent needed one in the Regional Transactional Store |

**Status:** Approved

---

See [diagram](../diagrams/aws-compute-order-orchestration.png).
