# Architecture Options and Styles  Solstice Retail Group

Step 4: the same two decisions this portfolio kept separate in Case Study 3  how each component moves (migration strategy) and what pattern the system evolves toward (target architecture style)  kept separate again here, for the same reason. Conflating them turns two defensible decisions into one vague "we're modernizing" gesture.

## 1. The Contrast Worth Naming First

Case Study 3 opened this step with a hard constraint: CareLink PM was a vendor product, so Refactor was off the table before any other analysis happened. Solstice is the mirror image. `problem-statement.md` §1 already established it: **Solstice owns 100% of the Solstice Commerce Engine source code.** Every one of the 6 R's is genuinely available for every component here  there's no single fact that eliminates a category the way vendor lock-in did in Case Study 3. That makes this step's job harder, not easier: the discipline has to come from matching each component's actual problem to a strategy, not from a constraint doing the work automatically.

## 2. Components and the 6 R's

`current-state.md` names four logical components inside the SCE monolith. Each gets its own strategy, not a single "rewrite everything" decision  the same principle Case Study 3 applied when it split CareLink PM, the Portal, Telehealth, and LinkEngine into four separate rows rather than one blanket migration strategy.

| Component | Strategy | Why |
| --- | --- | --- |
| Storefront & Catalog (browse, search, product pages) | **Rearchitect** | The most read-heavy, most cacheable, most globally latency-sensitive component, and  per `current-state.md` §2  the one whose shared-connection-pool coupling to the rest of the monolith directly caused the November 2024 outage. A Rehost or Replatform (bigger boxes, same coupling) doesn't fix the coupling that actually failed. This is the highest-value, most defensible Rearchitect target in the system. |
| Cart | **Refactor** | Needs to be fast, horizontally scalable, and independently deployable, but it's inherently synchronous request/response  a full event-driven rearchitecture buys little here. Extracting it into its own service with its own session store, without changing its fundamental interaction pattern, is the right-sized move. |
| Checkout & Payment | **Rearchitect** | The PCI-DSS finding (`current-state.md` §3) isn't a code-quality problem, it's a topology problem  cardholder data transits the general application tier. Fixing it requires a genuinely different shape: an isolated, narrowly-scoped service using the payment gateway's existing hosted-tokenization capability, not a bigger or better-organized version of the current code path. See ADR-002. |
| Inventory & Order Orchestration | **Rearchitect** | Order placement, inventory reservation, payment confirmation, and the fulfillment handoff are today's most tightly-coupled synchronous call chain inside the monolith. This is exactly the shape event-driven decoupling exists to fix  the same reasoning Case Study 3 applied to LinkEngine, arrived at independently because the underlying problem (a synchronous chain with no replay or isolation) is genuinely the same shape. |

Two strategies were seriously considered and explicitly **not** chosen for the storefront, worth recording rather than silently skipping:

- **Repurchase**  migrating to a commerce SaaS/PaaS platform (e.g., a hosted commerce platform) is a legitimate long-term option. It's deferred, not dismissed, for the same reason Case Study 3 deferred a full EHR replacement: it's a multi-year, brand-and-SEO-risk migration that doesn't fit inside the board-committed EU launch timeline or the one-parallel-initiative bandwidth constraint (`requirements.md` §4).
- **Retire**  no component is being shut down outright. Supporting infrastructure (self-managed Redis, self-managed Elasticsearch) will very likely be replaced by managed equivalents once a platform is chosen in Steps 6–8, but that's an implementation-tier decision, not a strategic retirement of a capability  the same distinction Case Study 3 drew between its owned components and its infrastructure-tier Replatform/Retire row.

## 3. Target Style  What Was Chosen and What Was Deliberately Refused

- **Event-driven order orchestration: adopted, scoped to the write path.** Order placement, inventory reservation, and the fulfillment handoff move to asynchronous, replayable events. This is not a full CQRS or event-sourcing adoption  the storefront's read side stays a conventional cached/replicated read path, not a separate command/query architecture. Naming that boundary explicitly matters: adopting event-driven patterns in the one place they solve a real, named problem is different from adopting them everywhere because they're fashionable.
- **Multi-region active-active for the storefront read path: adopted.** This is a genuinely different posture from Case Study 3's warm-standby DR, and worth stating plainly rather than reusing the same term loosely: Case Study 3's multi-region design exists for **failover** (a region is down, promote the other one). This one exists for **latency** (every region serves live production traffic all the time, because customers on three continents can't all be well-served from one place). Both are legitimate multi-region patterns; they solve different problems and should never be described with the same vocabulary as if they were the same decision.
- **Regional-primary writes for cart, checkout, and orders: adopted.** Unlike the read-heavy storefront, write paths carry real consistency and data-residency requirements  an EU customer's cart, checkout, and order records are written and stored in an EU region as the primary copy, directly satisfying the GDPR data-residency requirement structurally rather than bolting on a compliance control after the fact.
- **PCI scope isolation via edge/hosted tokenization: adopted, narrowly.** Unlike Case Study 3's Zero Trust overlay (a cross-cutting boundary around the entire application layer, motivated by a credential-compromise incident), this design's compliance mechanism is deliberately narrow: only the checkout/payment path is pulled into a reduced-scope boundary. Applying the same all-encompassing Zero Trust treatment here would be solving a problem Solstice doesn't have  the PCI finding is about one specific data flow, not about the trust posture of the whole platform.
- **A small number of independently-scalable services, not a full microservices explosion: adopted.** Four components, rearchitected where the underlying problem calls for it  not a service-per-feature decomposition. Solstice's 22-person engineering org is larger than Meridian's 16-person infrastructure team, but it's still not staffed for a service-mesh-heavy operating model with dozens of independently-owned services. The same restraint Case Study 3 applied for the same reason: match the architecture's operational surface area to the team that has to run it.
- **Personalization/recommendations, a fulfillment/warehouse redesign, and a payment-gateway replacement: explicitly out of scope**, per `problem-statement.md` §5  named again here because a target-style decision that doesn't repeat its own boundaries is easy to scope-creep past later.

## 4. ADRs From This Step

- [ADR-001  Modernization Strategy for the Solstice Commerce Engine Components](../adr/ADR-001-modernization-strategy-sce-components.md)
- [ADR-002  Target Architecture Style](../adr/ADR-002-target-architecture-style.md)

## 5. Reading the Target-Style Diagram

Every element in [`diagrams/target-architecture-style.png`](../diagrams/target-architecture-style.png) traces back to a decision above, not an aesthetic choice:

- The four component boxes (Storefront & Catalog, Cart, Checkout & Payment, Inventory & Order Orchestration) are the four rows from the 6-R table, each carrying its own strategy.
- The dashed PCI-scope boundary around Checkout & Payment only is the direct, deliberately narrow implementation of the PCI isolation decision  it does not wrap the whole diagram the way Case Study 3's Zero Trust boundary did, on purpose.
- The three region markers (US, EU, APAC) around Storefront & Catalog show active-active read replication  every region live, all the time, for latency, not failover.
- The single-region-per-customer marker on Cart/Checkout/Orders shows regional-primary writes  an EU customer's write path stays in the EU region.
- The event bus between Inventory & Order Orchestration and the fulfillment handoff is the one place asynchronous, replayable messaging is actually adopted  not a platform-wide messaging fabric.
