"""Offline regression checks: bad discovery queries must not become cached retries."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector-skill-trainer/scripts"))
import campaign
from broker import discover
from corpus import parse_article
from runner import collect_call_records


TARGET_TITLE="Synthetic Target Full Paper Title"
QUERY_GUARD="Rejected answer-bearing or long manuscript search"
PROFILE={
    "field":"Public health", "article_type":"Original research",
    "design":"Cross-sectional association analysis", "data_sources":["NHANES"],
    "method_labels":["secondary population-data analysis"],
    "validation":"No independent external prediction validation", "limitations":[],
    "keywords":["frailty","aging","population","association","survey","health"],
    "queries":["TITLE_ABS:frailty AND TITLE_ABS:survey",
               "TITLE_ABS:frailty AND TITLE_ABS:NHANES",
               "TITLE_ABS:frailty AND TITLE_ABS:aging"],
    "primary_stratum":"public_database", "medical_relevance":True,
    "summary":"Synthetic association study", "abstract_summary":"Frailty in a population survey."
}
REJECTED_QUERIES=(
    " ".join("concept"+str(i) for i in range(19)),
    "TITLE_ABS:\""+TARGET_TITLE.lower()+"\"",
    'TITLE_ABS:"seven distinct words copied from manuscript text"',
    "TITLE_ABS:frailty AND GSE26440",
    "TITLE_ABS:frailty AND NCT07098208",
)


class FinishedFixtureProcess:
    """An already completed transport fixture, never an actual model call."""
    returncode=0
    def poll(self):return self.returncode
    def wait(self,timeout=None):return self.returncode


def fixture_cli(messages):
    pending=iter(messages)
    def spawn(command,**kwargs):
        context,message,usage=next(pending)
        events=[{"type":"thread.started","thread_id":context},
                {"type":"item.completed","item":{"type":"agent_message","text":message}},
                {"type":"turn.completed","usage":usage}]
        kwargs["stdout"].write("\n".join(json.dumps(event) for event in events))
        kwargs["stdout"].flush()
        return FinishedFixtureProcess()
    return spawn


def make_case(root):
    corpus=Path(root)/"corpus"
    source=corpus/"synthetic-development-case"
    source.mkdir(parents=True)
    xml=('''<article><front><journal-meta/><article-meta><title-group><article-title>'''
         +TARGET_TITLE+'''</article-title></title-group><permissions><license><license-p>
         Creative Commons Attribution License CC BY
         </license-p></license></permissions></article-meta></front><body><sec><title>Methods</title>
         <p>A synthetic population study analysed frailty in older adults using NHANES.
         The principal objective was cross-sectional association analysis, not prediction.</p>
         </sec><sec><title>Results</title><p>Associations were reported without causal guarantees.</p>
         </sec></body></article>''')
    rights,masked=parse_article(xml)
    if not rights["permitted"]:raise AssertionError("Synthetic license fixture is invalid")
    (source/"source.xml").write_text(xml,encoding="utf-8")
    (source/"masked.txt").write_text(masked,encoding="utf-8")
    (source/"answer.json").write_text(json.dumps({"title":TARGET_TITLE,"issns":["9000-0005"],"ids":{}}),encoding="utf-8")
    case={"case_id":source.name,"input_hash":hashlib.sha256(masked.encode()).hexdigest(),
          "stratum":"public_database","split":"development","license":"CC BY"}
    return case,corpus,Path(root)/"runs"


class ProfileQueryContractTests(unittest.TestCase):
    def test_each_broker_guard_is_rejected_by_profile_contract_before_any_search(self):
        answer={"title":TARGET_TITLE}
        for query in REJECTED_QUERIES:
            with self.subTest(query=query):
                value=copy.deepcopy(PROFILE)
                value["queries"][0]=query
                errors=campaign.profile_contract(value,answer)
                self.assertTrue(errors)
                # The reason must not reveal the target title or a study code.
                self.assertNotIn(TARGET_TITLE.casefold()," ".join(errors).casefold())
                self.assertNotIn("GSE26440"," ".join(errors))
                self.assertNotIn("NCT07098208"," ".join(errors))
                with patch("broker.search") as search:
                    with self.assertRaisesRegex(ValueError,QUERY_GUARD):
                        discover([query],answer,"Synthetic masked content","2024-10-02","2026-10-02","unused.json")
                search.assert_not_called()

    def test_guard_checks_every_query_not_just_first(self):
        for position in range(3):
            value=copy.deepcopy(PROFILE)
            value["queries"][position]="TITLE_ABS:frailty AND PRJNA12345"
            self.assertTrue(campaign.profile_contract(value,{"title":TARGET_TITLE}))

    def test_ordinary_database_names_and_short_concepts_remain_allowed(self):
        value=copy.deepcopy(PROFILE)
        value["queries"]=["TITLE_ABS:frailty AND NHANES", "TITLE_ABS:aging AND GEO",
                          'TITLE_ABS:"older adult" AND MIMIC']
        self.assertEqual(campaign.profile_contract(value,{"title":TARGET_TITLE}),[])

    def test_non_string_or_wrong_size_queries_fail_cleanly(self):
        for queries in ([None,{},1],[],[" ","frailty","aging"],"frailty"):
            with self.subTest(queries=queries):
                value=copy.deepcopy(PROFILE)
                value["queries"]=queries
                self.assertTrue(campaign.profile_contract(value,{"title":TARGET_TITLE}))

    def test_existing_bad_profile_is_invalidated_even_when_literature_is_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            case,corpus,runs=make_case(folder)
            work=runs/case["case_id"]
            work.mkdir(parents=True)
            # A prior completed checkpoint is genuine but its query is unsafe.
            value=copy.deepcopy(PROFILE)
            value["queries"][2]='TITLE_ABS:"'+TARGET_TITLE+'"'
            raw=json.dumps(value)
            with patch("runner.shutil.which",return_value="fixture-codex"), \
                 patch("runner.subprocess.Popen",side_effect=fixture_cli([
                     ("old-unsafe-profile-context",raw,{"output_tokens":12})])):
                # Build the exact preparation prompt/checkpoint through the
                # old structural-only contract, without executing retrieval.
                actual_contract=campaign.profile_contract
                with patch("campaign.profile_contract",side_effect=lambda output,answer=None:actual_contract(output)), \
                     patch("campaign.discover",side_effect=RuntimeError("synthetic retrieval stop")):
                    with self.assertRaisesRegex(RuntimeError,"synthetic retrieval stop"):
                        campaign.prepare_case(case,corpus,work,"2026-10-02")
            (work/"literature.json").write_text('{"records":[],"papers":[]}',encoding="utf-8")
            original=work.joinpath("profile.json").read_bytes()
            with patch("runner.subprocess.Popen") as spawn, patch("campaign.discover") as retrieval:
                with self.assertRaises(campaign.ModelOutputError):
                    campaign.prepare_case(case,corpus,work,"2026-10-02")
            spawn.assert_not_called()
            retrieval.assert_not_called()
            self.assertEqual(work.joinpath("profile.json").read_bytes(),original)
            receipt=json.loads(work.joinpath("profile.json.record.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"],"completed")
            self.assertEqual(receipt["output_contract_status"],"failed")
            self.assertEqual(receipt["context_id"],"old-unsafe-profile-context")

    def test_failed_profile_case_retries_in_fresh_context_and_preserves_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            case,corpus,runs=make_case(folder)
            bad=copy.deepcopy(PROFILE)
            bad["queries"][1]="TITLE_ABS:frailty AND GSE26440"
            bad_raw=json.dumps(bad)
            good_raw=json.dumps(PROFILE)
            with patch("runner.shutil.which",return_value="fixture-codex"), \
                 patch("runner.subprocess.Popen",side_effect=fixture_cli([
                     ("bad-profile-context",bad_raw,{"output_tokens":7}),
                     ("fresh-profile-context",good_raw,{"output_tokens":11})])) as spawn, \
                 patch("campaign.discover",side_effect=RuntimeError("synthetic network outage")) as retrieval:
                first=campaign.execute(case,corpus,runs,{},None,"2026-10-02")
                self.assertEqual(first["status"],"model_failed")
                self.assertEqual(retrieval.call_count,0)
                second=campaign.execute(case,corpus,runs,{},None,"2026-10-02")
            self.assertEqual(spawn.call_count,2)
            self.assertEqual(retrieval.call_count,1)
            self.assertEqual(second["status"],"infrastructure_failed")
            work=runs/case["case_id"]
            archive=work/"profile.attempts/attempt-01"
            self.assertEqual((archive/"profile.json").read_text(encoding="utf-8"),bad_raw)
            receipt=json.loads((archive/"profile.json.record.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"],"completed")
            self.assertEqual(receipt["output_contract_status"],"failed")
            self.assertEqual(receipt["usage"]["output_tokens"],7)
            self.assertTrue(receipt["terminal_output_matches"])
            self.assertEqual(receipt["output_hash"],hashlib.sha256(bad_raw.encode()).hexdigest())
            first_ledger=json.loads((work/"ledger-attempts/ledger-attempt-01.json").read_text(encoding="utf-8"))
            self.assertEqual(first_ledger["status"],"model_failed")
            calls=collect_call_records(work)
            self.assertEqual(len(calls),2)
            self.assertEqual({c["context_id"] for c in calls},{"bad-profile-context","fresh-profile-context"})
            self.assertEqual(sum(c["usage"]["output_tokens"] for c in calls),18)
            # Private preparation checks must not leak the answer into the prompt.
            self.assertNotIn(TARGET_TITLE,(work/"profile.json.input.txt").read_text(encoding="utf-8"))

    def test_guard_rejection_after_contract_marks_profile_failed_not_infrastructure(self):
        with tempfile.TemporaryDirectory() as folder:
            case,corpus,runs=make_case(folder)
            with patch("runner.shutil.which",return_value="fixture-codex"), \
                 patch("runner.subprocess.Popen",side_effect=fixture_cli([
                     ("valid-shape-context",json.dumps(PROFILE),{"output_tokens":5})])), \
                 patch("campaign.discover",side_effect=ValueError(QUERY_GUARD)):
                ledger=campaign.execute(case,corpus,runs,{},None,"2026-10-02")
            self.assertEqual(ledger["status"],"model_failed")
            receipt=json.loads((runs/case["case_id"]/"profile.json.record.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["output_contract_status"],"failed")
            self.assertEqual(receipt["status"],"completed")

    def test_other_broker_value_error_retains_infrastructure_classification(self):
        with tempfile.TemporaryDirectory() as folder:
            case,corpus,runs=make_case(folder)
            with patch("runner.shutil.which",return_value="fixture-codex"), \
                 patch("runner.subprocess.Popen",side_effect=fixture_cli([
                     ("profile-before-retrieval-failure",json.dumps(PROFILE),{"output_tokens":5})])), \
                 patch("campaign.discover",side_effect=ValueError("synthetic malformed API response")):
                ledger=campaign.execute(case,corpus,runs,{},None,"2026-10-02")
            self.assertEqual(ledger["status"],"infrastructure_failed")
            receipt=json.loads((runs/case["case_id"]/"profile.json.record.json").read_text(encoding="utf-8"))
            self.assertNotIn("output_contract_status",receipt)


if __name__=="__main__":unittest.main()
