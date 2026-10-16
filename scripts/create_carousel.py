#!/usr/bin/env python3
"""Prepare a preview-only licensed-photography Bengali carousel and MP4."""
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen
from urllib.parse import urlencode
import json
import os
import io
import re
from PIL import ImageOps
import math
import subprocess
import wave
import struct
from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont
from photo_relevance import PhotoRelevanceGuard

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FONT = next((p for p in Path("/usr/share/fonts").rglob("*.ttf") if "Bengali" in p.name and "Regular" in p.name), None)
if not FONT:
    raise RuntimeError("Install fonts-noto-core to render Bengali")
if not features.check("raqm"):
    raise RuntimeError("Pillow must support libraqm for correct Bengali shaping")
# NotoSansBengali-Regular.ttf has NO Latin glyphs. Always use a genuine
# Latin fallback for words like "Land Share" rather than rendering □□□□.
LATIN_FONT = next((p for p in Path("/usr/share/fonts").rglob("NotoSans-Regular.ttf")), None)
if not LATIN_FONT:
    raise RuntimeError("Install fonts-noto-core: NotoSans-Regular.ttf is required for bilingual hooks")
BN_CMAP = TTFont(str(FONT)).getBestCmap()
LATIN_CMAP = TTFont(str(LATIN_FONT)).getBestCmap()
LATIN_FONTS = {}
def latin_font(size):
    if size not in LATIN_FONTS:
        LATIN_FONTS[size] = ImageFont.truetype(str(LATIN_FONT),size)
    return LATIN_FONTS[size]

def word_font(word, bengali_font):
    # Keep Bengali combining marks and their base consonants in one shaping run.
    return bengali_font if any(0x0980 <= ord(c) <= 0x09FF for c in word) else latin_font(bengali_font.size)

def mixed_tokens(value, bengali_font):
    for token in re.findall(r"\\s+|\\S+", value):
        fnt = word_font(token, bengali_font)
        cmap = BN_CMAP if fnt is bengali_font else LATIN_CMAP
        missing = [f"U+{ord(ch):04X}" for ch in token
                   if not ch.isspace() and ord(ch) not in cmap
                   and ch not in ("\\u200c","\\u200d")]
        if missing:
            raise RuntimeError(f"Unsupported glyphs {missing} in on-screen text; refusing □ boxes: {value[:75]}")
        yield token,fnt

def mixed_text_width(draw, value, bengali_font):
    return sum(draw.textlength(piece,font=fnt) for piece,fnt in mixed_tokens(value,bengali_font))

# Curated Bengali housing content, not invented legal advice.
catalog = json.loads((ROOT / "content" / "topics.json").read_text(encoding="utf-8"))
if len(catalog)<10:
    raise RuntimeError("Too few topics")
today = datetime.now(ZoneInfo("Asia/Dhaka")).date()
current_catalog=[x for x in catalog if not x.get("expires_on") or today<=date.fromisoformat(x["expires_on"])]
if len(current_catalog)<10:raise RuntimeError("Outdated carousel catalog")
daily_story_file=os.getenv("ABASONPLUS_DAILY_STORY","")
if daily_story_file:
    target=Path(daily_story_file).resolve()
    if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
        raise RuntimeError("AI story must be a real, in-repository output file")
    item=json.loads(target.read_text(encoding="utf-8"))
    if date.fromisoformat(item["verified_on"]) != today:
        raise RuntimeError("AI story verified date is not today")
    from urllib.parse import urlparse
    trusted_hosts={"www.tbsnews.net","www.bssnews.net","bdlaws.minlaw.gov.bd",
                   "investbangladesh.gov.bd","mohpw.gov.bd","dmtcl.gov.bd",
                   "hbri.gov.bd","ss.pwd.gov.bd","nsez.gov.bd","nha.gov.bd"}
    if urlparse(item.get("source_url","")).hostname not in trusted_hosts:
        raise RuntimeError("Daily carousel source not among the approved publishers")
    if item.get("source_kind") not in ("external_news_report","official_law_reference"):
        raise RuntimeError("Carousel was not grounded in an approved factual source")
    print("NEW_SOURCE_GROUNDED_CAROUSEL:",item["source_url"],flush=True)
