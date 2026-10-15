#!/usr/bin/env python3
"""Render an original 15-second Bengali housing-tips video with free tools."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen
from urllib.parse import urlencode
import json
import io
import re
from PIL import ImageOps
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
hooks = {
    "জমি কেনার আগে": "জমি কিনবেন? এই ৪টি ভুল এড়ান!",
    "ফ্ল্যাট কেনার আগে": "ফ্ল্যাট কেনার আগে ৪টি বিষয় জানুন!",
    "বাড়ি নির্মাণের আগে": "বাড়ি বানাবেন? আগে এই ৪টি দেখুন!",
}
hook = hooks[heading]
slides = [(hook, "শেষ পর্যন্ত দেখুন • গুরুত্বপূর্ণ ৪টি টিপস")] + [(tip, f"পরামর্শ {i}/৪") for i, tip in enumerate(tips, 1)]
hashtags = "#Bangladesh #RealEstate #Property #Housing #Home #জমি #আবাসন #AbasonPlus"
(OUT / "title.txt").write_text(f"{hook} | আবাসন+ #Bangladesh #RealEstate #Property", encoding="utf-8")
(OUT / "caption.txt").write_text(
    f"{hook}\\n\\n" + "\\n".join(f"✅ {i}. {tip}" for i, tip in enumerate(tips, 1))
    + f"\\n\\nআরও তথ্য: https://abasonplus.wordpress.com/\\n\\n{hashtags}", encoding="utf-8"
)
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

# Search Wikimedia Commons for topic-specific photographs with reusable licenses.
# Search terms are tied to each slide's message, not random stock photos.
SCENES = {
    "জমি কেনার আগে": ["green agricultural land Bangladesh", "landscape green fields", "land survey landscape", "rural landscape", "agricultural land"],
    "ফ্ল্যাট কেনার আগে": ["modern apartment buildings", "residential apartment exterior", "apartment building construction", "modern residential building", "apartment architecture"],
    "বাড়ি নির্মাণের আগে": ["house construction building", "architectural house plan", "building foundation construction", "building construction site", "civil engineer construction"],
}
KEYWORDS = {
    "গাছ": "lush green trees forest", "বাগান": "beautiful flower garden",
    "গার্ডেন": "beautiful green garden", "ফুল": "colorful flower garden",
    "জমি": "green agricultural land", "দলিল": "paper documents desk",
    "খতিয়ান": "land survey map", "সীমানা": "rural field fence",
    "ফ্ল্যাট": "modern apartment building", "প্রকল্প": "residential apartment construction",
    "চুক্তি": "paperwork signing contract", "হস্তান্তর": "modern apartment interior",
    "বাড়ি": "beautiful residential house", "নকশা": "architectural blueprint",
    "মাটি": "construction ground foundation", "উপকরণ": "building materials construction",
    "প্রকৌশলী": "construction engineer hardhat", "মালিকানা": "property deed document",
    "দাগ": "survey field landscape", "বিরোধ": "property documents",
}

def image_for(query, slide_index):
    params = urlencode({"action": "query", "generator": "search", "gsrsearch": f'filetype:bitmap {query}',
        "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 1100, "format": "json"})
    api = "https://commons.wikimedia.org/w/api.php?" + params
    try:
        req = Request(api, headers={"User-Agent": "AbasonPlusEducationBot/1.0 (https://abasonplus.wordpress.com/)"})
        with urlopen(req, timeout=12) as response:
            pages = json.load(response).get("query", {}).get("pages", {})
        for page in sorted(pages.values(), key=lambda x: x.get("index", 999)):
            info = (page.get("imageinfo") or [{}])[0]
            metadata = info.get("extmetadata") or {}
            license_name = re.sub("<[^>]+>", "", metadata.get("LicenseShortName", {}).get("value", ""))
            if not (license_name.startswith("CC BY") or license_name in ("CC0", "Public domain", "Public Domain")):
                continue
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue
            with urlopen(Request(url, headers={"User-Agent": "AbasonPlusEducationBot/1.0"}), timeout=15) as response:
                raw = response.read(7_000_000)
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            if min(image.size) < 400:
                continue
            attribution = metadata.get("Artist", {}).get("value", "Wikimedia Commons")
            attribution = re.sub("<[^>]+>", "", attribution).strip()[:150]
            with (OUT / "image_credits.txt").open("a", encoding="utf-8") as credits:
                credits.write(f"Slide {slide_index + 1}: {page.get('title')} | {license_name} | {attribution} | {info.get('descriptionurl', '')}\\n")
            print(f"Slide {slide_index + 1} scene: {query}, source: {page.get('title')}")
            return ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
    except Exception as exc:
        print("Commons image lookup failed:", query, str(exc)[:150])
    return None

for i, (main, subtitle) in enumerate(slides):
    query = next((term for key, term in KEYWORDS.items() if key in main), None)
    if not query:
        query = SCENES[heading][i]
    im = image_for(query, i)
    if im is None:
        im = Image.new("RGB", (1080, 1920), (9, 29, 49))
    # The text area spans 80% of image width, with translucent contrast panel.
    im = im.convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    panel = ImageDraw.Draw(overlay)
    panel.rounded_rectangle((108, 650, 972, 1310), radius=48, fill=(3, 24, 32, 185), outline=(125, 239, 207, 220), width=5)
    panel.rounded_rectangle((80, 1540, 1000, 1760), radius=35, fill=(3, 24, 32, 185))
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im)
    if logo:
        im.paste(logo, ((1080-logo.width)//2, 195), logo)
    else:
        centered(d, "আবাসন+", 240, big, (125, 239, 207))
    # Fit the Bengali headline inside 80% width; wrap long text into two lines.
    words = main.split()
    lines = [main]
    if d.textbbox((0, 0), main, font=big)[2] > 830 and len(words) > 1:
        midpoint = (len(words) + 1) // 2
        lines = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
    y = 820 if len(lines) == 1 else 760
    for line in lines:
        font = big
        while d.textbbox((0, 0), line, font=font)[2] > 825 and font.size > 40:
            font = ImageFont.truetype(str(FONT), font.size - 4)
        centered(d, line, y, font, (255, 255, 255))
        y += 100
    centered(d, subtitle, 1110, medium, (203, 230, 235))
    centered(d, "abasonplus.wordpress.com", 1630, small, (125, 239, 207))
    im.convert("RGB").save(OUT / f"slide_{i}.png", optimize=True)

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
print("Soundtrack:", audio_path, "bytes:", audio_path.stat().st_size)
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
