import copy,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from recover_one_platform import validate_receipt,multipart,IDENTITIES
class RecoveryTests(unittest.TestCase):
    def fixture(self,p):
        rows={'youtube':{'items':[{'snippet':{'channelId':IDENTITIES['youtube'],'publishedAt':'2026-10-21T04:00:00Z'}}]},
              'facebook':[{'created_time':'2026-10-21T04:00:00Z'}],
              'instagram':{'body':{'posts':[{'timestamp':'2026-10-21T04:00:00Z'}]}}}
        return dict(schema=1,platform=p,identity=IDENTITIES[p],date='2026-10-22',reserved=False,data=rows[p])
    def test_old_feed_unreserved_can_proceed(self):
        for p in IDENTITIES:self.assertFalse(validate_receipt(self.fixture(p),p,'2026-10-22')['reserved'])
    def test_reserved_unknown_wrong_identity_or_day_hold(self):
        for key,value in [('reserved',True),('reserved',None),('identity','wrong'),('date','2026-10-21'),('data',None)]:
            r=self.fixture('youtube');r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_receipt(r,'youtube','2026-10-22')
    def test_current_day_post_or_missing_time_holds(self):
        for ts in ['2026-10-22T00:30:00Z',None]:
            r=self.fixture('youtube');r['data']['items'][0]['snippet']['publishedAt']=ts
            with self.assertRaises(ValueError):validate_receipt(r,'youtube','2026-10-22')
    def test_empty_or_incomplete_native_lookup_holds(self):
        r=self.fixture('facebook');r['data']=[]
        with self.assertRaises(ValueError):validate_receipt(r,'facebook','2026-10-22')
        r=self.fixture('instagram');r['data']={'body':{'status':'error'}}
        with self.assertRaises(ValueError):validate_receipt(r,'instagram','2026-10-22')
    def test_entire_payload_size_includes_thumbnail_and_fields(self):
        with tempfile.TemporaryDirectory() as d:
            f=pathlib.Path(d)/'v.mp4';f.write_bytes(b'x'*4_990_000)
            t=pathlib.Path(d)/'c.jpg';t.write_bytes(b'x'*20_000)
            with self.assertRaises(ValueError):multipart({'caption':'news'},[('video',f,'video/mp4'),('thumbnail',t,'image/jpeg')])
    def test_no_upload_retry_or_tiktok_or_cron(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        w=(root/'.github/workflows/recover-one-platform.yml').read_text()
        self.assertNotIn('  schedule:',w);self.assertIn('default: true',w)
        self.assertIn('options: [youtube, facebook, instagram]',w)
        self.assertIn('persist-credentials: false',w)
