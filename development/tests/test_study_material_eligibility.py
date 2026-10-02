import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills/medical-journal-selector-skill-trainer/scripts'))
from corpus import study_material_eligibility, parse_article
from campaign import prepare_case, InputEligibilityError


def source(genre, title='A study', body='<p>Scientific study content.</p>', subject=''):
    return (f'<article article-type="{genre}"><front><journal-meta/><article-meta>'
            f'<title-group><article-title>{title}</article-title></title-group>'
            f'<article-categories><subj-group><subject>{subject}</subject></subj-group></article-categories>'
            '<permissions><license>Creative Commons Attribution License CC BY</license></permissions>'
            f'</article-meta></front><body>{body}</body></article>')


class FullMaterialEligibilityTests(unittest.TestCase):
    def test_long_notices_are_not_original_full_studies(self):
        for genre in ('correction', 'expression-of-concern', 'retraction', 'abstract', 'editorial', 'article-commentary'):
            with self.subTest(genre=genre):
                result = study_material_eligibility(source(genre, body='<p>'+'Long notice with scientific details. '*500+'</p>'))
                self.assertFalse(result['eligible'])
                self.assertEqual(result['source_article_type'], genre)

    def test_mistagged_notice_title_or_subject_still_stops(self):
        self.assertFalse(study_material_eligibility(source('research-article', 'Correction to: A study'))['eligible'])
        self.assertFalse(study_material_eligibility(source('research-article', subject='Expression of Concern'))['eligible'])
        self.assertTrue(study_material_eligibility(source('research-article', 'Correction factors for MRI measurements'))['eligible'])

    def test_protocols_and_valid_full_report_genres_do_not_require_results(self):
        for genre in ('research-article', 'review-article', 'systematic-review', 'case-report', 'case-study', 'brief-report', 'methods-article'):
            with self.subTest(genre=genre):
                self.assertTrue(study_material_eligibility(source(genre, 'Protocol for a clinical trial', '<sec><title>Methods</title><p>Planned enrolment.</p></sec>'))['eligible'])

    def test_absent_body_and_unknown_genre_require_preparation_review(self):
        self.assertFalse(study_material_eligibility(source('research-article', body=''))['eligible'])
        self.assertFalse(study_material_eligibility(source('unrecognised-study'))['eligible'])
        self.assertFalse(study_material_eligibility(source(''))['eligible'])

    def test_preparation_stops_before_answer_or_model_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root/'case'
            article.mkdir()
            xml = source('correction', body='<p>'+'Long correction concerning a table. '*100+'</p>')
            _, masked = parse_article(xml)
            (article/'source.xml').write_text(xml, encoding='utf-8')
            (article/'masked.txt').write_text(masked, encoding='utf-8')
            # No answer file exists; a successful guard must not need one.
            with patch('campaign.model_json') as model, patch('campaign.read') as answer_reader:
                with self.assertRaisesRegex(InputEligibilityError, 'full-material eligibility'):
                    prepare_case({'case_id':'case', 'input_hash':hashlib.sha256(masked.encode()).hexdigest()},
                                 root, root/'work', '2026-10-03')
                model.assert_not_called()
                answer_reader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
