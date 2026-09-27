# ADR-025: GCP Track — Fleet, Config Sync, and Policy Controller; GCP Landing Zone; VDI in Azure

**Status:** Approved (GCP track, subject to the Step 10 platform selection)
**Date:** Step 8 of the Case Study 6 pipeline

## Context

GDC clusters join a **fleet** that also contains GKE clusters in Google Cloud. **Config Sync** (GitOps) and **Policy Controller** (admission policy) apply across the fleet. Horizon doesn't support KubeVirt. The bank's identity is Entra ID, and its SIEM is Sentinel.

## Decision

- **Governance and delivery:** fleet + Config Sync + Policy Controller. **VMs, networks, and namespaces are declared in Git and reconciled.** ServiceNow approvals become pull requests. Terraform manages the fleet.
- **Identity:** Entra ID through Workforce Identity Federation (cloud) and OIDC (clusters), with local RBAC and break-glass kubeconfigs in PAM.
- **Landing zone:** **Google Cloud**. The AWS account is closed and its data purged.
- **Telemetry:** the local stack and Cloud Logging, forwarded to **Sentinel**.
- **VDI:** **Azure Virtual Desktop or Windows 365 in Azure**, the only mainstream replacement given Horizon's platform list.
- **Migration:** disk export, qcow2 conversion, and Containerized Data Importer import, scripted in waves. There is no change-block-tracking tool.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Horizon on a vSphere island.** Rejected. It keeps Broadcom for desktops.
2. **Keep Rancher alongside GDC.** Rejected. GDC *is* the Kubernetes platform.

## Consequences

- **Positive:** The best GitOps developer experience of any track.
- **Negative / accepted trade-off:** Three vendors in the operating picture (Google for the platform, Microsoft for identity, SIEM, and VDI, and the island). The weakest migration tooling for 2,000+ VMs.
