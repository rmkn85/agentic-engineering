# Global execution-efficiency defaults

- Preserve the requested outcome and quality; optimize execution, not scope.
- Use deterministic local tools for exact search, indexing, hashing, formatting, compiling, testing, moving, and filtering instead of spending model reasoning on mechanical work.
- Keep command output concise. Save full noisy output to a local file and return only status, relevant failures, and the path; inspect more only when needed.
- Reuse valid prior work. Do not reread, regenerate, or revalidate unchanged units unless changed inputs or new evidence invalidate the previous result.
- Run the cheapest relevant validation first. Repeat or broaden passing checks only after changes or unresolved risk justify it.
- Do not explicitly create broad fan-out unless the work is genuinely independent and the expected critical-path or quality gain justifies duplicated context and coordination. Do not override normal platform delegation behavior without a concrete reason.
- Persist important progress and validation state in files rather than relying on long conversational recall.
- Prefer concise final and intermediate messages unless detail is part of the requested deliverable.
