"""Synthetic retrieval scheduling tests; no allocated papers or answers read."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from broker import capture, capture_all, plan_followed_links


def page(url,links=()):
    return {'url':url,'status':'readable_snapshot','text':'Synthetic source text',
            'links':list(links),'source_type':'official'}


class BrokerLinkPlanningTests(unittest.TestCase):
    def test_six_dossiers_keep_method_gates_and_cover_supplemental_routes_within_thirty(self):
        starts=['https://link.springer.com/journal/'+str(i)+'/aims-scope' for i in range(6)]
        methods=['https://link.springer.com/journal/'+str(i)+'/data-policy' for i in range(6)]
        optional=['https://jcr.clarivate.com/jcr-jp/journal-profile?journal=SYNTHETIC',
                  'https://www.ncbi.nlm.nih.gov/nlmcatalog/?term=SYNTHETIC',
                  'https://link.springer.com/journal/2/open-access',
                  'https://link.springer.com/journal/3/publication-fees']
        journals=[{'journal_id':f'9000-000{i}','official_urls':[u]} for i,u in enumerate(starts)]
        # Twelve genuine initial web pages plus six identity requests occupy
        # all eighteen initial slots. General policies must not crowd out
        # the concrete six data policies or the four supplemental routes.
        initial=starts+['https://link.springer.com/journal/'+str(i)+'/submission-guidelines' for i in range(6)]
        lookup={u:page(u,[methods[i%6]]+
                        ['https://link.springer.com/journal/'+str(i%6)+'/editorial-policies/policy-'+str(k) for k in range(25)]+
                        ([optional[i]] if i<4 else [])) for i,u in enumerate(initial)}
        def fake(url,answer):return lookup.get(url,page(url))
        def registry(jid):return dict(page('https://api.crossref.org/journals/'+jid),allowed_fact_fields=['identity'])
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=fake),patch('broker.capture_identity',side_effect=registry),patch('broker.time.sleep'):
            records=capture_all(initial,{'ids':{}},Path(folder)/'pages.json','Original research',journals)
        self.assertEqual(len(records),30)
        followed={p['url'] for p in records if p.get('retrieval_round')==2}
        self.assertTrue(set(methods).issubset(followed))
        self.assertTrue(set(optional).issubset(followed))
        coverage=records[0]['retrieval_attempt_coverage']['categories']
        for category in ('jcr','indexing','open_access','fees'):
            self.assertGreater(coverage[category]['attempted_count'],0)
        self.assertTrue(all(p['status']!='verified' for p in records))

    def test_fees_do_not_displace_specific_method_links_when_twelve_gates_fill_budget(self):
        starts=['https://link.springer.com/journal/'+str(i)+'/aims-scope' for i in range(6)]
        methods=[['https://link.springer.com/journal/'+str(i)+'/data-policy',
                  'https://link.springer.com/journal/'+str(i)+'/external-validation'] for i in range(6)]
        fees=['https://link.springer.com/journal/'+str(i)+'/publication-fees' for i in range(6)]
        records=[page(u,[fees[i]]+methods[i]) for i,u in enumerate(starts)]
        selected,_=plan_followed_links(records,starts,{'ids':{}},'Original research',limit=12)
        self.assertEqual({p['url'] for p in selected},{u for pair in methods for u in pair})
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=lambda u,a:next((p for p in records if p['url']==u),page(u))):
            captured=capture_all(starts,{'ids':{}},Path(folder)/'pages.json','Original research')
        fee_coverage=captured[0]['retrieval_attempt_coverage']['categories']['fees']
        self.assertEqual(fee_coverage['status'],'not_attempted')
        self.assertEqual(fee_coverage['reason'],'endpoint_budget')
        self.assertEqual(fee_coverage['failed_count'],0)

    def test_candidate_balance_prevents_one_navigation_tree_taking_all_method_slots(self):
        starts=['https://link.springer.com/journal/'+str(i)+'/aims-scope' for i in range(6)]
        journals=[{'journal_id':f'9000-000{i}','official_urls':[u]} for i,u in enumerate(starts)]
        pages=[page(u,['https://link.springer.com/journal/'+str(i)+'/data-policy/'+str(k)
                       for k in range(20 if i==0 else 1)]) for i,u in enumerate(starts)]
        selected,_=plan_followed_links(pages,starts,{'ids':{}},'Original research',journals,12)
        covered={jid for lead in selected for jid in lead['lead_for_journal_ids']}
        self.assertEqual(covered,{j['journal_id'] for j in journals})
        self.assertEqual(len(selected),12)

    def test_readable_failed_unreadable_and_blocked_transport_are_distinct(self):
        url='https://link.springer.com/journal/42/journal-metrics'
        with patch('broker.fetch_page',side_effect=RuntimeError('HTTP Error 403')):
            failed=capture(url,{'ids':{}})
        self.assertEqual(failed['retrieval_attempt']['status'],'failed')
        blocked_html=('<p>Just a moment</p><p>'+'Browser challenge '*30+'</p>').encode()
        with patch('broker.fetch_page',return_value=(blocked_html,url,'text/html')):
            unreadable=capture(url,{'ids':{}})
        self.assertEqual(unreadable['retrieval_attempt']['status'],'unreadable')
        source_html=('<p>Synthetic journal metrics '+('descriptive text '*30)+'</p>').encode()
        with patch('broker.fetch_page',return_value=(source_html,url,'text/html')):
            readable=capture(url,{'ids':{}})
        self.assertEqual(readable['retrieval_attempt']['status'],'readable_snapshot')
        self.assertEqual(readable['status'],'readable_snapshot')
        with patch('broker.fetch_page') as fetch:
            blocked=capture('https://not-an-official-source.invalid/publication-fees',{'ids':{}})
            excluded=capture(url+'?doi=10.9999/hidden-paper',{'ids':{'doi':'10.9999/hidden-paper'}})
        fetch.assert_not_called()
        self.assertEqual(blocked['retrieval_attempt']['status'],'not_attempted')
        self.assertEqual(excluded['retrieval_attempt']['status'],'not_attempted')
        self.assertNotIn('hidden-paper',json.dumps(excluded))

    def test_failure_is_reported_as_attempted_while_jcr_without_a_lead_is_not_attempted(self):
        start='https://link.springer.com/journal/42/aims-scope'
        metrics='https://link.springer.com/journal/42/journal-metrics'
        def fake(url,answer):
            return page(start,[metrics]) if url==start else {'url':url,'status':'unverified','text':'','failure':'HTTP Error 403','retrieval_attempt':{'status':'failed'}}
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=fake):
            target=Path(folder)/'pages.json'
            records=capture_all([start],{'ids':{}},target)
            saved=json.loads(target.with_suffix('.retrieval.json').read_text(encoding='utf-8'))
        self.assertEqual(saved,records[0]['retrieval_attempt_coverage'])
        coverage=saved['categories']
        self.assertEqual(coverage['journal_metrics']['status'],'attempted_without_readable_snapshot')
        self.assertEqual(coverage['journal_metrics']['failed_count'],1)
        self.assertEqual(coverage['jcr']['status'],'not_attempted')
        self.assertEqual(coverage['jcr']['reason'],'no_matching_official_lead')

    def test_canonical_duplicates_blocked_hosts_documents_and_answer_links_are_not_followed(self):
        start='https://link.springer.com/journal/42/aims-scope'
        method='https://link.springer.com/journal/42/data-policy'
        metrics='https://link.springer.com/journal/42/journal-metrics'
        links=[method+'?utm_source=x',method+'#section',metrics+'?doi=10.9999/hidden-paper',
               'https://not-an-official-source.invalid/indexing',
               'https://link.springer.com/journal/42/author-guidelines.pdf']
        selected,_=plan_followed_links([page(start,links)],[start],{'ids':{'doi':'10.9999/hidden-paper'}})
        self.assertEqual([p['url'] for p in selected],[method])

    def test_identity_registry_remains_identity_only_and_does_not_count_as_indexing(self):
        raw=json.dumps({'status':'ok','message':{'title':'Synthetic Journal','ISSN':['9000-0005'],'publisher':'Synthetic Publisher'}}).encode()
        with tempfile.TemporaryDirectory() as folder,patch('broker.get',return_value=raw):
            records=capture_all([],{'ids':{}},Path(folder)/'pages.json',identity_journals=[{'journal_id':'9000-0005'}])
        self.assertEqual(records[0]['allowed_fact_fields'],['identity'])
        coverage=records[0]['retrieval_attempt_coverage']['categories']
        self.assertEqual(coverage['identity']['attempted_count'],1)
        self.assertEqual(coverage['indexing']['attempted_count'],0)
        self.assertEqual(coverage['indexing']['status'],'not_attempted')

    def test_about_page_is_one_broad_lead_without_implying_jcr_or_field_verification(self):
        start='https://link.springer.com/journal/42/aims-scope'
        about='https://link.springer.com/journal/42/about'
        selected,_=plan_followed_links([page(start,[about])],[start],{'ids':{}})
        self.assertEqual(len(selected),1)
        self.assertEqual(set(selected[0]['lead_categories']),{'journal_metrics','indexing','open_access','fees'})
        self.assertNotIn('jcr',selected[0]['lead_categories'])


if __name__=='__main__':unittest.main()
