# PEFY Governed Capability Layer

This directory adds governed, provider-neutral capability adapters without replacing the existing Mission Control runtime.

## Active capability intents

- Graphify adapter under ΩWORKGRAPH-style graph governance.
- Free/low-cost inference registry under ΩOmniRoute-style routing.
- Blockchain Dark Forest safeguards under ΩCSF / GARKAEL security governance.

## Runtime truth

Configuration in this repository can be enabled by default, but a capability is only considered **runtime-active** after:
1. a host is connected,
2. dependencies install successfully,
3. health checks pass,
4. required provider credentials are present where applicable,
5. privacy/risk policy permits the route.

No API secrets belong in this repository.

## External provenance

- Graphify upstream: https://github.com/Graphify-Labs/graphify
- SlowMist Blockchain Dark Forest Selfguard Handbook: https://github.com/slowmist/Blockchain-dark-forest-selfguard-handbook

The SlowMist handbook is used as a referenced security knowledge source. Its repository currently does not expose a top-level LICENSE file, so this integration records derived control concepts and links rather than copying the handbook wholesale.
