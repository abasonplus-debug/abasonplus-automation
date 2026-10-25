"""Elect one scheduled run per Berlin day. Never clear Make/provider reservations.

The whole workflow must share one concurrency group with cancel-in-progress=false.
A backup is for an absent trigger, NOT a retry of a failed or ambiguous delivery.
All network operations in this module are bounded GitHub GETs.
"""
import argparse
import json
import os
import time
from datetime import datetime, time as day_time, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo('Europe/Berlin')
REPOSITORY = 'abasonplus-debug/abasonplus-automation'
WORKFLOWS = ('daily-carousel.yml', 'wordpress-post.yml')


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('GitHub timestamp must include timezone')
    return result


def day_window(day):
    start = datetime.combine(day, day_time(), BERLIN)
    end = datetime.combine(day + timedelta(days=1), day_time(), BERLIN)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


class GitHub:
    def __init__(self, token=None):
        self.token = token if token is not None else os.environ.get('GITHUB_TOKEN', '')
        if not self.token:
            raise RuntimeError('GITHUB_TOKEN missing; fail closed')

    def request(self, path, method='GET', body=None):
        # Callers supply repository-relative fixed API routes, never arbitrary hosts.
        route = path.partition('?')[0]
        if not route.startswith('/') or route.startswith('//') or '..' in route:
            raise ValueError('Invalid repository API route')
        url = 'https://api.github.com/repos/' + REPOSITORY + path
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28',
                   'User-Agent': 'AbasonPlusReliability/1.0'}
        data = None if body is None else json.dumps(body).encode('utf-8')
        attempts = 3 if method == 'GET' else 1  # never replay an ambiguous write
        for attempt in range(attempts):
            try:
                with urlopen(Request(url, data=data, headers=headers, method=method), timeout=20) as response:
                    return json.load(response)
            except HTTPError as exc:
                if method == 'GET' and (exc.code == 429 or 500 <= exc.code < 600) and attempt + 1 < attempts:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f'GitHub {method} failed HTTP {exc.code}; no delivery authorized') from None
            except (URLError, TimeoutError, OSError):
                if method == 'GET' and attempt + 1 < attempts:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f'GitHub {method} unavailable; no delivery authorized') from None

    def collection(self, path, key, query=None):
        rows = []
        for page in range(1, 5):
            params = dict(query or {}, per_page=100, page=page)
            result = self.request(path + '?' + urlencode(params))
            items = result.get(key) if key else result
            if not isinstance(items, list):
                raise RuntimeError('Incomplete GitHub listing; fail closed')
            rows.extend(items)
            if len(items) < 100:
                return rows
        raise RuntimeError('GitHub pagination bound exceeded; fail closed')

    def runs(self, workflow, day):
        if workflow not in WORKFLOWS:
            raise ValueError('Unexpected publishing workflow')
        start, end = day_window(day)
        query = {'event': 'schedule', 'created': start.isoformat() + '..' + end.isoformat()}
        rows = self.collection('/actions/workflows/' + workflow + '/runs', 'workflow_runs', query)
        return [r for r in rows if r.get('event') == 'schedule'
                and start <= stamp(r['created_at']) < end]

    def jobs(self, run_id):
        return self.collection('/actions/runs/' + str(int(run_id)) + '/jobs', 'jobs')


def decide(current, runs, now):
    """Only the earliest first-attempt scheduled run may reach existing delivery gates."""
    local = now.astimezone(BERLIN)
    day = local.date().isoformat()
    if current.get('event') != 'schedule':
        return {'allowed': True, 'day': day, 'reason': 'manual_preview_only'}
    if stamp(current['created_at']).astimezone(BERLIN).date() != local.date():
        raise RuntimeError('Run crossed Berlin midnight; hold stale scheduled delivery')
    if (local.hour, local.minute) < (0, 30):
        raise RuntimeError('Before owner-selected 00:30 Berlin publication boundary')
    if int(current.get('run_attempt', 0)) != 1:
        raise RuntimeError('Scheduled rerun requires incident reconciliation; backup is not a retry')
    matching = [r for r in runs if r.get('event') == 'schedule'
                and stamp(r['created_at']).astimezone(BERLIN).date() == local.date()]
    if not any(int(r['id']) == int(current['id']) for r in matching):
        raise RuntimeError('Current run absent from listing; election incomplete, fail closed')
    winner = min(matching, key=lambda r: int(r['id']))
    allowed = int(winner['id']) == int(current['id'])
    return {'allowed': allowed, 'day': day,
            'reason': 'first_scheduled_attempt' if allowed else 'existing_scheduled_attempt_no_replay',
            'leader_run_id': int(winner['id']),
            'leader_url': 'https://github.com/' + REPOSITORY + '/actions/runs/' + str(int(winner['id']))}


def check_delivery_day(expected, now=None):
    local = (now or datetime.now(BERLIN)).astimezone(BERLIN)
    if expected != local.date().isoformat() or (local.hour, local.minute) < (0, 30):
        raise RuntimeError('Delivery day/time changed since election; hold without sending')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workflow', choices=WORKFLOWS)
    parser.add_argument('--check-day')
    args = parser.parse_args()
    now = datetime.now(BERLIN)
    if args.check_day:
        if os.environ.get('GITHUB_EVENT_NAME') == 'schedule' and os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
            raise RuntimeError('Delivery on a scheduled rerun is held for incident reconciliation')
        check_delivery_day(args.check_day, now)
        print('Berlin delivery date checked; no network or posts')
        return
    if not args.workflow:
        parser.error('--workflow is required for election')
    if os.environ.get('GITHUB_EVENT_NAME') == 'schedule':
        api = GitHub()
        run_id = int(os.environ['GITHUB_RUN_ID'])
        current = api.request('/actions/runs/' + str(run_id))
        result = decide(current, api.runs(args.workflow, now.date()), now)
    else:
        result = decide({'event': 'workflow_dispatch'}, [], now)
    print(json.dumps(result, ensure_ascii=False))
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with Path(output).open('a') as stream:
            stream.write('allowed=' + str(result['allowed']).lower() + '\n')
            stream.write('day=' + result['day'] + '\n')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a') as stream:
            stream.write('## Daily schedule election\n' + result['reason'] + '\n')
            if result.get('leader_url'):
                stream.write(result['leader_url'] + '\n')


if __name__ == '__main__':
    main()
