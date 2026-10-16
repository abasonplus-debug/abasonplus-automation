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
big = ImageFont.truetype(str(FONT), 130)
medium = ImageFont.truetype(str(FONT), 130)
small = ImageFont.truetype(str(FONT), 130)
# Curated Bengali housing content, not invented legal advice.
catalog = json.loads((ROOT / "content" / "topics.json").read_text(encoding="utf-8"))
if len(catalog) < 10:
    raise RuntimeError("Topic catalog too short: refusing repetitive content")
date = datetime.now(ZoneInfo("Europe/Berlin")).date()
item = catalog[date.toordinal() % len(catalog)]
heading, hook, points = item["title"], item["hook"], item["tips"]
if not 4 <= len(points) <= 9:
    raise RuntimeError("Carousel requires 5 to 10 slides")
slides = [{"main":hook,"photo":item["cover_query"],"sub":"জরুরি বিষয়গুলো জানুন"}]
slides += [{"main":p["text"],"photo":p["query"],"sub":f"পরামর্শ {i}/{len(points)}"}
           for i,p in enumerate(points,1)]
hashtags = "#AbasonPlus #আবাসন #PropertyTips #RealEstateBangladesh "
hashtags += ("#জমি #জমিকেনা" if "জমি" in heading else "#ফ্ল্যাট #HomeBuying" if "ফ্ল্যাট" in heading else "#বাড়ি #HousingTips")
(OUT / "title.txt").write_text(f"{hook} | AbasonPlus #Shorts",encoding="utf-8")
(OUT / "caption.txt").write_text(
    f"{hook}\n\n" + "\n".join(f"✅ {i}. {p['text']}" for i,p in enumerate(points,1))
    + f"\n\nআপনার অভিজ্ঞতা কী? মন্তব্যে জানান।\n\nhttps://abasonplus.wordpress.com/\n\n{hashtags}",
    encoding="utf-8")
photo_credits = []
used_photo_titles = set()
quality_results = []
logo = None
try:
    logo_path = OUT / "logo.png"
    urlretrieve("https://abasonplus.wordpress.com/wp-content/uploads/2026/10/abasonplus_round_transparent.png", logo_path)
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((180, 180))
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
            if image.width < 1080 or image.height < 1080:
                continue
            attribution = metadata.get("Artist", {}).get("value", "Wikimedia Commons")
            attribution = re.sub("<[^>]+>", "", attribution).strip()[:150]
            with (OUT / "image_credits.txt").open("a", encoding="utf-8") as credits:
                credits.write(f"Slide {slide_index + 1}: {page.get('title')} | {license_name} | {attribution} | {info.get('descriptionurl', '')}\n")
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
        raise RuntimeError(f"Slide {i+1}: no suitably licensed photograph found; refusing a fake photo fallback")
    # Draw the lettering directly on the topic-specific photograph: no panel or box.
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    if logo:
        im.paste(logo, ((1080-logo.width)//2, 195), logo)
    else:
        centered(d, "আবাসন+", 240, big, (255, 255, 255))
    # Borderless semi-transparent, non-bold Bengali lettering, minimum 130px.
    # Use fewer words per slide rather than shrinking text.
    def wrap(text, fnt, max_width=950):
        words, lines, current = text.split(), [], ""
        for word in words:
            test = (current + " " + word).strip()
            if current and d.textbbox((0, 0), test, font=fnt)[2] > max_width:
                lines.append(current)
                current = word
            else:
                current = test
        if current: lines.append(current)
        return lines

    font = ImageFont.truetype(str(FONT), 130)
    lines = wrap(main, font)
    if any(d.textbbox((0, 0), line, font=font)[2] > 950 for line in lines):
        raise RuntimeError(f"Slide {i+1}: text too long for 130px; edit slide copy")
    # Distribute lines across a large central text composition (60%+ height).
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # Use a spacious hook-first layout; measure actual glyph coverage below.
    spacing = 380 if len(lines) <= 4 else 260
    start_y = max(380, 960 - spacing*(len(lines)-1)//2)
    for j, line in enumerate(lines):
        width = ld.textbbox((0, 0), line, font=font)[2]
        ink = (255, 240, 55, 205) if j % 2 == 0 else (255, 255, 255, 205)
        ld.text(((1080-width)//2, start_y+j*spacing), line, font=font,
                fill=ink, stroke_width=2, stroke_fill=(0, 0, 0, 155))
    # Typography must be legible; reject instead of silently accepting tiny coverage.
    bbox = layer.getbbox()
    if not bbox or bbox[2] - bbox[0] < 450:
        raise RuntimeError(f"Slide {i+1}: hook typography too narrow; revise copy")
    im = Image.alpha_composite(im, layer)
    # Preserve 130px minimum by not adding smaller subtitle/footer text.
    # Slide zero is the dedicated hook/cover. Keep it identical to video frame 1.
    if i == 0:
        im.convert("RGB").save(OUT / "thumbnail.png", optimize=True)
        print("Saved first-frame hook thumbnail: thumbnail.png")
    im.convert("RGB").save(OUT / f"slide_{i}.png", optimize=True)

(OUT / "description.txt").write_text(f"{hook}\n" + "\n".join(f"{i}. {tip}" for i, tip in enumerate(tips, 1)) + f"\n\nhttps://abasonplus.wordpress.com/\n{hashtags} #Shorts", encoding="utf-8")
(OUT / "metadata.json").write_text(json.dumps({"date": str(date), "topic": heading, "hook": hook, "slides": len(slides), "status": "preview_only"}, ensure_ascii=False, indent=2), encoding="utf-8")
playlist = OUT / "slides.txt"
playlist.write_text("".join(f"file 'slide_{i}.png'\nduration 3\n" for i in range(5)) + "file 'slide_4.png'\n", encoding="utf-8")

# Only the owner's original music is allowed. Never silently substitute audio.
custom_audio = ROOT / "assets" / "abasonplus.mp3"
if not custom_audio.is_file() or custom_audio.stat().st_size < 1000:
    raise RuntimeError("Original assets/abasonplus.mp3 missing; refusing to substitute soundtrack")
audio_path = custom_audio
print("Original soundtrack verified:", audio_path.stat().st_size, "bytes")
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(playlist),
    "-i", str(audio_path),
    "-t", "15", "-r", "30", "-vf", "format=yuv420p",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
    str(OUT / "abasonplus_daily.mp4")
], cwd=OUT, check=True)
print("Created PREVIEW ONLY", OUT / "abasonplus_daily.mp4")
