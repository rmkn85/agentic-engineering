# Small offline adoption checks

The [newcomer contract](newcomer-contract.md) can be adopted without a package dependency. Copy `templates/contributor-core.md` and whichever helpers are useful into `.agents/engineering/`, and bind the local entry to existing native commands. Python helpers require Python 3.9+ and the checkout helper additionally requires Git. Do not add a Python runtime merely to adopt prose in an otherwise non-Python repository; use native equivalents where they already exist.

`tools/check-adoption.py` validates local snapshot hashes and nonempty entry files. It deliberately works with a dirty development tree, unlike the source synchronization guard. Invoke it from the existing fast test/build route, not an unrelated duplicate CI workflow. In GitHub Actions it also checks that HEAD equals the declared candidate SHA. It does not require a clone of the upstream, fetch policy updates, validate task status, prove the whole instruction hierarchy, or certify deployment.

Example `.agents/engineering/ORIGIN.json` shape (replace placeholders with actual identities):

```json
{
  "schema": 1,
  "upstream": {
    "repository": "rmkn85/agentic-engineering",
    "revision": "FULL_40_CHARACTER_COMMIT"
  },
  "files": [
    {"path": ".agents/engineering/CONTRIBUTOR-CORE.md", "source": "templates/contributor-core.md", "sha256": "ACTUAL_64_CHARACTER_DIGEST"}
  ],
  "entrypoints": ["AGENTS.md", "CONTRIBUTOR-ENTRY.md"]
}
```

List only managed exact copies under `files`; adapted local commands and policy belong in local documents and `entrypoints`. Optional adaptation notes are provenance, not a task ledger. Required resources must resolve locally. A digest match detects drift, not whether a rule is sensible. Review semantic changes and actual host delivery independently.

Maintenance is explicit: compare the last adopted upstream version, the selected replacement and the local copy. Never overwrite unexpected local changes. Record the new immutable version and hashes in the same coherent commit. Do not fail ordinary work merely because upstream advanced.

## Executed checks

On 2026-09-19, `python3 -m unittest discover -s tools/tests -v` passed **32 tests**: 21 real local-Git fixtures for checkout recovery and 11 offline adoption fixtures. The latter cover unchanged content without upstream availability, drift, missing files, path traversal, symlinks, duplicate paths, mutable upstream refs, missing entrypoints, malformed manifests and CI candidate matching. Tests use temporary fixtures and do not establish a real model/IDE task, full environment installation, integration or deployment. See the [checkout evidence](../../experiments/newcomer-checkout-evidence.md) for the initial regression.
