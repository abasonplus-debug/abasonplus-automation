#!/usr/bin/env python3
"""CosyVoice3 120s law-news sample: one chunk per isolated free GitHub job; no publishing."""
import json
import pathlib
import subprocess
import sys
import urllib.request
import wave
from gradio_client import Client, handle_file

TEXTS = [
  "শুভেচ্ছা। আপনি শুনছেন আবাসন প্লাসের বিশেষ আইন সংবাদ। জার্মানিতে চাকরি করেন? তাহলে জেনে রাখুন, দুই হাজার ছাব্বিশ সালে ঘণ্টায় ন্যূনতম কত টাকা বেতন পাওয়ার কথা, কারা এই সুবিধা পান, আর বেতন কম হলে কী কী প্রমাণ রাখা জরুরি।",
  "জার্মানির শ্রম মন্ত্রণালয়ের সরকারি তথ্য অনুযায়ী, দুই হাজার ছাব্বিশ সালের পয়লা জানুয়ারি থেকে সাধারণ আইনগত ন্যূনতম মজুরি ঘণ্টায় তেরো ইউরো নব্বই সেন্ট ব্রুটো। ব্রুটো মানে কর ও সামাজিক বীমার টাকা কাটার আগের আয়। নেটো বেতনের সঙ্গে এটিকে গুলিয়ে ফেলবেন না।",
  "এই নিয়ম সাধারণত ফুলটাইম, পার্টটাইম, মিনিজব এবং জার্মানিতে কর্মরত বিদেশি শ্রমিকদের ক্ষেত্রেও প্রযোজ্য। তবে কিছু আইনি ব্যতিক্রম আছে। ধরুন, মাসে একশ ষাট ঘণ্টা বেতনযোগ্য কাজ করেছেন। তখন এই হারে ন্যূনতম মাসিক হিসাব দুই হাজার দুইশ চব্বিশ ইউরো ব্রুটো।",
  "কাজের ঘণ্টা সঠিকভাবে জানা খুব গুরুত্বপূর্ণ। রেস্তোরাঁ, হোটেল ও নির্মাণসহ কিছু খাতে কাজের শুরু, শেষ এবং মোট সময় নথিবদ্ধ করার বিশেষ নিয়ম আছে। নিজের ডায়েরিতেও প্রতিদিন কাজের সময় লিখে রাখুন। মনে রাখবেন, কাজের সময় আর বিরতির সময় সবসময় এক নয়।",
  "বেতন কম পেলে আগে চুক্তি, বেতনপত্র, ব্যাংক লেনদেন, ডিউটি তালিকা এবং মেসেজের প্রমাণ গুছিয়ে নিন। প্রয়োজন হলে নিয়োগকর্তার কাছে লিখিতভাবে পাওনা দাবি করুন। দাবির সময়সীমা নিয়ে দেরি করবেন না। দরকারে আইনজীবী, পরামর্শ কেন্দ্র কিংবা শ্রম আদালতের সহায়তা নিন।",
  "আরেকটি খবর। দুই হাজার সাতাশ সালের পয়লা জানুয়ারি থেকে আইনগত ন্যূনতম মজুরি ঘণ্টায় চৌদ্দ ইউরো ষাট সেন্ট হবে। তবে ব্যক্তিগত দাবির ফল নির্ভর করে চুক্তি ও প্রযোজ্য আইনের ওপর। তথ্য যাচাই করুন সরকারি সূত্রে। প্রয়োজনীয় খবর পেতে আবাসন প্লাসের সঙ্গে থাকুন।"
]
TEXTS.append("সরকারি নজরদারির দায়িত্বে আছে জার্মানির জোল, অর্থাৎ কাস্টমস বিভাগের বিশেষ পরিদর্শক দল। তারা ন্যূনতম মজুরি আইন মানা হচ্ছে কি না তা পরীক্ষা করে। তবে নিজের বকেয়া টাকা আদায়ের জন্য সাধারণত আলাদাভাবে দাবি জানানো বা শ্রম আদালতে যেতে হয়।")
BASE=pathlib.Path("output/cosyvoice3_news120")
SOURCE="https://raw.githubusercontent.com/CoisLR/TTS-Reference-Voices/main/voices/alana_jordan.flac"

def main():
    idx=int(sys.argv[1])
    assert 0<=idx<len(TEXTS)
    out=BASE/f"segment_{idx+1:02}"
    out.mkdir(parents=True,exist_ok=True)
    text=TEXTS[idx]
    assert 100<len(text)<500
    raw=out/"reference.flac"
    request=urllib.request.Request(SOURCE,headers={"User-Agent":"AbasonPlus-Voice-Quality-Test/1.0"})
    with urllib.request.urlopen(request,timeout=30) as response: data=response.read(3000001)
    if not 3000<len(data)<=3000000: raise RuntimeError("Voice ref unavailable")
    raw.write_bytes(data)
    ref=out/"reference.wav"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),
          "-t","8","-ar","16000","-ac","1",str(ref)],check=True,timeout=30)
    with wave.open(str(ref)) as w:
        if not 1.0<=w.getnframes()/w.getframerate()<=30.0:raise RuntimeError("Reference duration invalid")
    print("CosyVoice3 real model synthesis segment",idx+1,":",text,flush=True)
    client=Client("kawshikbuet17/bengali-cosyvoice3-tts-demo",verbose=False)
    response=client.predict(text,handle_file(str(ref)),0,1.0,api_name="/generate_cross_lingual_audio")
    result=response[0] if isinstance(response,(list,tuple)) else response
    path=result.get("path") or result.get("name") if isinstance(result,dict) else result
    if not isinstance(path,str) or not pathlib.Path(path).is_file():raise RuntimeError("No generated audio from CosyVoice3")
    dest=out/f"part_{idx+1:02}.wav"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(path),
           "-ac","1","-ar","24000","-c:a","pcm_s16le",str(dest)],check=True,timeout=30)
    with wave.open(str(dest)) as w:
        duration=w.getnframes()/w.getframerate()
        if not 5<duration<70: raise RuntimeError(f"Invalid speech length: {duration}")
    (out/"text.txt").write_text(text,encoding="utf-8")
    (out/"duration.txt").write_text(str(duration),encoding="utf-8")
    print(f"COSYVOICE3_REAL_SEGMENT_SUCCESS part={idx+1} seconds={duration:.3f} bytes={dest.stat().st_size}",flush=True)

if __name__=="__main__":main()
