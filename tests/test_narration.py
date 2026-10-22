import hashlib,json,pathlib,sys,tempfile,unittest,wave
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from narration import prepare,verify,wave_seconds
class NarrationTests(unittest.TestCase):
    def test_missing_voice_and_changed_script_held(self):
        with tempfile.TemporaryDirectory() as d:
            brief={'hook':'বাংলা পরীক্ষা','tips':[]}
            with self.assertRaises(ValueError):verify({'narration':{}},brief,d)
    def test_silence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'silent.wav'
            with wave.open(str(p),'wb') as w:
                w.setparams((1,2,22050,0,'NONE','not compressed'));w.writeframes(b'\x00\x00'*22050)
            with self.assertRaises(ValueError):wave_seconds(p)
    def test_exact_script_local_command_no_shell_or_api(self):
        with tempfile.TemporaryDirectory() as d:
            def fake(args,**kw):
                if args[0]=='espeak-ng':
                    self.assertEqual(args[:3],['espeak-ng','-v','bn'])
                    self.assertEqual(kw['input'],'মূল বাংলা বক্তব্য।')
                    self.assertNotIn('shell',kw)
                    raise RuntimeError('fixture stops before synthesis')
            with patch('narration.subprocess.run',side_effect=fake):
                with self.assertRaisesRegex(RuntimeError,'fixture'):prepare(['মূল বাংলা বক্তব্য।'],d)
