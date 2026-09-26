# ADR-017: AWS Network Connectivity, Identity, and Pull-Based Edge Deployment

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

[ADR-003](ADR-003-ot-segmentation-reference-architecture.md) requires DMZ-only egress, outbound-only connections to the cloud, and plant-pulled deployments with an approval gate. Step 5 requires a per-node X.509 identity, signed artifacts, shadow-mode activation, and one-step rollback. Traffic volumes and WAN topology are as described in [ADR-011](ADR-011-azure-network-identity-and-deployment.md). Kestrel's workforce identity provider is Entra ID. SageMaker Edge Manager was discontinued on 26 April 2024, so edge model deployment on AWS uses standard Greengrass components.

## Decision

**Network**
- **Plant DMZ:** an **HTTPS forward proxy** (Squid or Envoy) with an allowlist of the AWS IoT Core data and credentials-provider endpoints, S3, Kinesis, and the Greengrass service endpoints. Greengrass, stream manager, and the SiteWise collector are configured to use it. The Level 3 nodes have no other egress.
- **US and Mexico plants:** MPLS to Columbus, then an **AWS Site-to-Site VPN** (two tunnels) to a **Transit Gateway** in **us-east-2 (Ohio)**. The same path carries Lambda's SAP OData calls back to Columbus.
- **German plants:** a VPN per plant to a Transit Gateway in **eu-central-1 (Frankfurt)**.
- **Endpoints:** interface VPC endpoints for IoT Core, Kinesis, SageMaker, and Secrets Manager, and a gateway endpoint for S3. Service control policies (SCPs) deny non-approved regions and public endpoint use.

**Identity**
- **Devices:** each Greengrass core has an **X.509 certificate in AWS IoT Core** and exchanges it for short-lived credentials through the token exchange role. The certificate is per node, revocable per node, and never shared, which matches Step 5 as written.
- **Humans:** **IAM Identity Center federated to Entra ID** (SAML + SCIM), with permission sets per role and per region. EU raw-data access is limited to EU-scoped permission sets.
- **Plant-local mTLS** for the broker and TimescaleDB uses a plant-local CA, so local operation never depends on AWS.

**Deployment (P9)**
- **Packaging:** models are trained and registered in **SageMaker AI**, then packaged as ONNX **Greengrass components**. Artifacts are signed with **AWS Signer** and published to S3.
- **Delivery:** deployments target per-plant **thing groups**. The Greengrass nucleus learns of a new deployment over its **outbound** MQTT session and **downloads** the artifacts through the DMZ proxy.
- **Activation:** a Kestrel-built activation component runs new models in shadow mode and promotes them only after a plant approval, recorded in the audit table. Rollback is a redeployment of the previous component version, which is cached locally.

**Landing zone**
- **Control Tower Organization** with accounts for OT-Data (US), OT-Data (EU), Analytics, Genealogy, Security/Log Archive, and Shared Network.
- The 2024 SageMaker PoC account is enrolled, its model code is extracted to the Analytics account, its historian data copy is purged, and the account is closed.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **AWS Direct Connect.** Rejected as disproportionate to about 60 Mbps of aggregate traffic with no production-critical WAN dependency, as on Azure.
2. **Greengrass connecting directly to the internet, with no DMZ proxy.** Rejected, because it violates ADR-003.
3. **A separate identity directory for AWS (IAM users, or a new IdP).** Rejected. Federating to the existing Entra ID avoids a second joiner/mover/leaver process.

## Consequences

- **Positive:** Device identity and outbound-only deployment are native and match Step 5 exactly, with no local registry mirror needed, since Greengrass caches components on the device.
- **Positive:** Identity Center federated to Entra shows that Kestrel's Microsoft identity estate is not a lock-in factor. It works cleanly on AWS too.
- **Negative / accepted trade-off:** Greengrass holds a **persistent outbound session** through which the cloud *notifies* the device of deployments. That is still outbound-initiated and consistent with ADR-003, but the plant's approval gate (not the network) is what stops an unwanted model from going live. The same is true of Azure's Arc agents, and it is noted here for honesty in both tracks.
- **Negative / accepted trade-off:** The DMZ proxy allowlist must track AWS endpoint changes for several services. This is a small but recurring operations task.
