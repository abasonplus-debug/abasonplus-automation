"""Font runs for adjacent Bengali and Latin text, without renderer side effects."""
from fontTools.ttLib import TTFont
from PIL import ImageFont


class BilingualText:
    def __init__(self, bengali_path, latin_path):
        self.bn_cmap = TTFont(str(bengali_path)).getBestCmap()
        self.latin_cmap = TTFont(str(latin_path)).getBestCmap()
        self.latin_path = str(latin_path)
        self.fonts = {}

    def tokens(self, value, bengali_font):
        latin = self.fonts.setdefault(bengali_font.size, None)
        if latin is None:
            latin = ImageFont.truetype(self.latin_path, bengali_font.size,
                                      layout_engine=ImageFont.Layout.RAQM)
            self.fonts[bengali_font.size] = latin
        current = None
        text = ''
        for ch in value:
            cp = ord(ch)
            if ch in ('\u200c', '\u200d'):
                chosen = current or bengali_font
            elif 0x0980 <= cp <= 0x09FF:
                chosen = bengali_font
            elif cp in self.latin_cmap or ch.isspace():
                chosen = latin
            elif cp in self.bn_cmap:
                chosen = bengali_font
            else:
                raise RuntimeError(f'Unsupported glyph U+{cp:04X} in on-screen text; refusing boxes')
            cmap = self.bn_cmap if chosen is bengali_font else self.latin_cmap
            if not ch.isspace() and ch not in ('\u200c', '\u200d') and cp not in cmap:
                raise RuntimeError(f'Unsupported glyph U+{cp:04X} in selected font; refusing boxes')
            if current is not None and chosen is not current:
                yield text, current
                text = ''
            current = chosen
            text += ch
        if text:
            yield text, current
