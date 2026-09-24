#!/usr/bin/env python3
"""Independent end-to-end acceptance for the generated release project."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def exercise(repo, seed):
    # Import the worker's implementation, while keeping these cases outside the
    # generated project and its editable public tests.
    sys.path.insert(0, str(repo))
    from release import publish  # pylint: disable=import-outside-toplevel
    from replay.consumer import read_current  # pylint: disable=import-outside-toplevel
    from replay.install import install  # pylint: disable=import-outside-toplevel

    def digest(data):
        return hashlib.sha256(data).hexdigest()

    with tempfile.TemporaryDirectory(prefix="coord-accept-") as temporary:
        root = Path(temporary)
        source = root / "selected.txt"
        work = root / "workspace"
        first = "edition %d: alpha\n" % seed
        second = "edition %d: beta with revised content\n" % seed
        source.write_text(first, encoding="utf-8")
        one = publish(source, work, "release-%d" % seed)
        assert one["served_text"] == first, "initial publish did not reach consumer"
        source.write_text(second, encoding="utf-8")
        two = publish(source, work, "release-%d" % seed)
        wanted = digest(second.encode("utf-8"))
        for field in ("source_sha256", "package_sha256", "installed_sha256", "served_sha256"):
            assert two[field] == wanted, "%s does not match selected source" % field
        assert two["served_text"] == second, "consumer is serving an older payload"
        assert two["status"] == "published", "successful release has wrong status"
        assert (work / "packages" / wanted / "payload.txt").read_bytes() == second.encode("utf-8"), "built package differs from source"
        assert (work / "installed" / wanted / "payload.txt").read_bytes() == second.encode("utf-8"), "installed copy differs from source"
        assert json.loads((work / "current.json").read_text(encoding="utf-8"))["sha256"] == wanted, "live pointer differs from source"
        pointer_before = (work / "current.json").read_bytes()
        again = publish(source, work, "release-%d" % seed)
        assert again["served_sha256"] == wanted, "repeat publish changed consumer identity"
        assert (work / "current.json").read_bytes() == pointer_before, "repeat changed live pointer"

        # A corrupt package with the same version must not be accepted through
        # the install cache or replace the currently served payload.
        corrupt = root / "corrupt-package"
        corrupt.mkdir()
        (corrupt / "manifest.json").write_text(json.dumps({
            "version": "release-%d" % seed,
            "sha256": digest(b"declared bytes"),
        }), encoding="utf-8")
        (corrupt / "payload.txt").write_bytes(b"different bytes")
        try:
            install(corrupt, work)
        except ValueError:
            pass
        else:
            raise AssertionError("corrupt same-version package was accepted")
        assert (work / "current.json").read_bytes() == pointer_before, "failed install changed live pointer"
        assert read_current(work)["text"] == second, "failed install changed served payload"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    exercise(args.repo.resolve(), args.seed)
    print("PASS: exact source/package/install/consumer identity and failed-install preservation")


if __name__ == "__main__":
    main()
