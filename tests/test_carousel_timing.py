import pathlib,sys,unittest,json,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from carousel_timing import validate_timing, SLIDE_SECONDS, MIN_SLIDES, MAX_SLIDES, MAX_DURATION_SECONDS

def metadata(ds):
    return dict(slides=len(ds),slide_seconds=None,timing_mode='narration_v1',slide_durations=ds,
                narration={'engine':'espeak-ng-bn','sha256':'a'*64,'segment_seconds':[d-.4 for d in ds]})

class TimingTests(unittest.TestCase):
    def test_no_fifteen_or_fifty_second_limit(self):
        for ds in ([1]*5,[8,14,22,18,31],[60]*8):
            self.assertEqual(validate_timing(metadata(ds),sum(ds)),sum(ds))
        self.assertIsNone(SLIDE_SECONDS);self.assertIsNone(MAX_DURATION_SECONDS)
    def test_malformed_nonfinite_or_cut_speech_held(self):
        for ds in ([8]*4,[8]*65,[True]*5,[float('nan')]*5,[0]*5):
            with self.assertRaises(ValueError):validate_timing(metadata(ds))
        m=metadata([8]*5);m['narration']['segment_seconds'][0]=9
        with self.assertRaises(ValueError):validate_timing(m)
        m=metadata([8]*5);m['narration']['sha256']=''
        with self.assertRaises(ValueError):validate_timing(m)
    def test_old_policy_rejected_for_new_renders(self):
        with self.assertRaises(ValueError):validate_timing(dict(slides=5,slide_seconds=3,slide_durations=[3]*5),15)
        with self.assertRaises(ValueError):validate_timing(metadata([8]*5),50)
    def test_style_contract_matches(self):
        p=json.loads((pathlib.Path(__file__).resolve().parents[1]/'config/carousel_style.json').read_text())
        self.assertEqual((p['slide_seconds'],p['min_slides'],p['max_slides']),(SLIDE_SECONDS,MIN_SLIDES,MAX_SLIDES))
