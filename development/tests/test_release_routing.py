import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'development'))
SPEC = importlib.util.spec_from_file_location('distribution_builder',ROOT/'development/build_release.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

class ReleaseRoutingTests(unittest.TestCase):
    def test_stable_uses_original_release_bytes_despite_current_r18(self):
        with tempfile.TemporaryDirectory() as temp:
            result = BUILDER.build('stable',Path(temp)/'stable')
            self.assertEqual(result['assets'],BUILDER.inventory()['releases']['v1.0.0']['assets'])
            self.assertEqual(len(result['assets']),3)

    def test_trainer_contains_own_helpers_and_no_selector(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'trainer'
            result = BUILDER.build('trainer',output)
            self.assertEqual(len(result['assets']),3)
            with zipfile.ZipFile(next(output.glob('*.zip'))) as archive:
                names = archive.namelist()
                self.assertIn('skills/medical-journal-selector-skill-trainer/scripts/campaign.py',names)
                self.assertFalse(any(n.startswith('skills/medical-journal-selector/') for n in names))
            self.assertEqual((output/'SKILL.md').read_text(encoding='utf-8'),BUILDER.portable(BUILDER.TRAINER))

    def test_ambiguous_target_and_source_output_rejected(self):
        with self.assertRaises(ValueError): BUILDER.build('all')
        with self.assertRaises(ValueError): BUILDER.build('trainer',ROOT/'skills')

if __name__=='__main__': unittest.main()
