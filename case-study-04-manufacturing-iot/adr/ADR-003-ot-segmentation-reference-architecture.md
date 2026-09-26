# ADR-003: OT Segmentation Reference Architecture and Plant-to-Cloud Conduit

**Status:** Approved
**Date:** Step 4 of the Case Study 4 pipeline

## Context

Most of Kestrel's plants have flat IT/OT networks. That is how the November 2025 ransomware reached Plant 09's HMIs and historian. Full renewal of Kestrel's cyber insurance in July 2027 is conditioned on three things at every plant: IEC 62443-aligned segmentation, MFA-protected remote access, and offline OT backups. The German plants also carry NIS2 obligations.

NFR-2 forbids any inbound connection from outside the plant to Levels 0–2, and NFR-9 sets IEC 62443-3-3 Security Level 2 as the target. The edge-first model ([ADR-001](ADR-001-edge-cloud-responsibility-split.md)) still needs a small amount of controlled traffic in the reverse direction: model and configuration deployments to edge nodes, and brokered remote access for vendors and engineers.

## Decision

Every plant is built to one **reference zone-and-conduit model**:

| Zone | Contents | Allowed conduits |
|---|---|---|
| Cell/line zones (L0–1) | PLCs, drives, safety systems. Safety systems sit in their own zone. | To their supervisory zone only |
| Supervisory zone (L2) | SCADA/HMI servers, OPC UA servers. Legacy/unpatchable hosts (Windows 7 HMIs) get a **dedicated containment zone**. | OPC UA *read* to the site-operations zone. No other outbound. |
| Site-operations zone (L3) | UNS broker, edge compute, edge connectors, historian, MES, engineering workstations | To the DMZ through defined conduits only |
| Industrial DMZ (L3.5) | Cloud bridge, secure-remote-access gateway, patch and model staging, jump hosts | Outbound-only to the cloud. MFA-brokered remote-access sessions terminate here. |
| Enterprise (L4–5) | Plant business IT, corporate WAN | To the DMZ only. **Never directly to L3 or below.** |

Rules that apply at every plant:

- **All traffic between OT and anything outside the plant terminates in the DMZ.** Nothing outside the plant can open a connection into Levels 0–3.
- **The cloud bridge holds outbound connections only.** Within the plant, it subscribes to the UNS broker through one conduit.
- **Model and configuration deployments are pulled, not pushed.** The cloud stages versioned artifacts, edge nodes fetch them through the DMZ, and a plant-side approval gate applies before activation.
- Every conduit is **default-deny** and runs through stateful firewalls.
- **Passive OT network monitoring** (asset discovery and anomaly detection) covers every zone.
- **Offline/immutable backups** of PLC programs and HMI/SCADA configurations are held per plant.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **VLAN separation only.** Rejected. Without stateful, policy-enforced conduits between VLANs it does not meet IEC 62443's zone/conduit intent or the insurer's condition, and it is roughly what failed at Querétaro.
2. **Full air gap.** Rejected. It is incompatible with the initiative's purpose, and in practice air gaps are bridged by removable media and vendor laptops, which moves the risk rather than removing it.
3. **A unidirectional gateway (hardware data diode) as the standard plant-to-cloud conduit.** Rejected as the *default*, but kept as an option. It gives the strongest guarantee against inbound traffic, but it would block pulled model and configuration deployment and brokered remote access, both of which the edge-first model and the insurer's remote-access condition need. It stays available for any zone a future risk assessment rates above Security Level 2, typically placed at the Level 2/3 boundary rather than at the DMZ.

## Consequences

- **Positive:** Connecting plants to the cloud *reduces* each plant's attack surface instead of increasing it. The cloud bridge is one narrow, monitored, outbound-only conduit in a network that today has none, which directly addresses driver 1.
- **Positive:** One reference model across all 12 plants lets the security design, firewall rule sets, and monitoring be templated. Plant-specific work is reduced to mapping assets into zones.
- **Negative / accepted trade-off:** Re-cabling and re-addressing at Levels 0–2 can only happen in the two annual shutdown windows, and only December 2026 fully precedes the July 2027 insurer deadline. Step 11 must therefore prioritize DMZ build-out and remote-access replacement (possible in monthly weekend windows) ahead of full cell-level zoning, and it may need to show the insurer a staged plan with compensating controls.
- **Negative / accepted trade-off:** Kestrel has no OT-security operations function today. Monitoring alerts from 12 plants need a place to go: either a managed OT security service or a new internal role. This is a named skills risk for Step 12.

## Open Question Carried to Step 5

Firewall and OT monitoring products are procurement choices outside this case study's platform comparison, much like the rail gateway vendor in Case Study 2. This ADR fixes the zone model and the conduit rules. Steps 6–8 decide only how each cloud platform terminates the bridge's outbound connection (private connectivity versus TLS over the internet, and certificate-based device identity).
