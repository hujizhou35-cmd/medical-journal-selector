import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector/scripts"))
from selector import render, validate
from fixtures import fixture, unknown

class LanguageTests(unittest.TestCase):
    def test_explicit_english_overrides_record(self):
        b=fixture()
        b["run"]["report_language"]="zh-CN"
        text=render(b,"en")
        self.assertIn("## Higher quartile",text)
        self.assertIn("## Time",text)
        self.assertIn("## Fit",text)
        self.assertNotIn("# 医学选刊报告",text)
    def test_record_language_and_legacy(self):
        b=fixture()
        self.assertIn("# 医学选刊报告",render(b))
        b["run"]["report_language"]="en"
        self.assertIn("# Medical Journal Selection Report",render(b))
    def test_english_unknown_and_quotes(self):
        b=fixture()
        b["journals"][0]["facts"]["jcr"]=unknown()
        text=render(b,"en")
        self.assertIn("Not verified（未核到）",text)
        self.assertIn(b["journals"][0]["facts"]["scope"]["value"]["quote"],text)
    def test_offline_has_no_ranking(self):
        b=fixture()
        b["run"]["web_available"]=False
        text=render(b,"en")
        self.assertIn("## Search plan",text)
        self.assertNotIn("- **Fictional",text)
    def test_invalid_declared_language_is_rejected(self):
        b=fixture()
        b["run"]["report_language"]="en-or-zh"
        self.assertIn("run.report_language must be en or zh-CN when supplied",validate(b))
    def test_scope_is_quoted_once_without_reprinting_support_passages(self):
        b=fixture()
        b["journals"]=b["journals"][:1]
        quote=b["journals"][0]["facts"]["scope"]["value"]["quote"]
        b["journals"][0]["facts"]["scope"]["evidence"][0]["support"]=quote
        text=render(b,"en")
        self.assertEqual(text.count(quote),1)
        self.assertIn("evidence record",text)

if __name__=="__main__":
    unittest.main()
