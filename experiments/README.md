# Experiments

This directory is for reproducible comparisons of agent-development techniques.

Useful experiment dimensions include:

- model choice at fixed operation mode
- local vs cloud at fixed model and task
- reasoning level
- single agent vs delegated workers
- cold vs warm dependency/build caches
- raw tool output vs reduced diagnostics
- semantic index vs ad-hoc repeated search
- read-once/invalidation workflow vs repeated global review

An experiment should define workload, environment, success criteria, model/settings, measured resources, quality checks, and limitations.
