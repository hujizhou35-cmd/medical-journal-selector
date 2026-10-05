import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("experimental_release", ROOT / "development/experimental_release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


class ExperimentalReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in sorted(RELEASE.SOURCE_FILES | {RELEASE.CONFIG}):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.out = self.root / "dist/experimental"

    def build(self):
        return RELEASE.build(self.root, self.out)

    def update_config(self, mutate):
        path = self.root / RELEASE.CONFIG
        config = json.loads(path.read_text(encoding="utf-8"))
        mutate(config)
        path.write_bytes(RELEASE.json_bytes(config))

    def rechecksum(self):
        names = sorted(p.name for p in self.out.iterdir() if p.name != "SHA256SUMS.txt")
        sums = "".join(RELEASE.sha256((self.out / name).read_bytes()) + "  " + name + "\n" for name in names)
        (self.out / "SHA256SUMS.txt").write_bytes(sums.encode("ascii"))

    def test_frozen_selector_matches_local_original_manifest(self):
        manifest = ROOT / "private/v2-run/selector-candidate-r18/snapshot-manifest.json"
        if not manifest.exists():
            self.skipTest("private provenance seal is local only; public CI validates canonical bindings")
        config = RELEASE.load_config()
        self.assertEqual(RELEASE.sha256(manifest.read_bytes()), config["frozen_selector_manifest_sha256"])
        original = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        self.assertEqual(set(original), RELEASE.SELECTOR_FILES)
        for name, raw_sha in original.items():
            self.assertEqual(config["sources"][RELEASE.SKILL_PREFIX + name]["frozen_raw_sha256"], raw_sha)
            self.assertEqual(RELEASE.sha256((ROOT / RELEASE.SKILL_PREFIX / name).read_bytes()), raw_sha)

    def test_deterministic_build_and_complete_content_verification(self):
        self.build()
        first = {p.name: p.read_bytes() for p in self.out.iterdir()}
        second = self.root / "dist/repeat"
        RELEASE.build(self.root, second)
        self.assertEqual(first, {p.name: p.read_bytes() for p in second.iterdir()})
        result = RELEASE.verify(self.root, self.out)
        self.assertEqual((result["assets"], result["archives"], result["bound_selector_files"]), (7, 3, 7))
        self.assertEqual(result["quality_gate"], "GATES_NOT_PASSED")
        manifest = json.loads((self.out / "software-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["overall_improvement_demonstrated"])

    def test_checkout_crlf_has_identical_package_bytes(self):
        self.build()
        first = {p.name: p.read_bytes() for p in self.out.iterdir()}
        for relative in RELEASE.SOURCE_FILES:
            path = self.root / relative
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.build()
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.out.iterdir()})

    def test_standalone_notice_preserves_frontmatter_and_all_seven_sources(self):
        before = {name: (self.root / RELEASE.SKILL_PREFIX / name).read_bytes()
                  for name in RELEASE.SELECTOR_FILES}
        self.build()
        standalone = (self.out / "SKILL.md").read_text(encoding="utf-8")
        original = before["SKILL.md"].decode("utf-8")
        boundary = original.find("\n---\n", 4) + len("\n---\n")
        notice = RELEASE.single_file_notice(RELEASE.load_config(self.root))
        self.assertEqual(standalone[:boundary], original[:boundary])
        self.assertTrue(standalone[boundary:].startswith(notice))
        self.assertIn("Experimental v2.0.0-experimental.1 — GATES_NOT_PASSED", notice)
        self.assertIn("稳定发布门槛未通过", notice)
        self.assertTrue(standalone[boundary + len(notice):].startswith(original[boundary:]))
        self.assertEqual(before, {name: (self.root / RELEASE.SKILL_PREFIX / name).read_bytes()
                                  for name in RELEASE.SELECTOR_FILES})
        with zipfile.ZipFile(next(self.out.glob("*.skill"))) as archive:
            for name, payload in before.items():
                self.assertEqual(archive.read(name), RELEASE.canonical(payload))
        manifest = json.loads((self.out / "software-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("release metadata wrapping", manifest["generated_content"]["portable_single_file"])

    def test_source_tampering_rejected(self):
        path = self.root / RELEASE.SKILL_PREFIX / "scripts/selector.py"
        path.write_bytes(path.read_bytes() + b"\n# altered candidate\n")
        with self.assertRaisesRegex(RELEASE.ReleaseError, "source hash mismatch"):
            self.build()

    def test_private_and_unexpected_source_paths_rejected(self):
        for relative in ("private/answers.json", "papers.md", "scripts/__pycache__/credentials.json"):
            with self.subTest(relative=relative):
                path = self.root / RELEASE.SKILL_PREFIX / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("must not publish", encoding="utf-8")
                with self.assertRaises(RELEASE.ReleaseError):
                    self.build()
                path.unlink()

    def test_config_cannot_add_private_source_or_promote_to_stable(self):
        original = (self.root / RELEASE.CONFIG).read_bytes()
        mutations = [
            lambda c: c["sources"].update({"private/answers.json": next(iter(c["sources"].values()))}),
            lambda c: c.update({"quality_gate": "PASSED"}),
            lambda c: c.update({"overall_improvement_demonstrated": True}),
            lambda c: c.update({"prerelease": False}),
            lambda c: c.update({"version": "2.0.0"}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.update_config(mutate)
                with self.assertRaises(RELEASE.ReleaseError):
                    self.build()
                (self.root / RELEASE.CONFIG).write_bytes(original)

    def test_legitimate_interpreter_cache_excluded(self):
        path = self.root / RELEASE.SKILL_PREFIX / "scripts/__pycache__/selector.cpython-312.pyc"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"ignored interpreter cache")
        self.build()
        for path in self.out.glob("*.zip"):
            with zipfile.ZipFile(path) as archive:
                self.assertFalse(any("__pycache__" in name for name in archive.namelist()))

    def test_archive_tamper_rejected_even_with_updated_checksums(self):
        self.build()
        path = next(self.out.glob("*.skill"))
        with zipfile.ZipFile(path) as archive:
            entries = {info.filename: archive.read(info) for info in archive.infolist()}
        entries["scripts/selector.py"] += b"\n# changed output\n"
        RELEASE.write_archive(path, entries)
        self.rechecksum()
        with self.assertRaisesRegex(RELEASE.ReleaseError, "archive content"):
            RELEASE.verify(self.root, self.out)

    def test_extra_archive_member_rejected_even_with_updated_checksums(self):
        self.build()
        path = next(self.out.glob("*.skill"))
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr("private/answers.json", "must not publish")
        self.rechecksum()
        with self.assertRaisesRegex(RELEASE.ReleaseError, "archive inventory"):
            RELEASE.verify(self.root, self.out)

    def test_checksum_tamper_rejected(self):
        self.build()
        (self.out / "SHA256SUMS.txt").write_text("0" * 64 + "  SKILL.md\n", encoding="ascii")
        with self.assertRaisesRegex(RELEASE.ReleaseError, "checksum mismatch"):
            RELEASE.verify(self.root, self.out)

    def test_output_extra_file_and_source_overwrite_rejected(self):
        self.build()
        (self.out / "answers.json").write_text("extra", encoding="utf-8")
        with self.assertRaisesRegex(RELEASE.ReleaseError, "unexpected release output"):
            RELEASE.verify(self.root, self.out)
        with self.assertRaisesRegex(RELEASE.ReleaseError, "overwrite source"):
            RELEASE.build(self.root, self.root / "skills")

    def test_symlink_source_rejected_if_supported(self):
        path = self.root / RELEASE.SKILL_PREFIX / "references/linked.md"
        try:
            path.symlink_to(self.root / "LICENSE")
        except OSError:
            self.skipTest("creating symlinks is unavailable on this host")
        with self.assertRaisesRegex(RELEASE.ReleaseError, "symbolic link"):
            self.build()

    def test_link_rejection_branch_without_host_symlink_permission(self):
        target = self.root / RELEASE.SKILL_PREFIX / "scripts/selector.py"
        with patch.object(RELEASE, "is_link", side_effect=lambda path: path == target):
            with self.assertRaisesRegex(RELEASE.ReleaseError, "symbolic link"):
                self.build()

    def test_output_parent_link_rejected_without_host_permission(self):
        self.out.parent.mkdir(parents=True)
        with patch.object(RELEASE, "is_link", side_effect=lambda path: path == self.out.parent):
            with self.assertRaisesRegex(RELEASE.ReleaseError, "unsafe release output"):
                self.build()

    def test_unsafe_archive_names_rejected(self):
        for name in (".", "../paper.md", "/answers.json", "a//b.md", "a\\b.md",
                     "private/answer.json", "a/.env", "C:/secret.txt", "./file.md"):
            with self.subTest(name=name):
                with self.assertRaises(RELEASE.ReleaseError):
                    RELEASE.safe_name(name)


if __name__ == "__main__":
    unittest.main()
