"""Regression tests for blocked-source visibility and exact-video consent."""
import copy,json,pathlib,subprocess,sys,tempfile,unittest
import yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from engagement_pack import hashtags_for
from tiktok_approval import validate_approval,reconcile

class Reliability(unittest.TestCase):
    def test_infrastructure_and_unknown_topics_do_not_get_homebuying_tags(self):
        for topic in ("কর্ণফুলী টানেল তদন্ত","সরকারি সেতু প্রকল্প","Bridge construction","অজানা নতুন খবর"):
            tags=hashtags_for(topic)
            self.assertGreaterEqual(len(set(tags)),5)
            self.assertNotIn("#ফ্ল্যাট",tags)
            self.assertNotIn("#HomeBuying",tags)
        self.assertIn("#Infrastructure",hashtags_for("কর্ণফুলী টানেল তদন্ত"))
        self.assertIn("#HomeBuying",hashtags_for("ফ্ল্যাট কেনা"))

    def test_source_failure_is_not_green_and_never_sets_ready(self):
        workflow=yaml.load((ROOT/'.github/workflows/daily-carousel.yml').read_text(),Loader=yaml.BaseLoader)
        script=workflow['jobs']['source']['steps'][1]['run']
        for code in (1,3):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as td:
                root=pathlib.Path(td);(root/'scripts').mkdir()
                (root/'scripts/select_video_story.py').write_text("raise SystemExit("+str(code)+")")
                import os
                env=dict(os.environ,GITHUB_OUTPUT=str(root/'result'),GITHUB_STEP_SUMMARY=str(root/'summary'))
                result=subprocess.run(['bash','-e','-c',script],cwd=root,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,code)
                self.assertNotIn("ready=true",(root/'result').read_text())
                self.assertIn("blocked",(root/'summary').read_text())

    def fixture(self):
        a=json.loads((ROOT/'audits/tiktok-approvals/2026-10-18.json').read_text())
        p=json.loads((ROOT/'audits/tiktok-publications/2026-10-18.json').read_text())
        s=json.loads((ROOT/'audits/daily/2026-10-18.json').read_text())
        return a,p,s

    def test_preapproval_false_is_reconciled_only_with_matching_real_records(self):
        a,p,s=self.fixture()
        s['context']['exact_tiktok_video_approved']=False
        result=reconcile(s,a,p)
        self.assertTrue(result['context']['exact_tiktok_video_approved'])
        self.assertFalse(s['context']['exact_tiktok_video_approved'])
        self.assertEqual(reconcile(result,a,p),result)

    def test_wrong_video_account_settings_date_and_caption_rejected(self):
        a,p,s=self.fixture()
        for key,value in (("video_sha256","f"*64),("account_id","wrong"),("privacy","SELF_ONLY"),("date","2026-10-19")):
            bad=copy.deepcopy(p);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):reconcile(s,a,bad)
        with self.assertRaises(ValueError):validate_approval(a,"2026-10-19")
        with self.assertRaises(ValueError):validate_approval(a,"2026-10-18",caption="changed")
        with self.assertRaises(ValueError):validate_approval(a,"2026-10-18",preview_run_id="other")

    def test_reviewed_workflow_requires_exact_record_for_recovery_artifact(self):
        text=(ROOT/'.github/workflows/tiktok-publish-reviewed.yml').read_text()
        self.assertIn("authorized video recovery",text)
        self.assertIn("validate_approval(approval,today",text)
        self.assertIn("Settings changed since owner OK",text)
        workflow=yaml.load(text,Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow['on']),{'workflow_dispatch'})

    def test_exact_published_recovery_name_is_accepted_without_widening_consent(self):
        import re
        text=(ROOT/'.github/workflows/tiktok-publish-reviewed.yml').read_text()
        pattern=re.search(r'test\("(\^AbasonPlus .*?)"\)',text).group(1)
        self.assertRegex('AbasonPlus Authorized Video Recovery 2026-10-19',pattern)
        self.assertRegex('AbasonPlus authorized video recovery 2026-10-19',pattern)
        self.assertNotRegex('AbasonPlus unrelated video 2026-10-19',pattern)
        self.assertIn('validate_approval(approval,today',text)
        self.assertIn('Settings changed since owner OK',text)

if __name__=="__main__":unittest.main()

