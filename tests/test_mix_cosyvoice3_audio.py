"""Generate tiny synthetic media locally to verify MP4 voice mixing without model calls."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mix_cosyvoice3_audio", ROOT / "scripts" / "mix_cosyvoice3_audio.py")
mixer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mixer)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe not available')
class AudioMixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.video, self.wav, self.output = root/'original.mp4', root/'speech.wav', root/'mixed.mp4'
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=blue:s=144x256:r=15:d=3',
                        '-f','lavfi','-i','sine=frequency=220:sample_rate=16000:duration=3',
                        '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(self.video)],
                       check=True, timeout=30)
        with wave.open(str(self.wav), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b'\x00\x00' * (16000 * 2))

    def test_mix_preserves_original_video(self):
        original_bytes = self.video.read_bytes()
        mixer.mix(self.video,self.wav,self.output)
        self.assertTrue(self.output.is_file())
        self.assertEqual(self.video.read_bytes(),original_bytes)
        streams = mixer.probe(self.output)['streams']
        self.assertTrue(any(x['codec_type']=='video' for x in streams))
        self.assertTrue(any(x['codec_type']=='audio' for x in streams))

    def test_refuses_overwrite(self):
        with self.assertRaisesRegex(ValueError,'overwritten'):
            mixer.mix(self.video,self.wav,self.video)

    def test_refuses_speech_over_video_duration(self):
        with wave.open(str(self.wav),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
            w.writeframes(b'\x00\x00' * (16000*4))
        with self.assertRaisesRegex(ValueError,'longer'):
            mixer.validate_media(self.video,self.wav)


if __name__=='__main__':
    unittest.main()
