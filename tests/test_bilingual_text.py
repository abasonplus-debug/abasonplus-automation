"""Offline regression checks; never publish content."""
import unittest
from pathlib import Path
from PIL import ImageFont
from fontTools.ttLib import TTFont
from scripts.bilingual_text import BilingualText

BN = Path("/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf")
LATIN = Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")
CASES = [
    "Eco-Build-নির্মাণখাতে", "AI-ভিত্তিক", "Wi-Fi সংযোগ",
    "২০২৬ সালের 20% উন্নয়ন", "EU-BD প্রকল্প", "5G ইন্টারনেট",
    "USD 100 কোটি টাকা", "Green-Building 2030", "B1-জার্মান ভাষা",
    "বাংলাদেশে Solar-Power", "Flat-১: নতুন নিয়ম", "Eco-Build—সবুজ নির্মাণ",
]

@unittest.skipUnless(BN.exists() and LATIN.exists(), "Noto test fonts unavailable")
class MixedFontTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.font = ImageFont.truetype(str(BN), 120, layout_engine=ImageFont.Layout.RAQM)
        cls.router = BilingualText(BN, LATIN)
        cls.coverage = {str(p): TTFont(str(p)).getBestCmap() for p in (BN, LATIN)}

    def test_mixed_cases(self):
        for source in CASES:
            with self.subTest(source=source):
                runs = list(self.router.tokens(source, self.font))
                self.assertEqual("".join(s for s, _ in runs), source)
                for segment, font in runs:
                    cmap = self.coverage[str(font.path)]
                    for char in segment:
                        if not char.isspace() and ord(char) not in (0x200C, 0x200D):
                            self.assertIn(ord(char), cmap)

    def test_unsupported_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, r"U\+10FFFD"):
            list(self.router.tokens("বাংলা\U0010fffd", self.font))

if __name__ == "__main__":
    unittest.main()
