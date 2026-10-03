"""Formatting differences in publication author credits cannot reveal authors."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from corpus import mask_text,parse_article


class AuthorFormatMaskingTests(unittest.TestCase):
    def test_initial_dots_commas_and_multispace_variants_are_masked(self):
        target={'authors':['Taylor J Sample','Sample Taylor J']}
        for author in ('Taylor J. Sample','Taylor  J Sample','Sample, Taylor J.',
                       'TAYLOR J. SAMPLE','Taylor\nJ.\tSample'):
            with self.subTest(author=author):
                result=mask_text('Concept and design: '+author+'.',target)
                self.assertNotIn('Sample',result)
                self.assertIn('[masked publication metadata]',result)

    def test_surname_alone_and_biomedical_words_are_preserved(self):
        target={'authors':['Taylor J Sample'],'journal':'Blood'}
        text='Sample collection measured blood cells. A prior study by Taylor differs.'
        self.assertEqual(mask_text(text,target),text)

    def test_token_boundaries_do_not_mask_longer_unrelated_names(self):
        target={'authors':['Taylor J Sample']}
        self.assertEqual(mask_text('Taylor J Sampleson',target),'Taylor J Sampleson')

    def test_inline_credit_format_is_hidden_and_scientific_declarations_remain(self):
        xml=b'''<article><front><journal-meta><journal-title-group><journal-title>Example Journal</journal-title></journal-title-group></journal-meta><article-meta><title-group><article-title>Example study</article-title></title-group><contrib-group><contrib><name><surname>Sample</surname><given-names>Taylor J</given-names></name></contrib></contrib-group><permissions><license>CC BY 4.0</license></permissions></article-meta></front><body><sec><title>Results</title><p>A clinical observation was recorded.</p></sec></body><back><sec><title>Additional information</title><p><bold>Concept and design:</bold> Taylor J. Sample</p><p><bold>Ethics and consent:</bold> Written informed consent was obtained.</p><p><bold>Data availability:</bold> Summary data are available on request.</p></sec></back></article>'''
        _,text=parse_article(xml)
        self.assertNotIn('Taylor',text)
        self.assertNotIn('Sample',text)
        self.assertIn('Written informed consent was obtained.',text)
        self.assertIn('Summary data are available on request.',text)


if __name__=='__main__':unittest.main()
