"""Owner-fixed timing: every image exactly two seconds, never three."""
SLIDE_SECONDS=2
MIN_SLIDES=5
MAX_SLIDES=25

def validate_timing(meta, duration=None):
    count=meta.get('slides')
    if type(count) is not int or not MIN_SLIDES<=count<=MAX_SLIDES:
        raise ValueError('Carousel must contain 5–25 slides within 50 seconds')
    if meta.get('slide_seconds')!=SLIDE_SECONDS or meta.get('slide_durations')!=[SLIDE_SECONDS]*count:
        raise ValueError('Every slide must be exactly two seconds')
    expected=count*SLIDE_SECONDS
    if duration is not None and abs(float(duration)-expected)>0.12:
        raise ValueError('MP4 duration does not match slide count × two seconds')
    return expected