else:
    item=current_catalog[today.toordinal() % len(current_catalog)]
heading,hook,points=item["title"],item["hook"],item["tips"]
if not 4<=len(points)<=9:raise RuntimeError("Carousel requires 5-10 slides")
slides=[{"main":hook,"photo":item["cover_query"],"sub":"জরুরি তথ্য"}]
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
relevance_guard = None
# Research-backed references are preview candidates, NOT user-approved publications.
researched_photos=json.loads((ROOT/"content"/"researched_photos.json").read_text(encoding="utf-8"))
selected_photos=researched_photos.get(heading)
if selected_photos is not None:
    if len(selected_photos)!=len(slides):
        raise RuntimeError("Research photo manifest does not match slide count")
    if len({x["url"] for x in selected_photos}) != len(selected_photos):
        raise RuntimeError("Photo manifest repeats an image")

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
def search_phrases(query):
    words=query.split()
    q=query.lower()
    fallback=[]
    if any(t in q for t in ("deed","document","paper","receipt","contract","record","agreement")):
        fallback=["documents", "paperwork", "paper"]
    elif any(t in q for t in ("survey","map","cadastral","boundary")):
        fallback=["surveying", "land surveying", "field"]
    elif any(t in q for t in ("land","field","farm","rural","garden","tree")):
        fallback=["agricultural land", "farmland", "field"]
    elif any(t in q for t in ("house","home","roof","building","apartment","construction")):
        fallback=["residential building", "house", "construction"]
    elif any(t in q for t in ("electric","wiring","circuit","socket")):
        fallback=["electrician", "electrical wiring", "electrical"]
    elif any(t in q for t in ("water","plumb","bathroom","drain","gutter")):
        fallback=["plumbing", "water pipe", "bathroom"]
    elif any(t in q for t in ("architect","blueprint","floor plan")):
        fallback=["architecture", "architect", "building"]
    else:
        fallback=[words[0], "house", "building"]
    phrases=[query, " ".join(words[:2]), *fallback]
    return list(dict.fromkeys(p for p in phrases if p))

def subject_guard(query, filename):
    """Conservative filename screen: reject unrelated archives, diagrams and scans.
    Not a substitute for manual visual review of licensed photo content."""
    name=filename.lower()
    q=query.lower()
    if not name.endswith((".jpg",".jpeg",".webp")): return False
    blocked=("certificate","membership","historic","cadastral map","old map",
             "illustration","engraving","diagram","painting","poster",
             "scan of","newspaper","cartoon","drawing","passport")
    if any(x in name for x in blocked): return False
    if any(x in q for x in ("advisor","meeting","consultation")):
        return any(x in name for x in ("meeting","discussion","consultation",
                   "advisor","consultant","realtor","estate agent","client"))
    if any(x in q for x in ("document","deed","paper","contract","record","agreement")):
        return any(x in name for x in ("document","deed","paperwork",
                   "property contract","agreement","registration","land record",
                   "title deed","office desk"))
    if any(x in q for x in ("survey","map","cadastral","boundary")):
        return any(x in name for x in ("survey","land parcel","boundary",
                   "field work","measuring","topographic"))
    return True

