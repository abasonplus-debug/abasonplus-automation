"""Carousel timing: three seconds minimum; voiced slides stay visible until speech finishes.

Old unvoiced previews preserve their historical exactly-three-seconds contract.
Narrated clip length equals the full spoken script, with no arbitrary video time ceiling.
"""
import math

SLIDE_SECONDS = 3
MIN_SLIDES = 5
MAX_SLIDES = 16  # Visual slide-count policy, not a limit on video duration

def validate_timing(meta, duration=None):
    count = meta.get("slides")
    if type(count) is not int or not MIN_SLIDES <= count <= MAX_SLIDES:
        raise ValueError("Carousel must contain 5–16 slides")
    times = meta.get("slide_durations")
    if not isinstance(times, list) or len(times) != count:
        raise ValueError("Each slide must have a duration")
    if meta.get("slide_seconds") != SLIDE_SECONDS:
        raise ValueError("Minimum slide time must be three seconds")
    voice = meta.get("voiceover")
    narrated = isinstance(voice, dict) and voice.get("complete") is True
    if narrated:
        if not (voice.get("engine") == "CosyVoice3" and
                voice.get("reference") == "Dan Mason" and
                voice.get("narrated_slide_count") == count):
            raise ValueError("Selected full CosyVoice3 voiceover not confirmed")
        if not all(type(t) in (float, int) and math.isfinite(t) and
                   t >= SLIDE_SECONDS for t in times):
            raise ValueError("Narration-aligned slide duration is invalid")
    elif times != [SLIDE_SECONDS] * count:
        raise ValueError("Without verified voiceover every slide must be exactly 3 seconds")
    expected = sum(times)
    if duration is not None and abs(float(duration) - expected) > 0.15:
        raise ValueError("MP4 duration does not align with slide/narration timeline")
    return expected
