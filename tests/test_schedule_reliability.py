"""Fixture-only tests: no network, render, upload, email or real alert writes."""
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from schedule_guard import BERLIN, GitHub, check_delivery_day, day_window, decide
from publication_watchdog import DELIVERY_STEPS, classify, issue_body, telegram_notice, upsert_issue


def now(value='2026-10-21T02:31:00+02:00'):
    return datetime.fromisoformat(value)


def run(run_id=100, **changes):
    item = dict(id=run_id, event='schedule', created_at='2026-10-21T00:00:00Z',
                run_attempt=1, status='completed', conclusion='success')
    item.update(changes)
    return item


class ScheduleReliability(unittest.TestCase):
    def test_first_scheduled_attempt_is_elected(self):
        self.assertTrue(decide(run(), [run()], now())['allowed'])

    def test_missing_primary_allows_backup(self):
        backup = run(200, created_at='2026-10-21T00:31:00Z')
        self.assertTrue(decide(backup, [backup], now())['allowed'])

    def test_existing_success_failure_timeout_cancelled_or_running_blocks_backup(self):
        backup = run(200, created_at='2026-10-21T00:31:00Z')
        for state in ('success', 'failure', 'timed_out', 'cancelled', None):
            first = run(conclusion=state, status='in_progress' if state is None else 'completed')
            with self.subTest(state=state):
                result = decide(backup, [first, backup], now())
                self.assertFalse(result['allowed'])
                self.assertEqual(result['leader_run_id'], 100)

    def test_late_primary_created_after_backup_cannot_send_twice(self):
        backup = run(200, created_at='2026-10-21T00:31:00Z')
        delayed = run(201, created_at='2026-10-21T00:36:00Z')
        self.assertFalse(decide(delayed, [backup, delayed], now('2026-10-21T02:40:00+02:00'))['allowed'])

    def test_queued_primary_wins_even_when_backup_starts(self):
        first = run(status='queued', conclusion=None)
        backup = run(200)
        self.assertFalse(decide(backup, [first, backup], now())['allowed'])

    def test_schedule_rerun_is_not_authorized_by_backup(self):
        current = run(run_attempt=2)
        with self.assertRaisesRegex(RuntimeError, 'reconciliation'):
            decide(current, [current], now())

    def test_rerunning_only_delivery_job_cannot_reuse_old_successful_gate(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/schedule_guard.py'), '--check-day', '2026-10-21'],
                                env=dict(os.environ, GITHUB_EVENT_NAME='schedule', GITHUB_RUN_ATTEMPT='2'),
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('incident reconciliation', result.stderr)

    def test_manual_preview_needs_no_history_and_never_claims_publication(self):
        result = decide({'event': 'workflow_dispatch'}, [], now())
        self.assertTrue(result['allowed'])
        self.assertEqual(result['reason'], 'manual_preview_only')

    def test_previous_berlin_day_does_not_block_today(self):
        previous = run(90, created_at='2026-10-20T00:00:00Z')
        self.assertTrue(decide(run(), [previous, run()], now())['allowed'])

    def test_cross_midnight_and_incomplete_listing_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'midnight'):
            decide(run(created_at='2026-10-20T19:00:00Z'), [], now())
        with self.assertRaisesRegex(RuntimeError, 'absent'):
            decide(run(), [], now())

    def test_day_rechecked_immediately_before_delivery(self):
        check_delivery_day('2026-10-21', now())
        for expected, at in [('2026-10-20', now()), ('2026-10-21', now('2026-10-21T00:59:00+02:00'))]:
            with self.assertRaises(RuntimeError):
                check_delivery_day(expected, at)

    def test_dst_windows_cover_25_and_23_hours(self):
        for day, hours in [(date(2026, 10, 25), 25), (date(2027, 3, 28), 23)]:
            start, end = day_window(day)
            self.assertEqual((end-start).total_seconds(), hours*3600)

    def test_repeated_autumn_0200_cannot_elect_second_delivery(self):
        first = run(created_at='2026-10-25T00:00:00Z')
        second = run(200, created_at='2026-10-25T01:00:00Z')
        self.assertFalse(decide(second, [first, second], now('2026-10-25T02:15:00+01:00'))['allowed'])

    def test_get_retries_bounded_but_write_never_retried(self):
        transient = HTTPError('redacted', 503, '', {}, None)
        api = GitHub(token='test-not-a-real-token')
        with patch('schedule_guard.urlopen', side_effect=transient) as req, patch('schedule_guard.time.sleep'):
            with self.assertRaises(RuntimeError):
                api.request('/actions/runs')
            self.assertEqual(req.call_count, 3)
        with patch('schedule_guard.urlopen', side_effect=transient) as req:
            with self.assertRaises(RuntimeError):
                api.request('/issues', 'POST', {'title': 'fixture'})
            self.assertEqual(req.call_count, 1)

    def test_pagination_bound_blocks_incomplete_election(self):
        api = GitHub(token='test')
        with patch.object(api, 'request', return_value={'workflow_runs': [run()]*100}):
            with self.assertRaisesRegex(RuntimeError, 'pagination'):
                api.collection('/actions/runs', 'workflow_runs')

    def test_real_date_range_query_is_accepted_by_route_validation(self):
        api = GitHub(token='fixture')
        response = io.BytesIO(json.dumps({'workflow_runs': [run()]}).encode())
        with patch('schedule_guard.urlopen', return_value=response) as request:
            rows = api.runs('daily-carousel.yml', date(2026, 10, 21))
            self.assertEqual(len(rows), 1)
            self.assertIn('created=', request.call_args.args[0].full_url)
            self.assertIn('..', request.call_args.args[0].full_url)
        with self.assertRaises(ValueError):
            api.request('/../outside')

    def test_unauthorized_response_never_retried_or_printed(self):
        api = GitHub(token='test')
        with patch('schedule_guard.urlopen', side_effect=HTTPError('secret-url', 403, '', {}, None)) as req:
            with self.assertRaises(RuntimeError) as error:
                api.request('/actions/runs')
            self.assertEqual(req.call_count, 1)
            self.assertNotIn('secret-url', str(error.exception))


