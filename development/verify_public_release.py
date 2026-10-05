#!/usr/bin/env python3
"""Verify public release downloads anonymously against a local allowlisted build."""
import argparse
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

REPO = "hujizhou35-cmd/medical-journal-selector"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.tag != "v2.0.0-experimental.1":
        raise SystemExit("Only the authorized experimental release may be verified.")
    directory = args.directory.resolve()
    sums = directory / "SHA256SUMS.txt"
    expected = {}
    for line in sums.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match or match[2] in expected:
            raise SystemExit("Invalid or duplicate checksum entry")
        expected[match[2]] = match[1]
    expected[sums.name] = hashlib.sha256(sums.read_bytes()).hexdigest()
    proof = {"tag": args.tag, "anonymous": True, "verified_assets": [], "failed": []}
    for name, digest in sorted(expected.items()):
        local = directory / name
        if not local.is_file() or local.is_symlink() or hashlib.sha256(local.read_bytes()).hexdigest() != digest:
            raise SystemExit("Local asset mismatch: " + name)
        url = f"https://github.com/{REPO}/releases/download/{args.tag}/{name}"
        observed = None
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "medical-journal-selector-public-download-check"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    payload = response.read()
                    observed = {"name": name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "status": response.status}
                if observed["sha256"] != digest or payload != local.read_bytes():
                    raise ValueError("Public payload differs from the local asset")
                proof["verified_assets"].append(observed)
                break
            except Exception as exc:
                if attempt == 2:
                    proof["failed"].append({"name": name, "error": type(exc).__name__, "message": str(exc), "observed": observed})
                else:
                    time.sleep(5)
    proof["passed"] = not proof["failed"] and len(proof["verified_assets"]) == len(expected)
    (directory / "public-download-proof.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": proof["passed"], "verified_count": len(proof["verified_assets"]), "failed": proof["failed"]}))
    if not proof["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
