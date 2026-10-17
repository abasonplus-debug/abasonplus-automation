"""Real Bengali raster/layout regression fixtures; no network or publication."""
import copy
import pathlib
import re
import sys
import unittest
from PIL import Image,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from carousel_style import STYLE_ID,layout,paint,photo_stats,validate_style

class CompactStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bn=next(p for p in pathlib.Path('/usr/share/fonts').rglob('*.ttf') if 'Bengali' in p.name and 'Bold' in p.name)
        cls.font=ImageFont.truetype(str(bn),120,layout_engine=ImageFont.Layout.RAQM)
        latin=list(pathlib.Path('/usr/share/fonts').rglob('NotoSans-Bold.ttf'))
        cls.latin=ImageFont.truetype(str(latin[0]) if latin else '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',120)
    def tokens(self,value,font):
        for t in re.findall(r'\s+|\S+',value):yield t,font if any(0x0980<=ord(c)<=0x09ff for c in t) else self.latin
    def fixture(self):
        rows=layout('জমির নথি দেখুন। মালিকানা যাচাই করুন। সীমানা মিলিয়ে নিন। সন্দেহ হলে পরামর্শ নিন।',self.font,self.tokens)
        layer,boxes=paint(rows,self.tokens)
        stats=photo_stats(Image.new('RGB',(1080,1920),'#777777'),boxes)
        info=dict(style_id=STYLE_ID,slide=2,font_px=120,main_font_px=120,text_colors=['#FFFFFF','#FFD24A'],stroke_px=4,text_stroke=True,text_shadow=True,text_background=False,photo_overlay=False,line_ink_boxes=boxes,text_lines=len(boxes),alignment='center',compact_spacing_qa=True,line_background_stats=stats,logo_position='omitted_unavailable')
        return rows,layer,boxes,info
    def test_four_sentences_are_centered_compact_and_do_not_collide(self):
        rows,layer,boxes,info=self.fixture()
        self.assertTrue(validate_style(info))
        self.assertIsNotNone(layer.getbbox())
        self.assertLess(abs((boxes[0][1]+boxes[-1][3])/2-960),4)
        for i,b in enumerate(boxes):
            self.assertLess(abs((b[0]+b[2])/2-540),7)
            if i:self.assertLessEqual(b[1]-boxes[i-1][3],14)
    def test_old_style_small_font_and_collisions_block_release(self):
        *_,base=self.fixture()
        for key,value in [('style_id','editorial_photo_overlay_v1'),('font_px',119),('text_stroke',False),('photo_overlay',True)]:
            bad=copy.deepcopy(base);bad[key]=value
            with self.assertRaises(ValueError):validate_style(bad)
        bad=copy.deepcopy(base);bad['line_ink_boxes'][1][1]=bad['line_ink_boxes'][0][3]
        with self.assertRaises(ValueError):validate_style(bad)
    def test_overflow_never_shrinks_type(self):
        with self.assertRaises(RuntimeError):layout('মালিকানা যাচাই করুন। '*60,self.font,self.tokens)
        self.assertEqual(self.font.size,120)
    def test_real_logo_corner_bounds_and_no_fake_logo(self):
        *_,base=self.fixture()
        base.update(logo_position='bottom_right',logo_box=[962,1802,1052,1892])
        self.assertTrue(validate_style(base))
        base['logo_box']=[900,1500,990,1590]
        with self.assertRaises(ValueError):validate_style(base)
    def test_all_existing_catalog_text_renders_with_new_style(self):
        import json
        topics=json.loads((ROOT/'content/topics.json').read_text())
        for topic in topics:
            for text in [topic['hook']]+[p['text'] for p in topic['tips']]:
                rows=layout(text,self.font,self.tokens)
                layer,boxes=paint(rows,self.tokens)
                self.assertTrue(boxes)
