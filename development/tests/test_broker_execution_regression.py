"""Generic source execution regressions using synthetic journals and pages."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from broker import capture, capture_all, link_targets, plan_followed_links


def page(url,links=(),metadata=()):
    return {'url':url,'status':'readable_snapshot','text':'Synthetic substantive source',
            'links':list(links),'link_metadata':list(metadata)}


class BrokerExecutionRegressionTests(unittest.TestCase):
    def test_publisher_about_navigation_is_not_a_metric_fee_or_indexing_dossier(self):
        utility=['https://www.frontiersin.org/about/'+slug for slug in
                 ('awards','contact','accessibility-statement','annual-reports','frontiers-planet-prize','leadership','history')]
        for url in utility:
            with self.subTest(url=url):self.assertEqual(link_targets(url)[0],[])
        self.assertEqual(link_targets('https://www.frontiersin.org/about/fee-policy')[0],['fees'])
        self.assertEqual(link_targets('https://www.frontiersin.org/about/collaboration-indexation')[0],['indexing'])
        journal='https://www.frontiersin.org/journals/synthetic-health/about'
        self.assertEqual(set(link_targets(journal)[0]),{'fees','indexing','journal_metrics','open_access'})

    def test_authentication_redirect_query_is_not_a_policy_or_about_lead(self):
        url='https://idp.springer.com/auth/personal/provider?redirect_uri=https%3A%2F%2Flink.springer.com%2Fjournal%2F42%2Fsubmission-guidelines'
        self.assertEqual(link_targets(url)[0],[])
        start='https://link.springer.com/journal/42/aims-scope'
        selected,_=plan_followed_links([page(start,[url])],[start],{'ids':{}})
        self.assertEqual(selected,[])
        self.assertEqual(link_targets('https://link.springer.com/utility?redirect_uri=/journal/42/about')[0],[])

    def test_article_listing_pagination_and_other_journal_menu_do_not_consume_follow_budget(self):
        start='https://www.frontiersin.org/journals/synthetic-health/about'
        own='https://www.frontiersin.org/journals/synthetic-health'
        policy='https://www.frontiersin.org/guidelines/policies-and-publication-ethics'
        links=['https://www.frontiersin.org/journals/other-'+str(i) for i in range(90)]+[own,policy]
        selected,_=plan_followed_links([page(start,links)],[start],{'ids':{}})
        self.assertEqual({p['url'] for p in selected},{own,policy})
        for url in ('https://www.nature.com/synthetic/research-articles',
                    'https://www.nature.com/synthetic/research-articles?page=2&sort=PubDate',
                    'https://link.springer.com/journal/42/submission-guidelines?page=2'):
            self.assertEqual(link_targets(url)[0],[])
        self.assertTrue(link_targets('https://link.springer.com/journal/42/submission-guidelines/research-article','Original research')[1])
        self.assertIn('method_policy',link_targets('https://www.sciencedirect.com/journal/synthetic/publish/guide-for-authors')[0])

    def test_client_challenge_and_human_check_are_unreadable_but_css_notice_is_not(self):
        url='https://www.springernature.com/gp/authors/research-data-policy/data-policy-faqs'
        challenge='Client Challenge\nA required part of this site couldn’t load. This may be due to a browser extension, network issues, or browser settings. Please check your connection, disable any ad blockers, or try using a different browser.'
        for text in (challenge,'Security verification\n'+('Verify that you are human. '*20)):
            with self.subTest(text=text[:30]),patch('broker.fetch_page',return_value=(('<p>'+text+'</p>').encode(),url,'text/html')):
                result=capture(url,{'ids':{}})
            self.assertEqual(result['status'],'unverified')
            self.assertEqual(result['retrieval_attempt']['status'],'unreadable')
            self.assertEqual(result['text'],'')
        substantive='Journal guidelines\nThank you for visiting. We display this site without styles and JavaScript.\n'+('Original research requires data availability and ethics approval. '*20)
        with patch('broker.fetch_page',return_value=(('<p>'+substantive+'</p>').encode(),url,'text/html')):
            result=capture(url,{'ids':{}})
        self.assertEqual(result['status'],'readable_snapshot')
        self.assertIn('Original research',result['text'])

    def test_captured_anchor_label_finds_a_real_metric_route_without_using_redirect_parameters(self):
        start='https://link.springer.com/journal/42/aims-scope'
        destination='https://link.springer.com/journal/42/performance'
        html=('<p>'+('Substantive scope text. '*20)+'</p><a href="'+destination+'">Journal metrics and time to acceptance</a>').encode()
        with patch('broker.fetch_page',return_value=(html,start,'text/html')):
            source=capture(start,{'ids':{}})
        selected,_=plan_followed_links([source],[start],{'ids':{}})
        self.assertEqual([p['url'] for p in selected],[destination])
        self.assertEqual(set(selected[0]['lead_categories']),{'acceptance_time','journal_metrics'})

    def test_metric_page_revealed_jcr_and_timing_links_use_remaining_follow_budget(self):
        start='https://link.springer.com/journal/42/aims-scope'
        methods=['https://link.springer.com/journal/42/data-policy/'+str(i) for i in range(5)]
        general=['https://link.springer.com/journal/42/editorial-policies/'+str(i) for i in range(3)]
        fees=['https://link.springer.com/journal/42/publication-fees/'+str(i) for i in range(4)]
        metrics='https://link.springer.com/journal/42'
        jcr='https://jcr.clarivate.com/journal-profile/SYNTHETIC'
        timing='https://link.springer.com/journal/42/publishing-times'
        indexing='https://www.ncbi.nlm.nih.gov/nlmcatalog/?term=SYNTHETIC'
        lookup={start:page(start,methods+general+fees+[metrics]),metrics:page(metrics,[jcr,timing,indexing])}
        requested=[]
        def fake(url,answer):
            requested.append(url)
            return lookup.get(url,page(url))
        with tempfile.TemporaryDirectory() as folder,patch('broker.capture',side_effect=fake):
            records=capture_all([start],{'ids':{}},Path(folder)/'pages.json','Original research')
        self.assertIn(jcr,requested)
        self.assertIn(timing,requested)
        self.assertIn(indexing,requested)
        self.assertEqual(sum(p.get('retrieval_round')==2 for p in records),12)
        self.assertLessEqual(len(records),30)
        self.assertEqual(len(requested),len(set(requested)))
        self.assertTrue(set(methods).issubset(requested))
        self.assertGreater(next(p for p in records if p['url']==jcr)['retrieval_hop'],2)
        coverage=records[0]['retrieval_attempt_coverage']['categories']
        self.assertEqual(coverage['jcr']['attempted_count'],1)
        self.assertGreater(coverage['acceptance_time']['attempted_count'],0)
        self.assertTrue(all(p['status']!='verified' for p in records))


if __name__=='__main__':unittest.main()
