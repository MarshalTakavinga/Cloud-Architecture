# ADR-013: VCF Track — VCF Automation Self-Service and vSphere Kubernetes Service

**Status:** Approved (VCF track, subject to the Step 10 platform selection)
**Date:** Step 6 of the Case Study 6 pipeline

## Context

[ADR-005](ADR-005-platform-api-and-portability.md) requires a platform API with a catalog, Terraform, ServiceNow approvals, pipeline images, and a platform-run conformant Kubernetes that replaces three Rancher clusters. VCF 9.1 includes **VCF Automation** and **vSphere Kubernetes Service (VKS)**. The bank licenses both today and uses neither.

## Decision

- **VCF Automation** (the "All Apps" organization model) provides the catalog:
  - standard VMs from Packer-built templates
  - VPC networks per project
  - VKS namespaces with quotas
  - Terraform through the VCF Automation provider
  - ServiceNow approvals, automatic for Tier 2 and dev/test
- **VKS** replaces the Rancher RKE2 clusters. The platform team runs the clusters. The digital team gets namespaces and GitOps.
- **Portability rules** ([ADR-005](ADR-005-platform-api-and-portability.md)) apply: no VKS-specific resource types in application manifests.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Keep Rancher on VMs, run by the platform team.** Rejected. It pays for a second Kubernetes product while an included one sits idle.
2. **EKS Anywhere on vSphere** (the AWS lens). Rejected on this track. It adds an AWS subscription for what VKS provides inside the VCF subscription.

## Consequences

- **Positive:** Driver 4 is met with licences the bank already holds. The target of a VM in under 1 hour is realistic.
- **Negative / accepted trade-off:** VCF Automation and VKS skills are new to the team, although closer to their VMware base than any other track.
