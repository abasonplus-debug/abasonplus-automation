"""Bounded photo repair and preflight. No video, compositing or publishing.

Only verified manifest candidates are used. Every crop is subject-matched again;
readability thresholds, font size and text placement are never relaxed.
"""
import io
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from PIL import Image, ImageOps
from carousel_style import photo_stats, readable_photo


def candidates(photo):
    alternatives = photo.get('alternatives', [])
    if not isinstance(alternatives, list) or len(alternatives) > 2:
        raise ValueError('At most two independently verified alternatives per slide')
    result = [photo] + alternatives
    for p in result:
        source = p.get('source') or p.get('source_page', '')
        if p.get('source') and p.get('source_page') and p['source'] != p['source_page']:
            raise ValueError('Conflicting photographic source fields')
        image_url = urlparse(p.get('url', ''))
        page = urlparse(source)
        if (image_url.scheme != 'https' or image_url.hostname != 'images.pexels.com'
                or page.scheme != 'https' or page.hostname != 'www.pexels.com'
                or not page.path.startswith('/photo/') or p.get('license') != 'Pexels Free License'
                or not p.get('creator') or not p.get('scene')):
            raise ValueError('Unverified photographic candidate; no automatic substitution')
        if p is not photo and not p.get('scene_match'):
            raise ValueError('Alternative needs an explicit topic-to-scene match')
    return result


def download(url, opener=urlopen, sleep=time.sleep):
    for attempt in range(3):
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 AbasonPlus preview research'})
            with opener(req, timeout=30) as response:
                final = urlparse(response.geturl())
                if final.scheme != 'https' or final.hostname != 'images.pexels.com':
                    raise ValueError('Photograph redirected outside approved host')
                raw = response.read(17_000_001)
            if len(raw) > 17_000_000:
                raise ValueError('Photograph exceeds bounded download size')
            picture = Image.open(io.BytesIO(raw)).convert('RGB')
            if min(picture.size) < 1600:
                raise ValueError('Photograph too small; refusing upscale')
            return picture
        except HTTPError as exc:
            transient = exc.code in (408, 429) or 500 <= exc.code < 600
            if not transient or attempt == 2:
                raise RuntimeError('Photograph HTTP ' + str(exc.code)) from None
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise RuntimeError('Photograph network/decode failure after bounded attempts') from None
        sleep(2 ** attempt)


def readable_crop(picture, placements, query, guard):
    # Center first; then a bounded natural crop search, never dark panels/blur/overlays.
    centers = ((.5,.5), (0,.5), (1,.5), (.25,.5), (.75,.5), (.5,0), (.5,1))
    for center in centers:
        crop = ImageOps.fit(picture, (1080,1920), method=Image.Resampling.LANCZOS, centering=center)
        for index, regions in enumerate(placements):
            if readable_photo(photo_stats(crop, regions)) and guard.approved(crop, query):
                return crop, index, list(center)
    raise ValueError('No subject-matched readable natural crop; QA preserved')


def select(photo, placements, query, guard, used, loader=download):
    if photo.get("asset_type")=="illustration":
        from illustration_assets import select_illustration
        return select_illustration(photo,placements,query,guard,used,Path(__file__).resolve().parents[1])
    failures = []
    for index, p in enumerate(candidates(photo)):
        identity = urlparse(p['url']).path  # query variants cannot bypass distinct-photo checks
        if identity in used:
            failures.append({'candidate': index, 'reason': 'duplicate photograph'})
            continue
        try:
            picture = loader(p['url'])
            crop, placement, center = readable_crop(picture, placements, query, guard)
        except (ValueError, RuntimeError) as exc:
            failures.append({'candidate': index, 'reason': str(exc)[:160]})
            continue
        used.add(identity)
        evidence = {'candidate': index, 'source': p.get('source') or p['source_page'],
                    'crop_center': center, 'prior_rejections': failures}
        return crop, placement, p, evidence
    raise RuntimeError('All verified photo candidates held: ' + json.dumps(failures))


def main():
    from PIL import ImageFont
    from bilingual_text import BilingualText
    from carousel_style import POLICY, layout, paint
    from photo_relevance import PhotoRelevanceGuard
    root = Path(__file__).resolve().parents[1]
    story = json.loads((root/'output/daily_research_story.json').read_text())
    fonts = Path('/usr/share/fonts')
    bn = next(p for p in fonts.rglob('*.ttf') if 'Bengali' in p.name and 'Bold' in p.name)
    latin = next(fonts.rglob('NotoSans-Bold.ttf'))
    tokens = BilingualText(bn, latin).tokens
    texts = [story['hook']] + [p['text'] for p in story['tips']]
    queries = [story['cover_query']] + [p['query'] for p in story['tips']]
    report = {'status': 'running', 'no_posts': True, 'slides': []}
    output = root/'output/photo_preflight.json'
    used = set()
    try:
        guard = PhotoRelevanceGuard()
        for i, (text, query, photo) in enumerate(zip(texts, queries, story['photos'], strict=True)):
            font = ImageFont.truetype(str(bn), POLICY['hook_font_px'] if i == 0 else POLICY['body_font_px'])
            _, boxes = paint(layout(text, font, tokens), tokens)
            _, _, _, evidence = select(photo, [boxes], query, guard, used)
            report['slides'].append({'slide': i+1, 'status': 'passed', **evidence})
        report['status'] = 'passed_photo_and_layout_only'
    except Exception as exc:
        report['status'] = 'held'
        report['error'] = str(exc)[:1500]
        raise
    finally:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
