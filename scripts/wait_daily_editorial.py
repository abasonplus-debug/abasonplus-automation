"""Wait only for today's missing input; never retry delivery or replace invalid input."""
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo


def validate_date(data, day):
    if data.get('date') != day or data.get('verified_on') != day:
        raise ValueError('Editorial date mismatch')


def main():
    day = datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
    path = Path('content') / ('daily_editorial_' + day + '.json')
    deadline = time.monotonic() + 2700
    while True:
        if datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat() != day:
            raise RuntimeError('Berlin date changed; hold')
        if path.exists():
            validate_date(json.loads(path.read_text(encoding='utf-8')), day)
            sha = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                    out.write('editorial_sha=' + sha + '\n')
            print('Current-day editorial available; normal validators still required')
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('Current-day editorial missing after bounded 45-minute wait')
        print('Waiting for current-day editorial; no rendering or delivery', flush=True)
        time.sleep(60)
        # Only fast-forward to the trusted main branch before ANY preparation/send.
        subprocess.run(['git','fetch','--quiet','origin','main'], check=True, timeout=60)
        subprocess.run(['git','merge','--ff-only','FETCH_HEAD'], check=True, timeout=60)


if __name__ == '__main__':
    main()
