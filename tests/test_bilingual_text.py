"""Exercise the production font path, including the failed daily hook."""
import json
import pathlib
import sys
import unittest
from PIL import ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bilingual_text import BilingualText
from carousel_style import layout, paint


class BilingualRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bn = next(pathlib.Path('/usr/share/fonts').rglob('NotoSansBengali-Bold.ttf'))
        latin = next(pathlib.Path('/usr/share/fonts').rglob('NotoSans-Bold.ttf'))
        cls.text = BilingualText(bn, latin)
        cls.hook = ImageFont.truetype(str(bn), 132, layout_engine=ImageFont.Layout.RAQM)
        cls.body = ImageFont.truetype(str(bn), 120, layout_engine=ImageFont.Layout.RAQM)

    def test_adjacent_scripts_keep_every_character_and_font_coverage(self):
        for value in ('Eco-Build—নির্মাণখাতে', 'brief-এ', 'batch-এর', 'নির্মাণEco', 'কি\u200dভাবে যাচাই করবেন?'):
            runs = list(self.text.tokens(value, self.hook))
            self.assertEqual(''.join(t for t, f in runs), value)
            for t, f in runs:
                if any('A' <= c <= 'z' for c in t):
                    self.assertIsNot(f, self.hook)
                if any(0x0980 <= ord(c) <= 0x09FF for c in t):
                    self.assertIs(f, self.hook)

    def test_real_daily_editorials_layout_without_missing_glyphs_or_collisions(self):
        for path in sorted((ROOT / 'content').glob('daily_editorial_*.json')):
            story = json.loads(path.read_text())['story']
            for n, value in enumerate([story['hook']] + [p['text'] for p in story['tips']]):
                with self.subTest(path=path.name, slide=n):
                    font = self.hook if n == 0 else self.body
                    rows = layout(value, font, self.text.tokens)
                    layer, boxes = paint(rows, self.text.tokens)
                    self.assertIsNotNone(layer.getbbox())
                    self.assertTrue(boxes)
                    self.assertEqual(font.size, 132 if n == 0 else 120)

    def test_unknown_glyph_still_blocks(self):
        with self.assertRaises(RuntimeError):
            list(self.text.tokens('পরীক্ষা\U0010FFFF', self.body))


if __name__ == '__main__':
    unittest.main()
