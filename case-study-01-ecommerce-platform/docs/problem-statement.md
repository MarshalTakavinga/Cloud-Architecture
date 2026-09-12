# Problem Statement  Solstice Retail Group

## 1. Who Solstice Is

Solstice Retail Group is a fictional, composite mid-market direct-to-consumer retailer  apparel, footwear, and home goods  headquartered in Denver, CO. Founded in 2011, now doing roughly $310M in annual revenue, about 70% of it online. ~2.4 million active customer accounts, currently shipping to the US and Canada only. 340 employees, including a 22-person engineering organization split across storefront, fulfillment, and platform/infrastructure teams.

The online storefront runs on the Solstice Commerce Engine (SCE)  a Node.js/PostgreSQL application Solstice built in-house starting in 2016 and has extended ever since. That detail matters architecturally: **Solstice owns 100% of this codebase.** Unlike a vendor product nobody can touch, every option  including a genuine rewrite of parts of it  is actually on the table here. That's a different starting constraint than a case study built around a vendor-locked core system, and it shapes everything from Step 4 onward.

## 2. The Problem, Stated Plainly

SCE was built for a single-region, steady-traffic retailer shipping to two countries. Solstice is no longer that company: it now needs to survive traffic spikes 20-25x its daily average, serve customers on three continents with acceptable latency, and satisfy a payment-security finding that has a deadline attached. The current architecture  a fixed fleet of statically-sized compute behind a single regional database, no CDN in front of static assets, no read replicas, autoscaling that exists on paper but doesn't meaningfully help  was never built to do any of that, and it showed.

Four forcing functions, each real and dated within this scenario, turned that gap from a backlog item into a board-level priority.

## 3. The Four Forcing Functions

**November 29, 2024  the Black Friday outage.** Checkout returned 5xx errors for roughly 52 minutes during the 10–11am MT peak. Traffic hit ~24x average-day throughput; the root cause was PostgreSQL connection-pool exhaustion on the single RDS instance backing the monolith. The autoscaling group *did* add EC2 instances during the spike, and made the problem worse, not better, because every new instance opened its own connection pool against the same single database, accelerating the exhaustion it was supposed to relieve. Estimated $1.4M in lost sales during the outage window, plus a visible run of customer complaints on social media during the year's highest-traffic shopping day.

**Q1 2025  the EU launch was approved.** The board approved entry into the UK, Germany, and France this fiscal year. Synthetic monitoring from EU test traffic shows a ~2.1s p95 page load against SCE today, versus ~600ms from US traffic. All requests are served from a single US region with no CDN in front of static assets. Early beta conversion data suggests EU visitors convert at roughly half the US rate, and page-load time is the leading suspect. Separately, GDPR requires EU customer PII to be processed and stored with real safeguards. The current single-region-US design has no answer for that at all, not even a partial one.

**Early 2025  a PCI-DSS assessment finding.** Solstice's annual PCI-DSS Level 2 assessment flagged that cardholder data transits the same application tier and network segment as the general storefront code: SCE calls the payment gateway directly from the same request handlers that serve product pages and search, so raw card data (in transit, pre-tokenization) passes through infrastructure that is, today, entirely in PCI scope. The finding requires payment processing to be isolated into a materially reduced-scope environment before the next assessment cycle, or Solstice risks losing its card-not-present processing standing with its acquiring bank.

**Ongoing  rising unit economics.** Because there's no reliable autoscaling, SCE's infrastructure is sized year-round for something close to November peak. Finance's numbers: infrastructure cost per order rose 22% year-over-year while order volume grew only 9%. The CFO has set an explicit target  cut infrastructure cost per order by at least 30% within 18 months  without giving up the peak-readiness the Black Friday outage made non-negotiable.

## 4. Business Drivers, Ranked

The same discipline this portfolio applies consistently: state the ordering, don't let it be inferred, and don't let a later cost analysis quietly contradict it.

1. **Eliminate peak-traffic outages.** The single largest, most concrete, most recently realized risk  a repeat of November 2024 during an even bigger 2025 peak  is the scenario every other decision in this case study is implicitly protecting against.
2. **Enable the EU launch with acceptable latency and GDPR-compliant data handling.** A hard deadline set by a board decision that already happened: this isn't a nice-to-have, it's a gate the business has already committed to publicly.
3. **Remediate the PCI-DSS finding.** A compliance deadline tied to the next assessment cycle, with a real consequence (loss of card-not-present processing standing) if missed.
4. **Reduce infrastructure cost per order.** A real, board-visible target  but ranked last deliberately. A cost-optimization architecture that quietly increases outage risk to hit a savings number would be solving the wrong problem in the wrong order.

## 5. What This Case Study Does and Doesn't Cover

This is a **target-architecture and platform-selection exercise with a real migration plan**, not primarily a compliance-driven vendor replatform as Case Study 3 is. The headline architectural questions here are different on purpose: how do you design for a 20-25x elastic traffic multiplier instead of a steady load, how do you serve three continents without three continents of latency, and how do you shrink a compliance boundary around a payment flow instead of replatforming an entire vendor application. Recommendation-engine/personalization work, a full fulfillment/warehouse-management redesign, and a rebuild of the payment gateway relationship itself are explicitly out of scope: named here as deliberate exclusions, not oversights, the same discipline this portfolio applied to ruling out data mesh and event sourcing in Case Study 3.
