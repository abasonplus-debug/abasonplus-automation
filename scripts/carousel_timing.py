"""22 October owner policy: narration determines slide/video length.

No editorial 15/50-second cap. Transport/provider limits remain separate gates.
"""
import math
TIMING_MODE = 'narration_v1'
SLIDE_SECONDS = None
MIN_SLIDES = 5
MAX_SLIDES = 64  # bounded processing count, not a duration target
MAX_DURATION_SECONDS = None

def validate_timing(meta, duration=None):
    count = meta.get('slides')
    ds = meta.get('slide_durations')
    voice = meta.get('narration', {})
    if type(count) is not int or not MIN_SLIDES <= count <= MAX_SLIDES:
        raise ValueError('Unsupported slide count')
    if meta.get('timing_mode') != TIMING_MODE or meta.get('slide_seconds') is not None:
        raise ValueError('New renders require narration-based timing')
    if not isinstance(ds,list) or len(ds)!=count or any(type(d) not in (int,float) or not math.isfinite(d) or d<=0 for d in ds):
        raise ValueError('Missing or invalid measured slide durations')
    measured = voice.get('segment_seconds')
    if (voice.get('engine') != 'espeak-ng-bn' or not isinstance(measured,list) or len(measured)!=count
        or any(type(d) not in (int,float) or not math.isfinite(d) or d<=0 for d in measured)
        or any(ds[i] < measured[i] or ds[i]-measured[i] > 1 for i in range(count))):
        raise ValueError('Slide timing must cover its complete measured narration')
    import re
    if not re.fullmatch(r'[a-f0-9]{64}',voice.get('sha256','')):
        raise ValueError('Narration identity missing')
    expected=sum(ds)
    if duration is not None and (not math.isfinite(float(duration)) or abs(float(duration)-expected)>0.15):
        raise ValueError('MP4 duration differs from measured script/narration timing')
    return expected
