# Necessity before method (2026-11)

Rationale for [kernel item 7](../docs/agent-corpus/README.md#execution-kernel):
ask whether something is needed before planning how to build it.

## Failure addressed

An agent receives a requirement, a proposed mechanism or its own earlier plan
step and treats it as fixed. Local technical competence then answers *how*
(wrap, clamp, add a command, add a layer, harden a hot path) and prevents the
upstream question *why must this exist in this form*. The observed case that
prompted this change: an agent designed a live in-place swap mechanism for a
rarely changed privileged component. The operator then noted that a rare
infrastructure change tolerates a planned interruption, which removed most of
the proposed mechanism and pointed to reuse of an existing one-shot route.

## Mechanism

Order the search, rather than adding a general instruction to "be critical":

1. question the requirement or proposed mechanism;
2. try deletion or reuse of an existing capability;
3. simplify what survives;
4. only then optimize, accelerate or automate.

Guard against the opposite failure ("long means delete"): for each removal,
name the user ability that could be lost and where it is preserved. If an
ability would be lost without a home, the element is needed.

## Sources and evidence status

- **Documented first-person practice (engineering hypothesis for agents).**
  Elon Musk's ordered process from the 2021 Starbase interview with Tim Dodd
  (Everyday Astronaut): make requirements less wrong, delete parts and process
  steps, simplify or optimize, accelerate, automate. Useful for its sequencing
  constraint, not as universal doctrine.
- **Measured result in humans.** Adams, Converse, Hales and Klotz, "People
  systematically overlook subtractive changes", *Nature* 592 (2021). Across
  eight experiments, people overlooked advantageous subtraction unless cued;
  cognitive load reduced it. This does not show that language models share the
  mechanism; it motivates testing an explicit deletion step.
- **Measured result in humans.** Jansson and Smith, "Design fixation",
  *Design Studies* 12 (1991): exposure to an existing solution constrains later
  exploration. For agents, reading a mature implementation first is
  solution-shaped context; whether it causes fixation is an open question.
- **Established practice.** The Design Council Double Diamond separates
  discovering and defining the problem from developing and delivering
  solutions. Don Norman argues that the problem as handed over is often a
  symptom, not the fundamental problem.
- **Unverified here.** A 2026 deep-research synthesis cites preprints on
  specification critique by coding agents (SpecBench) and implicit-requirement
  recovery (SWE-RPG). Their figures were not checked against primary sources
  and are not relied on.
- **Parable, historically uncertain.** The Technion "blood pipeline" story, in
  which students design the pipeline without asking why it is needed, is
  described by the Technion itself as a legend. Use it only as an illustration.

## Cost and when not to use it

The step is a short judgment, not a document or review ceremony. Skip the
deletion attempt for requirements whose authority is explicit and whose
removal would change the user contract; those need the owner, not the agent.

## Verification and revision

This change replaced duplicated runtime text instead of adding net words, so it
carries no behavioural trial yet. Revise or remove it if a trial shows no
difference in how often agents propose deletion or reuse before construction,
or if agents start removing needed elements without naming a preserved home.
