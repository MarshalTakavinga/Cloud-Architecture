# ADR-001: Edge/Cloud Responsibility Split

**Status:** Approved
**Date:** Step 4 of the Case Study 4 pipeline

## Context

Kestrel needs cross-plant predictive maintenance (driver 2), serial-level genealogy (driver 3), and comparable OEE (driver 4) across 12 plants. Two things constrain the design:

- Plants must keep producing, capturing data, and alerting with no WAN or cloud connection. The edge buffer must hold ≥ 72 hours (NFR-1), sized against Ramos Arizpe's 19-hour worst-case outage.
- No cloud component may sit in a control loop (NFR-2).

Critical-asset anomalies must alert at the plant within 10 seconds (NFR-5). Raw high-frequency vibration data (kHz sampling) cannot cross 50 Mbps plant links. Kestrel has no IT staff at most plants, so anything placed at the edge must be centrally managed as a fleet.

## Decision

Kestrel adopts an **edge-first, cloud-for-scale** split.

**The edge tier (one per plant, in the Level 3 site-operations zone)** owns everything that must survive an outage or react in seconds:
- collecting data from Level 2 sources
- normalizing it to the enterprise asset model
- a store-and-forward buffer of ≥ 72 hours for the enterprise data path, plus 30 days of local trending for plants without a historian
- reducing high-frequency vibration data to features
- anomaly detection and local alerting on critical assets
- the durable local write of genealogy records

**The cloud tier** owns everything that needs data from all plants or elastic compute:
- model training and the model registry
- fleet-wide KPIs and OEE
- long-term retention (90 days raw / 5 years downsampled)
- the immutable 15-year genealogy store, per-serial queries, and recall scoping
- near-real-time predictive insights and SAP PM integration

Models are trained in the cloud and **deployed to** the edge as versioned artifacts. Edge models raise alerts and recommendations only. They never write to Levels 0–2.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cloud-centric, thin edge.** Gateways forward everything and the cloud does all detection and storage. Rejected because it fails NFR-1: plants would lose alerting and genealogy capture during every WAN outage. It also cannot carry raw vibration data over plant links.
2. **Historian-centric.** Standardize on one historian product and replicate it to the cloud. Rejected as the enterprise path. It makes one historian vendor the enterprise data model, leaves two plants with nothing to replicate, does not provide exactly-once serial-level genealogy, and ties the cloud choice to that vendor's connector. The historians are retained for local use (see [ADR-002](ADR-002-plant-data-integration-pattern.md)).
3. **Fully plant-local analytics.** Rejected. It gives up cross-plant model training, which is the main source of predictive-maintenance value (failures are rare on any single asset), and it would place a compute cluster in each of 12 plants with no IT staff.

## Consequences

- **Positive:** Production, local alerting, and genealogy capture are independent of the WAN and the cloud, which satisfies NFR-1 and NFR-2 by construction rather than by SLA. This is also why NFR-11 can set the cloud target at 99.9% instead of the tighter targets in Case Studies 2–3.
- **Positive:** Only features and report-by-exception telemetry cross the WAN, an estimated 1–5 Mbps per plant, which fits existing links with no circuit upgrades.
- **Negative / accepted trade-off:** Kestrel now operates a fleet of edge nodes, at least two per plant for high availability, so roughly 24 or more in total, in environments without IT staff. Remote fleet management (deploy, configure, patch, roll back) becomes a mandatory capability of whichever edge software each platform track proposes, and it is scored in Step 9. It goes into the Step 12 risk register as "edge sprawl."
- **Negative / accepted trade-off:** Two model runtimes, cloud training and edge inference, must stay version-consistent. A model that behaves differently at the edge than in validation is a new failure mode that Step 5 must design for (model packaging, shadow mode before activation).

## Open Question Carried to Step 5

The exact edge node sizing and HA pattern (active/standby pair versus a small cluster), and whether fast anomaly detection is rule-based, model-based, or both at first, are Step 5/6 details. This ADR fixes the **placement of responsibilities**, not the edge hardware or software.