def image_for(query, slide_index):
    global relevance_guard
    if selected_photos is not None:
        from urllib.parse import urlparse
        item=selected_photos[slide_index]
        url=item["url"]
        if urlparse(url).hostname!="images.pexels.com":
            raise RuntimeError("Unapproved photographic host in manifest")
        if not item["source"].startswith("https://www.pexels.com/photo/"):
            raise RuntimeError("Missing verified photographer source page")
        try:
            req=Request(url,headers={"User-Agent":"Mozilla/5.0 AbasonPlus preview research"})
            with urlopen(req,timeout=30) as response:
                raw=response.read(17_000_000)
            picture=Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as exc:
            raise RuntimeError(f"Curated scene {slide_index+1} unavailable: {str(exc)[:100]}") from None
        if min(picture.size)<1600:
            raise RuntimeError(f"Curated scene {slide_index+1} too small; refusing upscale")
        if item.get("license")!="Pexels Free License":
            raise RuntimeError("Curated photograph licensing is not verified")
        if relevance_guard is None: relevance_guard=PhotoRelevanceGuard()
        if not relevance_guard.approved(picture, query):
            raise RuntimeError(f"Curated scene {slide_index+1} does not match its visual brief")
        photo_credits.append(f"Slide {slide_index+1}: {item['creator']} | {item['license']} | {item['source']} | Cropped and text overlaid")
        from PIL import ImageEnhance, ImageFilter
        picture=ImageOps.fit(picture,(1080,1920),method=Image.Resampling.LANCZOS)
        picture=ImageOps.autocontrast(picture,cutoff=0.4)
        picture=ImageEnhance.Color(picture).enhance(1.04)
        picture=picture.filter(ImageFilter.UnsharpMask(radius=1.0,percent=50,threshold=3))
        print(f"Researched real photograph for slide {slide_index+1}: {item['scene']}",flush=True)
        return picture

    for phrase in search_phrases(query):
        params=urlencode({"action":"query","generator":"search",
            "gsrsearch":f"filetype:bitmap {phrase}","gsrnamespace":6,
            "gsrlimit":35,"prop":"imageinfo","iiprop":"url|extmetadata|size",
            "iiurlwidth":1800,"format":"json"})
        api="https://commons.wikimedia.org/w/api.php?"+params
        try:
            req=Request(api,headers={"User-Agent":"AbasonPlusEducationBot/2.0 (https://abasonplus.wordpress.com/)"})
            with urlopen(req,timeout=18) as response:
                pages=json.load(response).get("query",{}).get("pages",{})
            print(f"Photo search {phrase!r}: {len(pages)} candidates",flush=True)
            for page in sorted(pages.values(),key=lambda p:p.get("index",999)):
                title=page.get("title","")
                if title in used_photo_titles or not subject_guard(query,title): continue
                info=(page.get("imageinfo") or [{}])[0]
                meta=info.get("extmetadata") or {}
                license_name=re.sub("<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")).strip()
                is_public=license_name.lower() in ("cc0","public domain","public domain mark")
                is_cc=license_name.startswith("CC BY ") or license_name.startswith("CC BY-SA ")
                if not (is_public or is_cc): continue
                # Exclude illustrations, logo graphics and thumbnail-sized photos.
                lower=title.lower()
                if any(term in lower for term in ("diagram","screenshot","icon","logo","cartoon","clipart",".svg",".gif",".pdf")):
                    continue
                iw,ih=info.get("width",0),info.get("height",0)
                if iw and ih and (iw<1080 or ih<1200): continue
                url=info.get("thumburl") or info.get("url")
                if not url: continue
                try:
                    with urlopen(Request(url,headers={"User-Agent":"AbasonPlusEducationBot/2.0"}),timeout=18) as response:
                        raw=response.read(10_000_000)
                    picture=Image.open(io.BytesIO(raw)).convert("RGB")
                except Exception as e:
                    print(f"Skipped unreadable photo: {str(e)[:90]}",flush=True)
                    continue
                if picture.width<1080 or picture.height<1200: continue
                if relevance_guard is None:
                    relevance_guard=PhotoRelevanceGuard()
                if not relevance_guard.approved(picture, query):
                    print(f"Rejected unrelated photograph: {title[:65]}",flush=True)
                    continue
                used_photo_titles.add(title)
                attribution=re.sub("<[^>]+>","",meta.get("Artist",{}).get("value","")).strip()[:120]
                extra=(" | Modified visual distributed under the same CC BY-SA license"
                       if license_name.startswith("CC BY-SA ") else "")
                photo_credits.append(f"Slide {slide_index+1}: {title} | {attribution or 'Wikimedia contributor'} | {license_name} | {info.get('descriptionurl','')}{extra}")
                from PIL import ImageEnhance, ImageFilter
                picture=ImageOps.fit(picture,(1080,1920),method=Image.Resampling.LANCZOS)
                picture=ImageOps.autocontrast(picture,cutoff=0.5)
                picture=ImageEnhance.Color(picture).enhance(1.04)
                picture=ImageEnhance.Contrast(picture).enhance(1.035)
                picture=picture.filter(ImageFilter.UnsharpMask(radius=1.2,percent=65,threshold=3))
                print(f"Selected photo for slide {slide_index+1}: {title}",flush=True)
                return picture
        except Exception as exc:
            print(f"Photo search failed {phrase!r}: {str(exc)[:120]}",flush=True)
    return None

