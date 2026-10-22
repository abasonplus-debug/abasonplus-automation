"""Detect absent/held daily workflows, without calling Make or any publisher.

Default/manual/push runs are read-only. Scheduled/completion checks may upsert ONE
GitHub alert issue per day. Optional Telegram is never retried after a transfer.
"""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from schedule_guard import BERLIN, REPOSITORY, WORKFLOWS, GitHub, stamp

DELIVERY_STEPS = {
    'daily-carousel.yml': 'Send ONE daily validated Reel and Short to Make on automatic schedule ONLY',
    'wordpress-post.yml': 'Send exactly one approved article on SCHEDULED runs only',
}
VERIFY_WP = 'Verify the article is actually published on WordPress, not merely accepted by Make'


def classify(workflow, runs, jobs, now):
    """Workflow evidence only: successful transfer never means platform publication."""
    now = now.astimezone(BERLIN)
    relevant = [r for r in runs if r.get('event') == 'schedule'
                and stamp(r['created_at']).astimezone(BERLIN).date() == now.date()]
    due = now.replace(hour=1, minute=0, second=0, microsecond=0)
    base = {'workflow': workflow, 'platform_publication': 'unverified'}
    if now < due:
        return dict(base, status='not_due', alert=False, run_ids=[])
    if not relevant:
        missing = now >= due + timedelta(minutes=45)
        return dict(base, status='missing_trigger' if missing else 'waiting_for_trigger',
                    alert=missing, run_ids=[])
    ids = sorted(int(r['id']) for r in relevant)
    base['run_ids'] = ids
    steps = [s for rid in ids for job in jobs.get(rid, []) for s in job.get('steps', [])]
    deliveries = [s for s in steps if s.get('name') == DELIVERY_STEPS[workflow]]
    sent = any(s.get('conclusion') == 'success' for s in deliveries)
    # A failed verification after a successful WordPress send also needs an alert.
    if sent and any(s.get('name') == VERIFY_WP and s.get('conclusion') == 'failure' for s in steps):
        return dict(base, status='wordpress_publication_unverified_after_send', alert=True)
    if sent:
        failed_jobs = any(j.get('conclusion') in ('failure', 'timed_out', 'cancelled')
                          for rid in ids for j in jobs.get(rid, []))
        return dict(base, status='delivery_completed_but_job_failed' if failed_jobs
                    else 'delivery_completed_publication_unverified', alert=failed_jobs)
    active = [r for r in relevant if r.get('status') != 'completed']
    if active:
        old = any(now - stamp(r['created_at']) > timedelta(minutes=90) for r in active)
        return dict(base, status='running_delayed' if old else 'running_or_queued', alert=old)
    failed = any(r.get('conclusion') in ('failure', 'timed_out', 'cancelled', 'action_required')
                 for r in relevant)
    return dict(base, status='failed_or_cancelled_before_confirmed_delivery' if failed
                else 'held_or_delivery_skipped', alert=True)


def issue_body(day, findings):
    lines = [f'AbasonPlus {day}: প্রকাশের workflow সতর্কতা।', '',
             'এটি GitHub execution evidence; platform-এ প্রকাশ নিশ্চিত করার রিপোর্ট নয়।', '']
    for item in findings:
        lines.append(f"- `{item['workflow']}`: `{item['status']}`")
        for rid in item['run_ids']:
            lines.append(f'  https://github.com/{REPOSITORY}/actions/runs/{int(rid)}')
        if not item['run_ids']:
            lines.append(f"  https://github.com/{REPOSITORY}/actions/workflows/{item['workflow']}")
    lines += ['', 'Existing Make daily reservations, QA, owner approval and exact-video TikTok OK remain required.',
              'Do not replay a reserved/ambiguous request. This watchdog never uploads, publishes or reruns jobs.']
    text = '\n'.join(lines)
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return text + '\n\n<!-- abasonplus-alert:' + digest + ' -->\n'