class WatchdogTests(unittest.TestCase):
    workflow = 'daily-carousel.yml'

    def test_absent_trigger_not_called_failure_before_due_or_during_grace(self):
        for at in ('2026-10-21T00:59:00+02:00', '2026-10-21T02:20:00+02:00'):
            self.assertFalse(classify(self.workflow, [], {}, now(at))['alert'])
        result = classify(self.workflow, [], {}, now('2026-10-21T03:07:00+02:00'))
        self.assertTrue(result['alert'])
        self.assertEqual(result['status'], 'missing_trigger')

    def test_source_green_delivery_skipped_is_held(self):
        jobs = {100: [{'conclusion': 'success', 'steps': [dict(name=DELIVERY_STEPS[self.workflow], conclusion='skipped')]}]}
        result = classify(self.workflow, [run()], jobs, now())
        self.assertTrue(result['alert'])
        self.assertEqual(result['status'], 'held_or_delivery_skipped')

    def test_accepted_delivery_never_means_published(self):
        jobs = {100: [{'conclusion': 'success', 'steps': [dict(name=DELIVERY_STEPS[self.workflow], conclusion='success')]}]}
        result = classify(self.workflow, [run(), run(200)], jobs, now())
        self.assertFalse(result['alert'])
        self.assertEqual(result['platform_publication'], 'unverified')

    def test_running_job_not_reported_as_failed_or_published(self):
        result = classify(self.workflow, [run(status='in_progress', conclusion=None)], {}, now())
        self.assertEqual(result['status'], 'running_or_queued')
        self.assertFalse(result['alert'])

    def test_failed_job_and_ambiguous_delivery_alert_without_retry(self):
        result = classify(self.workflow, [run(conclusion='failure')], {}, now())
        self.assertTrue(result['alert'])
        self.assertNotIn('retry', result)

    def test_dryrun_does_not_write_alert(self):
        class API:
            def collection(self, *args): return []
            def request(self, *args): raise AssertionError('No write permitted')
        result = upsert_issue(API(), '2026-10-21', 'fixture', dry_run=True)
        self.assertEqual(result['action'], 'would_create')
        self.assertFalse(result['write_performed'])

    def test_same_daily_alert_is_not_repeated_even_if_closed(self):
        class API:
            def collection(self, *args):
                return [dict(number=3, title='AbasonPlus publication alert 2026-10-21', body='fixture', state='closed')]
            def request(self, *args): raise AssertionError('Duplicate write')
        self.assertEqual(upsert_issue(API(), '2026-10-21', 'fixture', False)['action'], 'unchanged')

    def test_telegram_transfer_is_not_retried_or_leaked(self):
        with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '123:private_test_token', 'TELEGRAM_CHAT_ID': '1'}):
            with patch('publication_watchdog.urlopen', side_effect=URLError('private_test_token')) as request:
                result = telegram_notice('fixture', False)
                self.assertEqual(request.call_count, 1)
                self.assertNotIn('private_test_token', result)
            with patch('publication_watchdog.urlopen', side_effect=AssertionError('Unexpected send')):
                self.assertEqual(telegram_notice('fixture', True), 'not_sent_dry_run')

    def test_safe_issue_only_contains_fixed_status_and_real_run_ids(self):
        item = classify(self.workflow, [run(conclusion='failure')], {}, now())
        body = issue_body('2026-10-21', [item])
        self.assertIn('/actions/runs/100', body)
        self.assertNotIn('token', body)


