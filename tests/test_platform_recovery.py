import copy,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from recover_one_platform import validate_receipt,validate_readback,verified_async_receipt,multipart,IDENTITIES
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

    def test_exact_processed_readback_and_privacy_guard(self):
        row={'id':'abcdefghijk','snippet':{'channelId':IDENTITIES['youtube'],'title':'বাংলা hook','publishedAt':'2026-10-22T06:00:00Z'},'status':{'privacyStatus':'public','uploadStatus':'processed'},'processingDetails':{'processingStatus':'succeeded'}}
        receipt={'schema':1,'platform':'youtube_video','data':{'items':[row]}}
        self.assertEqual(validate_readback(receipt,'youtube','abcdefghijk','2026-10-22','বাংলা hook')['status'],'published')
        row['status']['privacyStatus']='private'
        with self.assertRaises(ValueError):validate_readback(receipt,'youtube','abcdefghijk','2026-10-22','বাংলা hook')
    def test_facebook_relative_link_only_from_actual_ready_public_post(self):
        row={'id':'123456789','published':True,'status':{'video_status':'ready'},'privacy':{'value':'EVERYONE'},'title':'বাংলা hook','created_time':'2026-10-22T06:00:00Z','permalink_url':'/reel/123456789/'}
        receipt={'schema':1,'platform':'facebook_video','data':row}
        self.assertEqual(validate_readback(receipt,'facebook','123456789','2026-10-22','বাংলা hook')['url'],'https://www.facebook.com/reel/123456789/')
        row['published']=False
        with self.assertRaises(ValueError):validate_readback(receipt,'facebook','123456789','2026-10-22','বাংলা hook')

    def test_async_snapshot_must_be_fresh_and_trace_actual_modules(self):
        import json
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now=datetime(2026,10,22,8,0,tzinfo=ZoneInfo('Europe/Berlin'))
        e={'observed_at':now.isoformat(),'lookup_scope':'latest_native_entry_in_descending_date_feed',
           'source_reference':{'scenario_id':7968544,'cycle':1,'execution_id':'a'*32,'reservation_module':49,'native_feed_module':52},'receipt':self.fixture('youtube')}
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'snapshot.json';p.write_text(json.dumps(e))
            self.assertFalse(verified_async_receipt(p,'youtube','2026-10-22',now)['reserved'])
            e['observed_at']='2026-10-22T07:50:00+02:00';p.write_text(json.dumps(e))
            with self.assertRaises(ValueError):verified_async_receipt(p,'youtube','2026-10-22',now)
            e['observed_at']=now.isoformat();e['source_reference']['native_feed_module']=54;p.write_text(json.dumps(e))
            with self.assertRaises(ValueError):verified_async_receipt(p,'youtube','2026-10-22',now)

    def test_native_instagram_created_time_keeps_current_day_hold(self):
        r=self.fixture('instagram')
        r['data']={'status':'success','posts':[{'id':'18022461680926341','createdTime':'2026-10-21T00:26:23.000Z'}]}
        self.assertFalse(validate_receipt(r,'instagram','2026-10-22')['reserved'])
        r['data']['posts'][0]['createdTime']='2026-10-22T00:26:23.000Z'
        with self.assertRaises(ValueError):validate_receipt(r,'instagram','2026-10-22')
