"""Strict mixed Bengali/Latin font runs, without glyph substitution boxes."""
import logging
import unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import ImageFont

LOG = logging.getLogger(__name__)
JOINERS = {0x200C, 0x200D}

def _coverage(path):
    font = TTFont(str(path), lazy=True)
    try:
        result = set()
        for table in font["cmap"].tables:
            if table.isUnicode():
                result.update(table.cmap)
        return result
    finally:
        font.close()

class BilingualText:
    def __init__(self, bengali_path, latin_path, fallback_paths=()):
        self.bn_path = str(bengali_path)
        self.latin_path = str(latin_path)
        self.paths = list(dict.fromkeys([self.bn_path, self.latin_path, *(str(p) for p in fallback_paths)]))
        self.coverage = {p: _coverage(p) for p in self.paths}
        self.fonts = {}

    def _font(self, path, size):
        key = (path, size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
        return self.fonts[key]

    @staticmethod
    def _script(cp):
        if 0x0980 <= cp <= 0x09FF:
            return "bn"
        if (0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A or
            0x0030 <= cp <= 0x0039 or 0x00C0 <= cp <= 0x024F):
            return "latin"
        return "neutral"

    def tokens(self, value, bengali_font):
        current_path = None
        run = ""
        size = bengali_font.size
        caller_path = str(getattr(bengali_font, "path", self.bn_path))
        for position, char in enumerate(value):
            cp = ord(char)
            script = self._script(cp)
            if script == "bn":
                preferred = [self.bn_path, self.latin_path]
            elif script == "latin":
                preferred = [self.latin_path, self.bn_path]
            else:
                preferred = [current_path] if current_path else [self.bn_path, self.latin_path]
            choices = [p for p in dict.fromkeys([*preferred, *self.paths]) if p]
            if cp in JOINERS or char.isspace():
                chosen = current_path or self.bn_path
            else:
                chosen = next((p for p in choices if cp in self.coverage[p]), None)
            if chosen is None:
                msg = (f"Unsupported glyph U+{cp:04X} {unicodedata.name(char, 'UNKNOWN')} "
                       f"at position {position}, script={script}; tried fonts: "
                       f"{', '.join(Path(p).name for p in choices)}; refusing tofu boxes")
                LOG.error(msg)
                raise RuntimeError(msg)
            if chosen != current_path and run:
                yield run, bengali_font if current_path == caller_path else self._font(current_path, size)
                run = ""
            run += char
            current_path = chosen
        if run:
            yield run, bengali_font if current_path == caller_path else self._font(current_path, size)
