"""JATS floated text is part of full scientific input, not fetched imagery."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from corpus import parse_article

BASE='''<article><front><journal-meta><journal-title-group><journal-title>Example Journal</journal-title></journal-title-group></journal-meta><article-meta><title-group><article-title>Example study</article-title></title-group><permissions><license>CC BY 4.0</license></permissions></article-meta></front><body><sec><title>Results</title><p>The readable scientific results refer to Table 1.</p></sec></body>{}</article>'''


class FloatedResearchTextTests(unittest.TestCase):
    def test_nested_group_partial_overlap_preserves_group_caption_and_new_item(self):
        first='<fig id="f1"><caption><p>Repeated scientific figure caption.</p></caption></fig>'
        second='<fig id="f2"><caption><p>New scientific figure caption.</p></caption></fig>'
        for group in ('fig-group','table-wrap-group'):
            with self.subTest(group=group):
                floated='<floats-group><'+group+'><caption><p>Distinct group caption.</p></caption>'+first+second+'</'+group+'></floats-group>'
                xml=BASE.format(floated).replace('</body>',first+'</body>')
                _,text=parse_article(xml.encode())
                self.assertEqual(text.count('Repeated scientific figure caption.'),1)
                self.assertEqual(text.count('New scientific figure caption.'),1)
                self.assertIn('Distinct group caption.',text)

    def test_partial_group_overlap_does_not_duplicate_inline_table(self):
        first='<table-wrap id="t1"><caption><p>Unique baseline table caption.</p></caption><table><tr><td>Baseline</td><td>74</td></tr></table></table-wrap>'
        second='<table-wrap id="t2"><caption><p>Unique validation table caption.</p></caption><table><tr><td>Validation</td><td>22</td></tr></table></table-wrap>'
        xml=BASE.format('<floats-group>'+first+second+'</floats-group>').replace('</body>',first+'</body>')
        _,text=parse_article(xml.encode())
        self.assertEqual(text.count('Unique baseline table caption.'),1)
        self.assertEqual(text.count('Unique validation table caption.'),1)

    def test_external_table_body_and_caption_are_supplied(self):
        floated='''<floats-group><table-wrap id="tab1"><label>Table 1</label><caption><p>Geographic evidence inventory.</p></caption><table><tr><td>North</td><td>24</td></tr><tr><td>South</td><td>18</td></tr></table></table-wrap></floats-group>'''
        _,text=parse_article(BASE.format(floated).encode())
        for value in ('Geographic evidence inventory.','North','24','South','18'):
            self.assertIn(value,text)

    def test_figure_caption_supplied_without_graphic_url(self):
        floated='''<floats-group><fig><caption><p>A qualitative thematic map.</p></caption><graphic xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="secret-image.png"/></fig></floats-group>'''
        _,text=parse_article(BASE.format(floated).encode())
        self.assertIn('A qualitative thematic map.',text)
        self.assertNotIn('secret-image.png',text)

    def test_floated_publishing_metadata_is_removed(self):
        floated='''<floats-group><sec><title>Author Contributions</title><p>Unrelated publication authors.</p></sec><table-wrap><caption><p>Readable research caption.</p></caption><table><tr><td>Clinical category</td><td>7</td></tr></table></table-wrap></floats-group>'''
        _,text=parse_article(BASE.format(floated).encode())
        self.assertNotIn('Unrelated publication authors.',text)
        self.assertIn('Readable research caption.',text)
        self.assertIn('Clinical category',text)


if __name__=='__main__':unittest.main()
