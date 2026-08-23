### ADR-001: Modernization strategy for the Solstice Commerce Engine components

**Context:**
`problem-statement.md` establishes that Solstice owns 100% of the Solstice Commerce Engine (SCE) source  unlike a vendor-locked core system, every one of the 6 R's (Rehost, Replatform, Repurchase, Refactor, Rearchitect, Retire) is genuinely available for every component. `current-state.md` names four logical components inside the monolith  Storefront & Catalog, Cart, Checkout & Payment, and Inventory & Order Orchestration  each with a different underlying problem: a connection-pool coupling failure (Storefront & Catalog, the direct cause of the November 2024 outage), a scalability/session-management need (Cart), a compliance topology problem (Checkout & Payment, the PCI-DSS finding), and a tightly-coupled synchronous call chain (Inventory & Order Orchestration). A single blanket strategy applied to all four would ignore that these are four different problems.

**Options considered (per component):**
- Storefront & Catalog: Rehost/Replatform (bigger instances, same architecture) vs. Repurchase (commerce SaaS/PaaS platform) vs. Rearchitect (extract into an independently-scaling, cache-friendly service)
- Cart: Rehost vs. Refactor (extract into its own service, same interaction pattern) vs. Rearchitect (event-driven)
- Checkout & Payment: Replatform (same topology, better infrastructure) vs. Rearchitect (isolated, narrowly-scoped service using gateway hosted-tokenization)
- Inventory & Order Orchestration: Refactor (reorganize the existing synchronous code) vs. Rearchitect (event-driven, asynchronous, replayable)

**Decision:**
Storefront & Catalog  Rearchitect. Cart  Refactor. Checkout & Payment  Rearchitect. Inventory & Order Orchestration  Rearchitect. Repurchase (a full commerce-platform migration) is recorded as a deferred, not dismissed, long-term option for the storefront.

**Rationale:**
Storefront & Catalog's actual failure mode  the November 2024 outage  was caused by shared-connection-pool coupling, not undersized infrastructure; Rehost or Replatform alone would not fix a coupling problem, so only Rearchitect addresses the root cause. Repurchase is a legitimate long-term option but a multi-year, brand-and-SEO-risk migration that doesn't fit the board-committed EU launch timeline or the one-parallel-initiative bandwidth constraint (`requirements.md` §4)  deferred, not eliminated, the same treatment Case Study 3 gave a full EHR replacement for CareLink PM. Cart doesn't need a fundamentally different interaction pattern  it's inherently synchronous request/response  so Refactor (extract, don't reinvent) is the right-sized move; a full event-driven Rearchitect here would add asynchronous complexity to a component that doesn't need it. Checkout & Payment's problem is topological, not a code-quality issue Replatform could fix  cardholder data transits the general application tier today, and only an architecturally isolated service, built around the payment gateway's existing hosted-tokenization capability, actually shrinks PCI scope. Inventory & Order Orchestration's synchronous call chain is exactly the shape event-driven decoupling exists to fix, independently arriving at the same reasoning Case Study 3 applied to LinkEngine because the underlying problem  a tightly-coupled synchronous chain with no replay or failure isolation  is genuinely the same shape in both case studies, not a copied conclusion.

**Trade-off:**
Rearchitecting three of four components at once is real engineering investment inside a compressed timeline, and it directly competes for the same bandwidth `requirements.md` §4 already bounds to one parallel initiative alongside the EU launch  Step 11's migration roadmap has to sequence this work carefully, not assume it happens all at once. Choosing Refactor instead of Rearchitect for Cart also means it inherits whatever regional-write-residency and scaling model the other three components settle into, rather than being designed as a fully independent target from day one  an accepted, deliberate scope-limiting choice, not an oversight.

**Status:** Approved
