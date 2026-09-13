---
name: refactoring-module
description: Use when restructuring an existing module or package across multiple units, especially its public surface, ownership, dependency direction, state, or internal boundaries.
---

# Refactoring an existing module

Goal: reduce the module's future context/change radius without hiding the same complexity behind more indirection.

1. **Map the module boundary before changing it.** Identify its owned responsibility, public surface, inbound callers, outbound dependencies, mutable state, side effects, and the tests/contracts that currently protect it.
2. **Name the structural problem precisely.** Examples: mixed responsibilities, cycles, excessive public surface, hidden state, duplicated decisions, too many semantic hops, brittle implementation-coupled tests. Do not use “clean architecture” as the diagnosis.
3. **Define the target boundary.** State what the module should own, what it should expose, permitted dependency directions, state ownership, and where effects/external variability belong.
4. **Preserve or intentionally migrate contracts.** Separate behavior-preserving restructuring from required behavior/API changes. Prefer staged, mechanically checkable transitions when callers must move.
5. **Reduce required traversal.** Co-locate things that change together; remove accidental cycles/indirection; keep stable public contracts narrow; avoid generic abstraction layers that couple unrelated concepts.
6. **Keep representative flows visible.** Sample key entry points and ensure a weak reader can follow their main/error paths through a small number of explicit dependencies. Do not optimize module metrics while making each path span more files.
7. **Strengthen independent evidence at the boundary.** Use contract/behavior tests for the public surface, focused unit tests for diagnostic precision, and structural checks for dependency/cycle/public-surface rules when useful.
8. **Check edit radius, not just code shape.** Exercise at least one representative future change or bug scenario. The refactor should reduce or preserve source/context expansion, changed-file count, validation effort, and recovery work.
9. **Run weak-reader samples before declaring success.** A fresh weaker model should model representative entry points at least as accurately with no more context/reasoning than before.

Do not recursively rewrite neighboring modules unless their boundary is part of the diagnosed problem. If a new independent ownership boundary is the actual solution, use `designing-module-boundary` for that new boundary.

For rationale and measurement, read `docs/code/agent-legible-code.md` and `experiments/agent-legibility.md` only when needed.
