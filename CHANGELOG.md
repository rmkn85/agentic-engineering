# Changelog

## Unreleased

- Initial repository foundation.
- Added principles for context economics, local execution, caching, incremental semantic work, collaboration, measurement, evidence, and local overrides.
- Added a focused default agent operating corpus and explicit reading boundary so ordinary agents do not crawl the full documentation/research tree.
- Added a separate `references/` archive preserving external context/instruction research without imposing it on normal runtime context.
- Added instruction/context adherence experiments covering baseline failure, ablation, instruction interference, context pressure, and model/enforcement escalation.
- Added deterministic instruction-footprint inventory tooling and context/adherence metrics.
- Added low-friction quick wins and tightened the global instruction template and efficiency skill to reduce recurring instruction cost.
- Added agent-legible code guidance: semantic locality, explicit contracts/dependencies/state, analyzable control flow, behavior-level tests, mechanically enforced invariants, and anti-patterns that increase future agent context/edit radius.
- Defined agent analyzability as **bounded mental-model construction by a fresh weaker coding model**, rather than formal proof or strongest-model eventual success; added weak-reader semantic accuracy/context-expansion metrics and experiments.
- Added a compact source-scoped `AGENTS.md` router plus four focused source-work skills: new module boundary, new unit inside a module, changing/refactoring a local unit, and refactoring a whole module/boundary.
- Added a skill-granularity experiment to test whether focused-skill context/adherence gains exceed discovery and routing overhead.
- Added code-legibility research spanning batch/punch-card systems, structured programming, information hiding, JPL/NASA, airborne/real-time assurance, repository-level LLM retrieval, SemBench/LongCodeU/CodeGlance/CodeSense, and agent-first engineering.
- Added agent-efficient runtime diagnostic guidance based on progressive disclosure: compact outcome/capsule first, correlated focused evidence next, retained raw artifacts last.
- Added offline postmortem bundles so crashes remain diagnosable after the target process is dead: a small manifest indexes progressively deeper stack/event/environment/trace/dump/log artifacts.
- Added bounded flight-recorder, deterministic record/replay, persistent crash-buffer and dynamic targeted-probe escalation guidance for hard incidents.
- Added focused skills for producing runtime feedback and consuming failure evidence, plus a diagnostic-feedback experiment covering dead targets, environmental failures, duplicate storms, CI/build failures, partial telemetry and self-healing attempts.
- Updated `quiet-run` to emit a structured layered diagnostic bundle instead of automatically pasting a fixed failure tail into agent context.
- Preserved diagnostic-feedback research covering Deep Space 1 beacon/fault protection, syslog, minidumps/crash reports, Java Flight Recorder, supervision/crash-only/autonomic systems, delta debugging, deterministic replay, Dapper/SRE/OpenTelemetry, Kubernetes, structured build/static-analysis protocols, and modern LLM-facing observability.
