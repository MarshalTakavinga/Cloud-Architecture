# Steps 2–3: Capabilities Required, Requirements, and NFRs

## Step 2: Business Capabilities Required

Traced directly to the five ranked drivers in `problem-statement.md`:

1. **Segmented, governed plant connectivity**: an IEC 62443 zone-and-conduit network design at every plant, with an industrial DMZ (Level 3.5) as the *only* path between OT and anything outside the plant, and MFA-brokered remote access replacing TeamViewer and vendor modems. (Driver 1)
2. **Edge data collection and buffering**: a standard edge layer at each plant that reads from PLCs and historians over OPC UA (or native drivers where necessary), normalizes tags to one enterprise asset model, and buffers locally through WAN outages. (Drivers 2, 4, 5)
3. **Condition monitoring and predictive maintenance**: fast anomaly detection at the edge on critical assets, plus model training and longer-horizon failure prediction in the cloud, with work orders raised in SAP PM. (Driver 2)
4. **Serial-level genealogy**: capture of machine, tooling, material lot, process parameters, and inspection results against each serial number, stored immutably and queryable in seconds. (Driver 3)
5. **Enterprise operational analytics**: one OEE definition and one data model across all 12 plants, available the next shift rather than 7–10 days later. (Driver 4)
6. **Plant autonomy**: every plant keeps producing, recording, and alerting locally with no WAN or cloud connection, and resynchronizes without data loss when it returns. (Driver 5)
7. **Governed cloud landing zone**: an identity-federated, policy-governed cloud foundation that hosts the platform and formally absorbs (or retires) the 2024 SageMaker proof-of-concept account and its copy of historian data. (Drivers 1, 2)

## Step 3: Non-Functional Requirements