def upsert_issue(api, day, body, dry_run=True):
    title = f'AbasonPlus publication alert {day}'
    # Includes closed issues so an owner-closed alert does not spawn duplicates.
    issues = api.collection('/issues', None, {'state': 'all', 'creator': 'github-actions[bot]'})
    exact = [i for i in issues if not i.get('pull_request') and i.get('title') == title]
    if len(exact) > 1:
        raise RuntimeError('Duplicate alert issues need owner review; no further alert write')
    prior = exact[0] if exact else None
    changed = prior is None or prior.get('body') != body
    if dry_run:
        return {'action': 'would_create' if prior is None else 'would_update' if changed else 'unchanged',
                'write_performed': False}
    if not changed:
        return {'action': 'unchanged', 'write_performed': False,
                'url': 'https://github.com/' + REPOSITORY + '/issues/' + str(int(prior['number']))}
    result = api.request('/issues' if prior is None else '/issues/' + str(int(prior['number'])),
                         'POST' if prior is None else 'PATCH',
                         {'title': title, 'body': body} if prior is None else {'body': body})
    return {'action': 'created' if prior is None else 'updated', 'write_performed': True,
            'url': 'https://github.com/' + REPOSITORY + '/issues/' + str(int(result['number']))}


def telegram_notice(message, dry_run=True):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat:
        return 'not_configured; GitHub issue is the alert destination'
    if dry_run:
        return 'not_sent_dry_run'
    if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+', token) or not re.fullmatch(r'-?[0-9]+', chat):
        return 'invalid_config; inspect secret names without logging values'
    data = json.dumps({'chat_id': chat, 'text': message, 'disable_web_page_preview': True}).encode()
    try:
        request = Request('https://api.telegram.org/bot' + token + '/sendMessage', data=data,
                          headers={'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=15) as response:
            result = json.load(response)
        return 'accepted' if result.get('ok') is True else 'unconfirmed_no_retry'
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        # Exception strings can contain a bot token. Never log them or retry this write.
        return 'unconfirmed_no_retry; inspect Telegram manually'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-alerts', action='store_true')
    args = parser.parse_args()
    dry_run = not args.write_alerts
    event = os.environ.get('GITHUB_EVENT_NAME')
    if not dry_run and event not in ('schedule', 'workflow_run'):
        raise RuntimeError('Only scheduled/completion watchdog checks can write alerts; manual is NO POSTS')
    now = datetime.now(BERLIN)
    api = GitHub()
    findings = []
    for workflow in WORKFLOWS:
        runs = api.runs(workflow, now.date())
        jobs = {int(run['id']): api.jobs(run['id']) for run in runs}
        findings.append(classify(workflow, runs, jobs, now))
    # Preflight failures need visibility before the 01:00 release boundary.
    start, end = __import__('schedule_guard').day_window(now.date())
    preview_runs = api.collection('/actions/workflows/editorial-photo-preflight.yml/runs',
                                  'workflow_runs', {'created': start.isoformat()+'..'+end.isoformat()})
    preview_runs = [r for r in preview_runs if start <= stamp(r['created_at']) < end]
    if preview_runs:
        latest = max(preview_runs, key=lambda r: int(r['id']))
        failed = latest.get('status') == 'completed' and latest.get('conclusion') in ('failure', 'timed_out', 'cancelled')
        findings.append({'workflow': 'editorial-photo-preflight.yml',
                         'status': 'preflight_held_before_release' if failed else 'preflight_'+latest['status'],
                         'alert': failed, 'run_ids': [int(latest['id'])],
                         'platform_publication': 'unverified'})
    alerts = [i for i in findings if i['alert']]
    summary = {'checked_at': now.isoformat(), 'date': now.date().isoformat(),
               'dry_run': dry_run, 'workflow_evidence': findings, 'no_publication_performed': True,
               'alert': {'action': 'none', 'write_performed': False}}
    if alerts:
        summary['alert'] = upsert_issue(api, summary['date'], issue_body(summary['date'], alerts), dry_run)
        if summary['alert']['write_performed']:
            summary['telegram'] = telegram_notice('AbasonPlus: প্রকাশের workflow আটকে আছে বা যাচাই বাকি।\n'
                                                  + summary['alert']['url'], dry_run)
    output = Path('output/reliability_watchdog.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)
    step_summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if step_summary:
        with Path(step_summary).open('a') as stream:
            stream.write('## Publication watchdog — NO POSTS\n```json\n' + text + '\n```\n')


if __name__ == '__main__':
    main()
