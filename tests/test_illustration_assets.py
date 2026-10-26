import hashlib,tempfile,unittest
from pathlib import Path
from PIL import Image
from scripts.illustration_assets import validate_asset,validate_visual_evidence

class IllustrationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);p=self.root/'assets/editorial/input.png';p.parent.mkdir(parents=True)
        Image.new('RGB',(1080,1920),'white').save(p)
        self.asset=dict(asset_type='illustration',contains_text=False,scene='buyer with records',scene_match='matches verification script',creator='owner provided',rights_evidence='test evidence reference',origin_reference='test immutable origin',rights_confirmed=True,illustrative_not_real_event=True,asset_path='assets/editorial/input.png',sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    def test_complete_manifest_accepts_actual_bytes(self):
        self.assertEqual(validate_asset(self.asset,self.root).name,'input.png')
    def test_rejects_changed_bytes(self):
        self.asset['sha256']='0'*64
        with self.assertRaises(ValueError):validate_asset(self.asset,self.root)
    def test_rejects_escape_and_absolute_path(self):
        for path in ('../outside.png','/tmp/outside.png'):
            with self.subTest(path=path),self.assertRaises(ValueError):validate_asset(dict(self.asset,asset_path=path),self.root)
    def test_rejects_missing_rights_and_precomposed_text(self):
        for field,value in [('rights_confirmed',False),('contains_text',True),('rights_evidence',''),('origin_reference','')]:
            with self.subTest(field=field),self.assertRaises(ValueError):validate_asset(dict(self.asset,**{field:value}),self.root)
    def test_illustration_cannot_impersonate_photo_qa(self):
        info=dict(asset_type='illustration',photo_semantic_qa=False,visual_semantic_qa=True,source='illustration-sha256:'+'a'*64,rights_evidence='record',origin_reference='origin')
        validate_visual_evidence(info)
        with self.assertRaises(ValueError):validate_visual_evidence(dict(info,photo_semantic_qa=True))
    def test_existing_photo_evidence_still_required(self):
        validate_visual_evidence({'photo_semantic_qa':True})
        with self.assertRaises(ValueError):validate_visual_evidence({'photo_semantic_qa':False})
