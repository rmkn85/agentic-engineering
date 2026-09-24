# Agentic efficiency frontier — September 2026

This note preserves research provenance behind the operational guidance added in September 2026. It is intentionally outside the normal execution-agent reading path.

Operational synthesis:

- [efficiency control plane](../docs/principles/efficiency-control-plane.md)
- [observation economy](../docs/execution/observation-economy.md)
- [bounded recovery](../docs/execution/bounded-recovery.md)
- [prompt-prefix stability](../docs/local-codex/prefix-stability.md)

## Research themes

### Externalize evidence; keep active context small

NVIDIA SoL-Pi combines Action Fusion, ObservationPack, evidence-preserving reduction, and online compaction. Its strongest portable lesson is to retain exact observations outside active model context and expose compact handles/receipts until deeper evidence is needed.

Source:
- https://github.com/NVlabs/SoL-Pi
- https://arxiv.org/abs/2609.20519

The paper reports 44.7–49.0% lower recorded token traffic on its 51-task EdgeBench while preserving roughly comparable task performance. Treat those numbers as evidence for that evaluated harness/workload, not a universal expected saving.

### Strong judgment at boundaries; cheaper execution in the bulk

Astra Flash Orchestrator keeps an expensive root model focused on planning/review while delegating discovery, implementation, testing, and debugging to a cheaper worker. Its field measurements are directionally interesting but are not a controlled causal estimate because task mixes and acceptance states differ.

Source:
- https://github.com/ethanplusai/astra-flash-orchestrator
- https://www.skillleaderboard.com/skill/ethanplusai-astra-flash-orchestrator

Portable rule: separate **capability selection** from **orchestration role**. A coordinator need not be the strongest model; strong capability can be reserved for bounded coupled decisions.

### Selective context management

Context as a Tool (CAT) makes context maintenance an explicit action and trains a compressor to decide when/how to compress SWE trajectories.

Source:
- https://arxiv.org/abs/2512.22087

fast-jev-compaction explores selective verbatim retention/deletion rather than rewriting all retained history into a lossy summary.

Source:
- https://github.com/tamaratran/fast-jev-compaction

Operational implication: do not assume "summarize at N tokens" is the only or best compaction policy. Compare native/default compaction, semantic summary, selective verbatim retention, and artifact-backed handles when the trade is material.

### Prefix/cache stability

Manus describes production context engineering around stable prompt prefixes, append-only state, deterministic serialization, stable tool schemas, and filesystem artifacts as external context.

Source:
- https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

vLLM Automatic Prefix Caching is the serving-layer analogue: repeated matching prefixes can reuse KV blocks and avoid repeated prefill work.

Source:
- https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/

Operational implication for API-hosted agent workflows: fix avoidable prefix churn before adding semantic compression machinery.

### Route before expensive inference

RouteMoA screens/ranks candidate models before invoking a dense mixture, balancing predicted performance, cost, and latency.

Source:
- https://arxiv.org/abs/2601.18130

AMRO-S combines a lightweight semantic router, task-specific routing memory, and asynchronous quality-gated updates.

Source:
- https://arxiv.org/abs/2603.12933

Operational implication: begin with an observable rule-based capability router and retained route/outcome traces. Learned routing adds training, calibration, drift, and another failure surface; justify it with data.

### Deterministic/local recovery before global replanning

Graph-Based Self-Healing Tool Routing uses a cost-weighted graph and deterministic rerouting, reserving the LLM for cases where no feasible route remains.

Source:
- https://arxiv.org/abs/2603.01548

Self-Healing Agentic Orchestrators uses failure classification, bounded targeted recovery, verification, and escalation rather than blind retry or full replanning.

Source:
- https://arxiv.org/abs/2606.01416

Layered tool orchestration similarly keeps global execution coarse while correcting local schema/argument failures locally.

Source:
- https://arxiv.org/abs/2602.18968

Operational implication: build a small explicit failure taxonomy and bounded recovery policy before a general autonomous recovery framework.

### Parallelism is not token efficiency

Anthropic's production multi-agent research system is useful as a counterexample to treating fan-out as a universal efficiency win: parallelism can improve breadth and wall time while multiplying token consumption.

Source:
- https://www.anthropic.com/engineering/built-multi-agent-research-system

Operational implication: measure wall-time speedup and token amplification separately.

### Serving optimizations are workload-regime dependent

LMCache's 2026 agentic benchmark shows tiered KV caching can materially help long-context concurrency when the active working set exceeds GPU cache, while adding overhead when HBM already suffices.

Source:
- https://github.com/LMCache/LMCache
- https://blog.lmcache.ai/en/2026/05/12/benchmarking-lmcache-for-multi-turn-agentic-workloads-on-amd-mi300x/

Operational implication: keep vLLM/LMCache/quantized-KV/speculative-decoding work optional and benchmark it only for self-hosted inference with a demonstrated serving bottleneck.

## Evidence discipline

Separate:

1. **controlled benchmark evidence** — strongest for deciding whether a mechanism can preserve quality while reducing resource use;
2. **production/field measurements** — useful but often confounded by workload and operational changes;
3. **engineering mechanisms** — plausible portable patterns that still require local validation;
4. **marketing claims** — do not promote without reproducible methodology and a quality gate.

The repository should adopt portable decision rules first and keep runtime/framework/model-specific implementations optional until local telemetry shows they are worth the dependency and maintenance cost.
