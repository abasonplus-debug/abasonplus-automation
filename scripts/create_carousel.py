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
slides = [{"main":hook,"photo":item["cover_query"],"sub":"জরুরি তথ্য"}]
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

# Real licensed photographs; do not fabricate or reuse scenes.
def image_for(query, slide_index):
    params = urlencode({"action":"query","generator":"search",
        "gsrsearch":f"filetype:bitmap {query}","gsrnamespace":6,
        "gsrlimit":20,"prop":"imageinfo","iiprop":"url|extmetadata",
        "iiurlwidth":1800,"format":"json"})
    api = "https://commons.wikimedia.org/w/api.php?" + params
    try:
        req = Request(api,headers={"User-Agent":"AbasonPlusEducationBot/2.0 (https://abasonplus.wordpress.com/)"})
        with urlopen(req,timeout=20) as response:
            pages=json.load(response).get("query",{}).get("pages",{})
        for page in sorted(pages.values(),key=lambda p:p.get("index",999)):
            title=page.get("title","")
            if title in used_photo_titles: continue
            info=(page.get("imageinfo") or [{}])[0]
            meta=info.get("extmetadata") or {}
            license_name=re.sub("<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")).strip()
            is_public=license_name.lower() in ("cc0","public domain","public domain mark")
            is_cc_by=license_name.startswith("CC BY ") and "SA" not in license_name.upper() and "NC" not in license_name.upper()
            if not (is_public or is_cc_by): continue
            url=info.get("thumburl") or info.get("url")
            if not url: continue
            with urlopen(Request(url,headers={"User-Agent":"AbasonPlusEducationBot/2.0"}),timeout=20) as response:
                raw=response.read(9_000_000)
            picture=Image.open(io.BytesIO(raw)).convert("RGB")
            if picture.width<1080 or picture.height<1400: continue
            used_photo_titles.add(title)
            attribution=re.sub("<[^>]+>","",meta.get("Artist",{}).get("value","")).strip()[:120]
            photo_credits.append(f"Slide {slide_index+1}: {title} | {attribution or 'Wikimedia contributor'} | {license_name} | {info.get('descriptionurl','')}")
            from PIL import ImageEnhance, ImageFilter
            picture=ImageOps.fit(picture,(1080,1920),method=Image.Resampling.LANCZOS)
            picture=ImageOps.autocontrast(picture,cutoff=0.5)
            picture=ImageEnhance.Color(picture).enhance(1.04)
            picture=ImageEnhance.Contrast(picture).enhance(1.035)
            picture=picture.filter(ImageFilter.UnsharpMask(radius=1.2,percent=65,threshold=3))
            print(f"Slide {slide_index+1} photo: {title}")
            return picture
    except Exception as exc:
        print(f"Photo fetch failed: {query}: {str(exc)[:180]}")
    return None

# Independent full-bleed frames; translucent Bengali, true 130px font size.
def fit_lines(draw, value, fnt, limit=940):
    lines=[]
    current=""
    for word in value.split():
        candidate=(current+" "+word).strip()
        if current and draw.textbbox((0,0),candidate,font=fnt)[2]>limit:
            lines.append(current)
            current=word
        else:
            current=candidate
    if current: lines.append(current)
    if not lines or any(draw.textbbox((0,0),line,font=fnt)[2]>limit for line in lines):
        raise RuntimeError(f"Text too long at 130px: {value[:80]}")
    return lines

def draw_line(draw,line,y,fnt,ink):
    width=draw.textbbox((0,0),line,font=fnt)[2]
    draw.text(((1080-width)//2,y),line,font=fnt,fill=ink,
              stroke_width=2,stroke_fill=(0,0,0,185))

for i, slide in enumerate(slides):
    picture=image_for(slide["photo"],i)
    if picture is None:
        raise RuntimeError(f"Slide {i+1}: no matching licensed full-resolution photo; fail closed")
    picture=picture.convert("RGBA")
    layer=Image.new("RGBA",picture.size,(0,0,0,0))
    draw=ImageDraw.Draw(layer)
    fnt=ImageFont.truetype(str(FONT),130)
    top=fit_lines(draw,heading if i else "আবাসনপ্লাস",fnt)
    middle=fit_lines(draw,slide["main"],fnt)
    bottom=fit_lines(draw,slide["sub"],fnt)
    if len(top)>2 or len(middle)>4 or len(bottom)>1:
        raise RuntimeError(f"Slide {i+1}: too many lines at minimum font size")
    for j,line in enumerate(top):
        draw_line(draw,line,265+j*170,fnt,(255,255,255,205))
    middle_y=960-((len(middle)-1)*170)//2
    for j,line in enumerate(middle):
        ink=(255,236,22,200) if j%2==0 else (255,255,255,200)
        draw_line(draw,line,middle_y+j*170,fnt,ink)
    draw_line(draw,bottom[0],1500,fnt,(255,245,170,205))
    bbox=layer.getbbox()
    if bbox is None or (bbox[3]-bbox[1]) < 1152:
        raise RuntimeError(f"Slide {i+1}: typography covers less than 60% of frame height")
    if logo:
        picture.paste(logo,((1080-logo.width)//2,65),logo)
    frame=Image.alpha_composite(picture,layer).convert("RGB")
    if frame.size!=(1080,1920): raise RuntimeError("Incorrect frame size")
    frame.save(OUT / f"slide_{i}.png",optimize=True)
    if i==0:
        frame.save(OUT / "thumbnail.png",optimize=True)
    coverage=round((bbox[3]-bbox[1])/1920,3)
    quality_results.append({"slide":i+1,"size":[1080,1920],
        "font_px":130,"vertical_composition_coverage":coverage,
        "source":photo_credits[-1]})
    print(f"Checked slide {i+1}/{len(slides)}: {coverage:.1%} vertical text span")

(OUT / "image_credits.txt").write_text("\n".join(photo_credits)+"\n",encoding="utf-8")
(OUT / "caption.txt").open("a",encoding="utf-8").write(
    "\n\nছবির উৎস ও লাইসেন্সের বিস্তারিত ভিডিওর Description-এ।")
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
