#!/usr/bin/env python3
"""Build or verify an allowlisted experimental r18 package, without network access.

The stable V1 builder, source VERSION and frozen selector files are not changed.
No private directory is required in a clean CI checkout.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "releases/experimental-v2.0.0.json"
SKILL_PREFIX = "skills/medical-journal-selector/"
SELECTOR_FILES = frozenset({
    "SKILL.md", "agents/openai.yaml", "references/evidence-format.md",
    "references/medical-methods.md", "references/sources-and-verification.md",
    "scripts/search_precedents.py", "scripts/selector.py",
})
SOURCE_FILES = frozenset(SKILL_PREFIX + name for name in SELECTOR_FILES) | {
    "LICENSE", ".codex-plugin/plugin.json",
}
BLOCKED_PARTS = frozenset({"private", ".git", ".work", "credentials.json", "auth.json"})


class ReleaseError(ValueError):
    """A source or package does not match the public release allowlist."""


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical(payload):
    # Same CRLF -> LF rule as development/build_release.py for these text assets.
    return payload.replace(b"\r\n", b"\n")


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or not path.parts or "\\" in name or ":" in name or path.is_absolute()
            or name != path.as_posix() or any(p in {".", ".."} for p in path.parts)
            or any(p.lower() in BLOCKED_PARTS or p.lower().startswith(".env") for p in path.parts)):
        raise ReleaseError("unsafe or private path: " + str(name))
    return path


def is_link(path):
    if path.is_symlink():
        return True
    # Windows directory junctions are also reparse points, including on Python
    # versions without Path.is_junction(). They must not escape the allowlist.
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    except FileNotFoundError:
        return False


def checked_path(root, relative):
    parts = safe_name(relative).parts
    path = root
    for part in parts:
        path = path / part
        if is_link(path):
            raise ReleaseError("symbolic link is not publishable: " + relative)
    if not path.is_file():
        raise ReleaseError("missing public source: " + relative)
    return path


def load_config(root=ROOT):
    config = json.loads(checked_path(root, CONFIG).read_text(encoding="utf-8"))
    if (config.get("schema") != "medical-journal-selector-experimental-release-v1"
            or not re.fullmatch(r"2\.0\.0-experimental\.[1-9][0-9]*", config.get("version", ""))
            or config.get("tag") != "v" + config["version"]
            or config.get("prerelease") is not True
            or config.get("candidate_revision") != "r18"
            or config.get("quality_gate") != "GATES_NOT_PASSED"
            or config.get("overall_improvement_demonstrated") is not False):
        raise ReleaseError("experimental release controls changed")
    sources = config.get("sources", {})
    for name in sources:
        safe_name(name)
    if set(sources) != SOURCE_FILES:
        raise ReleaseError("public source allowlist must match the exact seven r18 files and packaging inputs")
    for hashes in sources.values():
        if set(hashes) != {"frozen_raw_sha256", "canonical_lf_sha256"} or any(
                not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values()):
            raise ReleaseError("invalid bound source hash")
    return config


def source_payloads(root, config):
    skill = root / SKILL_PREFIX.rstrip("/")
    if is_link(skill):
        raise ReleaseError("symbolic link skill directory")
    # Ignore only interpreter caches, as the stable builder does. All other extras
    # fail closed; no directory is blindly copied into an experimental archive.
    for directory, dirs, files in os.walk(skill, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if is_link(path):
                raise ReleaseError("symbolic link in source inventory")
            safe_name(path.relative_to(skill).as_posix())
        for name in files:
            relative = (Path(directory) / name).relative_to(skill).as_posix()
            parts = PurePosixPath(relative).parts
            if "__pycache__" in parts and name.endswith(".pyc"):
                continue
            safe_name(relative)
            if relative not in SELECTOR_FILES:
                raise ReleaseError("unexpected selector source: " + relative)
    payloads = {}
    for name, binding in sorted(config["sources"].items()):
        payload = canonical(checked_path(root, name).read_bytes())
        if sha256(payload) != binding["canonical_lf_sha256"]:
            raise ReleaseError("canonical source hash mismatch: " + name)
        payloads[name] = payload
    return payloads


def release_notice(config):
    return ("# Medical Journal Selector " + config["tag"] + "\n\n"
        "**Experimental prerelease — GATES_NOT_PASSED.** This is the frozen r18 "
        "candidate evaluated after 100 development cases and a planned 50-case final cohort. "
        "The final cohort includes a disclosed reserve-order protocol deviation. "
        "The evidence does not demonstrate an overall improvement over V1; this is not a stable V2 promotion.\n\n"
        "V1.0.0 remains the stable release. Verify journal facts independently. The "
        "historical publication-outlet match is a benchmark proxy, not an acceptance probability. "
        "Reviews were performed by AI contexts of the same model, not independent human experts.\n\n"
        "The seven Selector files retain their frozen r18 content. Packaging converts "
        "CRLF to LF, as the existing stable builder does. The plugin version and this notice "
        "are release metadata; they do not create a new validated scientific candidate. "
        "The single-file SKILL.md in the release folder additionally inlines the existing references.\n\n"
        "Use one Selector version per workspace: the skill identifier remains "
        "medical-journal-selector. Try the experiment in a separate workspace to avoid "
        "replacing an installed V1. Trainer v1 is a separate tool and is not relabeled as V2.\n\n"
        "[Results and limitations](https://github.com/hujizhou35-cmd/medical-journal-selector/blob/main/docs/evaluation/final50/final-report.zh-CN.md)\n\n"
        "## 中文\n\n"
        "**这是实验预发布版，稳定发布门槛未通过（GATES_NOT_PASSED）。** "
        "本包保留冻结的 r18 候选。已完成 100 篇开发及计划中的 50 篇最终评测，"
        "最终评测保留了一项已披露的候补顺序偏差。结果不支持 V2 整体明显优于 V1，"
        "因此不作稳定 V2 晋级。V1.0.0 仍是稳定版。\n\n"
        "评审由同一模型的独立上下文完成，不是独立人类专家评审；历史发表期刊命中"
        "只是评测指标，不是录用概率。请自行核对当前期刊信息。软件内容未因最终结果"
        "重新修改，仅在打包时将换行统一为 LF，并添加实验版说明和版本元数据。"
        "技能名称未改变，建议在单独工作区尝试，避免覆盖已安装的 V1。\n").encode("utf-8")


def single_file_notice(config):
    return ("\n> **Experimental " + config["tag"] + " — GATES_NOT_PASSED.** "
        "This single-file edition wraps the frozen r18 candidate. Final results did not "
        "demonstrate an overall improvement over V1; V1.0.0 remains the stable release.\n"
        "> **实验版，稳定发布门槛未通过。** 本单文件版保留冻结的 r18 内容；"
        "最终结果未证明整体优于 V1，V1.0.0 仍为稳定版。\n"
        "> [Results and limitations / 结果与局限](https://github.com/hujizhou35-cmd/medical-journal-selector/blob/main/docs/evaluation/final50/final-report.zh-CN.md)\n\n")


def expected_artifacts(root, config):
    sources = source_payloads(root, config)
    notice = release_notice(config)
    plugin = json.loads(sources[".codex-plugin/plugin.json"])
    plugin["version"] = config["version"]
    plugin["description"] = "Experimental frozen r18 journal selector; stable quality gates did not pass."
    plugin["interface"]["displayName"] = "Medical Journal Selector (Experimental)"
    plugin_bytes = json_bytes(plugin)
    skill = {name[len(SKILL_PREFIX):]: sources[name] for name in sorted(sources) if name.startswith(SKILL_PREFIX)}
    common = {"LICENSE": sources["LICENSE"], "RELEASE-NOTICE.md": notice}
    version = config["version"]
    archives = {
        "medical-journal-selector-v" + version + ".skill": dict(skill, **common),
        "medical-journal-selector-portable-v" + version + ".zip": {
            "medical-journal-selector/" + name: payload for name, payload in dict(skill, **common).items()},
        "medical-journal-selector-codex-plugin-v" + version + ".zip": dict(
            {SKILL_PREFIX + name: payload for name, payload in skill.items()},
            **common, **{".codex-plugin/plugin.json": plugin_bytes}),
    }
    portable = skill["SKILL.md"].decode("utf-8")
    portable += "\n\n# Portable edition: inlined references\n\nAll references below are included in this file. If a relative reference cannot be opened, read its matching section below. Executable helpers are optional and are shipped only in the full bundles; apply their documented rules manually when unavailable.\n"
    for name in sorted(skill):
        if name.startswith("references/") and name.endswith(".md"):
            portable += "\n---\n\n## Inlined reference: " + PurePosixPath(name).name + "\n\n" + skill[name].decode("utf-8")
    frontmatter_end = portable.find("\n---\n", 4)
    if not portable.startswith("---\n") or frontmatter_end < 0:
        raise ReleaseError("single-file wrapping requires the original YAML frontmatter")
    boundary = frontmatter_end + len("\n---\n")
    portable = portable[:boundary] + single_file_notice(config) + portable[boundary:]
    manifest = {
        "schema": "medical-journal-selector-experimental-software-manifest-v1",
        "tag": config["tag"], "candidate_revision": "r18", "prerelease": True,
        "quality_gate": "GATES_NOT_PASSED", "overall_improvement_demonstrated": False,
        "source_hash_basis": config["source_hash_basis"],
        "frozen_selector_manifest_sha256": config["frozen_selector_manifest_sha256"],
        "sources": config["sources"],
        "archive_contents": {name: {entry: sha256(payload) for entry, payload in sorted(entries.items())}
                             for name, entries in sorted(archives.items())},
        "generated_content": {"plugin_metadata": ".codex-plugin/plugin.json inside the plugin ZIP",
                              "release_notice": "RELEASE-NOTICE.md",
                              "portable_single_file": "SKILL.md with a visible experimental status notice immediately after the unchanged YAML frontmatter, followed by the frozen body and existing references inlined; this is release metadata wrapping, not new scientific rules"},
        "privacy": "Only allowlisted public software, MIT license and generated release metadata; no papers, answers, prompts, raw logs or credentials.",
    }
    plain = {"SKILL.md": portable.encode("utf-8"), "RELEASE-NOTICE.md": notice,
             "software-manifest.json": json_bytes(manifest)}
    return archives, plain


def write_archive(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(entries.items()):
            safe_name(name)
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, payload)


def output_inventory(root, output, names):
    if any(is_link(path) for path in (output, *output.parents)) or any(
            part.lower() in BLOCKED_PARTS for part in output.parts):
        raise ReleaseError("unsafe release output directory")
    resolved = output.resolve()
    if any(part.lower() in BLOCKED_PARTS for part in resolved.parts):
        raise ReleaseError("private release output directory")
    for forbidden in (root / "skills", root / "development", root / "releases", root / ".codex-plugin"):
        if resolved == forbidden.resolve() or forbidden.resolve() in resolved.parents:
            raise ReleaseError("release output would overwrite source files")
    if output.exists():
        for entry in output.iterdir():
            if is_link(entry) or not entry.is_file() or entry.name not in names:
                raise ReleaseError("unexpected release output entry: " + entry.name)


def build(root=ROOT, output=None):
    root = Path(root)
    config = load_config(root)
    output = Path(output) if output is not None else root / "dist" / ("experimental-v" + config["version"])
    archives, plain = expected_artifacts(root, config)
    names = set(archives) | set(plain) | {"SHA256SUMS.txt"}
    output_inventory(root, output, names)
    output.mkdir(parents=True, exist_ok=True)
    for name, entries in sorted(archives.items()):
        write_archive(output / name, entries)
    for name, payload in sorted(plain.items()):
        (output / name).write_bytes(payload)
    sums = "".join(sha256((output / name).read_bytes()) + "  " + name + "\n"
                   for name in sorted(set(archives) | set(plain)))
    (output / "SHA256SUMS.txt").write_bytes(sums.encode("ascii"))
    verify(root, output)
    return output


def verify(root=ROOT, output=None):
    root = Path(root)
    config = load_config(root)
    output = Path(output) if output is not None else root / "dist" / ("experimental-v" + config["version"])
    archives, plain = expected_artifacts(root, config)
    names = set(archives) | set(plain) | {"SHA256SUMS.txt"}
    output_inventory(root, output, names)
    if not output.is_dir() or {p.name for p in output.iterdir()} != names:
        raise ReleaseError("release asset inventory mismatch")
    for name, payload in plain.items():
        if (output / name).read_bytes() != payload:
            raise ReleaseError("generated asset content mismatch: " + name)
    for name, expected in archives.items():
        with zipfile.ZipFile(output / name) as archive:
            infos = archive.infolist()
            if len(infos) != len(expected) or {i.filename for i in infos} != set(expected):
                raise ReleaseError("archive inventory mismatch: " + name)
            for info in infos:
                safe_name(info.filename)
                if (info.file_size != len(expected[info.filename]) or info.flag_bits & 1
                        or info.create_system != 3 or (info.external_attr >> 16) != (stat.S_IFREG | 0o644)
                        or info.date_time != (2026, 1, 1, 0, 0, 0)
                        or archive.read(info) != expected[info.filename]):
                    raise ReleaseError("archive content or metadata mismatch: " + name + "/" + info.filename)
    sums = "".join(sha256((output / name).read_bytes()) + "  " + name + "\n"
                   for name in sorted(set(archives) | set(plain)))
    if (output / "SHA256SUMS.txt").read_bytes() != sums.encode("ascii"):
        raise ReleaseError("release checksum mismatch")
    return {"tag": config["tag"], "assets": len(names), "archives": len(archives),
            "bound_selector_files": len(SELECTOR_FILES), "quality_gate": config["quality_gate"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", default="build", choices=("build", "verify"))
    parser.add_argument("--verify", action="store_true", help="Verify an existing release without rebuilding it")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "build" and not args.verify:
            output = build(output=args.output)
            print("Built and verified " + str(output))
        else:
            print(json.dumps(verify(output=args.output), sort_keys=True))
    except (ReleaseError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, "Experimental release rejected: " + str(error) + "\n")


if __name__ == "__main__":
    main()
