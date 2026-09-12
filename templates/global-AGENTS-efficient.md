# Global execution-efficiency defaults

- Preserve the requested outcome and quality; optimize execution, not scope.
- Use deterministic local tools for exact search, indexing, hashing, formatting, compiling, testing, moving, and filtering instead of spending model reasoning on mechanical work.
- Keep command output concise. Save full noisy output to a local file and return only status, relevant failures, and the path; inspect more only when needed.
- Reuse valid prior work. Do not reread, regenerate, or revalidate unchanged units unless changed inputs or new evidence invalidate the previous result.
- Run the cheapest relevant validation first. Repeat or broaden passing checks only after changes or unresolved risk justify it.
- Before a substantial work batch, choose exact tools, a bounded worker, or the orchestrator. Where authorized and supported, use sufficiently capable smaller workers for independent extraction, straightforward edits, and validation; retain synthesis/integration on the orchestrator. Record the selected model (inheritance is not a cheaper tier), require concise evidence, and avoid duplicating worker reads. Keep small or tightly coupled work local; do not add fan-out without a concrete benefit.
- Persist important progress and validation state in files rather than relying on long conversational recall.
- Prefer concise final and intermediate messages unless detail is part of the requested deliverable.
