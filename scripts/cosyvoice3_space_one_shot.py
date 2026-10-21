#!/usr/bin/env python3
"""One-off CosyVoice3 Bengali test via a public Hugging Face Gradio demo.
CC0 LibriVox speaker reference, no payment/login/secrets, never publishes.
"""
import json
import pathlib
import shutil
import subprocess
import urllib.request
import wave
from gradio_client import Client, handle_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "cosyvoice3_test"
OUT.mkdir(parents=True, exist_ok=True)
SPACE = "kawshikbuet17/bengali-cosyvoice3-tts-demo"
TEXT = ("স্কুলে যাওয়ার পথে ছেলেটি একটি অসহায় কুকুরকে দেখতে পেল। "
        "সে কুকুরটিকে খাবার দিল। শুরু হলো নতুন বন্ধুত্ব। "
        "একটু মমতা, অনেক ভালোবাসা।")
SOURCE = "https://raw.githubusercontent.com/CoisLR/TTS-Reference-Voices/main/voices/alana_jordan.flac"

print("Free one-off CosyVoice3 model demo. No fees/trial/tokens.", flush=True)
raw = OUT / "cc0_reference.flac"
ref = OUT / "cc0_reference.wav"
req = urllib.request.Request(SOURCE,headers={"User-Agent":"AbasonPlus-CosyVoice3-Preview/1.0"})
with urllib.request.urlopen(req,timeout=25) as response:
    data=response.read(3_000_001)
if not 3000<len(data)<=3_000_000:
    raise RuntimeError("CC0 reference unavailable or too large")
raw.write_bytes(data)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
                "-t","8","-ac","1","-ar","16000",str(ref)],check=True,timeout=30)
with wave.open(str(ref)) as w:
    duration=w.getnframes()/w.getframerate()
    assert 1<=duration<=30 and w.getframerate()==16000
print("CC0 reference duration:", duration,flush=True)

client=Client(SPACE,verbose=False)
api=client.view_api(return_format="dict",print_info=False)
(OUT/"available_api.json").write_text(json.dumps(api,indent=2,default=str),encoding="utf-8")
endpoints=api.get("named_endpoints",{})
names=[n for n in endpoints if "generate_cross_lingual_audio" in n]
if len(names)!=1:
    raise RuntimeError(f"No unambiguous CosyVoice3 TTS endpoint: {list(endpoints)}")
name=names[0]
print("Calling CosyVoice3",name,flush=True)
result=client.predict(TEXT,handle_file(str(ref)),0,1.0,api_name=name)
output=result[0] if isinstance(result,(tuple,list)) else result
path=(output.get("path") or output.get("name")) if isinstance(output,dict) else output
if not isinstance(path,str) or not pathlib.Path(path).is_file():
    raise RuntimeError("CosyVoice3 returned no speech file")
mp3=OUT/"boy_and_dog_cosyvoice3.mp3"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(path),
                "-ac","1","-ar","24000","-codec:a","libmp3lame","-qscale:a","3",str(mp3)],check=True,timeout=30)
assert mp3.is_file() and mp3.stat().st_size>1500
(OUT/"script.txt").write_text(TEXT,encoding="utf-8")
print("COSYVOICE3_AUDIO_SUCCESS",mp3,mp3.stat().st_size,flush=True)
