### ADR-004: Payment tokenization approach

**Context:**
`current-state.md` §3 traces the PCI-DSS finding precisely: the browser submits card data to Solstice's Checkout & Payment service, which constructs and transmits the gateway request itself  cardholder data transits Solstice's application tier before tokenization happens, which is what pulls the whole environment into PCI scope. ADR-002 already named the fix in principle: use the payment gateway's existing hosted-tokenization capability. This ADR decides the specific mechanism, because "use hosted tokenization" still has more than one real implementation.

**Options considered:**
- Server-side API tokenization (today's model): the Checkout & Payment service receives raw card data from the browser, then calls the gateway's API to tokenize and charge it.
- Client-side hosted fields / iframe: the gateway's own JavaScript renders the card-number, expiry, and CVV input fields directly in Solstice's checkout page, inside an iframe the gateway controls. Card data goes from the customer's browser straight to the gateway's servers  Solstice's own code never receives it, not even transiently.
- A hybrid model, tokenizing on the client but still routing the tokenization request through Solstice's own servers as a proxy.

**Decision:**
Client-side hosted fields / iframe tokenization. The Checkout & Payment service never receives, handles, or transmits raw cardholder data at any point.

**Rationale:**
Server-side API tokenization is the current model, and it's the model that produced the PCI finding  keeping it would mean the whole re-architecture effort in Checkout & Payment still doesn't close the actual gap. Client-side hosted fields is the gateway's own recommended integration pattern for exactly this reduction: because Solstice's servers never receive the card data at all, the PCI scope shrinks to just the page that embeds the iframe and the tokenized-reference handling after the fact  a materially narrower boundary than "isolate the network segment that still receives raw card data," which was the best a server-side approach could achieve. A hybrid proxy model was considered and rejected specifically because routing the tokenization request through Solstice's servers, even briefly, keeps cardholder data transiting Solstice's environment  the exact problem this ADR exists to eliminate, just relocated rather than removed.

**Trade-off:**
Hosted fields constrain the checkout page's UI to what the gateway's embeddable component supports  Solstice loses some control over the card-entry form's exact styling and validation behavior compared to owning that form outright. Client-side integration also means a gateway-side outage or degradation is now directly visible on Solstice's checkout page, in a UI element Solstice doesn't fully control  a real, accepted dependency, not a new one (the gateway relationship already existed), but a slightly more visible one at the point of integration.

**Status:** Approved
