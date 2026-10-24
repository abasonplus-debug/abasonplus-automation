import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from engagement_pack import hashtags_for,write_pack,hashtag_tokens,BROAD_TAGS
class PlatformHashtagTests(unittest.TestCase):
 def test_five_distinct_and_same_two_topic_tags(self):
  for topic in ('জমি','ফ্ল্যাট','অগ্নিনিরাপত্তা','সেতু'):
   groups=[hashtags_for(topic,p) for p in BROAD_TAGS]
   self.assertEqual(len({tuple(g[:2]) for g in groups}),1)
   self.assertEqual(len({tuple(g[2:]) for g in groups}),4)
   for g in groups:self.assertEqual(len(hashtag_tokens(' '.join(g))),5)
   self.assertIn('#Shorts',hashtags_for(topic,'youtube'))
 def test_output_files_reach_each_platform_without_repeated_tags(self):
  with tempfile.TemporaryDirectory() as d:
   out=pathlib.Path(d);tags=' '.join(hashtags_for('জমি'))
   p=write_pack(out,'দলিল দেখুন',tags,tags)
   self.assertIn('#Shorts',p['description'])
   self.assertIn('#ReelsBD',p['caption'])
   self.assertIn('#Reels',(out/'instagram_caption.txt').read_text())
   self.assertNotIn('#ReelsBD',(out/'instagram_caption.txt').read_text())
