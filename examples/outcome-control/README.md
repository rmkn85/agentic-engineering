# Local outcome-control example

This neutral example checks a real local-file reader against owner-declared
expected bytes. It generates an existing-format task, two independent applicable
claims, hashed positive evidence, a gate request, a frontier required-control
policy and an outside checkpoint. The native policy rejects deleting the task
extension to bypass controlled validation.
Remote integration, availability and human acceptance are explicitly outside
this example's authorized local outcome, with applicability fixed before proof.

Use new owned paths:

```sh
python3 examples/outcome-control/run.py --destination /tmp/outcome-example --checkpoint /tmp/outcome-checkpoint
python3 tools/project_work.py --root /tmp/outcome-example validate
python3 tools/outcome_control.py --root /tmp/outcome-example --task work/tasks/RESULT-1.json gate pre-completion --request /tmp/outcome-example/gate-request.json
python3 tools/outcome_control.py --root /tmp/outcome-example --task work/tasks/RESULT-1.json resume --checkpoint /tmp/outcome-checkpoint --destination /tmp/outcome-recovery
```

The last command restores only to `/tmp/outcome-recovery/restored`, refuses any
existing destination and does not start work. This is a local machinery trial;
it is not evidence that another product was delivered or that a model follows
the policy. The [operational contract](../../docs/execution/outcome-control.md)
describes the trust boundary, source-coverage decision and native writer binding.
