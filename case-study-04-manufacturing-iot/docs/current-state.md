# Current-State Architecture

A current-state diagram is still to be drawn. This document is written to be diagrammed directly: the Purdue-level layout in §2 maps onto the usual Purdue swim lanes.

## 1. Plant Estate at a Glance

| Plant | Location | Primary products | PLC family | SCADA / HMI | Historian | MES | IT/OT segmented? |
|---|---|---|---|---|---|---|---|
| 01 | Columbus, OH | Machined steering components | Rockwell ControlLogix | Ignition | AVEVA PI | Homegrown .NET MES | Partial (VLAN only) |
| 02 | Dayton, OH | Brake calipers (machined) | Rockwell ControlLogix | FactoryTalk View SE | AVEVA PI | Homegrown .NET MES | Partial (VLAN only) |
| 03 | Fort Wayne, IN | Stamped brackets, press lines | Rockwell ControlLogix | FactoryTalk View SE | AVEVA PI | None | No |
| 04 | Lansing, MI | Driveline shafts | Rockwell ControlLogix | Ignition | AVEVA PI | None | No |
| 05 | Toledo, OH | Stamped brake components | Rockwell CompactLogix | FactoryTalk View ME | Legacy Wonderware Historian | None | No |
| 06 | Kokomo, IN | Steering racks (machined + assembly) | Rockwell ControlLogix | Ignition | AVEVA PI | Homegrown .NET MES | Yes (firewalled DMZ, 2024) |
| 07 | Grand Rapids, MI | Industrial couplings | Mixed Rockwell / Mitsubishi | FactoryTalk View ME | None (paper logs + local HMI trends) | None | No |
| 08 | Saltillo, MX | Brake rotors (casting finish + machining) | Rockwell ControlLogix | FactoryTalk View SE | AVEVA PI | None | No |
| 09 | Querétaro, MX | Stamped steering components | Rockwell CompactLogix | FactoryTalk View SE | AVEVA PI (rebuilt after Nov 2025 incident) | None | Emergency firewall (Dec 2025), not designed |
| 10 | Ramos Arizpe, MX | Driveline sub-assemblies | Rockwell ControlLogix | FactoryTalk View ME | None (paper logs) | None | No |
| 11 | Stuttgart area, DE | Precision steering components | Siemens S7-1500 | Siemens WinCC | Siemens-bundled historian | Commercial MES (acquired with plant) | Yes (existing DMZ) |
| 12 | Chemnitz, DE | Brake components | Siemens S7-1500 | Siemens WinCC | AVEVA PI | None | Partial |

**Scale:** about 2,400 networked production assets (presses, CNC machining centers, robots, furnaces, test stands) and about 180,000 historized tags network-wide. Around 300 of those assets are classified as *critical*: a single failure stops a line with no alternate routing. These 300 are the first targets for condition monitoring.

## 2. Architecture by Purdue Level (Typical US/Mexico Plant)

- **Levels 0–1 (field devices and control):** sensors, drives, and PLCs on EtherNet/IP (Rockwell plants) or PROFINET (German plants). Safety PLCs and safety-rated interlocks are separate and **out of scope to touch**.
- **Level 2 (supervisory):** HMI/SCADA servers and operator panels, mostly Windows Server 2012 R2 or 2016. Two plants still run Windows 7 HMI panels. Some HMIs have TeamViewer installed for machine-builder remote support: unmanaged, no MFA, and in some cases always-on.
- **Level 3 (site operations):** the plant historian, the MES where one exists, engineering workstations, and a plant file server. At most plants, Level 3 shares a flat network with Level 2 **and with the plant's business (Level 4) network**. That is the path the Querétaro ransomware took.
- **Level 3.5 (industrial DMZ):** present at only three plants (06, 11, 09's emergency build). Elsewhere, nothing separates plant business IT from control systems.
- **Level 4–5 (enterprise):** SAP ECC in the Columbus data center (production orders, material master, plant maintenance/CMMS through SAP PM), Microsoft 365, Entra ID for office users. Plant OT accounts are local Windows accounts or plant-level AD domains that are **not** federated to Entra ID or the corporate AD forest.

## 3. Data Flows Today

- **Machine → historian:** tags are polled or subscribed by the historian's interface nodes at 1-second to 1-minute resolution. Only about half the configured tags are well-maintained. Tag naming follows no common convention across plants, and even differs between lines within a plant.
- **Historian → corporate:** there is no automated flow. Plant engineers export CSVs weekly and email them to the corporate operations-excellence team, which builds OEE and downtime reports in Excel. These arrive 7–10 days late.
- **Vibration and condition data:** collected monthly on handheld route-based analyzers by a contracted reliability vendor at seven plants. The data sits in the vendor's desktop software and is not connected to the historian or to SAP PM. The Fort Wayne bearing failure (see `problem-statement.md`) was visible in this data after the fact.
- **Traceability:** where an MES exists, serial numbers (laser-marked) are linked to work orders and some process data. Elsewhere, genealogy lives on paper travelers and in the quality lab's standalone database, which has lot-level resolution only.
- **MES ↔ SAP:** production confirmations post from the homegrown MES to SAP through nightly IDoc batch files. At non-MES plants, production is confirmed manually in SAP at the end of each shift.

## 4. WAN and Connectivity

- US plants: MPLS, 100–200 Mbps, to the Columbus data center. Internet breaks out centrally through Columbus.
- Mexico plants: MPLS at 50 Mbps, with LTE backup at Saltillo only. Ramos Arizpe logged 23 WAN outages longer than 30 minutes in the last 12 months, the longest lasting 19 hours.
- German plants: local ISP internet with site-to-site VPN to Columbus, 100 Mbps. Traffic to Columbus crosses the Atlantic, which will matter for EU data-residency decisions (see `requirements.md`).
- No plant currently sends anything directly to any public cloud.

## 5. Existing Cloud Footprint

- **Microsoft 365 / Entra ID:** office productivity and corporate identity only. No Azure landing zone beyond default subscriptions used for a few test VMs.
- **The 2024 AWS SageMaker proof of concept:** Kestrel's four-person data-science team stood up an AWS account in 2024 to trial a predictive-maintenance model on six months of exported Plant 01 historian data. The model showed promising precision on spindle failures but never went further, because there was no pipeline to feed it live data. The account has no landing zone and no SSO, and it still holds a copy of the exported historian data. As in Case Study 2, this ungoverned foothold is carried forward as a named risk. It is **not** a vote for AWS, and the evaluation in Steps 6–10 treats it neutrally.

## 6. OT Security Posture (As-Is)

- Asset inventory: none enterprise-wide. The Querétaro recovery team found 31 devices that were on no plant's list.
- Remote access: a mix of TeamViewer on HMIs, vendor-owned cellular modems on some machines, and a corporate VPN that lands users on the flat plant network.
- Backups: HMI and PLC program backups are inconsistent, and most are online-reachable (and so were encryptable by the ransomware).
- Monitoring: no OT network monitoring or anomaly detection anywhere.
- Patching: plant-by-plant, and effectively frozen on Level 2 servers because vendors will not certify updated operating systems.

## 7. Summary of What This Case Study Inherits

The plants run, and in the narrow sense of producing parts they run well. What they lack is structural: machine data stays trapped in five kinds of historian (or none), the network is flat, security is set plant by plant, and nothing moves data from the plant floor to where decisions get made. As in Case Study 2, this is a capability and resilience gap, not a system in crisis. The one real constraint on everything that follows is that **production must not be put at risk while the gap is being closed**: changes at Levels 0–2 happen only during planned shutdown windows, and the new platform reads from the control layer rather than replacing it.
