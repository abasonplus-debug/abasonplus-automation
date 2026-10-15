#!/usr/bin/env python3
"""Render an original 15-second Bengali housing-tips video with free tools."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlretrieve
import math
import subprocess
import wave
import struct
from PIL import Image, ImageDraw, ImageFont, features

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FONT = next((p for p in Path("/usr/share/fonts").rglob("*.ttf") if "Bengali" in p.name and "Regular" in p.name), None)
if not FONT:
    raise RuntimeError("Install fonts-noto-core to render Bengali")
if not features.check("raqm"):
    raise RuntimeError("Pillow must support libraqm for correct Bengali shaping")
big = ImageFont.truetype(str(FONT), 76)
medium = ImageFont.truetype(str(FONT), 51)
small = ImageFont.truetype(str(FONT), 33)
topics = [
    ("জমি কেনার আগে", ["মালিকানার কাগজ যাচাই করুন", "দলিল ও খতিয়ান মিলিয়ে দেখুন", "দাগ নম্বর ও সীমানা পরীক্ষা করুন", "বিরোধ বা দায় আছে কি না জানুন"]),
    ("ফ্ল্যাট কেনার আগে", ["প্রকল্পের অনুমোদন যাচাই করুন", "চুক্তির শর্ত ভালোভাবে পড়ুন", "হস্তান্তরের সময় জেনে নিন", "বিশেষজ্ঞের পরামর্শ নিন"]),
    ("বাড়ি নির্মাণের আগে", ["অনুমোদিত নকশা যাচাই করুন", "মাটির পরীক্ষা সম্পর্কে জানুন", "উপকরণের মান যাচাই করুন", "প্রকৌশলীর পরামর্শ নিন"]),
]
date = datetime.now(timezone(timedelta(hours=6))).date()
heading, tips = topics[date.toordinal() % len(topics)]
slides = [(heading, "আবাসন+ | আজকের চারটি পরামর্শ")] + [(tip, f"পরামর্শ {i}/৪") for i, tip in enumerate(tips, 1)]
logo = None
try:
    logo_path = OUT / "logo.png"
    urlretrieve("https://abasonplus.wordpress.com/wp-content/uploads/2026/10/abasonplus_round_transparent.png", logo_path)
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((240, 240))
except Exception as e:
    print("Logo unavailable, continuing with wordmark:", e)

def centered(draw, text, y, font, color):
    bbox = draw.textbbox((0, 0), text, font=font, direction="ltr")
    width = bbox[2] - bbox[0]
    draw.text(((1080 - width)/2, y), text, font=font, fill=color, direction="ltr")

for i, (main, subtitle) in enumerate(slides):
    im = Image.new("RGB", (1080, 1920), (9, 29, 49))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((65, 105, 1015, 1815), radius=65, fill=(22, 59, 80), outline=(62, 191, 167), width=7)
    if logo:
        im.paste(logo, ((1080-logo.width)//2, 215), logo)
    else:
        centered(d, "আবাসন+", 265, big, (125, 239, 207))
    d.line((145, 525, 935, 525), fill=(62, 191, 167), width=5)
    centered(d, main, 780, big, (255, 255, 255))
    centered(d, subtitle, 1060, medium, (203, 230, 235))
    centered(d, "abasonplus.wordpress.com", 1650, small, (125, 239, 207))
    im.save(OUT / f"slide_{i}.png", optimize=True)

playlist = OUT / "slides.txt"
playlist.write_text("".join(f"file 'slide_{i}.png'\nduration 3\n" for i in range(5)) + "file 'slide_4.png'\n", encoding="utf-8")

# Original, quiet four-note musical motif (no third-party copyrighted audio).
rate = 22050
notes = [261.63, 329.63, 392.0, 329.63, 293.66]
with wave.open(str(OUT / "original_audio.wav"), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(rate)
    for j in range(15 * rate):
        t = j / rate
        frequency = notes[int(t / 0.75) % len(notes)]
        envelope = min(1.0, (t % 0.75) * 12) * max(0.0, 1 - (t % 0.75) / 0.75)
        value = 0.12 * envelope * (math.sin(2 * math.pi * frequency * t) + 0.2 * math.sin(4 * math.pi * frequency * t))
        wav.writeframesraw(struct.pack("<h", int(32767 * value)))
# Prefer the user-supplied soundtrack when it is present in the repository.
custom_audio = ROOT / "assets" / "abasonplus.mp3"
audio_path = custom_audio if custom_audio.is_file() else OUT / "original_audio.wav"
print("Soundtrack:", audio_path)
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(playlist),
    "-i", str(audio_path),
    "-t", "15", "-r", "25", "-vf", "format=yuv420p",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
    "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart",
    str(OUT / "abasonplus_daily.mp4")
], cwd=OUT, check=True)
print("Created", OUT / "abasonplus_daily.mp4")
