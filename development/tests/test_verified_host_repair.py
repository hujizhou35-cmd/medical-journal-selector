"""Source-host repair keeps policy content and answer-isolation gates intact."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from broker import permitted_url,capture,OfficialRedirect


class VerifiedHostRepairTests(unittest.TestCase):
    def test_verified_journal_hosts_and_explicit_migration_routes(self):
        for host in ('www.cureus.com','westjem.com','www.egms.de',
                     'journals.publisso.de','journalpub.escholarship.org'):
            with self.subTest(host=host):
                self.assertTrue(permitted_url('https://'+host+'/author-guide'))

    def test_deceptive_hosts_credentials_and_ports_remain_rejected(self):
        for url in ('https://cureus.com.example.org/about',
                    'https://evilcureus.com/about','https://notwestjem.com/',
                    'https://egms.de@evil.example/', 'https://cureus.com:8443/',
                    'http://westjem.com/about','https://unverified.publisso.de/',
                    'https://other.escholarship.org/'):
            with self.subTest(url=url):
                self.assertFalse(permitted_url(url))

    def test_admitted_host_does_not_make_unreadable_content_verified(self):
        with patch('broker.fetch_page',return_value=(b'<html>Forbidden</html>',
                   'https://www.cureus.com/author_guide','text/html')):
            item=capture('https://www.cureus.com/author_guide',{})
        self.assertEqual(item['status'],'unverified')
        self.assertEqual(item['retrieval_attempt']['status'],'unreadable')

    def test_own_study_link_on_new_host_is_not_fetched(self):
        answer={'study_registration_ids':['NCT01234567']}
        with patch('broker.fetch_page') as fetch:
            item=capture('https://westjem.com/about?study=NCT01234567',answer)
        fetch.assert_not_called()
        self.assertEqual(item['retrieval_attempt']['status'],'not_attempted')

    def test_protected_redirect_and_unverified_platform_stay_blocked(self):
        handler=OfficialRedirect({'study_registration_ids':['NCT01234567']})
        req=Request('https://www.egms.de/en/journals/oc/')
        for url in ('https://journals.publisso.de/?trial=NCT01234567',
                    'https://unverified.publisso.de/author-guide'):
            with self.subTest(url=url),self.assertRaises(ValueError):
                handler.redirect_request(req,None,302,'Found',{},url)

    def test_verified_migration_is_allowed_without_relaxing_identity_binding(self):
        req=Request('https://www.egms.de/en/journals/oc/')
        redirect=OfficialRedirect().redirect_request(req,None,302,'Found',{},
                      'https://journals.publisso.de/en/journals/oc/')
        self.assertEqual(redirect.full_url,'https://journals.publisso.de/en/journals/oc/')


if __name__=='__main__':unittest.main()