| # | NFR | Target | Driven by |
|---|-----|--------|-----------|
| NFR-1 | Plant autonomy during WAN/cloud outage | Full production, local data capture, and local alerting continue indefinitely; edge buffer holds **≥ 72 hours** of plant telemetry (sized to beat Ramos Arizpe's 19-hour worst case with margin) | Driver 5 |
| NFR-2 | Control-path isolation | No cloud component in any control loop. No inbound connection from outside the plant to Levels 0–2. Plant-to-cloud connections are outbound-only from the Level 3.5 DMZ. Any cloud-originated recommendation (such as a setpoint change) reaches a machine only through a human-approved step at the plant | Drivers 1, 5 |
| NFR-3 | Sustained ingestion throughput | **60,000 values/sec** aggregate today (about 180K tags with report-by-exception); architected for **150,000 values/sec** (about 25 plants, allowing for acquisitions) without redesign | Drivers 2, 4 |
| NFR-4 | Backfill burst | Absorb **300,000 values/sec** aggregate while one or more plants drain a multi-hour buffer after an outage, without delaying live data from other plants by more than 60 seconds | Drivers 2, 5 |
| NFR-5 | Critical-asset anomaly alert latency | Edge-detected anomaly → maintenance alert at the plant **≤ 10 seconds** (works with no WAN). Cloud predictive insight → SAP PM notification **≤ 5 minutes** from data arrival | Driver 2 |
| NFR-6 | Data completeness | Telemetry: **≤ 0.01%** loss end-to-end, including across outages. Genealogy records: **zero loss, exactly-once**, where a missing or duplicated serial record counts as a quality-system nonconformance | Drivers 2, 3 |
| NFR-7 | Genealogy query performance | Full genealogy for one serial number in **≤ 5 seconds**. Recall scoping (every serial affected by a given material lot, tool, or process deviation) in **≤ 4 hours**, compared with 19 days today | Driver 3 |
| NFR-8 | Retention | Raw telemetry: 90 days hot. Downsampled (1-minute) telemetry: 5 years. Genealogy records: **15 years, immutable** (OEM contractual requirement) | Drivers 3, 4 |
| NFR-9 | OT security baseline | IEC 62443-3-3 Security Level 2 target for every plant zone and conduit. MFA on 100% of remote access. Offline/immutable backups of all PLC programs and HMI/SCADA configurations. Continuous OT network monitoring at every plant | Driver 1 (insurer, NIS2) |
| NFR-10 | Data residency | Raw telemetry and genealogy from the German plants remain in the EU. Shift and operator-linked events (operator badge IDs) are treated as personal data under GDPR and are subject to works-council agreement. Aggregated, non-personal KPIs may flow to a global analytics store | NIS2 / GDPR / German co-determination |
| NFR-11 | Cloud platform availability | **99.9%** for ingestion and analytics. This is deliberately lower than Case Studies 2–3, because NFR-1 moves production-critical availability to the edge | Driver 5 (by design) |
| NFR-12 | Economics | Platform run-rate (cloud, edge hardware amortization, licenses) must stay well inside the value of the downtime target: 30% of about $31M/year is about $9.3M/year of avoided cost. Per-plant cloud cost must be predictable and must scale roughly linearly with tag count, not with number of queries | Driver 2 |

## Requirement / Constraint / Assumption / Risk (Section 7.1 framework)

**Requirements**
- One enterprise asset and tag model (site → area → line → asset → signal), with the plant-to-enterprise mapping owned in one place, is a prerequisite for OEE comparability and for training models on more than one plant's data.
- Edge nodes must be centrally managed as a fleet: software, configuration, and models deployed and rolled back remotely, with no hands-on visit to each plant for routine changes.
- Genealogy records must be written at the point of production (the plant edge) and durable locally before production of that serial is confirmed, rather than depending on a cloud round trip.
- SAP PM integration must create maintenance notifications and work orders through a supported interface, not through direct database writes.

**Constraints**
- **Controls are out of scope.** No PLC logic, safety system, or HMI application is rewritten. The platform reads from Levels 0–2 and never writes to them automatically.
- **Plant change windows.** Changes touching Levels 0–2 (network cut-overs at the control layer, new PLC communication paths) happen only in planned shutdowns: about two weeks in July and about 10 days in late December each year. Changes at Levels 3–3.5 may use monthly weekend maintenance windows. With the insurer deadline in July 2027, only the December 2026 shutdown fully precedes the deadline. That fact will shape Step 12's sequencing, the way Case Study 1's single-concurrent-program limit shaped its rollout.
- The SAP S/4HANA migration is a separate program with its own timeline. The platform must integrate with SAP ECC now and S/4HANA later without being redesigned.
- Existing historians are not ripped out in this initiative. Where they exist and work, the edge layer reads from them or alongside them. Replacing them is a later decision, not a prerequisite.

**Assumptions**
- Most Level 2 systems and PLCs at the Rockwell and Siemens plants can expose data via OPC UA, either natively or through a gateway. Plant 07's Mitsubishi line and the two Windows 7 HMI plants are assumed to need protocol gateways. This is to be validated in Step 4, not taken as fact.
- Critical-asset vibration monitoring requires new wired or wireless sensors on about 300 assets. High-frequency waveform data (kHz sampling) is reduced to features at the edge, and only features, plus raw snapshots around anomalies, cross the WAN.
- Plant WAN bandwidth is sufficient for feature-level and report-by-exception telemetry: an estimated 1–5 Mbps sustained per plant against 50–200 Mbps links. Raw high-frequency data would not fit, which is a further reason the edge is not optional.
- Kestrel's data-science team (four people) can own model development. Kestrel has no existing OT-security or edge-platform operations staff, so these are new capabilities, bought or built.

**Risks (carried forward to the consolidated risk register in Step 13)**
- **Deadline compression:** only one full shutdown window precedes the July 2027 insurer renewal. If segmentation work slips from December 2026, Kestrel faces a second interim renewal at a higher premium.
- **Tag-model debt:** 180,000 tags with no naming convention across five historian platforms. Mapping them to an enterprise model is labor-intensive plant-engineering work, and it will set the pace of the whole program more than any technology choice.
- **Edge sprawl:** 12 plants × several edge nodes becomes a fleet of servers in environments without IT staff. Without disciplined fleet management, the edge layer turns into the next unpatched Level 2.
- **Vendor ecosystem churn:** managed IoT services change and retire. Google Cloud IoT Core was retired in August 2023. Any platform choice must keep the plant-side protocol layer (OPC UA, MQTT) standards-based and portable, so a future cloud-side retirement is a migration project rather than a re-instrumentation of every plant.
- **Works-council approval** at the German plants for operator-linked data could delay EU rollout. This is a business risk, not an architecture decision, but NFR-10 must accommodate either outcome.
- **The 2024 SageMaker account** holds an unmanaged copy of Plant 01 historian data. It is carried as a governance risk regardless of which platform is selected.

## Priority Weighting (feeds the Step 10 decision matrix)

Provisional weights, to be refined once options are on the table in Step 4, from highest to lowest:

1. OT security and edge-architecture fit (autonomy, outbound-only connectivity, edge fleet management)
2. Industrial protocol and edge ecosystem maturity (OPC UA, MQTT/Sparkplug B, asset modeling, partner support for the platform's missing pieces)
3. Ingestion and time-series economics at NFR-3/NFR-4 scale
4. Analytics and ML fit (predictive-maintenance model lifecycle from training in the cloud to deployment at the edge)
5. Operational and skills fit for a team with no edge or OT-security operations experience today
6. Data residency and portability (EU split, and exit cost if a managed IoT service is retired)

These are recorded here so that Step 10's weighted criteria can be traced back to this document rather than invented fresh at decision time.
