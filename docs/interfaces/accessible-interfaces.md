# Accessible interfaces by default

Accessibility and human comprehension are part of a correct interface, not optional polish. Apply this contract when designing, implementing, changing or reviewing human-facing interfaces, including internal tools, prototypes, dashboards, games, settings and generated visual/document output. An API-only task needs its machine contract, not an invented UI.

These are **local engineering requirements**, informed by the [standards and applicability map](standards.md), not quotations from ISO or a certification claim. Omission from a task does not authorize inaccessible defaults or regressions. Preserve the quality bar on the changed journey without turning a bounded task into an unrelated whole-product rewrite.

## Select the applicable profile

For the web, target all applicable **WCAG 2.2 Level A and AA** criteria and relevant **W3C COGA** cognitive-usability patterns. Use **ISO 9241-125:2017** and **ISO 9241-112:2025** for visual/information presentation and **ISO 9241-110:2020** for interaction principles. COGA is supplemental guidance, not part of WCAG conformance. Follow stricter applicable product, platform, contractual and legal requirements.

Before implementation, identify the primary task, users, shipped surfaces, input methods and viewing conditions. Do not assume a mouse, large monitor, perfect vision or uninterrupted attention. Consider narrow windows, scaling, color-vision differences, low vision and assistive technology. Derive needs from users and tasks; do not assign one universal design to a diagnosis.

Reuse the approved project profile and native components. Put applicable standards and decisive checks in the existing task/acceptance record. No new standards database, mandatory library, parallel design system or per-task upstream download is required.

## Implement complementary access paths

### Human visual comprehension

Preserve complete meaning in the specification; show the minimum sufficient meaning for the current human task. Orientation, action, monitoring and investigation need different detail. Make purpose, state, relationships and the next action discoverable through grouping, position, alignment, scale, contrast and conventional cues. Reserve emphasis for genuine priority.

Keep short, familiar visible labels where they identify controls, values or ambiguous symbols. Do not replace labels with obscure icons, hide necessary instructions in metadata, or depend only on color, shape, sound or location. Arrows must represent real direction or relationships. More badges, cards, borders and animation do not establish clarity.

Remove irrelevant attention demands before adding explanation. Add a label, cue or example only to resolve a specific ambiguity. Stage secondary detail without hiding task-critical information, warnings or frequent controls; preserve useful expert views. Neither minimum words nor maximum information density is the objective.

Limit unnecessary interruptions, motion and layout shifts; honor relevant motion, contrast and text-size preferences. Preserve task state across ordinary errors and interruptions. Support recovery and make consequential actions understandable before execution. A first-time user must not need the design document to discover the normal start-to-result journey.

### Human assistive access

Prefer semantic HTML or native accessible platform controls. Use WAI-ARIA patterns for custom web widgets only where native semantics are insufficient: adding a role does not implement keyboard behavior. Keep visible labels, accessible names, roles, values, states and logical reading order consistent. Use platform accessibility APIs for native software.

Provide keyboard operation, visible and unobscured focus, sensible focus movement/return and no traps. Make targets usable and provide alternatives to dragging or complex gestures where required. Announce relevant errors and status changes without stealing focus or flooding announcements. Support error correction and accessible authentication.

Apply the actual WCAG criteria and exceptions, not memorized slogans. Ordinary text generally needs 4.5:1 contrast, large text 3:1, and meaningful graphical/control boundaries 3:1 under their respective criteria. Exercise 200% text resizing and reflow at 320 CSS pixels where applicable. Do not shrink text to hide overflow; a genuine two-dimensional-content exception does not exempt surrounding controls.

Provide equivalent alternatives for meaningful non-text content and applicable captions, transcripts or audio description. Canvas, WebGL, charts and generated images are not accessible because a screenshot exists or OCR reads labels. Expose task-relevant meaning and operation through supported accessible structures or an equivalent usable route. Keep decorative content out of the accessibility tree.

### Authorized machine access

Preserve structured semantics independently of styling through semantic DOM/native accessibility structures and documented API/tool schemas when programmatic access is part of the product. Keep underlying state, permissions and action meaning consistent. Do not invent a parallel backend or JSON sidecar for every screen when existing structures suffice.

Machine completeness must not become visible text everywhere. A DOM snapshot, accessibility tree or MCP/API response cannot establish human visual usability. Crawlers, assistive technology and programmatic clients are distinct consumers. Support intended clients without weakening authentication, authorization, privacy, consent or destructive-action safeguards.

## Acceptance gates

Select a representative end-to-end task before implementation. Add repeatable checks to existing component/E2E commands and CI where feasible; retain human checks where tools cannot establish the property. Reuse evidence only while relevant inputs remain unchanged.

