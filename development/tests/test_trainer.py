import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector-skill-trainer/scripts"))
from corpus import mask_text, near_duplicate, fingerprint, parse_article, license_eligibility, prepare, attach_journal_identity,research_text
from broker import excluded_paper, strip_target_mentions, permitted_url, capture, capture_all,policy_excerpt,capture_identity,discover
from evaluation import fixed_baselines, require_reveal, wilson, summarize, promotion, journal_match,candidate_handoff,evidence_coverage
from freeze import freeze,verify
from campaign import prepare_case,InputEligibilityError,reveal_case,automatic_no_rule_reason,source_audit
from status import inspect as inspect_status

class TrainerTests(unittest.TestCase):
    def test_registration_answer_searches_are_rejected_before_network_access(self):
        identifiers=['NCT07098208','ISRCTN12345678','CRD42021234567','ChiCTR2400081234',
                     'ACTRN12624001234567','UMIN000012345','DRKS00012345','IRCT20240101012345N1','KCT0001234']
        with tempfile.TemporaryDirectory() as folder,patch('broker.search') as search:
            for identifier in identifiers:
                with self.subTest(identifier=identifier),self.assertRaises(ValueError):
                    discover(['clinical outcomes '+identifier],{'title':'Hidden complete manuscript title'},
                             'Masked research narrative','2024-10-02','2026-10-02',Path(folder)/'search.json')
            search.assert_not_called()

    def test_study_registrations_mask_consistently_without_removing_registration_facts(self):
        ids=['CRD42021234567','ChiCTR2400081234','ACTRN12624001234567',
             'UMIN000012345','DRKS00012345','IRCT20240101012345N1','KCT0001234']
        for identifier in ids:
            with self.subTest(identifier=identifier):
                text=mask_text('Prospectively registered: '+identifier+'. Repeated '+identifier+'. GSE26440.',{})
                self.assertNotIn(identifier,text)
                self.assertIn('Prospectively registered',text)
                self.assertEqual(text.count('[masked trial registry 1]'),2)
                self.assertIn('GSE26440',text)

    def test_registry_capture_is_selected_identity_metadata_only(self):
        raw=json.dumps({'status':'ok','message':{'title':'Fictional Registry Journal','ISSN':['9000-0005'],
                       'publisher':'Fictional Publisher','coverage':{'references-current':.91}}}).encode()
        with patch('broker.get',return_value=raw):
            page=capture_identity('9000-0005')
        self.assertEqual(page['status'],'readable_snapshot')
        self.assertEqual(page['allowed_fact_fields'],['identity'])
        self.assertIn('Fictional Registry Journal',page['text'])
        self.assertNotIn('coverage',page['text'])
        with patch('broker.get',return_value=raw):
            self.assertEqual(capture_identity('9000-0013')['status'],'unverified')

    def test_registry_sources_share_the_initial_and_total_budget(self):
        initial=['https://link.springer.com/journal/12876/aims-scope-'+str(i) for i in range(18)]
        follows=['https://link.springer.com/journal/'+str(i)+'/submission-guidelines/research-articles' for i in range(20)]
        ids=[{'journal_id':f'9000-000{i}'} for i in range(6)]
        fake=lambda u,a:{'url':u,'status':'readable_snapshot','text':'Fictional page','links':follows if u in initial else []}
        registry=lambda jid:{'url':'https://api.crossref.org/journals/'+jid,'status':'readable_snapshot','text':'Fictional identity','links':[],'allowed_fact_fields':['identity']}
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=fake),patch('broker.capture_identity',side_effect=registry),patch('broker.time.sleep'):
            records=capture_all(initial,{'ids':{}},Path(folder)/'pages.json','Original research',ids)
        self.assertEqual(len(records),30)
        self.assertEqual(sum('api.crossref.org' in p['url'] for p in records),6)
        self.assertEqual(sum(p.get('retrieval_round')==2 for p in records),12)

    def test_identity_registry_cannot_verify_scope_or_a_publication_precedent(self):
        from types import SimpleNamespace
        stamp='2026-10-02T00:00:00+00:00';url='https://api.crossref.org/journals/9000-0005'
        envelope={'status':'verified','value':{'quote':'Fictional identity text'},
                  'evidence':[{'url':url,'checked_at':stamp,'support':'Fictional identity text','source_type':'official'}]}
        page={'url':url,'checked_at':stamp,'text':'Fictional identity text','status':'readable_snapshot',
              'source_type':'official','allowed_fact_fields':['identity']}
        packet={'policies':[page],'literature':[{'journal_id':'9000-0005'}]}
        value={'evidence':{'constraints':{},'journals':[{'id':'9000-0005','facts':{'identity':copy.deepcopy(envelope),'scope':copy.deepcopy(envelope)},
                'precedents':[copy.deepcopy(envelope)]}]},'fit_sequence':[]}
        failures=source_audit(value,packet,SimpleNamespace(validate=lambda b:[]))
        self.assertEqual(len(failures),2)
        self.assertTrue(all('restricted to journal identity' in e for e in failures))

    def test_serialized_identity_source_type_must_match_its_actual_registry_record(self):
        from types import SimpleNamespace
        stamp='2026-10-02T00:00:00+00:00';url='https://api.crossref.org/journals/9000-0005'
        ev={'url':url,'checked_at':stamp,'support':'Fictional identity text','source_type':'bibliographic'}
        page={'url':url,'checked_at':stamp,'text':ev['support'],'status':'readable_snapshot',
              'source_type':'official','allowed_fact_fields':['identity']}
        value={'evidence':{'constraints':{},'journals':[{'id':'9000-0005','facts':{'identity':{
               'status':'verified','value':{'issns':['9000-0005']},'evidence':[ev]}}}]},'fit_sequence':[]}
        packet={'policies':[page],'literature':[{'journal_id':'9000-0005'}]}
        failures=source_audit(value,packet,SimpleNamespace(validate=lambda b:[]))
        self.assertEqual(len(failures),1)
        self.assertIn('source classification changed',failures[0])
        ev['source_type']='official'
        self.assertEqual(source_audit(value,packet,SimpleNamespace(validate=lambda b:[])),[])

    def test_essential_declarations_and_back_matter_are_not_publication_metadata(self):
        xml='''<article><front><journal-meta><journal-title-group><journal-title>Secret Journal</journal-title></journal-title-group></journal-meta><article-meta><title-group><article-title>Secret Paper Title</article-title></title-group><permissions><license><license-p>Creative Commons Attribution License CC BY</license-p></license></permissions></article-meta></front><body><sec><title>Methods</title><p>Two cohorts were analysed.</p></sec><sec><title>Declarations</title><sec><title>Ethics approval</title><p>Written informed consent was obtained.</p></sec><sec><title>Author contributions</title><p>Secret author workflow</p></sec></sec></body><back><sec><title>Data availability statement</title><p>Training used GSE26440; validation used GSE167363.</p></sec><sec><title>Consent for publication</title><p>Written publication consent was obtained from all patients.</p></sec><ref-list><ref>Secret Journal reference</ref></ref-list></back></article>'''
        _,text=parse_article(xml)
        self.assertIn('Written informed consent was obtained',text)
        self.assertIn('Written publication consent was obtained',text)
        self.assertIn('Training used GSE26440; validation used GSE167363',text)
        self.assertNotIn('Secret author workflow',text)
        self.assertNotIn('Secret Journal reference',text)

    def test_research_link_labels_survive_with_publication_clues_masked(self):
        import xml.etree.ElementTree as ET
        body=ET.fromstring('<body><p>Training used <ext-link>GSE26440</ext-link> and validation used <ext-link>GSE167363</ext-link>. Registry: <ext-link>NCT07098208</ext-link>. Repeated NCT07098208.</p><ref-list><ref>Secret publishing details</ref></ref-list></body>')
        text=mask_text(research_text(body),{'journal':'Medicine'})
        self.assertIn('Training used GSE26440 and validation used GSE167363',text)
        self.assertIn('[masked trial registry 1]',text)
        self.assertEqual(text.count('[masked trial registry 1]'),2)
        self.assertNotIn('NCT07098208',text)
        self.assertNotIn('Secret publishing details',text)
        self.assertNotIn('GSE26440',mask_text(research_text(body),{},'pseudonymize_accessions'))
        linked=mask_text('Data: https://example.org/query?acc=GSE26440 Trial: https://clinicaltrials.gov/study/NCT07098208',{})
        self.assertIn('GSE26440',linked)
        self.assertIn('[masked trial registry 1]',linked)
        self.assertNotIn('NCT07098208',linked)
        self.assertNotIn('https://',linked)

    def test_ambiguous_journal_names_do_not_erase_research_terms(self):
        text=mask_text('Medicine research measured blood cells. Published in Medicine. Journal: Medicine.',{'journal':'Medicine'})
        self.assertIn('Medicine research measured blood cells.',text)
        self.assertNotIn('Published in Medicine',text)
        self.assertNotIn('Journal: Medicine',text)
        self.assertIn('blood cells',mask_text('blood cells',{'journal':'Blood','journal_aliases':['Cells']}))

    def test_field_coverage_preserves_unknowns_and_does_not_certify_truth(self):
        coverage=evidence_coverage({'journals':[
            {'facts':{'scope':{'status':'verified'},'jcr':{'status':'unverified'},'fees':None},
             'timelines':{'acceptance':{'status':'unverified'}}},
            {'facts':{'scope':{'status':'unverified'}}}]})
        self.assertEqual(coverage['scope'],{'verified':1,'unverified':1,'invalid_status':0})
        self.assertEqual(coverage['jcr']['unverified'],1)
        self.assertEqual(coverage['fees']['invalid_status'],1)
        self.assertEqual(coverage['timeline:acceptance']['unverified'],1)
        result=summarize([
            {'status':'completed','stratum':'clinical','scores':{'v2':{'source_coverage':coverage,'hard_failures':['Unsupported scope claim']}}},
            {'status':'completed','stratum':'clinical','scores':{'v2':{}}}])
        summary=result['variants']['v2']
        self.assertEqual(summary['source_coverage_cases'],1)
        self.assertEqual(summary['n'],2)
        self.assertEqual(summary['hard_failure_cases'],1)
        self.assertEqual(summary['source_coverage'],coverage)

    def test_no_rule_bookkeeping_preserves_bad_outcomes_but_never_adopts_rules(self):
        ledger={'split':'development','status':'diagnosed','lesson_status':'change_review_pending',
                'revealed_at':'actual-time','lesson_record':{'status':'completed'},
                'scores':{'v2':{'hard_failures':[],'usable':False,'true_rank':None}},
                'diagnosis':{'hypotheses':[{'rule':'no rule'}],'stratum_confirmed':True,'no_change_reason':'Existing rules address the gap.'}}
        self.assertIsNotNone(automatic_no_rule_reason(ledger))
        changed=copy.deepcopy(ledger)
        changed['diagnosis']['hypotheses'][0]['rule']='Always prefer the revealed journal'
        self.assertIsNone(automatic_no_rule_reason(changed))
        changed=copy.deepcopy(ledger)
        changed['diagnosis']['stratum_confirmed']=False
        self.assertIsNone(automatic_no_rule_reason(changed))
        changed['diagnosis']['stratum_confirmed']='false'
        self.assertIsNone(automatic_no_rule_reason(changed))
        changed=copy.deepcopy(ledger)
        changed['scores']['v2']['hard_failures']=['Unsupported claim']
        self.assertIsNone(automatic_no_rule_reason(changed))
        changed=copy.deepcopy(ledger)
        changed['diagnosis']['hypotheses']=[]
        self.assertIsNotNone(automatic_no_rule_reason(changed))
        changed['diagnosis']['stratum_confirmed']=False
        self.assertIsNone(automatic_no_rule_reason(changed))

    def test_diagnostic_handoff_preserves_frozen_baseline_prefix(self):
        papers=[{'journal_id':str(i),'journal':'Journal '+str(i),'title':'asthma','abstract':'asthma clinical outcomes '+('lung '*i)} for i in range(1,16)]
        small=fixed_baselines('asthma lung',['asthma'],papers)
        complete=fixed_baselines('asthma lung',['asthma'],papers,limit=None)
        for kind in small:self.assertEqual(small[kind],complete[kind][:10])
        chosen={p['journal_id'] for rows in small.values() for p in rows}
        trace=candidate_handoff('asthma lung',['asthma'],papers,[p for p in papers if p['journal_id'] in chosen],{'journals':[]})
        self.assertEqual(len(trace),15)
        self.assertTrue(all(row['baseline_positions'] for row in trace))
        self.assertTrue(any(not row['delivered_papers'] for row in trace))

    def test_final_execution_protocol_cannot_change_silently(self):
        records=[{'case_id':str(i),'status':'completed','protocol_hashes':{'runner.py':str(i)},
                  'stratum':'clinical_nursing','scores':{'v1':{'true_rank':None,'usable':False},
                  'v2':{'true_rank':None,'usable':False,'hard_failures':[]}}} for i in range(2)]
        self.assertIn('Final execution protocol changed or unrecorded',promotion([],records,{})['failures'])

    def test_status_never_counts_pending_decision_or_unsealed_request(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            corpus=root/'corpus'
            corpus.mkdir()
            (corpus/'manifest.json').write_text(json.dumps({'cases':[{'case_id':'case','split':'development','stratum':'review'}]}),encoding='utf-8')
            work=root/'runs'/'case'
            work.mkdir(parents=True)
            (work/'ledger.json').write_text(json.dumps({'status':'completed','lesson_status':'change_review_pending'}),encoding='utf-8')
            (work/'selection.json.input.txt').write_text('request',encoding='utf-8')
            (corpus/'case').mkdir()
            # Deliberately malformed answer: status must not even open it.
            (corpus/'case'/'answer.json').write_text('ANSWER MUST NOT BE READ',encoding='utf-8')
            report=inspect_status(corpus,root/'runs')
            self.assertEqual(report['completed'],0)
            self.assertEqual(report['cases'][0]['requests_without_terminal_record'],['selection.json'])

    def test_long_navigation_does_not_displace_admission_standard(self):
        navigation='\n'.join('Pharmacology journal scope and submission navigation '+('topic '*35) for _ in range(500))
        policy='Standards for research methodology\nComputational public data requires independent experimental validation.\nAn observational cohort has separate requirements.'
        result=policy_excerpt(navigation+'\n'+policy)
        self.assertLessEqual(len(result),40000)
        self.assertIn('Computational public data requires independent experimental validation.',result)
        self.assertIn('observational cohort has separate requirements',result)

    def test_xml_citation_tail_preserves_research(self):
        xml='''<article><front><journal-meta/><article-meta/></front><body><sec>
        <title>Methods</title><p>We adjusted <xref ref-type="bibr">citation</xref> for age and sex.
        The external cohort had 800 participants.</p></sec></body></article>'''
        _,masked=parse_article(xml)
        self.assertIn('for age and sex',masked)
        self.assertIn('800 participants',masked)
        self.assertNotIn('citation',masked)

    def test_nested_metadata_and_reference_lists_do_not_leak(self):
        xml='''<article><front><journal-meta/><article-meta/></front><body><sec><title>Discussion</title>
        <p>The study evaluated 600 patients.</p><sec><title>References</title>
        <ref-list><ref>Known author Journal 2026</ref></ref-list></sec>
        <sec><title>Transparency Statement</title><p>Named author affirms this.</p></sec>
        <p>How to cite this article: Answer Author, Answer Journal 2026.</p>
        <fn-group><fn>Time of primary review: 20 days</fn></fn-group>
        <p>Patients received treatment on day 20.</p></sec></body></article>'''
        _,masked=parse_article(xml)
        for secret in ('Known author','Named author','Answer Author','primary review'):
            self.assertNotIn(secret,masked)
        self.assertIn('600 patients',masked)
        self.assertIn('Patients received treatment on day 20',masked)

    def test_extraction_change_rejected_before_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'case'
            source.mkdir()
            masked='Old extraction discarded all narrative after a citation.'
            (source/'masked.txt').write_text(masked,encoding='utf-8')
            (source/'source.xml').write_text('<article><front><journal-meta/><article-meta><permissions><license>Creative Commons Attribution</license></permissions></article-meta></front><body><p>Full research narrative.</p></body></article>',encoding='utf-8')
            with patch('campaign.model_json') as model:
                with self.assertRaisesRegex(InputEligibilityError,'text extraction changed'):
                    prepare_case({'case_id':'case','input_hash':hashlib.sha256(masked.encode()).hexdigest()},folder,Path(folder)/'runs','2026-10-02')
                model.assert_not_called()

    def test_policy_lead_after_long_navigation_is_kept_and_followed(self):
        start='https://www.frontiersin.org/journals/medicine/about'
        policy='https://www.frontiersin.org/guidelines/policies-and-publication-ethics'
        navigation=''.join(f'<a href="https://www.frontiersin.org/journals/other-{i}">Navigation</a>' for i in range(150))
        html=(navigation+f'<a href="{policy}">Research methodology standards</a><p>'+('Actual visible journal policy text. '*12)+'</p>').encode()
        with patch('broker.fetch_page',return_value=(html,start,'text/html')):
            page=capture(start,{'ids':{}})
        self.assertIn(policy,page['links'])
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=lambda url,answer: page if url==start else {'url':url,'status':'readable_snapshot','links':[],'text':'Standards'}):
            records=capture_all([start],{'ids':{}},Path(folder)/'policies.json')
        self.assertEqual([p['url'] for p in records],[start,policy])
        self.assertEqual(records[-1]['retrieval_round'],2)

    def test_identity_metadata_survives_a_long_policy_snapshot(self):
        start='https://link.springer.com/journal/12933'
        html=('<meta name="citation_journal_title" content="Clinical Journal"><meta name="citation_issn" content="1234-5679"><script>not source text</script><p>'+('Long methodology validation guidance. '*1800)+'</p><p>Electronic ISSN 1234-5679</p>').encode()
        with patch('broker.fetch_page',return_value=(html,start,'text/html')):
            page=capture(start,{'ids':{}})
        self.assertIn('1234-5679',page['text'])
        self.assertIn('citation_journal_title = Clinical Journal',page['text'])
        self.assertLessEqual(len(page['text']),40000)
        self.assertNotIn('not source text',page['text'])

    def test_research_admission_links_are_not_displaced_by_methodology_type(self):
        start='https://link.springer.com/journal/12933/submission-guidelines'
        unrelated=['https://link.springer.com/journal/'+str(i)+'/submission-guidelines/methodology' for i in range(20)]
        unrelated+=['https://www.nature.com/nature-portfolio/editorial-policies/policy-'+str(i) for i in range(20)]
        for suffix in ('original-investigation','research-articles'):
            research='https://link.springer.com/journal/12933/submission-guidelines/'+suffix
            initial={'url':start,'status':'readable_snapshot','links':unrelated+[research],'text':'Guidelines'}
            with self.subTest(suffix=suffix),tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=lambda u,a:initial if u==start else {'url':u,'status':'readable_snapshot','links':[],'text':'Rules'}):
                records=capture_all([start],{'ids':{}},Path(folder)/'pages.json','Original observational research')
            self.assertEqual(records[1]['url'],research)
            self.assertLessEqual(len(records),13)  # one initial page, at most twelve followed

    def test_missing_xml_issn_can_be_reconciled_from_exact_article_metadata(self):
        target={'journal':'Clinical Journal','issns':[],'ids':{'doi':'10.1234/study'}}
        item={'pmcid':'PMC42','doi':'10.1234/study','journalInfo':{'journal':{'title':'Clinical journal','issn':'1234-5679','essn':'9876-5432'}}}
        attached=attach_journal_identity(target,item,'PMC42','https://example.org/metadata','2026-01-01T00:00:00Z')
        self.assertTrue(journal_match(attached,'9876-5432','Clinical journal'))
        self.assertTrue(journal_match({'journal':'Clinical Journal','issns':[]},'1234-5679','Clinical journal'))
        self.assertFalse(journal_match({'journal':'Clinical Journal','issns':[]},'1234-5679','Clinical Journal of Surgery'))
        self.assertIsNone(journal_match({'issns':[]},'1234-5679',''))
        self.assertFalse(journal_match(attached,'1111-1111','Clinical journal'))

    def test_foreign_article_metadata_cannot_change_target_outlet(self):
        target={'journal':'Clinical Journal','issns':[],'ids':{'doi':'10.1234/study'}}
        with self.assertRaisesRegex(ValueError,'allocated article'):
            attach_journal_identity(target,{'pmcid':'PMCwrong'},'PMC42','url','time')
        with self.assertRaisesRegex(ValueError,'DOI conflict'):
            attach_journal_identity(target,{'pmcid':'PMC42','doi':'10.1234/other'},'PMC42','url','time')

    def test_adjudicated_source_decision_is_not_outvoted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'corpus'/'case'
            source.mkdir(parents=True)
            (source/'answer.json').write_text(json.dumps({'issns':['known']}),encoding='utf-8')
            work=root/'runs'
            work.mkdir()
            for name,data in (('literature.json',{'papers':[]}),('generator-packet.json',{'literature':[]}),('v1-audit.json',[]),('v2-audit.json',[])):
                (work/name).write_text(json.dumps(data),encoding='utf-8')
            output={'evidence':{'journals':[],'constraints':{}},'fit_sequence':[]}
            systems={label:{'hard_failures':[],'usable_journal_ids':[]} for label in ('A','B')}
            reviews=[{'systems':systems,'paired_decision':decision} for decision in ('A','A','B')]
            ledger={'identity_map':{'A':'v1','B':'v2'}}
            r=reveal_case({'case_id':'case','split':'holdout'},root/'corpus',work,ledger,{'v1':output,'v2':output},reviews,{},None)
            self.assertEqual(r['paired_decision'],'v2')

    def test_release_requires_baselines_and_genuine_final_seals(self):
        records=[{'case_id':'synthetic-case','status':'completed','stratum':'clinical_nursing',
                  'scores':{'v1':{'true_rank':None,'usable':False},'v2':{'true_rank':None,'usable':False,'hard_failures':[]}}}]
        failures=promotion([],records,{})['failures']
        self.assertIn('Missing fixed-baseline scores',failures)
        self.assertTrue(any(x.startswith('Final artifact/reveal gate:') for x in failures))

    def test_unauthorized_license_rejected_before_model_call(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'case'
            source.mkdir()
            masked='Research methods'
            (source/'masked.txt').write_text(masked,encoding='utf-8')
            (source/'source.xml').write_text('<article><front><journal-meta/><article-meta><permissions><license>Creative Commons Attribution-Non Commercial</license></permissions></article-meta></front><body/></article>',encoding='utf-8')
            with self.assertRaisesRegex(InputEligibilityError,'license eligibility'):
                prepare_case({'case_id':'case','input_hash':hashlib.sha256(masked.encode()).hexdigest()},folder,Path(folder)/'runs','2026-10-02')

    def test_changed_manuscript_rejected_before_model_call(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'case'
            source.mkdir()
            (source/'masked.txt').write_text('altered',encoding='utf-8')
            with self.assertRaisesRegex(InputEligibilityError,'changed after allocation'):
                prepare_case({'case_id':'case','input_hash':'original-hash'},folder,Path(folder)/'runs','2026-10-02')

    def test_resume_preserves_amended_frozen_corpus(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'manifest.json'
            allocation={'seed':20261002,'as_of':'2026-10-02','protocol_revision':3,
                        'cases':[{'case_id':'kept','split':'excluded_license'}]}
            file.write_text(json.dumps(allocation),encoding='utf-8')
            (Path(folder)/'manifest.in-progress.json').write_text(json.dumps({'seed':20261002,'cases':[]}),encoding='utf-8')
            self.assertEqual(prepare(folder),allocation)
            self.assertEqual(json.loads(file.read_text(encoding='utf-8')),allocation)
            with self.assertRaises(ValueError):prepare(folder,seed=5)

    def test_license_restrictions_not_mistaken_for_plain_attribution(self):
        for text in ("Creative Commons Attribution-Non Commercial License 4.0 (CCBY-NC)",
                     "Creative Commons Attribution NoDerivs", "Creative Commons Attribution ShareAlike",
                     "https://creativecommons.org/licenses/by-nc/4.0/",
                     "https://creativecommons.org/licenses/by/4.0/ and CC BY-ND"):
            self.assertFalse(license_eligibility(text)[0])
        self.assertTrue(license_eligibility("Creative Commons Attribution License (CC BY)")[0])
        self.assertTrue(license_eligibility("https://creativecommons.org/publicdomain/zero/1.0/")[0])
        self.assertFalse(license_eligibility("Open access article, all rights reserved")[0])

    def test_license_link_inside_xml_license_is_recorded(self):
        xml='''<article xmlns:xlink="http://www.w3.org/1999/xlink"><front><journal-meta/><article-meta>
        <title-group><article-title>Study</article-title></title-group><permissions><license>
        <license-p>Licensed under <ext-link xlink:href="https://creativecommons.org/licenses/by/4.0/">CC BY</ext-link>.</license-p>
        </license></permissions></article-meta></front><body><p>Research methods</p></body></article>'''
        target,_=parse_article(xml)
        self.assertTrue(target['permitted'])
        self.assertIn('https://creativecommons.org/licenses/by/4.0/',target['license_urls'])

    def test_mask_preserves_methods_and_removes_publication(self):
        a={"title":"A Secret Paper Title","journal":"Secret Journal","ids":{"doi":"10.1234/answer"},"authors":["Ada Author"]}
        text=mask_text("A Secret Paper Title Secret Journal Ada Author 10.1234/answer randomized 70/30 split",a)
        self.assertNotIn("Secret Journal",text)
        self.assertNotIn("10.1234",text)
        self.assertIn("70/30",text)
    def test_excludes_target_not_entire_journal(self):
        answer={"title":"Randomized asthma treatment trial","ids":{"doi":"10.1234/target"}}
        self.assertTrue(excluded_paper({"doi":"10.1234/target"},answer,""))
        self.assertFalse(excluded_paper({"doi":"10.1234/another","title":"Nursing pain assessment","journal":"Same Journal"},answer,""))
    def test_target_mentions_removed_before_delivery(self):
        self.assertEqual(strip_target_mentions("Scope is clinical\nRandomized asthma treatment trial published here",{"title":"Randomized asthma treatment trial"}),"Scope is clinical")
    def test_duplicate_versions(self):
        text=" ".join("research methods patients clinical validation outcomes experiment independent cohort sample".split()*12)
        self.assertTrue(near_duplicate(fingerprint(text),fingerprint(text+" added supplement")))
    def test_host_allowlist(self):
        self.assertTrue(permitted_url("https://journals.plos.org/plosone/s/journal-information"))
        self.assertTrue(permitted_url("https://haematologica.org/about"))
        self.assertTrue(permitted_url("https://tcr.amegroups.org/about"))
        self.assertTrue(permitted_url("https://publichealth.jmir.org/about-journal/aims-and-scope"))
        self.assertFalse(permitted_url("https://publichealth.jmir.org.evil.example/about"))
        self.assertFalse(permitted_url("https://haematologica.org.evil.example/about"))
        self.assertFalse(permitted_url("http://localhost:8000/answers"))
        self.assertFalse(permitted_url("https://plos.org.evil.example/"))
        self.assertFalse(permitted_url("https://user:password@plos.org/"))
    def test_counts_not_publication_volume(self):
        paper={"journal_id":"a","title":"Asthma randomized trial","abstract":"asthma randomized treatment respiratory outcomes"}
        other={"journal_id":"b","title":"Fracture review","abstract":"bone fracture surgery"}
        ranked=fixed_baselines("asthma randomized treatment respiratory outcomes",["asthma"],[paper,copy.deepcopy(paper),other])
        self.assertEqual([r["journal_id"] for r in ranked["abstract"]],["a"])
    def test_short_lists_not_padded(self):
        self.assertEqual(fixed_baselines("asthma",["asthma"],[]),{"keyword":[],"abstract":[]})
    def test_wilson_bounds_and_missing(self):
        self.assertIsNone(wilson(0,0))
        a,b=wilson(0,50)
        self.assertAlmostEqual(a,0)
        self.assertGreater(b,0)
    def test_failed_cases_not_completed(self):
        r=summarize([{"status":"infrastructure_failed"},{"status":"completed","stratum":"x","scores":{"v2":{"true_rank":None,"usable":False}}}])
        self.assertEqual(r["completed"],1)
        self.assertEqual(r["infrastructure_failed"],1)
        self.assertEqual(r["variants"]["v2"]["n"],1)
        self.assertEqual(r["unscored"],1)
        self.assertEqual(r["strata"]["unknown"]["states"]["infrastructure_failed"],1)
    def test_repeated_review_flags_are_separate_from_affected_case_count(self):
        result=summarize([{'status':'completed','stratum':'review','scores':{'v2':{'true_rank':None,'usable':False,'hard_failures':['same claim','same claim']}}}])
        score=result['variants']['v2']
        self.assertEqual(score['hard_failures'],2)
        self.assertEqual(score['hard_failure_cases'],1)
    def test_unknown_usable_metric_is_not_claimed_negative(self):
        r=summarize([{"case_id":"x","status":"completed","stratum":"review","scores":{"keyword":{"true_rank":2,"usable":None}}}])
        self.assertEqual(r["variants"]["keyword"]["usable_known"],0)
        self.assertEqual(r["strata"]["review"]["variants"]["keyword"]["hit3"],1)
    def test_incomplete_release_refused(self):
        self.assertFalse(promotion([],[],{})["publish_allowed"])
    def test_snapshot_mutation_detected_and_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"source"
            source.mkdir()
            (source/"SKILL.md").write_text("rules",encoding="utf-8")
            target=Path(folder)/"frozen"
            freeze(source,target)
            self.assertTrue(verify(target))
            with self.assertRaises(ValueError):freeze(source,target)
            (target/"SKILL.md").write_text("changed",encoding="utf-8")
            with self.assertRaises(ValueError):verify(target)
    def test_reveal_requires_two_real_review_seals(self):
        with self.assertRaises(ValueError):
            require_reveal([{"generations":[],"reviews":[]}])
    def test_reveal_detects_changed_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"result"
            file.write_text("changed")
            artifact={"path":str(file),"output_hash":hashlib.sha256(b"original").hexdigest(),"sealed_at":"2026-01-01T00:00:00+00:00","context_id":"ctx","status":"completed","isolation":"CONTROLLED_PACKET_FRESH_CONTEXT"}
            with self.assertRaises(ValueError):
                require_reveal([{"generations":[artifact],"reviews":[artifact,artifact]}])

if __name__=="__main__":
    unittest.main()
