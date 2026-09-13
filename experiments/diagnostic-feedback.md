# Diagnostic feedback experiment: does progressive evidence reduce diagnosis cost?

Status: comparison protocol. This does **not** assume that shorter output is better.

Use this when changing logs, crash artifacts, telemetry schemas, CI/test/build output, self-monitoring, sampling, failure grouping, or postmortem bundles partly to reduce future agent diagnosis cost.

## Governing question

> For the same failure and retained diagnostic truth, does the candidate feedback design let a fresh agent reach the same accepted diagnosis/action with less fresh evidence context, fewer probes and less recovery work?

## Core comparison

Prefer a controlled comparison between:

1. **raw-first baseline** — normal/full console/log/stack/dump style evidence;
2. **progressive evidence** — compact manifest/capsule + focused linked artifacts + same or richer raw evidence retained out-of-band.

Do not give the progressive variant less underlying evidence and call the smaller prompt a win. The point is **navigation**, not deletion.

## Important workload: dead target

At least one representative case should terminate or make the target unavailable.

The agent must be able to diagnose from persisted artifacts alone:

```text
manifest -> focused evidence -> raw artifact as needed
```

A design that requires querying the crashed process fails this case.

## Useful workloads

Choose the smallest set needed for the claim:

### Unhandled exception / crash

Provide a crash with a useful application frame, surrounding events, environment identity and a large retained raw artifact.

Tests whether the agent starts from the index and escalates only as needed.

### Environmental failure

Keep application code unchanged but alter a dependency/runtime/resource/config condition.

Tests whether environment fingerprints/deltas prevent unnecessary source-code excavation.

### Repeated failure storm

Generate many equivalent failures plus a few meaningfully different ones.

Tests grouping/fingerprinting without hiding real variation.

### CI/build/test failure

Compare raw terminal output with structured failed target/test/static-analysis records and artifact links.

### Partial diagnostic failure

Truncate an artifact, remove symbols, or make the telemetry collector fail partway.

Tests whether incompleteness is explicit rather than silently treated as absence of evidence.

### Self-healing attempt

Trigger a bounded retry/restart/fallback before final escalation.

Tests whether the agent can see what was already attempted and avoid repeating the same action.

## Hold constant

Where practical, keep constant:

- failure cause and inputs;
- application/release/config except when environment delta is the variable;
- model and reasoning effort;
- task prompt and acceptance criteria;
- retained raw evidence;
- source repository state;
- diagnostic correctness/privacy constraints.

The independent variable should be how evidence is structured, summarized, correlated, sampled or surfaced.

## Outcome gate

A variant qualifies only when diagnosis/recovery quality is non-inferior.

Check as appropriate:

- correct fault localization/root cause when determinable;
- correct distinction between fact and hypothesis;
- correct proposed or implemented remediation;
- no missed high-impact evidence caused by filtering/grouping;
- no false confidence from truncated/partial artifacts;
- privacy/security requirements preserved;
- raw evidence remains retrievable where the design claims it is retained.

## Agent-context metrics

Record what the harness exposes reliably:

- fresh input tokens used for diagnostic evidence;
- unique evidence bytes/tokens opened;
- number of artifacts/files opened;
- raw artifact bytes available vs actually consumed;
- model turns;
- search/filter/query/tool calls;
- repeated reads of the same evidence;
- time to first plausible hypothesis;
- time/turns to accepted diagnosis or fix;
- human corrections/escalations.

## Navigation metrics

For the progressive variant, also record:

- whether the first capsule/manifest correctly identified the next useful evidence class;
- number of evidence edges followed before acceptance;
- largest artifact opened;
- unnecessary deep-artifact opens;
- missing/broken references;
- whether the agent had to reconstruct correlation manually;
- whether a live query was required despite a postmortem claim.

Useful ratios include:

```text
evidence_context_ratio = progressive_evidence_tokens / raw_first_evidence_tokens
artifact_open_ratio     = progressive_artifacts_opened / raw_first_artifacts_opened
turn_ratio              = progressive_model_turns / raw_first_model_turns
resolution_time_ratio   = progressive_resolution_time / raw_first_resolution_time
```

Only interpret these after the outcome gate passes.

## Counter-tests

Progressive disclosure can fail in several ways. Test explicitly for:

- **over-compression:** first-level summary omits a fact needed to choose the right branch;
- **misleading derived view:** symbolication/filtering/grouping is wrong while raw evidence is correct;
- **broken graph:** referenced artifacts expired, moved or cannot be accessed;
- **grouping collision:** distinct failures collapse into one fingerprint;
- **sampling blindness:** the only useful failing trace/event was sampled out;
- **collector common-mode failure:** crash also breaks the reporting mechanism;
- **retry masking:** automatic recovery hides the original symptom;
- **sensitive evidence escalation:** agent opens a raw dump that should not be model-visible;
- **diagnostic overhead:** instrumentation meaningfully harms application latency/resources.

## Interpretation

Prefer the candidate when:

1. diagnostic/recovery acceptance is non-inferior;
2. the agent consumes less fresh evidence or fewer probes on representative failures;
3. deeper evidence remains available and trustworthy;
4. dead-target cases remain diagnosable;
5. runtime/storage/privacy cost is justified;
6. the result survives more than one cherry-picked incident.

If the compact summary is cheaper only because it omits evidence needed for hard cases, it is not an efficiency improvement.

## Related guidance

- operational design: [`../docs/runtime/diagnostic-feedback.md`](../docs/runtime/diagnostic-feedback.md)
- postmortem bundles: [`../docs/runtime/postmortem-bundles.md`](../docs/runtime/postmortem-bundles.md)
- producer skill: [`../skills/instrumenting-runtime-feedback/SKILL.md`](../skills/instrumenting-runtime-feedback/SKILL.md)
- consumer skill: [`../skills/diagnosing-runtime-failure/SKILL.md`](../skills/diagnosing-runtime-failure/SKILL.md)