| Gate | Decisive evidence on the changed journey | Not a substitute |
| --- | --- | --- |
| Visual comprehension | Inspect rendered pixels at intended sizes/states; identify purpose, priority, relationships and next action from presentation. | Extracted labels, DOM/source, specification or implementer's explanation. |
| Interaction and recovery | Exercise ordinary inputs through start, action, result and relevant error/cancel/return behavior. | Pre-completed fixtures or presence of buttons. |
| Accessible operation | Applicable automated checks plus keyboard/focus, resize/reflow/contrast and representative assistive-technology checks, including dynamic states. | Scanner success, ARIA attributes or accessibility-tree snapshots alone. |
| Cross-path consistency | Visual, accessible and exposed API/tool state agree and preserve permissions. | Hard-coded descriptions or a separate mock. |
| Human usability | Where acceptance or material novelty/risk requires it, representative users complete the task; record confusion and outcomes. Include disabled users when assessing their experience. | Agent self-approval, disability filters or automated success. |

Follow the [E2E evidence rules](../runtime/e2e-readiness.md). Report **passed**, **failed**, **blocked** or **not run**, with build/surface identity and evidence. Use **not applicable** only with a concrete scope reason, never for unavailable tooling. Finish independent work when a check is blocked, but do not claim unverified accessibility or human acceptance.

### Comprehension under degradation

Apply the [controlled-disturbance method](../execution/bounded-recovery.md#controlled-disturbances). Declare what must be understood at a glance, in ordinary use and on deliberate inspection. Select viewing conditions from the task or explicit test request; record which checks gate acceptance and which are diagnostics before evaluating the result.

For image reduction, blur, noise, skew, rotation or color reduction, record the capture/state, dimensions, transformation order and parameters. One-fifth width and height tests detail loss; a smaller live viewport tests responsive layout. A 37-degree rotation can challenge grouping, but need not preserve text readability or absolute directional meaning unless required by the use case. Fine values may disappear while a declared critical-state distinction must survive. Test individual transformations before relevant combinations. Grayscale is not a substitute for contrast or color-vision checks.

Use fresh, context-limited evaluators. For novice/ELI5 checks, provide only the intended user's task and background, not the specification or builder's explanation. Ask what the screen is for, what to do first, what should change and how success is recognized; observe the task, not just verbal repetition. A model critic is not a human usability trial.

Include an altered-state control that requires a different answer and an information-loss control that requires uncertainty. A reviewer repeating the baseline explanation fails. Configured timings and distortions are project criteria, not ISO/WCAG thresholds or disability simulations. Failed required comprehension cannot be averaged away by scanner success, attractive styling or a stronger model's vote. Unrun checks remain open.

If the intended action is not perceptible, fix composition or interaction rather than add another explanatory panel. Text-centric evaluation is a risk, not a proven universal mechanism of all models.

## Completion and deviations

New or worsened known accessibility barriers on the changed path block an unqualified completion claim. Fix them; do not silently defer them to polish, dismiss affected users or mark unrun checks passed. Report unrelated pre-existing debt with scope rather than silently expanding the assignment.

For genuine technical or essential-activity constraints, record the affected task/users, exact requirement, evidence, accessible alternative/mitigation, owner decision needed and review condition in the existing issue/acceptance record. Do not self-approve a deviation. An authorized deviation remains a limitation, not conformance, and cannot waive applicable law. Ordinary in-scope accessibility fixes need no additional approval.

Name the standard edition, level, evaluated surface/process and evidence when reporting results. This guide, documentation tests, scanner success and visual review do not establish full WCAG/ISO conformance or certification. WCAG conformance also concerns complete processes, not only selected components.

## Behavioral regression probes

Test these under the normal instruction stack against the same task before/after adoption:

- Ordinary settings screen, no accessibility request: accessible defaults and relevant checks appear without prompting.
- All labels present but dashboard priority unreadable: critic identifies visual failure from pixels; extra text does not make it pass.
- Icon-only/color-only redesign: recognizable, accessible operation is preserved rather than optimizing only for fewer words.
- Passing scanner, no assistive-technology/human trial: report scoped results and open checks, not blanket success.
- API-only edit: apply machine/security contracts without inventing a UI or loading all visual guidance.
- New keyboard trap dismissed as polish: repair it or expose an unresolved limitation instead of declaring completion.

These are proposed probes, not measured behavior. Expected benefit: fewer omitted requirements and less accessibility/visual rework. Cost: relevant design and validation effort. Revisit placement/detail if trials show routing failures, excessive context or unchanged behavior. Navigation tests establish discoverability only; real agent, assistive-technology and human trials need separate evidence.
