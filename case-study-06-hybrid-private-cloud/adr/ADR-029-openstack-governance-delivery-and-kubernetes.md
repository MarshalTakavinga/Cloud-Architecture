# ADR-029: OpenStack Track — Native APIs and Terraform, OpenShift on OpenStack, and Satellite/AAP with Arc Guests

**Status:** Approved (OpenStack track, subject to the Step 10 platform selection)
**Date:** Step 9 of the Case Study 6 pipeline

## Context

OpenStack's APIs and Terraform provider are mature. RHOSO already uses OpenShift for its own control plane, but application Kubernetes needs its own OpenShift subscription. Driver 3 wants one governance plane, and the bank's identity and SIEM are Microsoft.

## Decision

- **Delivery:** OpenStack projects, quotas, and APIs through Terraform, with ServiceNow approvals. Golden images go to Glance.
- **Kubernetes:** **OpenShift on OpenStack** (installer-provisioned) replaces the Rancher clusters.
- **Governance:**
  - **Satellite + Ansible Automation Platform** for hosts, guest patching, and compliance.
  - **Arc-enabled servers** in guests for inventory and policy reporting alongside the **Azure landing zone**.
  - Everything reconciles to ServiceNow, and telemetry goes to Sentinel.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Magnum or Cluster API for Kubernetes.** Rejected on supportability for a Tier-2 platform the digital team depends on.
2. **A GCP or AWS landing zone.** Possible, because the track is cloud-neutral. Azure is chosen because of Entra ID, Sentinel, and M365.

## Consequences

- **Positive:** The most mature infrastructure-as-code path of any track.
- **Negative / accepted trade-off:** Governance spans several consoles (partial on driver 3), and OpenShift is an additional subscription and skill.