class WiringTests(unittest.TestCase):
    def load(self, path):
        return yaml.load((ROOT/path).read_text(), Loader=yaml.BaseLoader)

    def test_backups_and_primary_share_gate_and_serialization(self):
        for name, cron in [('daily-carousel.yml', '31 1 * * *'), ('wordpress-post.yml', '23 1 * * *')]:
            workflow = self.load('.github/workflows/'+name)
            self.assertEqual(workflow['on']['schedule'], [{'cron': '0 1 * * *', 'timezone': 'Europe/Berlin'},
                                                        {'cron': cron, 'timezone': 'Europe/Berlin'}])
            self.assertEqual(workflow['concurrency']['cancel-in-progress'], 'false')
            self.assertIn('schedule-gate', workflow['jobs'])
            for job in workflow['jobs'].values():
                for step in job.get('steps', []):
                    if 'MAKE_WEBHOOK_URL' in step.get('env', {}):
                        self.assertIn("github.event_name == 'schedule'", step['if'])
                        self.assertIn('--check-day', step['run'])

    def test_watchdog_separate_schedule_and_completion_triggers_never_upload(self):
        w = self.load('.github/workflows/publication-watchdog.yml')
        self.assertEqual(w['on']['schedule'], [{'cron': '7 2 * * *', 'timezone': 'Europe/Berlin'}])
        self.assertIn('workflow_run', w['on'])
        self.assertEqual(w['jobs']['check']['permissions']['actions'], 'read')
        source = (ROOT/'scripts/publication_watchdog.py').read_text()
        self.assertNotIn('MAKE_WEBHOOK_URL', source)
        self.assertNotIn('rerun_workflow', source)
        self.assertNotIn('create_carousel', source)

    def test_wordpress_missing_daily_file_is_red_without_any_network(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td)
            (path/'scripts').mkdir()
            (path/'content').mkdir()
            for name in ('wordpress_email_prepare.py', 'scripts/publication_policy.py'):
                (path/name).write_bytes((ROOT/name).read_bytes())
            (path/'content/researched_wordpress_posts.json').write_text('[]')
            (path/'wordpress_posts.json').write_text('[]')
            result = subprocess.run([sys.executable, 'wordpress_email_prepare.py', '--skip-public-lookup'],
                                    cwd=td, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('NO_CHATGPT_DAILY_EDITORIAL', result.stderr)


if __name__ == '__main__':
    unittest.main()
