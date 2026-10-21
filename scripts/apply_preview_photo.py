"""Apply a photo-only correction to output, never to a published editorial.

Used by the existing daily workflow's explicit preview-request push. The Make
delivery step remains schedule-only. No facts, slide text, timing or approval is
changed by this helper; the changed MP4 needs a fresh exact owner OK.
"""
import copy
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def apply(story, editorial_bytes, request, day):
    if request.get('date') != day or story.get('verified_on') != day:
        raise ValueError('Preview correction is not for today in Europe/Berlin')
    if hashlib.sha256(editorial_bytes).hexdigest() != request.get('editorial_sha256'):
        raise ValueError('Editorial changed since photo correction was prepared')
    index = request.get('slide_index')
    photos = story.get('photos', [])
    if type(index) is not int or not 1 <= index < len(photos):
        raise ValueError('Photo-only tip slide index required')
    if photos[index].get('url') != request.get('expected_original_url'):
        raise ValueError('Original photo identity mismatch')
    photo = copy.deepcopy(request.get('photo', {}))
    if (urlparse(photo.get('url', '')).scheme != 'https'
        or urlparse(photo.get('url', '')).hostname != 'images.pexels.com'
        or urlparse(photo.get('source_page', '')).scheme != 'https'
        or urlparse(photo.get('source_page', '')).hostname != 'www.pexels.com'
        or not urlparse(photo.get('source_page', '')).path.startswith('/photo/')
        or photo.get('license') != 'Pexels Free License'
        or not photo.get('creator') or not photo.get('scene') or not photo.get('scene_match')):
        raise ValueError('Verified photograph, creator and license required')
    query = request.get('query', '')
    if not isinstance(query, str) or not 8 <= len(query) <= 130:
        raise ValueError('Matching photographic query required')
    photo['source'] = photo['source_page']
    result = copy.deepcopy(story)
    result['photos'][index] = photo
    result['tips'][index-1]['query'] = query
    if len({p['url'] for p in result['photos']}) != len(result['photos']):
        raise ValueError('Preview photographs must remain distinct')
    result['preview_correction'] = {'original_preview_run_id': request['original_preview_run_id'],
                                    'slide_index': index, 'reason': request['reason'],
                                    'requires_new_exact_approval': True}
    return result


def main():
    if os.environ.get('GITHUB_EVENT_NAME') != 'push':
        raise RuntimeError('Photo correction only runs on an explicit preview-request push; NO POSTS')
    day = datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
    story_path = ROOT/'output/daily_research_story.json'
    request = json.loads((ROOT/'previews/tiktok/current.json').read_text())
    editorial = (ROOT/'content'/f'daily_editorial_{day}.json').read_bytes()
    result = apply(json.loads(story_path.read_text()), editorial, request, day)
    story_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Photo correction applied to preview output only; source editorial unchanged; NO POSTS')


if __name__ == '__main__':
    main()
