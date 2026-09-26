# Step 1: Business Problem

## Organization

**Harborline Mutual Insurance Group** (fictional, composite) is a US property-and-casualty carrier headquartered in Hartford, Connecticut. It writes personal auto, homeowners, and small-commercial lines in 22 states, with about **$4.2B in direct written premium**, about **3.1 million policies in force**, and roughly **620,000 claims a year** handled by about 3,800 claims staff.

Harborline grew by acquisition:
- **Prairie Shield** (a Midwest regional carrier, 2019) has since been migrated onto Harborline's core systems.
- **Coastal Assurance** (a Southeast personal-lines carrier, 2022) still runs its own legacy policy and claims system.

Harborline's core insurance systems are Guidewire PolicyCenter, ClaimCenter, and BillingCenter, self-managed. Its analytical estate is a 12-year-old **Teradata enterprise data warehouse** fed by about 2,400 nightly Informatica PowerCenter jobs. Actuarial and pricing work is done in **SAS**. Around 95 million claim documents (adjuster notes, estimates, photos, police reports, medical records) sit in an enterprise content management system, mostly unsearchable except by claim number.

## Forcing Functions

Four pressures are forcing this initiative now:

1. **Staff are using public AI tools with customer data, and Harborline has no sanctioned alternative.** In March 2026, an internal audit found that a claims unit had been pasting claim notes, some containing bodily-injury medical details, into a public generative-AI chatbot to summarize files. Harborline blocked the tools, but adjusters are still asking for the capability, and the productivity case is real. Adjusters report spending about **30% of their time searching** claim files, coverage forms, and state-specific handling guidelines. Blocking the tools without offering a governed alternative has only moved the behavior onto personal phones.
2. **AI regulation for insurers has arrived.** Most of Harborline's 22 states have adopted the **NAIC Model Bulletin on the Use of Artificial Intelligence Systems by Insurers** (adopted December 2023). It expects a written AI program covering governance, risk management, documentation, testing for unfair discrimination, and oversight of third-party AI. New York's DFS has issued its own guidance on AI and external data in underwriting and pricing, and Colorado has a statutory framework (SB21-169) that is being applied line by line. Regulators can now ask Harborline to *show* how any AI system is governed. Today there is no model inventory, no evaluation evidence, and no audit trail. There is only a ban that is being worked around.
3. **The Teradata contract term ends on 30 June 2027, and notice is due by 31 December 2026.** Renewing means about **$3.9M a year** in licence and support plus an estimated **$6M appliance refresh**, because the current hardware is near end of support. Teradata has offered a **one-year extension at a 25% premium** as a bridge. A multi-year renewal would lock Harborline into its most expensive, least flexible platform for another cycle, precisely when the AI initiative needs data in open, cloud-accessible formats.
4. **Three post-acquisition data estates, and none of them is authoritative.** Customer, policy, and claims data live in Guidewire, in Coastal's legacy system, and in Teradata's integrated but nightly-stale copy, with different keys and definitions. The quarterly **actuarial reserving close takes 18 business days**, mostly spent reconciling loss triangles across the three estates. Harborline's combined ratio was **104%** last year (an underwriting loss), and the board has asked for a 2-point improvement within three years. Faster reserving insight and claims handling are both named as levers.

## Ranked Business Drivers

1. **Stand up governed AI as a precondition.** This means an AI governance program and platform controls that meet the NAIC bulletin and NYDFS expectations: a model inventory, pre-deployment evaluation, bias testing where models touch rating or claims decisions, audit logging, and no customer data used to train third-party models. It ranks first even though it is not where the money is, because every AI capability that follows depends on it. It is the same logic Case Study 4 applied to OT security.
2. **Deliver a claims knowledge assistant (RAG) to adjusters and underwriters.** The goal is to cut search time and claim cycle time, and so loss adjustment expense (LAE). This is where most of the operating value lives.
3. **Exit Teradata** on a timeline that at worst uses the one-year bridge extension, and never another multi-year renewal.
4. **Build a unified, governed data model** for customer, policy, and claims across all three estates. The goal is to cut the reserving close from 18 to 8 business days and make regulatory statistical reporting repeatable.
5. **Make data and AI spend predictable and attributable (FinOps).** Every dollar is allocated to a business unit and use case, and there is a unit cost per claim handled and per assistant query. Steady-state run cost must stay at or below today's legacy data-platform run cost (Teradata + SAS + Informatica), excluding the new AI capability, which must justify itself on its own unit economics.

## The Invariant

**No AI system makes an adverse decision about a customer on its own, and no customer data leaves Harborline's governed boundary to train anyone else's model.** The assistant informs adjusters and underwriters. It does not deny claims, set reserves, or rate policies. This is the property that must not regress, the equivalent of Case Study 2's batch-settlement invariant and Case Study 4's control-loop isolation.

## What This Case Study Is — and Is Not

This is a **data-platform modernization with a governed AI capability built on top of it**. It is not a core-systems replacement: Guidewire stays, and Coastal's legacy system is being decommissioned in a separate program. It is not an AI moonshot either. The RAG assistant is deliberately a *retrieval and summarization* tool with citations, not an autonomous agent.

The central design question, carried through every later step, is the one most enterprises face in 2026: **build the data and AI platform on a hyperscaler's native stack, or on a cross-cloud data platform (Databricks or Snowflake) that runs on top of one, and in either case how to keep the data in open formats so this is the last proprietary warehouse migration Harborline ever does.**

A secondary named risk, carried forward in the same way Case Studies 2 and 4 treated their ad hoc cloud accounts, is an **ungoverned Snowflake account** that the actuarial team opened in 2024. It holds copies of claims and policy extracts.
