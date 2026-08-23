# Current-State Architecture — Solstice Commerce Engine

See [`../diagrams/current-state-architecture.png`](../diagrams/current-state-architecture.png) for the full deployment diagram — hand-drawn, checked against this document across three review rounds (a mislabeled managed-service icon, a VPC-placement fix for the self-managed data stores, and a data-tier duplication fix across the two Availability Zones — see the case study's Step 4/current-state handoff notes for the detail on each).

Grounds each forcing function in `problem-statement.md` with the actual infrastructure behind it. Solstice already runs in the cloud — this is not an on-premises-to-cloud migration story. It migrated to a single AWS region in 2019 as a straight lift-and-shift and has never re-architected since; the point of this case study is a genuine, vendor-neutral re-evaluation across Azure, AWS, and GCP, not an assumption that "already on AWS" settles anything (see `problem-statement.md` §5 and the architecture-options step for why that neutrality matters).

## 1. Deployment Topology

Everything runs in a single AWS region, `us-east-1`, across two Availability Zones — no multi-region presence anywhere, for either compute or data.

| Layer | Today | Sized for |
| --- | --- | --- |
| Compute | Fixed Auto Scaling Group, 12–18 `m5.2xlarge` EC2 instances, running the SCE Node.js monolith behind an Application Load Balancer | Manually tuned toward November peak, not actual daily demand |
| Database | Single Amazon RDS for PostgreSQL instance (`db.r5.4xlarge`), Multi-AZ for failover only — **no read replicas** | Whatever one instance can hold; every read and write, from every service in the monolith, hits it |
| Cache | Self-managed Redis (single primary, one replica) on EC2, used for session state and a thin product-catalog cache | Sized for baseline traffic; not part of the autoscaling group |
| Static assets / images | Amazon S3, served **directly** — no CDN in front of it | N/A — every request, domestic or international, crosses the public internet to `us-east-1` |
| Search | Self-managed Elasticsearch (3-node cluster) on EC2 | Baseline catalog size; not a bottleneck today |
| Payments | SCE's checkout service calls a third-party PCI Level 1 payment gateway directly over HTTPS, from the same request-handling code path that serves product and search pages | See §3 — this is the PCI finding |

## 2. Why Autoscaling Doesn't Actually Help

The Auto Scaling Group is configured and technically "on," which is what makes this worth documenting precisely rather than waving at generically: SCE's Node process has a cold-start time of roughly 3–4 minutes (dependency injection bootstrap, in-memory catalog cache warm from Postgres, Redis connection pool establishment) before a new instance can serve traffic — too slow to react to a flash-sale ramp that goes from baseline to 20x within minutes, not tens of minutes. Worse, and this is the specific mechanism behind the November 2024 outage: every new instance opens its own PostgreSQL connection pool against the *same single RDS instance*. During the Black Friday spike, the ASG added instances as designed, and each one made the underlying `max_connections` exhaustion on the database worse, not better — autoscaling the stateless tier without also addressing the stateful tier turned a mitigation into an accelerant. Fixing this requires more than "add a read replica" — it requires deciding, architecturally, which parts of SCE can scale statelessly and which can't, which is exactly what Step 4/5 do.

## 3. The Payment Flow, Precisely (why the PCI finding is real)

The QSA's finding is specific, not a vague "improve security" note, and worth stating exactly since a compliance narrative without the actual data flow it's about is decoration, not architecture — the same standard this portfolio held itself to in Case Study 3's DR diagrams.

Today: browser → ALB → SCE checkout service (same EC2 fleet, same VPC, same security groups as product/search/cart) → payment gateway API, with the card-holder-data-bearing request constructed and transmitted from inside SCE's own request handler. The card number and CVV are never *stored* by Solstice — the gateway tokenizes on receipt — but they do **transit** Solstice's general-purpose application tier before tokenization happens. That transit is what pulls the entire monolith's environment into PCI scope: the network segment, the EC2 fleet, the load balancer, the logging pipeline, all of it, because cardholder data crosses through them. The gateway itself already offers a hosted-fields/tokenization-at-the-browser option that would let a card number go directly from the customer's browser to the gateway, never touching Solstice's servers at all — SCE simply isn't built to use it yet. That's the concrete gap Step 5's PCI scope-reduction ADR closes.

## 4. Observability and Operational Gaps

- No distributed tracing across the monolith's internal service boundaries — the November 2024 post-incident review took over six hours to isolate the connection-pool exhaustion as root cause, working backward from database metrics rather than forward from a trace.
- CloudWatch alarms exist on infrastructure metrics (CPU, memory, ALB 5xx rate) but nothing tied to business-relevant signals (checkout success rate, cart-to-order conversion latency) — the kind of gap this portfolio flagged and closed in Case Study 3's observability design, and should close here too.
- Deployments are a single monolithic build — every release ships the entire application, including the payment-adjacent code, which is itself part of why PCI scope is as broad as it is: there's no independently deployable boundary around the payment path today.

## 5. What Already Works and Shouldn't Be Thrown Out

Not everything here is a problem. Two things are worth carrying forward rather than re-litigating in Step 4: the third-party payment gateway relationship is solid, PCI Level 1 certified, and already offers the tokenization API this design needs — this is an integration problem, not a vendor problem. And the core data model (catalog, cart, order, customer) is reasonably well-normalized PostgreSQL schema with no known data-integrity issues — the problem is topology and elasticity, not data design, which is why a full database-technology re-evaluation isn't a headline decision in this case study the way it might be elsewhere.
