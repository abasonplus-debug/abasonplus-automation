#!/usr/bin/env python3
"""Isolated CC0-reference male CosyVoice3 test; never changes daily automation or publishes."""
import pathlib
import subprocess
import sys
import urllib.request
import wave
from gradio_client import Client, handle_file

SPEAKERS = {
    "dan_mason": "dan_mason.flac",
    "dave_chase": "dave_chase.flac",
    "clayton_j_smith": "clayton_j_smith.flac",
}
TEXT = "স্বাগতম। আপনি শুনছেন আবাসন প্লাস। জার্মানির গুরুত্বপূর্ণ আইন ও আপনার অধিকার নিয়ে থাকছে আজকের বিশেষ প্রতিবেদন।"
SPACE="kawshikbuet17/bengali-cosyvoice3-tts-demo"

def run(cmd,timeout=35):
    subprocess.run(cmd,timeout=timeout,check=True)

def seconds(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True).strip())

def main():
    speaker=sys.argv[1]
    if speaker not in SPEAKERS:
        raise ValueError("Invalid CC0 male voice identifier")
    out=pathlib.Path("output/cosyvoice3_deeper_male")/speaker
    out.mkdir(parents=True,exist_ok=True)
    url="https://raw.githubusercontent.com/CoisLR/TTS-Reference-Voices/main/voices/"+SPEAKERS[speaker]
    request=urllib.request.Request(url,headers={"User-Agent":"AbasonPlus-CC0-Voice-Experiment/1.0"})
    with urllib.request.urlopen(request,timeout=30) as stream: data=stream.read(3_000_001)
    if not 3000<len(data)<=3_000_000:raise RuntimeError("Invalid reference voice download")
    flac=out/"cc0_source.flac"
    flac.write_bytes(data)
    ref=out/"male_reference.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(flac),"-t","8",
         "-ar","16000","-ac","1",str(ref)])
    with wave.open(str(ref)) as f:
        duration=f.getnframes()/f.getframerate()
        if not 2<duration<=8.02:raise RuntimeError("Invalid reference duration")
    print(f"Male reference {speaker} length={duration:.2f}s from CC0 voice pack",flush=True)
    client=Client(SPACE,verbose=False)
    ans=client.predict(TEXT,handle_file(str(ref)),0,1.0,api_name="/generate_cross_lingual_audio")
    item=ans[0] if isinstance(ans,(tuple,list)) else ans
    voice=(item.get("path") or item.get("name")) if isinstance(item,dict) else item
    if not isinstance(voice,str) or not pathlib.Path(voice).is_file():
        raise RuntimeError("CosyVoice3 model returned no audio")
    original=seconds(voice)
    if not 3.0<original<14.0:raise RuntimeError(f"Unexpected original length {original}")
    # Mildly adjust tempo, pad with silence only. Never deliberately cut narration.
    tempo=max(0.93,min(1.13,original/9.4))
    played=original/tempo
    if played>9.85:raise RuntimeError(f"Would cut spoken words: {played:.3f}s")
    mp3=out/f"CosyVoice3_male_{speaker}_10s.mp3"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(voice),
         "-filter:a",f"atempo={tempo:.5f},apad=whole_dur=10",
         "-t","10","-ac","1","-ar","24000","-codec:a","libmp3lame","-qscale:a","3",str(mp3)])
    duration=seconds(mp3)
    if abs(duration-10)>0.15 or mp3.stat().st_size<1500:
        raise RuntimeError("MP3 duration/size invalid")
    (out/"script.txt").write_text(TEXT,encoding="utf-8")
    (out/"source.txt").write_text(url,encoding="utf-8")
    print(f"COSYVOICE3_DEEP_MALE_SUCCESS speaker={speaker} original={original:.3f} tempo={tempo:.3f} final={duration:.3f} bytes={mp3.stat().st_size}",flush=True)

if __name__=="__main__":
    main()
