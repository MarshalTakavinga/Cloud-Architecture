# Current-State Architecture — Meridian Health Network

See [`../diagrams/current-state-architecture.png`](../diagrams/current-state-architecture.png) for the full current-state diagram — organization profile, application stack, infrastructure, network architecture, identity/security posture, HA/DR posture, and the operational incidents driving this migration, all in one hand-reproduced, verified-against-this-document view.

## 1. Organization Profile

**Meridian Health Network** is a fictional, composite mid-size regional health system headquartered in Independence, Ohio, built as a realistic stand-in for the kind of organization that actually carries this exact migration problem. It was founded in 1987 as a three-physician family practice and grew through three decades of independent-practice acquisitions across Cuyahoga, Summit, and Stark counties.

- 42 outpatient clinics, 3 urgent care centers, 1 ambulatory surgery center — 46 physical sites total
- Specialties: primary care, pediatrics, OB/GYN, cardiology, orthopedics, behavioral health
- Referral relationships (not ownership) with two regional hospital systems
- ~1,180 credentialed providers (physicians, NPs, PAs); ~4,300 total employees
- ~2.05 million unique patient records accumulated over 20+ years; ~410,000 patients active in the last 24 months
- ~3.6 million scheduled appointments per year across all sites
- Corporate IT/infrastructure staff: 16 people (4 network/systems, 4 DBAs/application admins, 3 security & compliance, 2 service desk leads, 3 leadership/PM), supplemented by an after-hours NOC MSP and a specialist consulting vendor for practice-management patching

## 2. Application & Clinical Systems Stack

| System | Role | Notes |
| --- | --- | --- |
| CareLink PM 8.2 | Practice management, scheduling, registration, billing | Windows thick client, first deployed 2011, last major upgrade 2019; published to all 46 sites via Citrix Virtual Apps 7 (2003 LTSR) |
| LinkEngine 4 | HL7v2 interface engine | ~1.1M messages/month to LabCorp, Quest, 3 hospital-affiliated radiology/PACS feeds, and the Surescripts e-prescribing network |
| MeridianConnect | Patient portal | Self-hosted ASP.NET app in the on-prem DMZ; bolted onto CareLink PM, not natively integrated |
| Third-party video visit vendor | Telehealth | Stitched in via a scheduling plug-in added in 2020; separate login from the portal, frequent support tickets |
| Microsoft SQL Server 2014 Enterprise | System of record | 2-node Always On Availability Group — **both replicas live in the same primary data center**; extended support has ended, so the platform runs unpatched against newly disclosed CVEs |

## 3. Infrastructure

**Data center:** a converted server room inside the Independence, OH corporate HQ — not a commercial colocation facility. Raised floor added in 2014. Single utility feed, one 10-year-old diesel generator, single-carrier fiber uplink (200 Mbps, no redundant ISP).

**Compute:** VMware vSphere 6.7 cluster, 6× Dell PowerEdge R740 hosts, average age 6.5 years, approaching vendor end-of-life. Peak utilization (Monday mornings, flu season) runs ~85% CPU/memory with no real burst headroom.

**Storage:** Dell EMC Unity SAN, ~180 TB raw, thin-provisioned and at 91% used.

**Backup:** Veeam nightly disk-to-disk to a target on the same SAN, plus LTO-7 tape rotated offsite weekly by courier. Some branch-site local scan/imaging caches are not protected between nightly backup windows.

## 4. Network Architecture

Hub-and-spoke MPLS from HQ to all 46 sites, with ad hoc site-to-site IPsec VPN backup links at some newer or acquired clinics. Most clinics run a flat internal network with limited VLAN segmentation between clinical workstations, guest Wi-Fi, and connected medical devices. A single aging hardware firewall sits at the HQ edge (firmware patched quarterly); most branch sites have no next-gen firewall or IDS/IPS of their own.

```
Patients / Referring Providers
        |
   Public Internet
        |
  HQ Edge Firewall (single, aging)
        |
  +-----+------------------------------+
  |                                    |
MeridianConnect Portal (DMZ)     Site-to-Site MPLS Hub
  |                                    |
CareLink PM DB tier                46 Spoke Sites (clinics/UCs/ASC)
(SQL Server 2014 AAG,             — flat internal VLANs
 both nodes, same DC) <---HL7---> LinkEngine 4 --> LabCorp/Quest/PACS/Surescripts
  |
VMware vSphere 6.7 (6x R740, ~85% peak util)
  |
Dell EMC Unity SAN (180TB, 91% used)
  |
Veeam D2D (same SAN) + weekly LTO-7 courier offsite
  |
DR "closet" — Stark County clinic
(2 aging standby servers, tape drive, tabletop-tested only)
```

## 5. Identity, Security & Compliance Posture

- Single on-prem Active Directory forest/domain
- MFA is **not** enforced for clinical staff logging into CareLink PM or the portal admin console; MFA is only required for a subset of remote VPN users
- Several legacy integrations still use shared/generic service accounts
- Encryption at rest is inconsistent: newer SAN volumes are encrypted, several older LUNs — including some patient-imaging archive volumes — are not
- Audit logging exists inside SQL Server and Windows Event Logs but is not centralized into a SIEM; a coordinated forensic review after an incident is a manual, multi-system exercise

## 6. HA/DR Posture

| Metric | Current State |
| --- | --- |
| Secondary data center | None — DR "closet" at one clinic, not a real facility |
| RTO (documented) | 24–48+ hours (order hardware, restore from tape, manually rebuild AD/DNS/SQL) |
| RPO (documented) | Up to 24 hours (nightly backup cycle) |
| DR testing | Tabletop exercises only — never a live failover |
| Failover mechanism | None automated; fully manual |

## 7. Operational Incidents (Why This Is Urgent Now)

- **January 2025:** a regional ice storm caused a 14-hour power outage; generator fuel ran low before utility power returned. Scheduling and check-in were down at all 46 sites for nearly a full business day, forcing paper scheduling and manual charge capture.
- **March 2026:** a phishing email compromised a front-desk credential with no MFA on the VPN account; the attacker moved laterally for ~36 hours before the after-hours MSP caught it. No confirmed data exfiltration, but it triggered a cyber-insurance review — the insurer's renewal now conditions premiums on organization-wide MFA, immutable/offsite backups, and annual tested DR, or a 3x premium increase.
- **Flu season 2025:** scheduling page loads spiked to 8–12 seconds during Monday-morning peak booking; patient portal self-scheduling abandonment rose and call-center volume climbed in response.
- SQL Server 2014's end of extended support is flagged as a recurring finding in the annual third-party security risk assessment.
- Meridian is mid-acquisition of a 9-clinic independent pediatric group; onboarding a new site onto CareLink PM under the current architecture takes an estimated 4–6 months per site (VPN circuit provisioning, hardware capacity), and leadership wants that down to weeks.
- Patient portal self-scheduling and telehealth usage grew roughly 340% since 2020 but the platform was never re-architected for that scale, and the bolted-on video vendor is a persistent source of patient and staff complaints.
