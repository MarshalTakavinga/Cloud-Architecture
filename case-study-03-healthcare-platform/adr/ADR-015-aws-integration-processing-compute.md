### ADR-015: Compute for LinkEngine's message-subscriber logic on AWS

**Context:**
ADR-002 decided LinkEngine becomes an event-driven integration service — platform-neutral. Something still has to run the code that subscribes to each message queue, writes results into the primary database, and archives the raw payload to object storage. The EC2 instances hosting CareLink PM (ADR-012) are a candidate simply because they already exist and are already connected to the data VPC — the same starting question ADR-008 answered for Azure.

**Options considered:**
- Run the subscriber logic on the existing Citrix/CareLink PM EC2 tier, as a background Windows service
- AWS Lambda, VPC-attached, one function per message category
- Amazon ECS on Fargate, running a small subscriber container/service

**Decision:** AWS Lambda, one function per topic/queue.

**Rationale:**
The Citrix EC2 tier is sized and autoscaled around interactive clinical session load — providers opening charts, entering orders. Message-processing load (a burst of lab results arriving overnight, a backlog after an outage) follows a completely different pattern; coupling the two means a spike in one workload competes for capacity with the other, and autoscaling logic tuned for one makes the wrong call for the other — the identical reasoning ADR-008 used to reject the Citrix tier for Azure. AWS Lambda is chosen over ECS Fargate specifically because Lambda has first-class, native event source mappings for both SQS and SNS (the messaging services chosen in ADR-018), and the workload here is genuinely event-driven, short-lived processing per message — exactly Lambda's design point — rather than a long-running service Fargate is better suited to. This mirrors ADR-008's choice of Azure Functions over Container Apps for the same reason: native trigger integration over general-purpose container hosting.

**Trade-off:**
This adds a third distinct compute platform to the AWS environment (EC2 for Citrix, ECS Fargate for the Portal, and now Lambda), which is one more thing to monitor and staff for operationally — a real cost, not free modularity, the same trade-off ADR-008 named for Azure. Accepted because the alternative (background processing on interactive session hosts) risks clinical-facing performance during exactly the periods — a message backlog after an outage — when reliability matters most.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Function structure | 4 Lambda functions (lab results, imaging, e-prescribing, appointment events), one per SQS FIFO queue | Direct parity with ADR-008's "one function app per topic" — each function scales independently on its own queue's backlog |
| Trigger | SQS event source mapping, batch size 1 (session/patient-ordering-sensitive) | Because the underlying SQS FIFO queues use `MessageGroupId` = patient ID (ADR-018) to preserve per-patient order, batch size is kept small so ordering isn't broken by out-of-order batch processing within a single invocation |
| Memory / timeout | 512 MB, 30 second timeout (starting point) | The subscriber workload is I/O-bound, not compute-bound — parse an HL7 message, write to the database, archive to S3, complete the message — mirroring ADR-008's reasoning for choosing EP1 over a larger, compute-oriented SKU. Revisit if real usage shows CPU/memory pressure |
| Reserved concurrency | 20 per function (starting ceiling) | Direct parity with ADR-008's 20-instance burst ceiling — headroom for a backlog-catch-up scenario, using the platform default range rather than inventing a number not backed by real data |
| Provisioned concurrency | 1 per function (avoids cold start) | AWS Lambda's equivalent of ADR-008's "1 Always Ready instance per function app" — avoids cold-start latency on every topic, including the clinically time-sensitive ones (lab results, e-prescribing), without paying to keep a large fleet warm |
| VPC integration | New subnets: `subnet-lambda-linkengine-az1/az2/az3`, 10.20.5.0/26, 10.20.5.64/26, 10.20.5.128/26, Application VPC | **A genuine platform difference worth naming, not inherited wholesale from ADR-008.** Azure's regional VNet Integration requires one dedicated subnet per App Service Plan — that's why `snet-func-linkengine` had to exist as its own subnet in the Azure design. AWS Lambda does **not** have that restriction: multiple Lambda functions can share the same VPC subnet without conflict. Dedicated subnets are still used here, but for a different, AWS-specific reason — each concurrent Lambda execution consumes an IP address from the subnet's available range for the duration of its VPC-attached ENI, so a subnet shared with other tiers (Citrix, the Portal's Fargate tasks) risks IP exhaustion under a genuine backlog-catch-up burst (up to 20 x 4 = 80 concurrent executions at the ceiling above). These same subnets are also shared with ADR-018's ingest-side Publish Function (reserved concurrency 10), for a combined ceiling of up to 90 concurrent executions across all five LinkEngine Lambda functions — still comfortably within a /26's usable address range per AZ. Isolating LinkEngine's Lambda functions in their own subnets avoids that failure mode without over-provisioning the other tiers' subnets to compensate. Three subnets, not one, because an AWS subnet is scoped to a single Availability Zone — a Lambda VPC configuration spanning 3 AZs for resilience needs 3 subnets, the same correction applied across every multi-AZ tier in `aws-implementation.md` §4.1 |
| Identity | IAM execution role per function, least-privilege (read/write to its own queue + DLQ, write to the database, write to its S3 archive prefix) | Same least-privilege discipline as ADR-008's managed identity per function app — no shared, over-privileged role across all four functions |

This sizing is a directional starting point, same discipline as ADR-012/013/017/018: there's no per-message-processing telemetry from the current on-prem LinkEngine to validate concurrency or instance-count assumptions against, only the message-volume figures already used in ADR-018. Validate against real CloudWatch/X-Ray data after cutover. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-aws.md`](../docs/application-architecture-aws.md) §4 for the full hosting narrative, [`../diagrams/linkengine-architecture-aws.png`](../diagrams/linkengine-architecture-aws.png) for the message-flow component view, and [`../diagrams/linkengine-functions-hosting-architecture-aws.png`](../diagrams/linkengine-functions-hosting-architecture-aws.png) for the detailed sizing/hosting diagram matching this ADR's Proposed Configuration (per-function concurrency, dedicated Lambda subnets, event bus, and the full account/VPC topology).
