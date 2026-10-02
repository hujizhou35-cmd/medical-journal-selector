"""Synthetic-only final-entry and export read-order regressions; no model calls."""
import copy
from datetime import datetime,timedelta,timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'development'))
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import export_evaluation
import parallel_campaign
import runner
from corpus import STRATA
from preparation_seal import REQUIRED_FILES,seal_preparation
from review_bundle import CONTRACT,LABELS,seal_review_bundles


def write(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')


def model_artifact(work,name,variant,context,start,end,payload,prompt='Synthetic controlled request'):
    path=Path(work)/name
    text=json.dumps(payload)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')
    output_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    # runner.run writes the exact UTF-8 packet bytes, without Windows newline
    # translation. A text-mode fixture would hash LF but store CRLF.
    (work/(name+'.input.txt')).write_bytes(prompt.encode('utf-8'))
    input_hash=runner.digest(prompt.encode()+runner.MODEL.encode()+runner.EFFORT.encode()+b'controlled-packet-env-closed-tools-disabled-v3')
    record={'status':'completed','context_id':context,'started_at':start,'completed_at':end,
            'output_hash':output_hash,'input_hash':input_hash,
            'model':runner.MODEL,'effort':runner.EFFORT,'terminal_output_matches':True,
            'isolation':'CONTROLLED_PACKET_FRESH_CONTEXT','usage':{'output_tokens':1}}
    write(work/(name+'.record.json'),record)
    events=[{'type':'thread.started','thread_id':context},
            {'type':'item.completed','item':{'type':'agent_message','text':text}},
            {'type':'turn.completed','usage':record['usage']}]
    (work/(name+'.events.jsonl')).write_text('\n'.join(json.dumps(event) for event in events),encoding='utf-8')
    return {'path':str(path.resolve()),'variant':variant,'context_id':context,
            'output_hash':output_hash,'sealed_at':end,'status':'completed',
            'model':runner.MODEL,'effort':runner.EFFORT,'isolation':record['isolation']}


def allocated_case(corpus,case_id,stratum,split):
    source=corpus/case_id
    source.mkdir(parents=True)
    masked='Synthetic independently allocated manuscript '+case_id
    (source/'masked.txt').write_text(masked,encoding='utf-8')
    (source/'source.xml').write_text('<article>Synthetic research '+case_id+'</article>',encoding='utf-8')
    write(source/'answer.json',{'journal':'Synthetic hidden outlet '+case_id,'license_urls':[],
                              'permission_basis':'synthetic fixture'})
    return {'case_id':case_id,'stratum':stratum,'split':split,
            'input_hash':hashlib.sha256(masked.encode()).hexdigest(),'pmcid':'SYNTHETIC-'+case_id,
            'license':'Synthetic CC BY'}


class FinalEntrySafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temporary.name)
        cls.corpus=cls.root/'corpus'
        cls.development=cls.root/'development'
        cls.final=cls.root/'final'
        cls.dev_cases=[]
        cls.final_cases=[]
        cls.now=datetime.now(timezone.utc)
        cls.old=(cls.now-timedelta(days=2)).replace(microsecond=0)
        cls.future=(cls.now+timedelta(days=2)).replace(microsecond=0)
        for index in range(100):
            case_id='synthetic-dev-'+str(index+1).zfill(3)
            case=allocated_case(cls.corpus,case_id,list(STRATA)[index//10],'development')
            cls.dev_cases.append(case)
            work=cls.development/case_id
            generations=[model_artifact(work,'v2-selection.json','v2',case_id+'-generator',
                                        cls.when(cls.old,0),cls.when(cls.old,1),{'evidence':{'journals':[]}})]
            reviews=[model_artifact(work,'review-'+str(i)+'.json','blind_review',case_id+'-review-'+str(i),
                                   cls.when(cls.old,2),cls.when(cls.old,2+i),{'systems':{},'paired_decision':'single'}) for i in (1,2)]
            diagnosis={'diagnosis':[],'hypotheses':[],'no_change_reason':'Synthetic no-change decision',
                       'stratum_confirmed':True,'classification_reason':'Synthetic objective'}
            lesson=model_artifact(work,'lesson.json','post_reveal_diagnosis',case_id+'-lesson',
                                  cls.when(cls.old,6),cls.when(cls.old,7),diagnosis)
            ledger={'case_id':case_id,'stratum':case['stratum'],'split':'development','status':'completed',
                    'lesson_status':'completed','masked_input_hash':case['input_hash'],'license_recorded':True,
                    'protocol_hashes':{'campaign.py':'synthetic-legacy-protocol'},'generations':generations,
                    'reviews':reviews,'lesson_record':lesson,'diagnosis':diagnosis,
                    'revealed_at':cls.when(cls.old,5),'completed_at':cls.when(cls.old,9),
                    'changes':[{'decision':'no_change','reason':'Synthetic existing rules sufficient',
                                'at':cls.when(cls.old,8),'files':[]}],
                    'scores':{label:{'true_rank':None,'usable':False,'hard_failures':[]}
                              for label in ('v2','keyword','abstract')}}
            write(work/'ledger.json',ledger)
        for index in range(50):
            case_id='synthetic-final-'+str(index+1).zfill(3)
            case=allocated_case(cls.corpus,case_id,list(STRATA)[index//5],'holdout')
            cls.final_cases.append(case)
            work=cls.final/case_id
            work.mkdir(parents=True)
            for name in REQUIRED_FILES:
                if not name.endswith(('.record.json','.events.jsonl','.input.txt')):
                    write(work/name,{})
            write(work/'generator-packet.json',{'started_at':cls.when(cls.old,0),'policies':[],
                                              'retrieval_records':[],'literature':[]})
            write(work/'fixed-baselines.json',{'keyword':[],'abstract':[]})
            for name in ('profile.json','source-plan.json'):
                model_artifact(work,name,'preparation',case_id+'-'+name,
                               cls.when(cls.old,0),cls.when(cls.old,1),{},prompt='Synthetic preparation packet')
                (work/(name+'.input.txt')).write_text('Synthetic preparation packet',encoding='utf-8')
            binding=seal_preparation(work,cls.corpus/case_id,case_id,expected_masked_hash=case['input_hash'])
            generations=[]
            for variant in ('v1','v2'):
                now=datetime.now(timezone.utc).isoformat()
                generations.append(model_artifact(work,variant+'-selection.json',variant,case_id+'-'+variant,
                                                   now,now,{'evidence':{'journals':[]}}))
            packet=json.loads((work/'generator-packet.json').read_text(encoding='utf-8'))
            baseline=json.loads((work/'fixed-baselines.json').read_text(encoding='utf-8'))
            outputs={variant:json.loads((work/(variant+'-selection.json')).read_text(encoding='utf-8')) for variant in ('v1','v2')}
            bundle_binding,bundle_entries=seal_review_bundles(work,case_id,packet,baseline,outputs,binding)
            reviews=[]
            for i in (1,2):
                payload=json.loads((work/f'review-{i}.bundle.json').read_text(encoding='utf-8'))
                review={'systems':{label:{'hard_failures':[],'usable_journal_ids':[],
                                         'quality_notes':['Synthetic empty result has no evidenced usable candidate.'],
                                         'ranking_assessment':{'judgment':'empty','reason':'Synthetic result has no ranked candidates.','sources':[]}}
                                   for label in LABELS},
                        'pairwise_decisions':[{'left':left,'right':right,'decision':'tie','reason':'Synthetic comparison'}
                                              for left,right in itertools.combinations(LABELS,2)]}
                prompt=('Synthetic blind review\n'+json.dumps(payload,ensure_ascii=False)+
                        '\nShared source packet\n'+json.dumps(packet,ensure_ascii=False))
                now=datetime.now(timezone.utc).isoformat()
                reviews.append(model_artifact(work,f'review-{i}.json','blind_review',case_id+f'-review-{i}',
                                               now,now,review,prompt=prompt))
            ledger={'case_id':case_id,'stratum':case['stratum'],'split':'holdout','status':'completed',
                    'masked_input_hash':case['input_hash'],'generations':generations,'reviews':reviews,
                    'preparation_seal':binding,'revealed_at':cls.when(cls.future,8),'changes':[],
                    'review_bundle_seal':bundle_binding,'review_bundles':bundle_entries,'review_bundle_contract':CONTRACT,
                    'protocol_hashes':{'campaign.py':'synthetic-final-protocol'},
                    'skill_hashes':{'v1':'synthetic-frozen-v1','v2':'synthetic-frozen-v2'},'paired_decision':'tie',
                    'scores':{label:{'true_rank':None,'usable':False,'hard_failures':[]}
                              for label in ('v1','v2','keyword','abstract')}}
            write(work/'ledger.json',ledger)
        cls.manifest={'status':'input_allocation_frozen','seed':17,'as_of':'2026-10-03',
                      'cases':cls.dev_cases+cls.final_cases}
        write(cls.corpus/'manifest.json',cls.manifest)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    @staticmethod
    def when(start,seconds):return (start+timedelta(seconds=seconds)).isoformat()

    def alter(self,path,value):
        path=Path(path)
        old=path.read_bytes()
        self.addCleanup(path.write_bytes,old)
        write(path,value)

    def read_json(self,path):return json.loads(Path(path).read_text(encoding='utf-8'))

    def run_export(self):
        output=self.root/(self.id().split('.')[-1]+'.json')
        return export_evaluation.export(self.corpus,self.development,self.final,output,{})

    def spy_export_read(self):
        actual=export_evaluation.read
        opened=[]
        def recording(path):
            opened.append(Path(path))
            return actual(path)
        return opened,recording

    def test_final_entry_requires_explicit_development_root_before_any_input_access(self):
        with patch('parallel_campaign.read') as read,patch('parallel_campaign.FrozenInputs') as frozen:
            for action in (parallel_campaign.run_campaign,parallel_campaign.reveal_final):
                with self.subTest(action=action.__name__),self.assertRaisesRegex(ValueError,'development-runs'):
                    action('not-opened-corpus','not-created-runs','unused-trainer',{'v1':'a','v2':'b'},None,
                           '2026-10-03','unused-epoch',**({'split':'holdout'} if action is parallel_campaign.run_campaign else {}))
            read.assert_not_called()
            frozen.assert_not_called()

    def test_fake_summary_cannot_start_final_or_open_holdout_material(self):
        first=self.development/self.dev_cases[0]['case_id']/'ledger.json'
        ledger=self.read_json(first)
        ledger['lesson_status']='change_review_pending'
        self.alter(first,ledger)
        summary=self.development/'run-summary.json'
        write(summary,{'completed':100})
        self.addCleanup(summary.unlink)
        with patch('parallel_campaign.FrozenInputs') as frozen,patch('parallel_campaign.campaign.execute') as execute:
            with self.assertRaisesRegex(ValueError,'not genuinely decided'):
                parallel_campaign.run_campaign(self.corpus,self.final,'unused',{'v1':'a','v2':'b'},None,
                                               '2026-10-03','unused',split='holdout',development_runs=self.development)
        frozen.assert_not_called()
        execute.assert_not_called()

    def test_hundred_real_decisions_keep_nonhits_and_disclose_legacy_boundary(self):
        before={case['case_id']:(self.development/case['case_id']/'ledger.json').read_bytes() for case in self.dev_cases}
        gate=parallel_campaign.require_development_complete(self.corpus,self.development)
        self.assertEqual(gate['status'],'passed')
        self.assertEqual(gate['allocated_cases'],100)
        self.assertEqual(len(gate['legacy_preparation_cases']),100)
        for case in self.dev_cases:
            path=self.development/case['case_id']/'ledger.json'
            self.assertEqual(path.read_bytes(),before[case['case_id']])
            self.assertIsNone(self.read_json(path)['scores']['v2']['true_rank'])

    def test_protocol_pilots_cannot_supply_missing_development_cases(self):
        manifest=copy.deepcopy(self.manifest)
        manifest['cases'][0]['split']='protocol_pilot'
        self.alter(self.corpus/'manifest.json',manifest)
        with self.assertRaisesRegex(ValueError,'exactly 100'):
            parallel_campaign.require_development_complete(self.corpus,self.development)

    def test_duplicate_allocation_or_wrong_stratum_cannot_fake_one_hundred(self):
        for defect in ('duplicate','stratum'):
            with self.subTest(defect=defect):
                manifest=copy.deepcopy(self.manifest)
                if defect=='duplicate':manifest['cases'][0]=copy.deepcopy(manifest['cases'][1])
                else:manifest['cases'][0]['stratum']='laboratory'
                original=(self.corpus/'manifest.json').read_bytes()
                write(self.corpus/'manifest.json',manifest)
                try:
                    with self.assertRaises(ValueError):parallel_campaign.require_development_complete(self.corpus,self.development)
                finally:(self.corpus/'manifest.json').write_bytes(original)

    def test_development_completed_flags_cannot_bypass_sealed_artifact_or_real_events(self):
        work=self.development/self.dev_cases[0]['case_id']
        events=work/'v2-selection.json.events.jsonl'
        raw=events.read_bytes()
        self.addCleanup(events.write_bytes,raw)
        events.write_text(json.dumps({'type':'turn.failed'}),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'terminal context'):
            parallel_campaign.require_development_complete(self.corpus,self.development)

    def test_development_receipt_and_decision_tamper_are_rejected(self):
        path=self.development/self.dev_cases[0]['case_id']/'ledger.json'
        original=path.read_bytes()
        for defect in ('receipt_context','no_decision','early_decision','missing_new_preparation'):
            with self.subTest(defect=defect):
                value=json.loads(original)
                if defect=='receipt_context':value['generations'][0]['context_id']='forged-ledger-context'
                elif defect=='no_decision':value['changes']=[]
                elif defect=='early_decision':value['changes'][0]['at']=self.when(self.old,0)
                else:value['protocol_hashes']['preparation_seal.py']='new-protocol-needs-preparation'
                write(path,value)
                try:
                    with self.assertRaises(ValueError):parallel_campaign.require_development_complete(self.corpus,self.development)
                finally:path.write_bytes(original)

    def test_diagnosis_start_before_reveal_cannot_be_hidden_by_later_seal(self):
        work=self.development/self.dev_cases[0]['case_id']
        receipt=work/'lesson.json.record.json'
        value=self.read_json(receipt)
        value['started_at']=self.when(self.old,4)
        self.alter(receipt,value)
        with self.assertRaisesRegex(ValueError,'diagnosis began or was sealed before reveal'):
            parallel_campaign.require_development_complete(self.corpus,self.development)

    def test_export_checks_last_final_review_before_first_answer_read(self):
        path=self.final/self.final_cases[-1]['case_id']/'ledger.json'
        ledger=self.read_json(path)
        ledger['reviews']=ledger['reviews'][:1]
        self.alter(path,ledger)
        opened,recording=self.spy_export_read()
        with patch('export_evaluation.read',side_effect=recording),self.assertRaisesRegex(ValueError,'two blind review'):
            self.run_export()
        self.assertFalse(any(path.name=='answer.json' for path in opened))

    def test_export_checks_last_preparation_baseline_before_first_answer_read(self):
        path=self.final/self.final_cases[-1]['case_id']/'fixed-baselines.json'
        self.alter(path,{'keyword':['post-seal-forged-candidate']})
        opened,recording=self.spy_export_read()
        with patch('export_evaluation.read',side_effect=recording),self.assertRaisesRegex(ValueError,'pinned input changed'):
            self.run_export()
        self.assertFalse(any(path.name=='answer.json' for path in opened))

    def test_export_checks_last_four_comparator_private_map_before_first_answer_read(self):
        path=self.final/self.final_cases[-1]['case_id']/'review-2.identity-map.json'
        self.alter(path,{'label_to_comparator':{'A':'v1','B':'v1','C':'keyword','D':'abstract'}})
        opened,recording=self.spy_export_read()
        with patch('export_evaluation.read',side_effect=recording),self.assertRaisesRegex(ValueError,'Review bundle file changed'):
            self.run_export()
        self.assertFalse(any(path.name=='answer.json' for path in opened))

    def test_whole_final_preparation_and_development_gates_pass_before_answer_read(self):
        markers=[]
        actual_prepare=export_evaluation.require_final_preparation
        actual_development=export_evaluation.require_development_complete
        actual_bundles=export_evaluation.require_final_review_bundles
        actual_read=export_evaluation.read
        def preparation(*args,**kwargs):
            result=actual_prepare(*args,**kwargs)
            markers.append('all50_prepared')
            return result
        def development(*args,**kwargs):
            result=actual_development(*args,**kwargs)
            markers.append('all100_decided')
            return result
        def bundles(*args,**kwargs):
            result=actual_bundles(*args,**kwargs)
            markers.append('all4_blind_reviewed')
            return result
        def reading(path):
            if Path(path).name=='answer.json':
                self.assertEqual(markers[:3],['all50_prepared','all4_blind_reviewed','all100_decided'])
                markers.append('answer_read')
            return actual_read(path)
        with patch('export_evaluation.require_final_preparation',side_effect=preparation), \
             patch('export_evaluation.require_development_complete',side_effect=development), \
             patch('export_evaluation.require_final_review_bundles',side_effect=bundles), \
             patch('export_evaluation.read',side_effect=reading):
            result=self.run_export()
        self.assertEqual(result['export_schema_version'],2)
        self.assertEqual(result['final_preparation_gate']['status'],'passed')
        self.assertEqual(result['development_completion_gate']['allocated_cases'],100)
        self.assertEqual(result['completed_development'],100)
        self.assertEqual(result['completed_final'],50)
        self.assertEqual(markers.count('answer_read'),150)
        self.assertFalse(result['final_gate']['publish_allowed'])

    def test_unrevealed_or_absent_final_does_not_block_development_progress_or_read_final_answers(self):
        for case in self.final_cases:
            path=self.final/case['case_id']/'ledger.json'
            ledger=self.read_json(path)
            ledger.pop('revealed_at')
            ledger['status']='reviewed'
            self.alter(path,ledger)
        opened,recording=self.spy_export_read()
        with patch('export_evaluation.read',side_effect=recording), \
             patch('export_evaluation.require_final_preparation') as final_gate:
            result=self.run_export()
        final_gate.assert_not_called()
        self.assertEqual(result['final_preparation_gate']['status'],'not_revealed')
        self.assertFalse(any(path.name=='answer.json' and path.parent.name.startswith('synthetic-final') for path in opened))
        final_entries=[entry for entry in result['cases'] if entry['split']=='holdout']
        self.assertTrue(all('pmcid' not in entry and 'original_outlet' not in entry for entry in final_entries))
        result=export_evaluation.export(self.corpus,self.development,None,self.root/'dev-only.json',{})
        self.assertEqual(result['completed_development'],100)
        self.assertEqual(result['completed_final'],0)


class FastFinalEntryGuardTests(unittest.TestCase):
    def test_wrong_holdout_count_or_stratum_fails_before_any_case_material_read(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus=Path(folder)/'corpus'
            development=[{'case_id':'synthetic-dev-'+str(index).zfill(3),'stratum':list(STRATA)[index//10],
                          'split':'development','input_hash':'dev-hash-'+str(index)} for index in range(100)]
            holdout=[{'case_id':'synthetic-final-'+str(index).zfill(3),'stratum':list(STRATA)[index//5],
                      'split':'holdout','input_hash':'final-hash-'+str(index)} for index in range(50)]
            for invalid in (holdout[:-1],[dict(case,stratum=list(STRATA)[0]) for case in holdout]):
                write(corpus/'manifest.json',{'status':'input_allocation_frozen','cases':development+invalid})
                with self.assertRaisesRegex(ValueError,'fifty distinct holdout cases'):
                    parallel_campaign.require_development_complete(corpus,Path(folder)/'development')

    def test_cross_split_manuscript_duplicate_fails_before_any_case_material_read(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus=Path(folder)/'corpus'
            development=[{'case_id':'synthetic-dev-'+str(index).zfill(3),'stratum':list(STRATA)[index//10],
                          'split':'development','input_hash':'dev-hash-'+str(index)} for index in range(100)]
            holdout=[{'case_id':'synthetic-final-'+str(index).zfill(3),'stratum':list(STRATA)[index//5],
                      'split':'holdout','input_hash':'final-hash-'+str(index)} for index in range(50)]
            holdout[0]['input_hash']=development[0]['input_hash']
            write(corpus/'manifest.json',{'status':'input_allocation_frozen','cases':development+holdout})
            with self.assertRaisesRegex(ValueError,'distinct manuscripts and case IDs'):
                parallel_campaign.require_development_complete(corpus,Path(folder)/'development')

    def test_duplicate_manuscript_hash_is_rejected_before_any_case_material_read(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus=Path(folder)/'corpus'
            cases=[{'case_id':'synthetic-'+str(index).zfill(3),'stratum':list(STRATA)[index//10],
                    'split':'development','input_hash':'unique-synthetic-hash-'+str(index)} for index in range(100)]
            cases[0]['input_hash']=cases[1]['input_hash']
            write(corpus/'manifest.json',{'status':'input_allocation_frozen','cases':cases})
            # No case material or ledgers exist. This fails on allocation
            # duplication, rather than opening anything in a holdout directory.
            with self.assertRaisesRegex(ValueError,'duplicate the same masked manuscript'):
                parallel_campaign.require_development_complete(corpus,Path(folder)/'development')

    def test_final_artifact_model_metadata_must_match_actual_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            work=Path(folder)/'synthetic-final'
            start='2026-10-02T00:00:00+00:00'
            end='2026-10-02T00:01:00+00:00'
            artifact=model_artifact(work,'v2-selection.json','v2','synthetic-context',start,end,{})
            artifact['model']='forged-model-label'
            with self.assertRaisesRegex(ValueError,'actual receipt: model'):
                parallel_campaign.verify_completed_artifact(artifact,work)


if __name__=='__main__':unittest.main()
