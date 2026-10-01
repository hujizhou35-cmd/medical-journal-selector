#!/usr/bin/env python3
"""Build deterministic bundles from the checked-out source. No network access."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/medical-journal-selector"


def bundle(path, roots):
    entries = []
    for root, prefix in roots:
        for f in ([root] if root.is_file() else root.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
                name = prefix if root.is_file() else (prefix + "/" + f.relative_to(root).as_posix()).lstrip("/")
                entries.append((name, f))
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, f in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            payload = f.read_bytes()
            if f.suffix in (".md", ".py", ".json", ".yaml", ".yml") or f.name == "LICENSE":
                payload = payload.replace(b"\r\n", b"\n")
            z.writestr(info, payload)


def portable():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    text += "\n\n# Portable edition: inlined references\n\nAll references below are included in this file. If a relative reference cannot be opened, read its matching section below. Executable helpers are optional and are shipped only in the full bundles; apply their documented rules manually when unavailable.\n"
    for ref in sorted((SKILL / "references").glob("*.md")):
        text += f"\n---\n\n## Inlined reference: {ref.name}\n\n" + ref.read_text(encoding="utf-8")
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "dist")
    p.add_argument("--sync-portable", action="store_true", help="Explicitly update root SKILL.md")
    args = p.parse_args()
    version = (ROOT / "VERSION").read_text().strip()
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest["version"] != version:
        raise SystemExit("manifest/version mismatch")
    expected = portable()
    if args.sync_portable:
        (ROOT / "SKILL.md").write_text(expected, encoding="utf-8", newline="\n")
    elif not (ROOT / "SKILL.md").exists() or (ROOT / "SKILL.md").read_text(encoding="utf-8") != expected:
        raise SystemExit("root SKILL.md is stale; run with --sync-portable")
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    name = f"medical-journal-selector-v{version}.skill"
    bundle(out / name, [(SKILL, ""), (ROOT / "LICENSE", "LICENSE")])
    bundle(out / f"medical-journal-selector-portable-v{version}.zip", [(SKILL, "medical-journal-selector"), (ROOT / "LICENSE", "medical-journal-selector/LICENSE")])
    bundle(out / f"medical-journal-selector-codex-plugin-v{version}.zip", [(ROOT / ".codex-plugin", ".codex-plugin"), (SKILL, "skills/medical-journal-selector"), (ROOT / "LICENSE", "LICENSE")])
    (out / "SKILL.md").write_text(expected, encoding="utf-8", newline="\n")
    assets = sorted([out / name, out / f"medical-journal-selector-portable-v{version}.zip", out / f"medical-journal-selector-codex-plugin-v{version}.zip", out / "SKILL.md"])
    sums = "".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n" for f in assets)
    (out / "SHA256SUMS.txt").write_text(sums, encoding="ascii", newline="\n")
    print(sums, end="")


if __name__ == "__main__":
    main()
