# ADR-018: GCP Edge Platform — Google Distributed Cloud (Bare Metal) + Manufacturing Connect Edge

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

Google retired Cloud IoT Core on 16 August 2023 and has no first-party IoT hub. Its industrial edge story combines three pieces:
- **Google Distributed Cloud (GDC) software-only for bare metal**: Kubernetes on Kestrel's own hardware, with an **edge profile** for resource-constrained sites and 3-node HA with replicated storage
- **Manufacturing Connect edge (MCe)**: Litmus Edge built for Google Cloud, with 270+ protocols, store-and-forward, Sparkplug B edge-node and client support, and about 10,000 tags per edge deployment. It is sold and supported by Litmus.
- **Litmus Edge Manager** for central management of MCe

Google's documentation on disconnection states that when GDC clusters are disconnected, local Kubernetes operations and application deployment continue with no time limit, and Config Sync keeps working if Git is reachable. Creating, upgrading, and adding nodes to clusters stops, and so does Cloud Identity sign-in.

## Decision

Each plant runs a **3-node GDC bare-metal cluster (edge profile)** in the Level 3 zone, hosting:
- **MCe** as P1: one instance per 10K tags, so two at the larger plants. It publishes Sparkplug B.
- a **commercially licensed, clustered Kubernetes-native MQTT broker** as P2, because MCe is a Sparkplug edge node and client, not a broker
- Kestrel-built P3–P5, the outbox ([ADR-019](ADR-019-gcp-store-and-forward-implementation.md)), and the activation controller

Operator sign-in to clusters during an outage uses **local break-glass credentials** held in the plant, because Cloud Identity-based sign-in is unavailable while disconnected.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **GDC connected (Google-supplied hardware).** Rejected. It puts Google-owned hardware into 12 plants under a heavier commercial model. Kestrel's servers are commodity and replaceable locally, and the software-only edition gives the same Kubernetes behavior.
2. **MCe on standalone VMs or appliances without Kubernetes.** Rejected. HA would fall back to hypervisor clustering or DIY failover (the problem the AWS track has), and Kestrel's own components would have no uniform scheduler.
3. **An open-source-only edge (a K3s cluster, an open-source broker, open-source OPC UA collectors) with GCP only in the cloud.** Considered. It is cheapest in licences, but Kestrel would then be building and supporting collection for three PLC families itself. MCe's protocol coverage is exactly the capability Kestrel lacks.
4. **Litmus Edge's own clustering instead of Kubernetes.** Not selected, because the HA characteristics were not found in the documentation reviewed. Kubernetes restarting the MCe pod on another node over replicated storage is the documented path.

## Consequences

- **Positive:** This is the strongest match to Step 4 of the three tracks. Sparkplug B is native, and protocol coverage handles the Mitsubishi and Windows 7 plants with no extra gateways. Plant autonomy has no documented ceiling, compared with Azure's 72-hour limit ([ADR-006](ADR-006-azure-edge-platform.md)), and it keeps real Kubernetes HA, which AWS lacks ([ADR-012](ADR-012-aws-edge-platform.md)).
- **Negative / accepted trade-off:** **There are three edge vendors**: Google for GDC, Litmus for MCe, and the broker vendor. Incident ownership and patch coordination span three contracts, in plants without IT staff. This is scored under operational fit.
- **Negative / accepted trade-off:** MCe's roughly 10K-tag limit per instance means about 16 licensed instances, and it caps growth per instance. Tag growth at a plant becomes a licensing event.
- **Negative / accepted trade-off:** Cluster upgrades require connectivity. That is acceptable, since upgrades are planned, but it means a plant with a prolonged outage also falls behind on security patches.
