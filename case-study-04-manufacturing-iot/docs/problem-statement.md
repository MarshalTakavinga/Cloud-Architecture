# Step 1: Business Problem

## Organization

**Kestrel Industrial Components** (fictional, composite) is a Tier-1 automotive and industrial components supplier with approximately $1.6B in annual revenue and 12 manufacturing plants: seven in the US Midwest, three in Mexico (Saltillo, Querétaro, Ramos Arizpe), and two in Germany (Stuttgart area and Chemnitz). Kestrel makes stamped and machined brake, steering, and driveline components, many of them classified by its OEM customers as safety-critical. It is IATF 16949 certified at every plant.

Kestrel grew by acquisition, and it shows on the plant floor. Its 12 plants run three PLC families, four SCADA/HMI products, five different process-historian installations (and two plants with no historian at all), and a manufacturing execution system (MES) at only four of them. Corporate IT runs SAP ECC on-premises in the Columbus, Ohio data center, with Microsoft 365 and Entra ID for the office workforce. Operational technology (OT), meaning the machines, controllers, and the software that runs lines, has always been owned plant by plant, with no enterprise OT architecture and no enterprise OT security function.

## Forcing Functions

Four pressures are forcing this initiative now:

1. **Unplanned downtime is Kestrel's largest controllable cost.** Unplanned downtime averages about 6.5% of scheduled production time across the network, roughly double what Kestrel's own best plant achieves. Finance puts its annual cost at about **$31M** in lost contribution margin, expedited freight, overtime recovery, and OEM line-down penalties. The event that made it a board topic came in February 2026. The main-drive bearing of a 1,600-ton transfer press at Plant 03 (Fort Wayne, Indiana) failed. The press was down for 3.5 days, which starved a customer's assembly line and cost about **$2.9M** including the OEM's line-down chargeback. The vibration trend that predicted the failure was actually recorded, but only on a handheld route collected once a month and filed in a spreadsheet nobody reviewed in time.
2. **A ransomware incident exposed a flat IT/OT network.** In November 2025, ransomware entered Plant 09 (Querétaro) through a phished engineering laptop on the plant's business network. Because the plant's IT and OT networks were not segmented, it reached the HMIs and the historian server. The plant was down for four days and its HMIs were restored from two-year-old images. Kestrel's cyber insurer renewed only on an interim basis, with the premium up about 40%. Full renewal in July 2027 is conditioned on IEC 62443-aligned OT network segmentation, MFA-protected remote access, and offline OT backups at every plant. Separately, Germany's transposition of the EU NIS2 Directive brings Kestrel's two German plants into scope as motor-vehicle-component manufacturers, with their own risk-management and incident-reporting obligations.
3. **Serial-level traceability has become a condition of new business.** Kestrel's largest customer, a North American OEM, now requires serial-level part genealogy for safety-critical brake and steering components. For each serial number the supplier must show which machine, tooling, material lot, process parameters, and inspection results produced it. This is a condition of the model-year 2028 program award, due for production readiness in Q4 2027. The cost of not having it is already known. In a 2025 field containment it took Kestrel **19 days** to identify the affected parts, and without serial-level data Kestrel had to contain about **41,000 parts** when roughly 3,000 were actually suspect.
4. **Corporate cannot see or compare its own plants.** Overall Equipment Effectiveness (OEE) is calculated three different ways across the network, mostly in spreadsheets assembled weekly from historian exports. Leadership cannot tell whether Plant 03's 71% OEE and Plant 11's 78% are comparable numbers, so it cannot target capital or replicate what the best plants do.

## Ranked Business Drivers

These forcing functions become five ranked drivers. Every later architecture decision in this case study must trace back to them.

1. **Close the OT security gap**: segment every plant along IEC 62443 zone-and-conduit lines, put remote access behind MFA, and meet the insurer's July 2027 conditions and NIS2 obligations. It ranks first even though downtime costs more in dollars, because it is a precondition. Connecting 12 plants to a cloud platform before they are segmented would widen exactly the attack path that took down Querétaro.
2. **Cut unplanned downtime by at least 30% within 24 months** through condition monitoring and predictive maintenance on critical assets. This is where most of the financial return lives.
3. **Deliver serial-level traceability** for safety-critical components at the plants that build them, by Q4 2027, with genealogy records that cannot be lost or altered.
4. **Standardize OEE and operational KPIs** across all 12 plants on one definition and one data model, so plant comparisons mean something.
5. **Never compromise safety or line control.** Plants must keep producing if the WAN or the cloud is unavailable, and no cloud component may sit in a machine control loop. This is the property that must not regress, the equivalent of Case Study 2's batch-settlement invariant.

## What This Case Study Is — and Is Not

This is an **IT/OT convergence and industrial data platform** initiative. It is not a controls replacement: PLCs, safety systems, and HMIs stay where they are, and the platform reads from them. It is also not an ERP project. Kestrel's separate SAP S/4HANA migration is out of scope, and this case study treats SAP only as an integration endpoint.

The central design question, carried through every later step, is **where each piece of work runs**. Some logic must sit at the edge inside each plant: local buffering, anomaly detection that has to fire in seconds, and anything that must survive a WAN outage. Some belongs in the cloud: cross-plant analytics, model training, long-term retention, and fleet-wide KPIs. And the design must decide how data crosses the boundary between the two without opening a path back into the control network.

This case study also changes where resiliency lives. In Case Studies 2 and 3, availability was a property of the cloud platform and its DR design. Here the plants must be autonomous, so the resiliency obligation sits mostly at the edge, and the cloud is important but not in the critical path of production.
