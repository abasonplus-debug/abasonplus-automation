import array, pathlib, sys, tempfile, unittest, wave
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from cosyvoice3_daily_voiceover import validate_segment

class VoiceSignalQualityTests(unittest.TestCase):
    def check_samples(self, samples):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'segment.wav'
            with wave.open(str(p),'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
                f.writeframes(array.array('h',samples).tobytes())
            return validate_segment(p)
    def test_sustained_clipping_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'clipping'):
            self.check_samples([32767,-32767]*12000)
    def test_dc_corruption_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'DC offset'):
            self.check_samples([4000]*24000)
    def test_isolated_peak_does_not_disguise_near_silence(self):
        with self.assertRaisesRegex(RuntimeError,'usable signal'):
            self.check_samples([500]+[0]*23999)
