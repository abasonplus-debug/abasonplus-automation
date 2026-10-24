import pathlib
import unittest
import yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]

class WorkflowContracts(unittest.TestCase):
    def path(self,name):
        archived=ROOT/'archive/workflows'/name
        return archived if archived.exists() else ROOT/'.github/workflows'/name

    def load(self,name):
        return yaml.load(self.path(name).read_text(), Loader=yaml.BaseLoader)

    def test_daily_local_schedules_and_manual_publication_gate(self):
        for name,cron in [('daily-carousel.yml','0 1 * * *'),('wordpress-post.yml','0 1 * * *'),('official-source-monitor.yml','45 0 * * *')]:
            d=self.load(name)
            self.assertEqual(d['on']['schedule'][0],{'cron':cron,'timezone':'Europe/Berlin'})
            self.assertTrue(all(s['timezone']=='Europe/Berlin' for s in d['on']['schedule']))
        d=self.load('daily-carousel.yml')
        self.assertEqual(d['jobs']['render-and-publish']['if'], "${{ needs.source.outputs.ready == 'true' }}")
        for name in ('daily-carousel.yml','wordpress-post.yml'):
            d=self.load(name)
            send=[s for j in d['jobs'].values() for s in j['steps'] if 'MAKE_WEBHOOK_URL' in s.get('env',{})]
            self.assertTrue(send)
            for step in send: self.assertIn("github.event_name == 'schedule'",step['if'])

    def test_tiktok_and_completed_one_time_deliveries_do_not_run_daily(self):
        self.assertNotIn('schedule', self.load('tiktok-publish-reviewed.yml')['on'])
        for name in ('instagram-first-validated.yml','tiktok-first-approved-once.yml'):
            self.assertFalse((ROOT/'.github/workflows'/name).exists())
            d=self.load(name)
            self.assertNotIn('push', d['on'])
            self.assertTrue(all(j.get('if')=='${{ false }}' for j in d['jobs'].values()))

    def test_automatic_code_validation_does_not_render_or_publish(self):
        d=self.load('validate-carousel.yml')
        for job in d['jobs'].values():
            for step in job['steps']:
                command=step.get('run','')
                self.assertNotIn('python scripts/create_carousel.py',command)
                self.assertNotIn('MAKE_WEBHOOK_URL',step.get('env',{}))
        self.assertEqual(set(self.load('test-daily-editorial.yml')['on']),{'workflow_dispatch'})

    def test_exact_day_recovery_has_no_cron_or_tiktok_consent(self):
        name='recover-video-2026-10-19.yml'
        d=self.load(name)
        self.assertEqual(set(d['on']),{'workflow_dispatch'})
        self.assertEqual(d['jobs']['source']['if'],'${{ false }}')
        text=self.path(name).read_text()
        self.assertIn("delivery[0]['conclusion']=='skipped'",text)
        self.assertIn("manifest['date']=='2026-10-19'",text)
        self.assertIn('tiktok_publish_approved=false',text)
        self.assertIn("github.run_attempt == 1",text)
        self.assertIn('scripts/verify_video_release.py',text)

if __name__=='__main__': unittest.main()

