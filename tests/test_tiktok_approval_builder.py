import copy, hashlib, pathlib, sys, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from build_tiktok_approval import build_approval
from reviewed_video_timing import validate_reviewed_timing

class ApprovalBuilderTests(unittest.TestCase):
    def setUp(self):
        self.run=dict(id=123,head_sha='a'*40,conclusion='success',head_branch='main',created_at='2026-10-23T23:30:00Z')
        voice=dict(engine='CosyVoice3',reference='Dan Mason',complete=True,voice_gain=1,music_gain=.2,narrated_slide_count=5,script_sha256='b'*64)
        self.preview=dict(date='2026-10-24',status='preview_only',posting_enabled=False,caption='exact caption',caption_sha256=hashlib.sha256(b'exact caption').hexdigest(),video_sha256='c'*64,first_comment='prepared comment',format=dict(slides=5,slide_durations=[12]*5,voiceover=voice))
        self.settings=dict(privacy_level='PUBLIC_TO_EVERYONE',allow_comment=True,allow_duet=True,allow_stitch=True,video_made_with_ai=True,commercialContentType='none')
    def build(self,evidence='Owner Ok immediately after exact preview'):
        return build_approval(self.preview,self.run,'c'*64,self.settings,evidence,'2026-10-24T01:45:00+02:00')
    def test_complete_record_passes_downstream_narration_gate_without_truncation(self):
        a=self.build()
        meta=copy.deepcopy(self.preview['format']);meta['slide_seconds']=3
        self.assertEqual(validate_reviewed_timing(meta,60,a,self.run,"ENGINE='CosyVoice3'"),60)
        a['format']['voiceover']['script_sha256']='d'*64
        self.assertEqual(self.preview['format']['voiceover']['script_sha256'],'b'*64)
        with self.assertRaises(ValueError):validate_reviewed_timing(meta,60,a,self.run,"ENGINE='CosyVoice3'")
    def test_missing_consent_wrong_commit_caption_or_voice_fail_before_dispatch(self):
        with self.assertRaises(ValueError):self.build('')
        for target,key,value in [(self.run,'head_sha',''),(self.run,'conclusion','failure'),(self.preview,'caption','changed'),(self.preview['format'],'voiceover',{})]:
            old=copy.deepcopy(target[key]);target[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.build()
            target[key]=old
