import hashlib
import json
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from cosyvoice3_daily_voiceover import (
    REFERENCE_URL, SPACE, VOICE_GAIN, MUSIC_GAIN, check, source_texts, slide_durations,
    validate_segment, concat_with_padding, render_with_narration, verify_voiceover,
)
from carousel_timing import validate_timing

def make_wav(path, duration, hz=150):
    import struct
    sr = 24000
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        samples = (struct.pack("<h", round(math.sin(2*math.pi*hz*n/sr)*4500))
                   for n in range(round(sr*duration)))
        f.writeframes(b"".join(samples))

def news_story():
    return {
        "hook": "জার্মানিতে কর্মীদের ন্যূনতম বেতন সম্পর্কে জেনে নিন।",
        "tips": [{"text": f"আইনি অধিকার ও গুরুত্বপূর্ণ তথ্য জানুন। পর্ব {i}।"}
                 for i in range(4)],
        "source_url": "https://www.bmas.de/DE/Service/Presse/Pressemitteilungen/2025/lohn.html",
        "verified_on": "2026-10-22",
    }

class VoiceoverTests(unittest.TestCase):
    def test_all_written_slides_are_spoken_exactly(self):
        story=news_story()
        got=source_texts(story)
        self.assertEqual(got,[story["hook"]]+[x["text"] for x in story["tips"]])
        self.assertEqual(len(got),5)
        story["tips"][1]["text"]="English only"
        with self.assertRaisesRegex(RuntimeError,"Bengali"):
            source_texts(story)

    def test_spoken_text_expands_slide_duration_without_truncation(self):
        times=slide_durations([2.0,4.11,6.01,3.3,2.4])
        self.assertEqual(len(times),5)
        self.assertEqual(times[0],3)
        self.assertGreater(times[2],6.2)
        meta=dict(slides=5,slide_seconds=3,slide_durations=times,
                  voiceover=dict(complete=True,engine="CosyVoice3",reference="Dan Mason",
                                 narrated_slide_count=5))
        self.assertAlmostEqual(validate_timing(meta,sum(times)),sum(times),2)
        with self.assertRaisesRegex(ValueError,"align"):
            validate_timing(meta,sum(times)-1.0)

    def test_no_old_50_second_cap_and_fail_closed_for_incomplete_voice(self):
        self.assertGreater(sum(slide_durations([14.0]*5)), 50)
        self.assertGreater(sum(slide_durations([65.0]*5)), 300)
        self.assertEqual((VOICE_GAIN, MUSIC_GAIN), (1.0, 0.20))
        with self.assertRaisesRegex(RuntimeError,"slide count"):
            slide_durations([2.0]*4)
        with self.assertRaisesRegex(ValueError,"exactly 3"):
            validate_timing(dict(slides=5,slide_seconds=3,slide_durations=[3,4,3,3,3]))
        with self.assertRaises(ValueError):
            validate_timing(dict(slides=5,slide_seconds=3,slide_durations=[3]*5,
                                 voiceover=dict(complete=True,engine="CosyVoice3",
                                                reference="OTHER",narrated_slide_count=5)))

    def test_real_wav_concat_and_script_sha_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            out=pathlib.Path(td)
            voice=out/"narration_segments"; voice.mkdir()
            story=news_story(); texts=source_texts(story)
            durations=[2.2]*5
            files=[]
            for i,text in enumerate(texts):
                p=voice/f"slide_{i:02}.wav";make_wav(p,2.2);files.append(p)
            times=slide_durations(durations)
            joined=out/"cosyvoice3_narration.wav"
            concat_with_padding(files,times,joined)
            self.assertAlmostEqual(validate_segment(joined),15.0,2)
            manifest={"model":SPACE,"reference_url":REFERENCE_URL,"source_url":story["source_url"],
                      "verified_on":story["verified_on"],
                      "segments":[{"slide":i+1,"text_sha256":hashlib.sha256(text.encode()).hexdigest(),
                                   "audio_sha256":hashlib.sha256(files[i].read_bytes()).hexdigest(),
                                   "seconds":durations[i]} for i,text in enumerate(texts)]}
            (out/"voiceover_manifest.json").write_text(json.dumps(manifest))
            meta={"slides":5,"slide_seconds":3,"slide_durations":times,
                  "voiceover":{"complete":True,"engine":"CosyVoice3","reference":"Dan Mason",
                               "reference_url":REFERENCE_URL,"narrated_slide_count":5,
                               "script_sha256":hashlib.sha256("\n".join(texts).encode()).hexdigest(),
                               "mix":"narration_100_music_20_no_amix_normalization",
                               "voice_gain":1.0,"music_gain":0.20}}
            verify_voiceover(out,story,meta)
            (out/"narration_segments"/"slide_02.wav").write_bytes(b"bad")
            with self.assertRaisesRegex(RuntimeError,"missing or altered"):
                verify_voiceover(out,story,meta)

    def test_music_mix_preserves_unity_voice_and_twenty_percent_background(self):
        self.assertEqual(VOICE_GAIN,1.0)
        self.assertEqual(MUSIC_GAIN,0.20)
        self.assertGreater(VOICE_GAIN,MUSIC_GAIN)
        self.assertEqual(round(VOICE_GAIN/MUSIC_GAIN),5)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg not installed")
    def test_script_length_over_50_seconds_is_rendered_not_truncated(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            out=pathlib.Path(td)
            durations=[11.0]*5
            for i in range(5):
                Image.new("RGB",(96,176),(20+i*20,80,160)).save(out/f"slide_{i}.png")
            voice=out/"narration.wav"
            make_wav(voice,55.0)
            music=out/"music.mp3"
            subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi",
                            "-i","sine=frequency=450:duration=3","-q:a","7",
                            str(music)],check=True,timeout=30)
            dest=out/"long_script.mp4"
            sec=render_with_narration(voice,music,durations,dest)
            self.assertGreater(sec,50.0)
            self.assertAlmostEqual(sec,55.0,delta=.15)
            self.assertGreater(dest.stat().st_size,500000)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg not installed")
    def test_full_video_mixes_actual_pcm_voice_and_music_without_online_service(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            out=pathlib.Path(td)
            durations=[3.0]*5
            for i in range(5):
                Image.new("RGB",(320,568),(30+i*35,90,160)).save(out/f"slide_{i}.png")
            voice=out/"narration.wav"
            make_wav(voice,15.0)
            music=out/"music.mp3"
            subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi",
                            "-i","sine=frequency=450:duration=16","-q:a","6",
                            str(music)],check=True,timeout=30)
            # Renderer intentionally does not require API credentials or publish.
            target=out/"sample.mp4"
            duration=render_with_narration(voice,music,durations,target)
            self.assertTrue(target.is_file())
            self.assertAlmostEqual(duration,15.0,delta=.15)
            info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
                          "-of","json",str(target)]))
            self.assertTrue(any(x.get("codec_type")=="audio" and x.get("codec_name")=="aac"
                                for x in info["streams"]))
            self.assertTrue(any(x.get("codec_type")=="video" and x.get("codec_name")=="h264"
                                for x in info["streams"]))

if __name__=="__main__":
    unittest.main()
