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
from publication_policy import trusted_source_url, validate_social_copy
from engagement_pack import hashtags_for, write_pack
from carousel_timing import SLIDE_SECONDS
from carousel_style import STYLE_ID, POLICY, layout, paint, photo_stats, readable_photo, validate_style

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FONT = next((p for p in Path("/usr/share/fonts").rglob("*.ttf") if "Bengali" in p.name and "Bold" in p.name), None)
if not FONT:
    raise RuntimeError("Install fonts-noto-core with Noto Sans Bengali Bold")
if not features.check("raqm"):
    raise RuntimeError("Pillow must support libraqm for correct Bengali shaping")
# NotoSansBengali-Regular.ttf has NO Latin glyphs. Always use a genuine
# Latin fallback for words like "Land Share" rather than rendering □□□□.
LATIN_FONT = next((p for p in Path("/usr/share/fonts").rglob("NotoSans-Bold.ttf")), None)
if not LATIN_FONT:
    raise RuntimeError("Install fonts-noto-core: NotoSans-Bold.ttf is required for bilingual hooks")
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
    for token in re.findall(r"\s+|\S+", value):
        fnt = word_font(token, bengali_font)
        cmap = BN_CMAP if fnt is bengali_font else LATIN_CMAP
        missing = [f"U+{ord(ch):04X}" for ch in token
                   if not ch.isspace() and ord(ch) not in cmap
                   and ch not in ("\u200c","\u200d")]
        if missing:
            raise RuntimeError(f"Unsupported glyphs {missing} in on-screen text; refusing □ boxes: {value[:75]}")
        yield token,fnt

def mixed_text_width(draw, value, bengali_font):
    return sum(draw.textlength(piece,font=fnt) for piece,fnt in mixed_tokens(value,bengali_font))

# Curated Bengali housing content, not invented legal advice.
catalog = json.loads((ROOT / "content" / "topics.json").read_text(encoding="utf-8"))
if len(catalog)<10:
    raise RuntimeError("Too few topics")
today = datetime.now(ZoneInfo("Europe/Berlin")).date()
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
    if not trusted_source_url(item.get("source_url", "")):
        raise RuntimeError("Daily carousel source not among the approved publishers")
    if item.get("source_kind") not in ("external_news_report","official_law_reference"):
        raise RuntimeError("Carousel was not grounded in an approved factual source")
    print("NEW_SOURCE_GROUNDED_CAROUSEL:",item["source_url"],flush=True)
else:
    item=current_catalog[today.toordinal() % len(current_catalog)]
heading,hook,points=item["title"],item["hook"],item["tips"]
if not 4<=len(points)<=24:raise RuntimeError("Carousel requires 5-25 slides")
slides=[{"main":hook,"photo":item["cover_query"],"sub":"জরুরি তথ্য"}]
slides += [{"main":p["text"],"photo":p["query"],"sub":f"পরামর্শ {i}/{len(points)}"}
           for i,p in enumerate(points,1)]
hashtags = ' '.join(hashtags_for(heading))
(OUT / "title.txt").write_text(hook if len(hook + " | AbasonPlus") > 100 else hook + " | AbasonPlus",encoding="utf-8")
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
selected_photos=item.get("photos") or researched_photos.get(heading)
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
    logo.thumbnail((90, 90))
except Exception as e:
    print("Logo unavailable, continuing without logo:", e)

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
    subject=re.split(r"\s+under bright|,\s*portrait|\s+with spacious",query,flags=re.I)[0].strip()
    phrases=[subject+" bright daylight",subject," ".join(words[:3])," ".join(words[:2]), *fallback]
    return list(dict.fromkeys(p for p in phrases if p))

def subject_guard(query, filename):
    """Require subject-specific photo titles before CLIP; reject name collisions."""
    name=filename.lower()
    q=query.lower()
    if not name.endswith((".jpg",".jpeg",".webp")):
        return False
    blocked=("certificate","membership","historic","cadastral map","old map",
             "illustration","engraving","diagram","painting","poster","scan of",
             "newspaper","cartoon","drawing","passport","blueprint",
             "moon","lunar","apollo","spacecraft","nasa","mars rover",
             "surveyor 1","surveyor 2","surveyor 3","surveyor 4",
             "surveyor 5","surveyor 6","surveyor 7")
    if any(term in name for term in blocked):
        return False
    if any(term in q for term in ("survey","cadastral","boundary","total station")):
        return any(term in name for term in
                   ("land survey","land-survey","surveyor","surveying instrument",
                    "total station","theodolite","field survey","cadastral survey",
                    "property boundary"))
    if any(term in q for term in ("advisor","meeting","consultation")):
        return any(term in name for term in
                   ("meeting","discussion","consultation","advisor",
                    "consultant","realtor","estate agent","client"))
    if any(term in q for term in ("document","deed","paper","contract","record","agreement")):
        return (any(term in name for term in
                    ("property","real estate","house sale","land deed","title deed",
                     "contract","agreement","registration"))
                and any(term in name for term in
                        ("document","paper","deed","contract","agreement","record","signing")))
    if any(term in q for term in ("farm","field","fence","farmland","rural")):
        return any(term in name for term in
                   ("farm","field","fence","rural","pasture","agricultural","countryside"))
    return True

