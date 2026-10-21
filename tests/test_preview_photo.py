"""Preview photo substitutions must not change editorial text or live gates."""
import copy
import hashlib
import pathlib
import sys
import unittest
import yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from apply_preview_photo import apply

class PreviewPhoto(unittest.TestCase):
    def fixture(self):
        data=b'fixed-editorial'
        story={'verified_on':'2026-10-21','hook':'fixed hook','title':'fixed title','tips':[{'text':'fixed tip','query':'original query'}],
               'photos':[{'url':'cover'},{'url':'original'}]}
        request={'date':'2026-10-21','editorial_sha256':hashlib.sha256(data).hexdigest(),'slide_index':1,
                 'expected_original_url':'original','query':'parking garage stairs','original_preview_run_id':123,'reason':'scene mismatch',
                 'photo':{'url':'https://images.pexels.com/photos/11921920/photo.jpeg','source_page':'https://www.pexels.com/photo/example-11921920/',
                          'creator':'fixture','license':'Pexels Free License','scene':'stairs','scene_match':'common access'}}
        return story,data,request

    def test_only_photo_and_query_change_and_original_untouched(self):
        story,data,request=self.fixture();before=copy.deepcopy(story)
        result=apply(story,data,request,'2026-10-21')
        self.assertEqual(story,before)
        self.assertEqual(result['hook'],story['hook'])
        self.assertEqual(result['tips'][0]['text'],story['tips'][0]['text'])
        self.assertTrue(result['preview_correction']['requires_new_exact_approval'])

    def test_stale_or_changed_editorial_and_wrong_photo_fail_closed(self):
        story,data,request=self.fixture()
        for key,value in [('date','2026-10-20'),('editorial_sha256','0'*64),('expected_original_url','wrong'),('slide_index',99)]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                apply(story,data,dict(request,**{key:value}),'2026-10-21')

    def test_license_and_direct_photo_host_required(self):
        story,data,request=self.fixture()
        for key,value in [('license','unknown'),('creator',''),('url','https://wrong.example/photo')]:
            bad=copy.deepcopy(request);bad['photo'][key]=value
            with self.assertRaises(ValueError):apply(story,data,bad,'2026-10-21')

    def test_preview_request_never_enables_live_delivery(self):
        workflow=yaml.load((ROOT/'.github/workflows/daily-carousel.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['on']['push']['paths'],['previews/tiktok/current.json'])
        for job in workflow['jobs'].values():
            for step in job.get('steps',[]):
                if 'MAKE_WEBHOOK_URL' in step.get('env',{}):
                    self.assertEqual(step['if'],"${{ github.event_name == 'schedule' }}")
        self.assertNotIn('schedule',yaml.load((ROOT/'.github/workflows/tiktok-publish-reviewed.yml').read_text(),Loader=yaml.BaseLoader)['on'])

if __name__=='__main__':unittest.main()
