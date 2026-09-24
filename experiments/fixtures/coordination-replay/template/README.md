# Release replay

`release.publish(source_file, workspace, version)` builds a package, installs
it, and reads what the consumer currently serves. The return value is the
release receipt. `python3 release.py SOURCE WORKSPACE VERSION` prints it as
JSON. All stages use SHA-256 of the exact payload bytes as content identity.

The storage contract is `workspace/packages/<sha256>/` for built packages,
`workspace/installed/<sha256>/` for installed copies, and
`workspace/current.json` as the live consumer pointer. A successful receipt
must identify the selected source and the bytes currently served. A failed
install must leave the previous live pointer and payload intact.

Run `python3 -m unittest discover -s tests -q` for the public tests.