def choose_text_area(picture, placements):
    cropped=ImageOps.fit(picture,(1080,1920),method=Image.Resampling.LANCZOS)
    for index,regions in enumerate(placements):
        if readable_photo(photo_stats(cropped,regions)):return index
    return None

def image_for(query, slide_index, placements):
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
        original_picture=picture.copy()
        picture=ImageOps.autocontrast(picture,cutoff=0.4)
        picture=ImageEnhance.Color(picture).enhance(1.04)
        picture=picture.filter(ImageFilter.UnsharpMask(radius=1.0,percent=50,threshold=3))
        if choose_text_area(picture,placements) is None:
            # Processing can darken an otherwise readable natural photograph.
            picture=original_picture
        if choose_text_area(picture,placements) is None:
            for factor in (1.12,1.25,1.4):
                brightened=ImageEnhance.Brightness(original_picture).enhance(factor)
                if choose_text_area(brightened,placements) is not None:
                    picture=brightened
                    break
        if choose_text_area(picture,placements) is None:
            raise RuntimeError(f"Curated scene {slide_index+1} has no readable headline area")
        print(f"Researched real photograph for slide {slide_index+1}: {item['scene']}",flush=True)
        return picture,choose_text_area(picture,placements)

    for phrase in search_phrases(query):
        params=urlencode({"action":"query","generator":"search",
            "gsrsearch":f"filetype:bitmap {phrase}","gsrnamespace":6,
            "gsrlimit":50,"prop":"imageinfo","iiprop":"url|extmetadata|size",
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
                if choose_text_area(picture,placements) is None:
                    print(f"Rejected dark text area: {title[:65]}",flush=True)
                    continue
                if relevance_guard is None:
                    relevance_guard=PhotoRelevanceGuard()
                if not relevance_guard.approved(picture, query):
                    print(f"Rejected unrelated photograph: {title[:65]}",flush=True)
                    continue
                attribution=re.sub("<[^>]+>","",meta.get("Artist",{}).get("value","")).strip()[:120]
                extra=(" | Modified visual distributed under the same CC BY-SA license"
                       if license_name.startswith("CC BY-SA ") else "")
                from PIL import ImageEnhance, ImageFilter
                picture=ImageOps.fit(picture,(1080,1920),method=Image.Resampling.LANCZOS)
                original_picture=picture.copy()
                picture=ImageOps.autocontrast(picture,cutoff=0.5)
                picture=ImageEnhance.Color(picture).enhance(1.04)
                picture=ImageEnhance.Contrast(picture).enhance(1.035)
                picture=picture.filter(ImageFilter.UnsharpMask(radius=1.2,percent=65,threshold=3))
                if choose_text_area(picture,placements) is None:
                    picture=original_picture
                if choose_text_area(picture,placements) is None:
                    print(f"Rejected photo with poor text contrast: {title[:65]}",flush=True)
                    continue
                used_photo_titles.add(title)
                photo_credits.append(f"Slide {slide_index+1}: {title} | {attribution or 'Wikimedia contributor'} | {license_name} | {info.get('descriptionurl','')}{extra}")
                print(f"Selected photo for slide {slide_index+1}: {title}",flush=True)
                return picture,choose_text_area(picture,placements)
        except Exception as exc:
            print(f"Photo search failed {phrase!r}: {str(exc)[:120]}",flush=True)
    return None

# Locked compact style applies independently to every hook and tip image.
for i, slide in enumerate(slides):
    size=POLICY['hook_font_px'] if i==0 else POLICY['body_font_px']
    main_font=ImageFont.truetype(str(FONT),size,layout_engine=ImageFont.Layout.RAQM)
    rows=layout(slide['main'],main_font,mixed_tokens)
    layer,line_boxes=paint(rows,mixed_tokens)
    regions=[tuple(box) for box in line_boxes]
    chosen=image_for(slide['photo'],i,[regions])
    if chosen is None:raise RuntimeError(f'Slide {i+1}: no relevant licensed photo passes readable compact typography')
    picture,_=chosen
    picture=picture.convert('RGBA')
    stats=photo_stats(picture,regions)
    if not readable_photo(stats):raise RuntimeError('Background too busy behind outlined text')
    logo_box=None
    if logo:
        pos=(1080-logo.width-28,1920-logo.height-28)
        logo_box=[*pos,pos[0]+logo.width,pos[1]+logo.height]
        picture.alpha_composite(logo,pos)
    frame=Image.alpha_composite(picture,layer).convert('RGB')
    if frame.size!=(1080,1920):raise RuntimeError('Incorrect canvas')
    bbox=layer.getbbox()
    info={'slide':i+1,'size':[1080,1920],'font_px':size,'main_font_px':size,
          'style_id':STYLE_ID,'text_colors':['#FFFFFF','#FFD24A'],'text_opacity':255,
          'text_lines':len(rows),'text_bbox':list(bbox),'line_ink_boxes':line_boxes,
          'alignment':'center','compact_spacing_qa':True,
          'text_background':False,'text_stroke':True,'stroke_px':4,'text_shadow':True,'photo_overlay':False,
          'logo_position':'bottom_right' if logo else 'omitted_unavailable','logo_box':logo_box,
          'line_background_stats':stats,'photo_semantic_qa':True,'font_glyph_coverage_qa':True,
          'latin_fallback_font':LATIN_FONT.name,'source':photo_credits[-1]}
    validate_style(info)
    frame.save(OUT/f'slide_{i}.png',optimize=True)
    if i==0:
        frame.save(OUT/'thumbnail.png',optimize=True)
        # YouTube custom-cover upload limit is 2 MiB; preserve full canvas/font size.
        for jpeg_quality in (92,85,75,65):
            frame.save(OUT/'thumbnail_upload.jpg',quality=jpeg_quality,optimize=True)
            if (OUT/'thumbnail_upload.jpg').stat().st_size<=2_000_000:break
        if (OUT/'thumbnail_upload.jpg').stat().st_size>2_000_000:
            raise RuntimeError('Cover exceeds upload size limit at original dimensions')
    quality_results.append(info)
    print(f'Checked slide {i+1}/{len(slides)}: {size}px, centered compact white/gold outline style')

# Approximate mobile interface guides: diagnostic artifact only, NEVER publish it.
qa=Image.new('RGB',(216*min(5,len(slides)),424*((len(slides)+4)//5)),(245,245,245))
for n in range(len(slides)):
    tile=Image.open(OUT/f'slide_{n}.png').convert('RGB').resize((216,384),Image.Resampling.LANCZOS)
    guide=ImageDraw.Draw(tile)
    guide.rectangle((0,0,215,39),outline='#FF5555',width=2)
    guide.rectangle((0,314,215,383),outline='#FF5555',width=2)
    guide.rectangle((180,40,215,313),outline='#FF5555',width=2)
    x=(n%5)*216;y=(n//5)*424
    qa.paste(tile,(x,y));ImageDraw.Draw(qa).text((x+4,y+390),f'Slide {n+1}: approximate UI guides',fill='black')
qa.save(OUT/'mobile_qa_contact_sheet.jpg',quality=90)
(OUT/'mobile_qa_notes.json').write_text(json.dumps({'status':'generated_not_device_reviewed','approximate_guides':True,'logo_bottom_right_ui_risk':True,'published_asset':False,'note':'UI varies by platform/device/caption. Do not claim a live mobile preview was reviewed.'},indent=2))

(OUT / "image_credits.txt").write_text("\n".join(photo_credits)+"\n",encoding="utf-8")
credits = "\n".join(photo_credits)
(OUT / "caption.txt").open("a",encoding="utf-8").write("\n\nছবির উৎস ও লাইসেন্স:\n"+credits)
(OUT / "description.txt").write_text(
    f"{hook}\n" + "\n".join(f"{i}. {p['text']}" for i,p in enumerate(points,1))
    + f"\n\nhttps://abasonplus.wordpress.com/\n{hashtags} #Shorts"
    + (f"\n\nSource: {item['source_url']}\nVerified: {item.get('verified_on','')}" if item.get("source_url") else "")
    + "\n\nPhoto sources and licenses:\n" + credits,encoding="utf-8")
validate_social_copy((OUT/"caption.txt").read_text(encoding="utf-8"),
                     (OUT/"description.txt").read_text(encoding="utf-8"),
                     (OUT/"title.txt").read_text(encoding="utf-8"))
write_pack(OUT,hook,(OUT/'caption.txt').read_text(encoding='utf-8'),(OUT/'description.txt').read_text(encoding='utf-8'))
(OUT / "metadata.json").write_text(json.dumps(
    {"date":str(today),"topic":heading,"hook":hook,"slides":len(slides),"slide_seconds":SLIDE_SECONDS,"slide_durations":[SLIDE_SECONDS]*len(slides),"style_id":STYLE_ID,"source_url":item.get("source_url"),"verified_on":item.get("verified_on"),
     "status":"preview_only","visual_approval":"automated_semantic_qa_only","manual_review":"not_performed",
     "photo_selection":("curated_plus_semantic_screened" if selected_photos else "commons_semantic_screened"),
     "quality":quality_results},
    ensure_ascii=False,indent=2),encoding="utf-8")
playlist = OUT / "slides.txt"
slide_seconds=SLIDE_SECONDS
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
    "-t", str(duration), "-r", "30", "-vf", "fps=30,format=yuv420p",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
    "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={max(0,duration-1)}:d=1", "-shortest", "-movflags", "+faststart",
    str(OUT / "abasonplus_daily.mp4")
], cwd=OUT, check=True)
print("Created PREVIEW ONLY", OUT / "abasonplus_daily.mp4")

