"""Study-family leakage boundaries; all inputs below are synthetic."""
import sys
import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from corpus import own_study_registrations,parse_article
from broker import excluded_paper, strip_target_mentions,capture,plan_followed_links,OfficialRedirect
from campaign import prepare_case,InputEligibilityError


class StudyFamilyTests(unittest.TestCase):
    def test_protocol_with_different_title_and_doi_is_filtered_by_own_registry(self):
        target={'ids':{'doi':'10.0000/results'},'title':'Completed clinical outcomes',
                'study_registration_ids':['NCT01234567']}
        protocol={'doi':'10.0000/design','title':'A prospective feasibility protocol',
                  'abstractText':'Trial registration: NCT01234567. Planned outcomes and methods.'}
        self.assertTrue(excluded_paper(protocol,target,'Completed scientific results'))
        cached={**protocol,'abstract':protocol['abstractText']}
        del cached['abstractText']
        self.assertTrue(excluded_paper(cached,target,'Completed scientific results'))

    def test_independent_trial_and_reused_dataset_remain_discoverable(self):
        target={'title':'A clinical study','study_registration_ids':['NCT01234567']}
        for paper in [{'title':'An independent protocol','abstractText':'Registered NCT07654321.'},
                      {'title':'Independent analysis','abstractText':'NHANES and GSE1234 data were analyzed.'}]:
            self.assertFalse(excluded_paper(paper,target,'Distinct research'))

    def test_only_explicit_own_registration_is_extracted(self):
        root=ET.fromstring('''<article><front><article-meta><abstract><sec><title>Trial registration</title><p>NCT01234567</p></sec></abstract></article-meta></front><body><sec><title>Methods</title><p>This study was prospectively registered (ISRCTN12345678).</p><p>Prior studies reported NCT11111111 and NCT22222222.</p><p>Public data GSE1234 were reused.</p></sec></body><back><ref-list><ref><p>The trial was registered NCT33333333.</p></ref></ref-list></back></article>''')
        self.assertEqual(own_study_registrations(root),['ISRCTN12345678','NCT01234567'])

    def test_ambiguous_multi_trial_description_does_not_infer_ownership(self):
        root=ET.fromstring('''<article><body><p>The study was registered after comparisons with NCT11111111 and NCT22222222.</p></body></article>''')
        self.assertEqual(own_study_registrations(root),[])

    def test_cited_single_trial_and_separate_sentence_do_not_become_own_registry(self):
        paragraphs=[
            'A previous trial was registered NCT01234567 and informed the intervention used here.',
            'The study by Smith was registered NCT01234567, whereas our analysis was retrospective.',
            'This study was registered prospectively. We compared our findings with independent trial NCT01234567.',
            'This study was registered after comparisons with independent trial NCT01234567.'
        ]
        for text in paragraphs:
            with self.subTest(text=text):
                root=ET.fromstring('<article><body><p>'+text+'</p></body></article>')
                self.assertEqual(own_study_registrations(root),[])

    def test_heading_does_not_override_independent_trial_or_denied_registration(self):
        examples=[
            ('Registration of included trials','The prior trial was registered NCT01234567.'),
            ('Trial registration','Previous trial NCT01234567 informed the design; this study has no registration.'),
            ('Methods','This study was not registered NCT01234567.')
        ]
        for title,text in examples:
            with self.subTest(title=title,text=text):
                root=ET.fromstring('<article><body><sec><title>'+title+'</title><p>'+text+'</p></sec></body></article>')
                self.assertEqual(own_study_registrations(root),[])

    def test_review_registration_and_dual_explicit_registry_are_supported(self):
        root=ET.fromstring('''<article><front><article-meta><abstract><sec><title>Registration</title><p>PROSPERO CRD42021234567</p></sec></abstract></article-meta></front><body><sec><title>Trial registration</title><p>NCT01234567; ISRCTN12345678</p></sec></body></article>''')
        self.assertEqual(own_study_registrations(root),['CRD42021234567','ISRCTN12345678','NCT01234567'])

    def test_registry_answer_clue_is_removed_as_complete_line(self):
        text='Publisher policy\nProtocol NCT01234567 appeared in Answer Journal\nIndependent scope sentence'
        result=strip_target_mentions(text,{'study_registration_ids':['NCT01234567']})
        self.assertEqual(result,'Publisher policy\nIndependent scope sentence')

    def test_own_registry_never_survives_urls_redirects_or_link_metadata(self):
        answer={'study_registration_ids':['NCT01234567']}
        start='https://www.nature.com/policies'
        forbidden='https://www.nature.com/policies/NCT01234567'
        with patch('broker.fetch_page') as fetch:
            result=capture(forbidden,answer);fetch.assert_not_called()
            self.assertNotIn('NCT01234567',json.dumps(result))
        html=('<p>'+('Journal authors and submission scope information. '*10)+'</p><a href="'+forbidden+'">Author policies</a><a href="https://www.nature.com/author-policies">Independent policy</a>').encode()
        with patch('broker.fetch_page',return_value=(html,start,'text/html')):
            result=capture(start,answer)
            self.assertEqual(result['status'],'readable_snapshot')
            self.assertNotIn('NCT01234567',json.dumps(result))
            self.assertIn('https://www.nature.com/author-policies',result['links'])
        with patch('broker.fetch_page',return_value=(html,forbidden,'text/html')):
            result=capture(start,answer)
            self.assertEqual(result['status'],'unverified')
            self.assertNotIn('NCT01234567',json.dumps(result))
        with self.assertRaisesRegex(ValueError,'study-family redirect'):
            OfficialRedirect(answer).redirect_request(None,None,302,'redirect',{},forbidden)
        planned,_=plan_followed_links([{'url':start,'links':[forbidden]}],[start],answer)
        self.assertEqual(planned,[])

    def test_leaking_cache_is_rejected_before_source_planning_without_rewriting(self):
        xml='''<article article-type="research-article"><front><journal-meta/><article-meta><title-group><article-title>Synthetic final outcomes</article-title></title-group><permissions><license><license-p>CC BY Creative Commons Attribution License</license-p></license></permissions></article-meta></front><body><p>This trial was prospectively registered NCT01234567.</p><p>Clinical outcomes were measured.</p></body></article>'''
        rights,masked=parse_article(xml)
        self.assertTrue(rights['permitted'])
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); source=base/'corpus'/'case';source.mkdir(parents=True)
            work=base/'work';work.mkdir()
            (source/'source.xml').write_text(xml)
            (source/'masked.txt').write_text(masked)
            # Old answer files do not have the new registration field.
            (source/'answer.json').write_text(json.dumps({'title':'Synthetic final outcomes','issns':['9000-0005'],'ids':{}}))
            cache=work/'literature.json'
            original=json.dumps({'papers':[{'title':'Prospective protocol','abstract':'Registered NCT01234567.'}]})
            cache.write_text(original)
            case={'case_id':'case','stratum':'clinical_nursing','input_hash':hashlib.sha256(masked.encode()).hexdigest()}
            profile={'medical_relevance':True,'primary_stratum':'clinical_nursing','queries':['topic','method','readership'],
                     'abstract_summary':'Synthetic clinical outcomes','keywords':['care','trial','clinical']}
            with patch('campaign.model_json',return_value=(profile,{})) as model,patch('campaign.capture_all') as capture:
                with self.assertRaisesRegex(InputEligibilityError,'same-study material') as error:
                    prepare_case(case,base/'corpus',work,'2026-10-03')
                self.assertNotIn('NCT01234567',str(error.exception))
                self.assertEqual(model.call_count,1)
                self.assertNotIn('NCT01234567',model.call_args.args[0])
                capture.assert_not_called()
            self.assertEqual(cache.read_text(),original)
            # A separately leaking old policy cache is rejected too; neither
            # source cache is silently rewritten into a successful blind run.
            cache.write_text(json.dumps({'papers':[],'records':[]}))
            policy=work/'policies.json';policy_original=json.dumps([{'url':'https://www.nature.com/policies','links':['https://www.nature.com/NCT01234567']}]);policy.write_text(policy_original)
            with patch('campaign.model_json',side_effect=[(profile,{}),({'journals':[]},{})]),patch('campaign.capture_all') as capture:
                with self.assertRaisesRegex(InputEligibilityError,'Retained policies contain study identity'):
                    prepare_case(case,base/'corpus',work,'2026-10-03')
                capture.assert_not_called()
            self.assertEqual(policy.read_text(),policy_original)
            self.assertFalse((work/'generator-packet.json').exists())


if __name__=='__main__':unittest.main()
