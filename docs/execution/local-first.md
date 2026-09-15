# Local-first execution

For established repositories, local execution is often the most efficient default because the working environment is already warm.

Typical reusable local state includes:

- checkout and Git object database
- installed dependencies
- compiler and language-server caches
- test caches
- build artifacts
- local services and emulators
- credentials and developer tooling already configured for the project

The model remains the reasoning component; local tools perform filesystem, build, test, search, formatting, and indexing work.

## Choose cloud intentionally

Cloud execution remains valuable when its benefits exceed duplicated setup/context overhead, for example:

- independent parallel tasks
- clean-environment verification
- long-running work that should not occupy the local execution environment
- reproducible remote environments

Local and cloud should be chosen for execution characteristics, not treated as competing ideologies.
