#!/usr/bin/env python3
"""Check release contract and local document links without network access."""
import importlib.util
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def public_files():
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in (".work", ".git", "dist", "private", "__pycache__", "node_modules")]
        for name in files:
            yield Path(directory) / name


def main():
    errors = []
    spec = importlib.util.spec_from_file_location("builder", ROOT / "development/build_release.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    canonical = (builder.SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not canonical.startswith("---\nname: medical-journal-selector\n"):
        errors.append("invalid skill frontmatter")
    for name in ("SKILL.md", "TRAINER-SKILL.md"):
        if (ROOT / name).exists():
            errors.append("generated standalone file belongs in dist/: " + name)
    files = list(public_files())
    for path in (p for p in files if p.suffix == ".md"):
        if any(p in (".work", ".git", "dist", "private", "__pycache__") for p in path.parts):
            continue
        if path in (ROOT / "SKILL.md", ROOT / "TRAINER-SKILL.md"):
            continue  # Inlined references intentionally retain canonical relative names.
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            link = link.strip("<>").split("#", 1)[0]
            if not link or "://" in link or link.startswith("mailto:"):
                continue
            if not (path.parent / link).exists():
                errors.append(f"broken local link {path.relative_to(ROOT)} -> {link}")
    forbidden = [p for p in files if p.name in ("auth.json", ".env", "credentials.json")]
    if forbidden:
        errors.append("private credential filenames in publishable tree")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Project structure, generated-file boundaries and local links: passed")


if __name__ == "__main__":
    main()
