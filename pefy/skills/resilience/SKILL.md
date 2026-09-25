# ΩResilience Fabric Skill

## Purpose
Make resilience, business continuity, disaster recovery, and data recovery mandatory characteristics of every PEFY capability.

## Scope
Applies automatically to every skill, tool, agent, multi-agent swarm, MCP server/client, API, workflow, connector, provider adapter, runtime, queue, datastore, document pipeline, model integration, automation, and future capability.

## Core operating rule
A capability is not complete merely because it works in normal conditions. It must also define how it:
1. detects failure,
2. contains failure,
3. continues in a degraded or alternate mode,
4. protects state and evidence,
5. recovers to a known-good state,
6. reconciles queued/in-flight work,
7. proves recovery.

## Mandatory resilience contract
Every registered capability must declare:
- criticality tier,
- dependencies,
- health signal,
- timeout policy,
- retry policy,
- circuit breaker behavior,
- fallback chain,
- degraded/offline mode,
- state location,
- backup method,
- RTO,
- RPO,
- recovery owner,
- recovery runbook,
- evidence location,
- post-recovery reconciliation rule.

## Continuity modes
Normal → Degraded → Offline/Local → Read-only → Manual-assisted → DR → Reconciliation → Normal.

The orchestrator must choose the least-disruptive safe mode that preserves business intent. A failure in one agent/provider/tool must not automatically terminate the whole mission when an authorized substitute exists.

## Collaboration and substitution
Capabilities expose a common contract to ΩMission Control and ΩOmniRoute. When a dependency fails:
- reroute to an equivalent healthy capability,
- preserve inputs, context, checkpoints, provenance, and approval state,
- never broaden permissions during failover,
- never silently downgrade privacy/security requirements,
- queue non-urgent work durably if immediate execution is unsafe,
- allow human-assisted/manual execution for critical workflows.

## Runtime patterns
Use health checks, watchdogs, circuit breakers, bounded exponential backoff with jitter, bulkheads, backpressure, idempotency, durable queues/outbox, checkpoints, safe restart, provider failover, local fallback, caching, and read-only degraded modes where applicable.

## State and data recovery
- Prefer stateless/rebuildable runtimes.
- Externalize durable state to governed stores.
- Use versioning and integrity checks.
- Baseline backup model: 3-2-1-1-0.
- Tier 0/1 require an immutable or WORM-capable copy where technically available.
- Encryption is required in transit and at rest.
- Backups are not considered valid until restore is tested.
- In-flight work must be checkpointed or safely replayable.
- After restore, perform integrity, duplication, ordering, authorization, and ledger reconciliation.

## Criticality targets
- Tier 0 Control Plane: RTO 15 min; RPO 5 min.
- Tier 1 Critical Business: RTO 60 min; RPO 15 min.
- Tier 2 Standard Business: RTO 4 h; RPO 1 h.
- Tier 3 Noncritical: RTO 24 h; RPO 24 h.

These are default engineering targets; stricter contractual or regulatory objectives override them.

## Admission gate
Do not mark a Tier 0/1 capability production-ready when it has:
- no health signal,
- no usable fallback,
- state without a recovery plan,
- uncontrolled retry of non-idempotent actions,
- an unaccepted single-provider dependency,
- no recovery owner/runbook,
- untested restore for required data.

## Security during continuity
Failover does not suspend ΩCSF, GARKAEL, privacy, IP, tenant isolation, approval gates, or least privilege. Break-glass paths must be explicit, time-bounded, logged, and reviewed.

## Evidence
Continuity and recovery events must produce audit evidence: incident ID, trigger, selected fallback, lost/deferred work, RTO/RPO actuals, data-integrity result, recovery timestamp, reconciliation result, and corrective action.