# Independent full-bleed frames; translucent Bengali, true 130px font size.
def fit_lines(draw, value, fnt, limit=940):
    lines=[]
    current=""
    for word in value.split():
        candidate=(current+" "+word).strip()
        if current and mixed_text_width(draw,candidate,fnt)>limit:
            lines.append(current)
            current=word
        else:
            current=candidate
    if current: lines.append(current)
    if not lines or any(mixed_text_width(draw,line,fnt)>limit for line in lines):
        raise RuntimeError(f"Text too long at 130px: {value[:80]}")
    return lines

def draw_line(draw,line,y,fnt,ink):
    width=mixed_text_width(draw,line,fnt)
    x=(1080-width)/2
    for part, font in mixed_tokens(line,fnt):
        if not part.isspace():
            draw.text((x,y),part,font=font,fill=ink,
                      stroke_width=2,stroke_fill=(0,0,0,150))
        x+=draw.textlength(part,font=font)

for i, slide in enumerate(slides):
    picture=image_for(slide["photo"],i)
    if picture is None:
        raise RuntimeError(f"Slide {i+1}: no matching licensed full-resolution photo; fail closed")
    picture=picture.convert("RGBA")
    # Edge-to-edge gentle darkening for transparent text legibility; no boxes.
    picture=Image.alpha_composite(picture,Image.new("RGBA",picture.size,(0,0,0,44)))
    layer=Image.new("RGBA",picture.size,(0,0,0,0))
    draw=ImageDraw.Draw(layer)
    fnt=ImageFont.truetype(str(FONT),130)
    top=fit_lines(draw,heading if i else "আবাসনপ্লাস",fnt)
    bottom=fit_lines(draw,slide["sub"],fnt)
    # Prioritize the large hook and tip. NEVER lower than 130px.
    main_font=fnt
    middle=[]
    for size in range(220,129,-10):
        candidate_font=ImageFont.truetype(str(FONT),size)
        try: candidate_lines=fit_lines(draw,slide["main"],candidate_font)
        except RuntimeError: continue
        if len(candidate_lines)<=4:
            middle=candidate_lines
            main_font=candidate_font
            break
    if len(top)>2 or not middle or len(bottom)>1:
        raise RuntimeError(f"Slide {i+1}: too much text for 130px+ layout")
    for j,line in enumerate(top):
        draw_line(draw,line,205+j*170,fnt,(255,255,255,205))
    line_step=max(220,int(main_font.size*1.18))
    middle_y=930-((len(middle)-1)*line_step)//2
    for j,line in enumerate(middle):
        ink=(255,236,22,206) if j%2==0 else (255,255,255,206)
        draw_line(draw,line,middle_y+j*line_step,main_font,ink)
    draw_line(draw,bottom[0],1540,fnt,(255,245,170,205))
    bbox=layer.getbbox()
    if bbox is None or (bbox[3]-bbox[1]) < 1152:
        raise RuntimeError(f"Slide {i+1}: typography covers less than 60% of frame height")
    # Reserve 60%+ of the ENTIRE canvas for large typographic composition.
    # This is a design region, not the proportion of opaque ink pixels.
    design_zone=(20,155,1060,1775)
    design_area=(design_zone[2]-design_zone[0])*(design_zone[3]-design_zone[1])/(1080*1920)
    if design_area<0.60:
        raise RuntimeError("Reserved typography design region below 60% of frame area")
    if bbox[0]<design_zone[0] or bbox[2]>design_zone[2] or bbox[1]<design_zone[1] or bbox[3]>design_zone[3]:
        raise RuntimeError(f"Slide {i+1}: typography extends outside reserved design zone: text={bbox}, zone={design_zone}")
    if logo:
        picture.paste(logo,((1080-logo.width)//2,65),logo)
    frame=Image.alpha_composite(picture,layer).convert("RGB")
    if frame.size!=(1080,1920): raise RuntimeError("Incorrect frame size")
    frame.save(OUT / f"slide_{i}.png",optimize=True)
    if i==0:
        frame.save(OUT / "thumbnail.png",optimize=True)
    coverage=round((bbox[3]-bbox[1])/1920,3)
    quality_results.append({"slide":i+1,"size":[1080,1920],
        "font_px":130,"main_font_px":main_font.size,
        "vertical_composition_coverage":coverage,
        "typography_reserved_area_fraction":round(design_area,3),
        "actual_ink_bounding_area_fraction":round((bbox[2]-bbox[0])*(bbox[3]-bbox[1])/(1080*1920),3),
        "photo_semantic_qa":True,
        "font_glyph_coverage_qa":True,
        "latin_fallback_font":LATIN_FONT.name,
        "source":photo_credits[-1]})
    print(f"Checked slide {i+1}/{len(slides)}: {coverage:.1%} vertical text span")

(OUT / "image_credits.txt").write_text("\n".join(photo_credits)+"\n",encoding="utf-8")
credits = "\n".join(photo_credits)
(OUT / "caption.txt").open("a",encoding="utf-8").write("\n\nছবির উৎস ও লাইসেন্স:\n"+credits)
(OUT / "description.txt").write_text(
    f"{hook}\n" + "\n".join(f"{i}. {p['text']}" for i,p in enumerate(points,1))
    + f"\n\nhttps://abasonplus.wordpress.com/\n{hashtags} #Shorts"
    + (f"\n\nSource: {item['source_url']}\nVerified: {item.get('verified_on','')}" if item.get("source_url") else "")
    + "\n\nPhoto sources and licenses:\n" + credits,encoding="utf-8")
(OUT / "metadata.json").write_text(json.dumps(
    {"date":str(today),"topic":heading,"hook":hook,"slides":len(slides),"source_url":item.get("source_url"),"verified_on":item.get("verified_on"),
     "status":"preview_only","visual_approval":"automated_semantic_qa_only","manual_review":"not_performed",
     "photo_selection":("curated_plus_semantic_screened" if selected_photos else "commons_semantic_screened"),
     "quality":quality_results},
    ensure_ascii=False,indent=2),encoding="utf-8")
playlist = OUT / "slides.txt"
slide_seconds=3
duration=len(slides)*slide_seconds
playlist.write_text("".join(f"file 'slide_{i}.png'\nduration {slide_seconds}\n"
    for i in range(len(slides))) + f"file 'slide_{len(slides)-1}.png'\n",
    encoding="utf-8")

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
    "-t", str(duration), "-r", "30", "-vf", "format=yuv420p",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
    "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={max(0,duration-1)}:d=1", "-shortest", "-movflags", "+faststart",
    str(OUT / "abasonplus_daily.mp4")
], cwd=OUT, check=True)
print("Created PREVIEW ONLY", OUT / "abasonplus_daily.mp4")
