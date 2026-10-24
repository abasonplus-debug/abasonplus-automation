"""Build a complete exact-video approval only AFTER an explicit owner response.

Offline only: never uploads, dispatches, generates media or grants future consent.
"""
import copy
import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from .tiktok_approval import ACCOUNT, validate_approval
except ImportError:
    from tiktok_approval import ACCOUNT, validate_approval


def build_approval(preview, source_run, video_sha256, settings, owner_evidence, approved_at):
    """Copy immutable preview metadata, never reconstruct or omit narrated format."""
    if not isinstance(owner_evidence, str) or not owner_evidence.strip():
        raise ValueError('Explicit exact-preview owner evidence is required')
    if preview.get('status') != 'preview_only' or preview.get('posting_enabled') is not False:
        raise ValueError('Expected original non-publishing preview package')
    if video_sha256 != preview.get('video_sha256') or not re.fullmatch(r'[a-f0-9]{64}', video_sha256):
        raise ValueError('Actual MP4 hash differs from reviewed preview')
    head = source_run.get('head_sha', '')
    if (not re.fullmatch(r'[a-f0-9]{40}', head) or source_run.get('conclusion') != 'success'
            or source_run.get('head_branch') != 'main' or not str(source_run.get('id', '')).isdigit()):
        raise ValueError('Successful immutable main preview run required')
    day = preview.get('date')
    stamp = datetime.fromisoformat(approved_at.replace('Z', '+00:00'))
    created = datetime.fromisoformat(source_run['created_at'].replace('Z', '+00:00'))
    if (stamp.tzinfo is None or created.tzinfo is None or stamp < created
            or created.astimezone(ZoneInfo('Europe/Berlin')).date().isoformat() != day):
        raise ValueError('Owner approval must follow the current-day preview')
    caption = preview.get('caption', '').strip()
    if not caption or hashlib.sha256(caption.encode()).hexdigest() != preview.get('caption_sha256'):
        raise ValueError('Preview caption hash mismatch')
    fmt = copy.deepcopy(preview.get('format', {}))
    voice = fmt.get('voiceover', {})
    times = fmt.get('slide_durations', [])
    if (voice.get('complete') is not True or voice.get('engine') != 'CosyVoice3'
            or voice.get('reference') != 'Dan Mason' or voice.get('voice_gain') != 1
            or voice.get('music_gain') != .2 or not re.fullmatch(r'[a-f0-9]{64}', voice.get('script_sha256',''))
            or not 5 <= fmt.get('slides', 0) <= 16 or len(times) != fmt['slides']
            or voice.get('narrated_slide_count') != fmt['slides']):
        raise ValueError('Complete exact narrated format is required')
    if settings.get('video_made_with_ai') is not True or settings.get('commercialContentType') not in ('none','brand_organic','brand_content'):
        raise ValueError('Reviewed AI and commercial disclosures required')
    approval = dict(copy.deepcopy(settings), date=day, approved_at=approved_at,
                    approval=owner_evidence.strip(), consent_scope='Only this exact displayed MP4, caption, comment and settings; no future consent.',
                    account_id=ACCOUNT, account_username='abasonplus',
                    preview_run_id=str(source_run['id']), preview_head_sha=head,
                    video_sha256=video_sha256, caption_sha256=preview['caption_sha256'],
                    format=fmt, first_comment=preview.get('first_comment', ''))
    validate_approval(approval, day, video_sha256, caption, source_run['id'])
    return approval
