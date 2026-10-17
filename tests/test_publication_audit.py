import copy,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from publication_audit import build,retry_decision,quota_report
class AuditTests(unittest.TestCase):
    def snapshot(self):return {'checked_at':'2026-10-18T11:00:00+02:00','context':{'fresh_content_ready':True,'lookup_complete':{'instagram':True}},'evidence':[]}
    def row(self):return dict(platform='instagram',post_id='123',url='https://www.instagram.com/reel/real/',status='published',published_at='2026-10-18T09:02:00+02:00',verification='platform_readback',identity_matched=True)
    def test_provider_acceptance_is_not_publication(self):
        s=self.snapshot();r=self.row();r['status']='publishing';s['evidence']=[r]
        self.assertEqual(build(s)['platforms']['instagram']['status'],'processing')
    def test_exact_readback_and_date_required(self):
        for mutation in ({'verification':'make_success'},{'identity_matched':False},{'url':'https://www.instagram.com.evil.test/x'},{'published_at':'2026-10-17T09:00:00+02:00'}):
            s=self.snapshot();r=self.row();r.update(mutation);s['evidence']=[r]
            self.assertNotEqual(build(s)['platforms']['instagram']['status'],'published_verified')
    def test_duplicates_and_repeated_observation(self):
        s=self.snapshot();r=self.row();s['evidence']=[r,copy.deepcopy(r)]
        self.assertEqual(build(s)['platforms']['instagram']['status'],'published_verified')
        r2=copy.deepcopy(r);r2['post_id']='456';s['evidence'].append(r2)
        self.assertEqual(build(s)['platforms']['instagram']['status'],'duplicate')
    def test_before_schedule_and_tiktok_consent(self):
        s=self.snapshot();s['checked_at']='2026-10-18T00:50:00+02:00'
        report=build(s)
        self.assertEqual(report['platforms']['youtube']['status'],'not_due')
        self.assertEqual(report['platforms']['tiktok']['status'],'awaiting_video_review')
    def test_only_one_pre_delivery_transient_retry(self):
        e=dict(delivery_attempted=False,failure_phase='before_delivery',transient_failure=True,github_job_status='failure',prior_retries=0,current_day_verified=True,quota_safe=True)
        self.assertEqual(retry_decision(e),'retry_failed_pre_delivery_job_once')
        for mutation in ({'delivery_attempted':True},{'provider_accepted':True},{'prior_retries':1},{'quota_safe':False}):
            self.assertNotEqual(retry_decision(dict(e,**mutation)),'retry_failed_pre_delivery_job_once')
    def test_quota_forecast_and_unknown_metrics(self):
        self.assertEqual(quota_report(dict(remaining=100,used=900,days_until_reset=10,measured_daily_credits=20))['status'],'insufficient')
        report=build(self.snapshot());self.assertEqual(report['weekly_metrics']['status'],'unavailable')
