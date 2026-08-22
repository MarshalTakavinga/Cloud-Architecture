### ADR-029: Private-cloud network topology

**Context:**
The logical design carries forward Meridian's existing hub-and-spoke mental model — platform-neutral (ADR-007 for Azure, ADR-014 for AWS, ADR-021 for GCP). ADR-026 already chose VMware Cloud Foundation, which bundles NSX as its software-defined networking layer — so unlike the hyperscaler tracks, the networking *product* isn't really an open question here; what this ADR actually decides is how NSX is used to implement the hub-and-spoke shape, and how the two colocation facilities from ADR-026 connect to each other.

**Options considered:**
- Traditional VLAN-based segmentation with physical perimeter firewalls at each facility — essentially reproducing the current-state network model at the new facilities
- NSX-based software-defined segmentation: a Tier-0 gateway (hub) with per-tier Tier-1 gateways (spokes), enforced by the NSX Distributed Firewall and NSX Edge
- A single flat network per facility, no segmentation

**Decision:** NSX-based hub-and-spoke: a shared Tier-0 gateway acting as the hub, with per-tier Tier-1 gateways (Application, Data, Integration, Management) as spokes, all traffic between spokes and to the internet enforced through the NSX Distributed Firewall and NSX Edge, plus redundant private circuits between the Columbus and Dallas facilities.

**Rationale:**
A flat network is ruled out for the identical reason it was never on the table for Azure, AWS, or GCP — it carries forward the current state's flat-VLAN weakness (`current-state.md` §4) into the new facilities instead of fixing it, and it's incompatible with the Zero Trust posture ADR-002 already decided. Traditional VLAN segmentation with physical firewalls is a real, working option — it's what Meridian already knows — but it's rejected because it reproduces the *specific* current-state weakness named in `current-state.md` §4 (limited VLAN segmentation, a single aging hardware firewall) at a new address rather than fixing it, the same category of objection that ruled out "flat network" everywhere else in this case study. NSX is chosen not because it mirrors what the hyperscaler platforms did, but because of a genuine platform-specific efficiency worth naming plainly: **on Azure, AWS, and GCP, the hub-and-spoke networking construct (VNet peering/hub VNet, Transit Gateway, Network Connectivity Center) is a separate managed service Meridian provisions and pays for on top of the compute/database services it's connecting. Here, NSX is not a separate purchase — it's already included in the VCF platform ADR-026 chose.** The marginal cost of getting Zero-Trust-capable microsegmentation is close to zero once VCF itself is standing up, a genuine strength of this track worth naming alongside the very real operational burdens named in ADR-028 and ADR-030.

**Trade-off:**
Redundant private circuits between the Columbus and Dallas facilities (needed for SQL Server Always On replication traffic per ADR-028, NSX network extension, and Veeam backup replication) are a real, ongoing telecom cost Meridian must contract and manage directly — unlike a hyperscaler's inter-region backbone, which is invisible and included in the platform. NSX operational expertise is also a genuinely new skill beyond core vSphere administration, a real training or hiring cost, not a cosmetic one. On the strength side of the ledger: the NSX Distributed Firewall enforces policy at the individual VM's virtual NIC, independent of which subnet or host that VM happens to sit on — arguably finer-grained by default than several of the sibling platforms' subnet-oriented Network Security Group/Security Group models, worth naming as a genuine capability strength, not just a cost center.

**Status:** Proposed

---

**Proposed Configuration:**

| Tier-1 segment | Address space | Range | Purpose |
| --- | --- | --- | --- |
| Management (Tier-0 hub itself) | 10.10.0.0/16 | 10.10.0.0/24 | vCenter, NSX Manager cluster, SDDC Manager, Aria Suite — the VCF platform's own control plane, mirroring the Inspection VPC's hub role on the Azure/AWS/GCP tracks |
| Application | 10.20.0.0/16 | 10.20.1.0/24 | Citrix Cloud Connectors and VDA session hosts (ADR-027), the Portal's Tanzu-hosted workload (ADR-032) |
| Data | 10.30.0.0/16 | 10.30.1.0/24 | SQL Server Always On VMs (ADR-028) |
| Integration | 10.50.0.0/16 | 10.50.1.0/24 | LinkEngine's Tanzu-hosted subscriber workers (ADR-030) — isolated for the identical externally-triggered-traffic trust-boundary reason ADR-022/ADR-015/ADR-008 gave on every other platform |
| DR facility mirror (Dallas): Management | 10.110.0.0/16 | 10.110.1.0/24 | Same one-segment-per-tier pattern, reused at the DR facility |
| DR facility mirror: Application | 10.120.0.0/16 | 10.120.1.0/24 | — |
| DR facility mirror: Data | 10.130.0.0/16 | 10.130.1.0/24 | — |
| DR facility mirror: Integration | 10.150.0.0/16 | 10.150.1.0/24 | Unlike the GCP track's own flagged gap (no DR mirror yet built for its Integration VPC — see `gcp-implementation.md` §4.1), this design provisions the DR Integration segment from day one, consistent with ADR-026's "DR facility built to full target capacity up front" decision — physical hardware cannot be added mid-incident, so neither can a missing network segment |

The address ranges above are deliberately the same CIDR scheme used across the Azure, AWS, and GCP tracks — reused for the identical reason `gcp-implementation.md` §4.1 gave: it's already validated not to collide with anything, and using the same ranges across every platform implementation makes the Step 10 comparison easier to read.

- **Inter-facility connectivity**: redundant, carrier-diverse private circuits between Columbus and Dallas (a dedicated point-to-point private line and a secondary SD-WAN/IPsec backup path over separate carriers) — replacing the single-carrier, no-redundant-ISP link named in `current-state.md` §4. NSX Federation or L2VPN extension carries the segments above between facilities where cross-facility connectivity is required (SQL Always On, Veeam replication).
- **Perimeter and load balancing**: NSX Edge clusters at each facility handle north-south traffic and host the NSX Advanced Load Balancer (Avi) instances that front the Portal (ADR-032).
- **Remaining clinic connectivity during migration**: the existing hub-and-spoke MPLS network (`current-state.md` §4) continues serving clinics not yet cut over, terminating at the Columbus facility's Edge cluster rather than the HQ server room — a phased retirement, mirroring the "Retire (phased)" strategy `architecture-options-and-styles.md` already recorded for the MPLS network.
- **Route enforcement**: spoke Tier-1 gateways default-route through the Tier-0 hub, which enforces Distributed Firewall policy before any traffic reaches another segment or the internet — the private-cloud-native equivalent of Azure's UDR-forced-tunnel, AWS's Transit Gateway route-table association, and GCP's NCC hub route policies.

No detail diagram exists yet for this ADR — hand-drawn diagrams are added incrementally and checked against this document once available, the same standard applied to every diagram in the Azure/AWS/GCP sections of this repository.
