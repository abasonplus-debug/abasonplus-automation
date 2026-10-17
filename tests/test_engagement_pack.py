import json,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from engagement_pack import hashtags_for,hashtag_tokens,write_pack,validate_pack
class EngagementTests(unittest.TestCase):
    def test_topic_hashtags_distinct_and_unicode(self):
        for t in ('জমি','ভূমি আইন','নির্মাণ সামগ্রী','ফ্ল্যাট'):
            tags=' '.join(hashtags_for(t));self.assertGreaterEqual(len(hashtag_tokens(tags)),5)
        self.assertEqual(len(hashtag_tokens('#জমি #জমি #জমি #জমি #জমি')),1)
    def test_first_comment_roundtrips_quotes_and_newlines(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td);tags=' '.join(hashtags_for('জমি'))
            pack=write_pack(p,'জমির "দলিল" দেখুন',tags,tags)
            self.assertEqual(json.loads((p/'first_comment_json.txt').read_text()),pack['first_comment'])
            self.assertFalse(pack['view_growth_guaranteed'])
            pack['music']='other.mp3'
            with self.assertRaises(ValueError):validate_pack(pack)
