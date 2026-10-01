#!/usr/bin/env python3
"""Check release contract and local document links without network access."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    spec = importlib.util.spec_from_file_location("builder", ROOT / "development/build_release.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    canonical = (builder.SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not canonical.startswith("---\nname: medical-journal-selector\n"):
        errors.append("invalid skill frontmatter")
    if (ROOT / "SKILL.md").read_text(encoding="utf-8") != builder.portable():
        errors.append("portable SKILL.md is stale")
    for path in ROOT.rglob("*.md"):
        if any(p in (".work", ".git", "dist", "__pycache__") for p in path.parts):
            continue
        if path == ROOT / "SKILL.md":
            continue  # Inlined references intentionally retain canonical relative names.
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            link = link.strip("<>").split("#", 1)[0]
            if not link or "://" in link or link.startswith("mailto:"):
                continue
            if not (path.parent / link).exists():
                errors.append(f"broken local link {path.relative_to(ROOT)} -> {link}")
    forbidden = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and ".work" not in p.parts and p.name in ("auth.json", ".env", "credentials.json")]
    if forbidden:
        errors.append("private credential filenames in publishable tree")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Project structure, portable parity and local links: passed")


if __name__ == "__main__":
    main()
