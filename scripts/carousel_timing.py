"""Owner timing (20 October 2026): every slide exactly three seconds."""
SLIDE_SECONDS=3
MIN_SLIDES=5
MAX_DURATION_SECONDS=50
MAX_SLIDES=MAX_DURATION_SECONDS//SLIDE_SECONDS

def validate_timing(meta, duration=None):
    count=meta.get('slides')
    if type(count) is not int or not MIN_SLIDES<=count<=MAX_SLIDES:
        raise ValueError('Carousel must contain 5–16 slides within 50 seconds')
    if meta.get('slide_seconds')!=SLIDE_SECONDS or meta.get('slide_durations')!=[SLIDE_SECONDS]*count:
        raise ValueError('Every slide must be exactly three seconds')
    expected=count*SLIDE_SECONDS
    if duration is not None and abs(float(duration)-expected)>0.12:
        raise ValueError('MP4 duration does not match slide count × three seconds')
    return expected
