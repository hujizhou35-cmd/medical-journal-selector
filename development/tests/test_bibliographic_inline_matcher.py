"""Synthetic captured-source matching tests; no real papers or model calls."""
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import campaign


class BibliographicInlineMatcherTests(unittest.TestCase):
    SUPPORT = 'Using MarkerA with 7 samples.'

    def fixture(self, raw='Using <i>MarkerA</i> with 7 samples.', *, official=False, key='precedent', timeline=False):
        when = '2001-01-01T00:00:00Z'
        url = 'https://example.invalid/official' if official else 'https://example.invalid/api?q=SYNTHETIC'
        paper = {'journal_id': 'synthetic-journal', 'title': 'Synthetic title.', 'abstract': raw,
                 'record_url': 'https://example.invalid/api?q=SYNTHETIC',
                 'url': 'https://example.invalid/article/SYNTHETIC', 'checked_at': when,
                 'source_type': 'bibliographic', 'read_extent': 'Synthetic captured metadata only.'}
        ev = {'url': url, 'checked_at': when, 'source_type': 'official' if official else 'bibliographic', 'support': self.SUPPORT}
        fact = {'status': 'verified', 'evidence': [ev]}
        journal = {'id': 'synthetic-journal', 'facts': {}, 'timelines': {}, 'precedents': []}
        if key == 'precedent':
            journal['precedents'] = [fact]
        else:
            journal['timelines' if timeline else 'facts'][key] = fact
        if key == 'scope':
            fact['value'] = {'quote': self.SUPPORT}
        page = {'url': url, 'checked_at': when, 'source_type': 'official', 'status': 'readable_snapshot', 'text': raw}
        packet = {'policies': [page] if official else [], 'literature': [paper]}
        value = {'evidence': {'constraints': {}, 'journals': [journal]}, 'fit_sequence': []}
        selector = SimpleNamespace(validate=lambda evidence: [], eligibility=lambda journal, constraints: ('eligible', []))
        return value, packet, selector, ev, fact

    def audit(self, fixture):
        value, packet, selector, _, _ = fixture
        before = copy.deepcopy((value, packet))
        failures = campaign.source_audit(value, packet, selector)
        self.assertEqual((value, packet), before, 'Raw packet/evidence must remain unchanged')
        return failures

    def test_four_attribute_free_inline_tags(self):
        for tag in ('i', 'b', 'em', 'strong'):
            with self.subTest(tag=tag):
                raw = f'Using <{tag}>MarkerA</{tag}> with 7 samples.'
                self.assertTrue(campaign.bibliographic_precedent_inline_support(self.SUPPORT, [raw]))
                self.assertEqual(self.audit(self.fixture(raw)), [])

    def test_balanced_nesting_and_literal_word_boundaries(self):
        self.assertEqual(self.audit(self.fixture('Using <i><strong>MarkerA</strong></i> with 7 samples.')), [])
        self.assertFalse(campaign.bibliographic_precedent_inline_support('Using Marker A with 7 samples.',
                                                                      ['Using <i>Marker</i>A with 7 samples.']))

    def test_existing_literal_strict_path_short_circuits_fallback(self):
        fixtures = [self.fixture(self.SUPPORT), self.fixture('Using MarkerA\nwith 7 samples.'),
                    self.fixture('<script>HiddenMarker</script>')]
        fixtures[-1][3]['support'] = 'HiddenMarker'
        raw_tags = self.fixture()
        raw_tags[3]['support'] = 'Using <i>MarkerA</i> with 7 samples.'
        fixtures.append(raw_tags)
        # These are historical literal matches, not a claim of new HTML rendering.
        with patch.object(campaign, 'bibliographic_precedent_inline_support', side_effect=AssertionError('strict path should win')):
            for fixture in fixtures:
                with self.subTest(support=fixture[3]['support']):
                    self.assertEqual(self.audit(fixture), [])

    def test_changed_words_numbers_punctuation_and_missing_words_fail(self):
        for support in ('Involving MarkerA with 7 samples.', 'Using MarkerA with 8 samples.',
                        'Using MarkerA with samples.', 'Using MarkerA: with 7 samples.'):
            with self.subTest(support=support):
                fixture = self.fixture()
                fixture[3]['support'] = support
                self.assertIn('supporting passage absent', ' '.join(self.audit(fixture)))

    def test_unknown_attributes_hidden_or_invalid_markup_has_no_fallback(self):
        for raw in ('Using <span>MarkerA</span> with 7 samples.',
                    'Using <i class="x">MarkerA</i> with 7 samples.',
                    'Using <I>MarkerA</I> with 7 samples.',
                    'Using <i/>MarkerA with 7 samples.',
                    'Using <i>MarkerA with 7 samples.',
                    'Using <i><b>MarkerA</i></b> with 7 samples.',
                    'Using <i>Marker</i><sup>A</sup> with 7 samples.',
                    'Using <i>Marker</i><sub>A</sub> with 7 samples.',
                    'Using <script><i>MarkerA</i></script> with 7 samples.',
                    'Using <style><i>MarkerA</i></style> with 7 samples.',
                    'Using <!--x--><i>MarkerA</i> with 7 samples.',
                    'Using <p><i>MarkerA</i></p> with 7 samples.'):
            with self.subTest(raw=raw):
                self.assertFalse(campaign.bibliographic_precedent_inline_support(self.SUPPORT, [raw]))
                self.assertIn('supporting passage absent', ' '.join(self.audit(self.fixture(raw))))

    def test_entity_decode_and_support_markup_are_not_allowed(self):
        self.assertFalse(campaign.bibliographic_precedent_inline_support('Using MarkerA & MarkerB.',
                                                                      ['Using <i>MarkerA</i> &amp; MarkerB.']))
        fixture = self.fixture()
        fixture[3]['support'] = 'Using <b>MarkerA</b> with 7 samples.'
        self.assertIn('supporting passage absent', ' '.join(self.audit(fixture)))

    def test_new_fallback_never_joins_lines_paragraphs_or_title_abstract(self):
        for raw in ('Using <i>MarkerA</i>\nwith 7 samples.', 'Using <i>MarkerA</i>\n\nwith 7 samples.',
                    'Using <i>MarkerA</i>\u2029with 7 samples.', 'Using <i>MarkerA\n</i> with 7 samples.'):
            with self.subTest(raw=raw):
                self.assertIn('supporting passage absent', ' '.join(self.audit(self.fixture(raw))))
        fixture = self.fixture('with 7 samples.')
        fixture[1]['literature'][0]['title'] = 'Using <i>MarkerA</i>'
        self.assertIn('supporting passage absent', ' '.join(self.audit(fixture)))

    def test_visible_title_and_article_url_alias_remain_paired_with_capture(self):
        fixture = self.fixture('Unrelated abstract.')
        fixture[1]['literature'][0]['title'] = 'Using <i>MarkerA</i> with 7 samples.'
        fixture[3]['url'] = fixture[1]['literature'][0]['url']
        self.assertEqual(self.audit(fixture), [])

    def test_official_scope_policy_timeline_are_not_normalized(self):
        for key, timeline in (('scope', False), ('article_type', False), ('first_decision', True)):
            with self.subTest(key=key):
                self.assertIn('supporting passage absent', ' '.join(self.audit(self.fixture(official=True, key=key, timeline=timeline))))
        self.assertEqual(self.audit(self.fixture(self.SUPPORT, official=True, key='scope')), [])

    def test_official_scope_quote_needs_its_own_literal_support(self):
        fixture = self.fixture(self.SUPPORT, official=True, key='scope')
        fixture[4]['value']['quote'] = 'Involving MarkerA with 7 samples.'
        self.assertIn('scope quotation absent', ' '.join(self.audit(fixture)))

    def test_acquisition_timestamp_remains_exact(self):
        fixture = self.fixture()
        fixture[3]['checked_at'] = '2001-01-02T00:00:00Z'
        self.assertIn('acquisition timestamp changed', ' '.join(self.audit(fixture)))

    def test_source_classification_remains_exact(self):
        fixture = self.fixture()
        fixture[3]['source_type'] = 'official'
        self.assertIn('source classification changed', ' '.join(self.audit(fixture)))

    def test_identity_only_page_cannot_admit_precedent(self):
        fixture = self.fixture(self.SUPPORT, official=True)
        fixture[1]['policies'][0]['allowed_fact_fields'] = ['identity']
        self.assertIn('restricted to journal identity metadata', ' '.join(self.audit(fixture)))

    def test_bibliographic_match_cannot_verify_journal_fact(self):
        fixture = self.fixture(self.SUPPORT, key='article_type')
        self.assertIn('bibliographic-only record', ' '.join(self.audit(fixture)))

    def test_unknown_url_does_not_resolve_to_the_captured_source(self):
        fixture = self.fixture()
        fixture[3]['url'] = 'https://example.invalid/api?q=SYNTHETIC%28extra%29'
        self.assertIn('supporting passage absent', ' '.join(self.audit(fixture)))

    def test_undiscovered_candidate_remains_rejected(self):
        fixture = self.fixture()
        fixture[0]['evidence']['journals'][0]['id'] = 'not-discovered'
        self.assertIn('Undiscovered candidate inserted', ' '.join(self.audit(fixture)))

    def test_fit_sequence_duplicates_cap_and_pending_remain_rejected(self):
        for sequence in (['synthetic-journal', 'synthetic-journal'], list(map(str, range(11)))):
            with self.subTest(sequence=sequence):
                fixture = self.fixture()
                fixture[0]['fit_sequence'] = sequence
                self.assertIn('Fit sequence exceeds cap', ' '.join(self.audit(fixture)))
        fixture = self.fixture()
        fixture[0]['fit_sequence'] = ['synthetic-journal']
        fixture[2].eligibility = lambda journal, constraints: ('pending', [])
        self.assertIn('ineligible/pending candidate', ' '.join(self.audit(fixture)))

    def test_schema_failure_remains_returned_without_promotion(self):
        fixture = self.fixture()
        fixture[2].validate = lambda evidence: ['SYNTHETIC schema sentinel']
        self.assertEqual(self.audit(fixture), ['SYNTHETIC schema sentinel'])
        fixture = self.fixture()
        fixture[4]['status'] = 'unverified'
        fixture[3]['support'] = 'Absent words.'
        self.assertEqual(self.audit(fixture), [])
        self.assertEqual(fixture[4]['status'], 'unverified')

    def test_failed_official_capture_cannot_verify_source(self):
        fixture = self.fixture(self.SUPPORT, official=True, key='scope')
        fixture[1]['policies'][0]['status'] = 'retrieval_failed'
        self.assertIn('supporting passage absent', ' '.join(self.audit(fixture)))

    def test_numbers_and_comparison_version_are_literal(self):
        self.assertEqual(campaign.BIBLIOGRAPHIC_PRECEDENT_COMPARISON_VERSION, 'captured-inline-visible-v1')
        self.assertTrue(campaign.bibliographic_precedent_inline_support('MarkerA when x<0.05 and y>2.',
                                                                     ['<i>MarkerA</i> when x<0.05 and y>2.']))
        self.assertFalse(campaign.bibliographic_precedent_inline_support('MarkerA when x<0.5 and y>2.',
                                                                      ['<i>MarkerA</i> when x<0.05 and y>2.']))


if __name__ == '__main__':
    unittest.main()
