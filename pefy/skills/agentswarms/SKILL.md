# ΩAgentSwarms Governed Adapter

## Purpose
Provide swarm-style multi-agent planning and execution patterns without making AgentSwarms the sovereign control plane.

## Authority
- Parent control plane: ΩMission Control / MƐTAPEFYON Ω.
- Routing: ΩOmniRoute / ΩGAAI.
- Security: ΩCSF / GARKAEL.
- Review: PEA/council gates.
- Consequential external, financial, legal, HR, security, contractual, or irreversible actions require explicit human approval.

## Runtime policy
1. Upstream AgentSwarms is a referenced internal workbench pinned to an approved commit.
2. The upstream application remains quarantined while production dependency audit contains any High or Critical vulnerability.
3. No third-party hosted service may be offered from the Elastic-2.0 upstream code.
4. A dedicated Supabase project is required before application runtime; never reuse SIRAYA or another business-domain database.
5. Provider credentials are injected only through secret stores/environment variables; never committed.
6. Swarms must expose task graph, assigned agent, tool scope, evidence, risk class, approval state, cost/quota, and outcome.
7. Default execution is least privilege, bounded concurrency, deterministic retry limits, idempotency where possible, and full audit trail.

## Fallback behavior
When the upstream runtime is unavailable or quarantined, implement swarm behavior natively through ΩMission Control using planner → specialist agents → council review → approval gate → executor → verifier → evidence ledger. This preserves capability without inheriting upstream runtime risk.
