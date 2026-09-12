### ADR-009: Identity provider for patient-facing authentication

**Context:**
ADR-002's Zero Trust decision assumed a single identity provider verifying every call. That holds for staff and providers, who are already represented in Meridian's on-prem Active Directory and synced to Microsoft Entra ID via Entra Connect. Patients are not — they have no corporate directory account, and putting them in one would be both wrong (they aren't employees) and a security problem (it would mix a consumer population into the workforce directory that also gates clinical system access).

**Options considered:**
- Extend the existing workforce Microsoft Entra ID tenant to also hold patient accounts
- Microsoft Entra External ID (CIAM) — a separate, consumer-facing identity product built for external users
- A patient login system built and hosted by the portal application itself

**Decision:** Microsoft Entra External ID, as a distinct identity population from workforce Entra ID.

**Rationale:**
Building and hosting patient login directly in the portal application means owning password storage, MFA, account recovery, and breach response for ~2 million patient identities — undifferentiated heavy lifting that has nothing to do with what CareLink PM or the portal actually do, and a direct security liability if done imperfectly. Extending the workforce Entra ID tenant is worse, not better: it mixes a consumer population with materially different risk and lifecycle characteristics into the same directory that governs Conditional Access for clinical system access, and every future workforce policy change (Conditional Access rules, Privileged Identity Management, license assignment) now has to account for patient accounts that shouldn't be affected by it. Entra External ID is purpose-built for exactly this split: same underlying Microsoft identity platform and OIDC/SAML support the portal already needs, but a genuinely separate tenant boundary from the workforce directory.

**Trade-off:**
This means the portal integrates against two identity providers instead of one — more configuration, two sets of Conditional Access-equivalent policies to reason about, and two places an identity-related incident could originate. Accepted because collapsing them into one directory trades a manageable integration cost now for a much harder-to-reverse governance problem later.

**Status:** Proposed

See [`../diagrams/patient-identity-architecture.png`](../diagrams/patient-identity-architecture.png) for the two-tenant identity architecture, the patient OIDC authentication flow, and how the Portal integrates both providers.
