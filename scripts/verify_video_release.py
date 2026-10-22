#!/usr/bin/env python3
"""Fail-closed scheduled-video release checks. NEVER uploads media.

This only creates a local marker AFTER reliable independent metadata, licensed
photograph, typography, MP4, and provenance checks pass.
Semantic CLIP screening is a useful heuristic, not proof of aesthetic quality.
"""
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageStat
from publication_policy import validate_social_copy
from carousel_style import STYLE_ID, validate_style
from carousel_timing import validate_timing, MIN_SLIDES, MAX_SLIDES
from engagement_pack import validate_pack

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
DATE=datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
MARKER=OUT/"video_qa_passed.txt"
MARKER.unlink(missing_ok=True)

def required(check, reason):
    if not check:
        raise RuntimeError("VIDEO RELEASE BLOCKED: "+reason)

def read_json(filename):
    return json.loads((OUT/filename).read_text(encoding="utf-8"))

report=read_json("metadata.json")
brief=read_json("daily_research_story.json")
required(report.get("date")==DATE and report.get("verified_on")==DATE,
         "stale video creation or verification date")
required(brief.get("verified_on")==DATE and brief.get("expires_on")==DATE,
         "video brief must be verified and expire today")
required(report.get("source_url")==brief.get("source_url") and
         brief.get("source_url","").startswith("https://"),
         "video source not linked to matching fresh editorial")
required(brief.get("source_kind") in ("official_law_reference","external_news_report"),
         "untrusted source provenance")
required(report.get("manual_review")=="not_performed" and
         report.get("visual_approval")=="automated_semantic_qa_only",
         "unknown photography review status")
required(report.get("photo_selection") in ("curated_plus_semantic_screened","commons_semantic_screened"),
         "photographs were not CLIP screened")
slides=int(report.get("slides",0))
required(MIN_SLIDES<=slides<=MAX_SLIDES and len(brief.get("tips",[]))==slides-1,
         "incorrect carousel story length")
quality=report.get("quality",[])
required(len(quality)==slides,"missing individual slide QA")
required(report.get("style_id")==STYLE_ID,
         "selected carousel style missing")
sources=set()
fingerprints=[]
for n,info in enumerate(quality):
    required(info.get("slide")==n+1 and info.get("size")==[1080,1920],
             "incorrect individual slide or dimensions")
    required(info.get("font_px",0)>=120 and info.get("main_font_px",0)>=120,
             "font below agreed minimum")
    validate_style(info)
    required(info.get("photo_semantic_qa") is True,
             "visual brief was not semantically screened")
    required(info.get("font_glyph_coverage_qa") is True,
             "Bengali and English font coverage unverified; reject tofu □ boxes")
    credit=info.get("source","")
    required(bool(credit) and ("Pexels Free License" in credit or
             re.search(r"\b(?:CC0|CC BY|Public Domain)\b",credit,re.I)),
             "no clear approved photographic license attribution")
    required(credit not in sources,"repeated photo credited as different slides")
    sources.add(credit)
    filename=OUT/f"slide_{n}.png"
    with Image.open(filename) as im:
        im.load()
        required(im.size==(1080,1920) and im.mode in ("RGB","RGBA"),
                 "invalid full-bleed photo")
        # Tiny blank/monochrome fillers must never go into published videos.
        deviation=ImageStat.Stat(im.convert("RGB").resize((180,320))).stddev
        required(max(deviation)>18, "bland placeholder instead of real photography")
        thumb=im.convert("L").resize((9,8))
        pixels=list(thumb.getdata())
        fingerprints.append(tuple(1 if pixels[y*9+x]>pixels[y*9+x+1] else 0
                                 for y in range(8) for x in range(8)))
for i in range(len(fingerprints)):
    for j in range(i+1,len(fingerprints)):
        distance=sum(a!=b for a,b in zip(fingerprints[i],fingerprints[j]))
        required(distance>4,f"visually near-duplicate slide {i+1} and {j+1}")
required((OUT/"thumbnail.png").read_bytes()==(OUT/"slide_0.png").read_bytes(),
         "thumbnail differs from slide 1")
credits=(OUT/"image_credits.txt").read_text(encoding="utf-8")
required(len(credits.strip().splitlines())==slides,"incomplete photo attributions")
video=OUT/"abasonplus_daily.mp4"
required(video.is_file() and video.stat().st_size>500_000,"MP4 missing or incomplete")
probe=json.loads(subprocess.check_output(
    ["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(video)],
    timeout=20))
v=[s for s in probe["streams"] if s.get("codec_type")=="video"]
a=[s for s in probe["streams"] if s.get("codec_type")=="audio"]
required(len(v)==1 and v[0].get("codec_name")=="h264" and
         v[0].get("width")==1080 and v[0].get("height")==1920,
         "invalid H.264 1080x1920 video")
required(len(a)>=1 and a[0].get("codec_name")=="aac","original background music missing")
duration=float(probe["format"]["duration"])
validate_timing(report,duration)
from narration import verify as verify_narration
verify_narration(report,brief,OUT)
required((ROOT/"assets"/"abasonplus.mp3").is_file(),"original music asset missing")
expected_caption=(OUT/"caption.txt").read_text(encoding="utf-8")
expected_description=(OUT/"description.txt").read_text(encoding="utf-8")
required(brief["source_url"] in expected_description,"source absent from Shorts description")
validate_social_copy(expected_caption, expected_description, (OUT/"title.txt").read_text(encoding="utf-8"))
required("#AbasonPlus" in expected_caption and "#AbasonPlus" in expected_description,
         "SEO caption or description absent")
engagement=read_json('engagement_pack.json')
validate_pack(engagement)
required(engagement['hook']==brief['hook'] and engagement['caption']==expected_caption and engagement['description']==expected_description,'social package differs from approved story/copy')
required((OUT/'first_comment.txt').read_text(encoding='utf-8')==engagement['first_comment'],'first comment differs from package')
required(json.loads((OUT/'first_comment_json.txt').read_text(encoding='utf-8'))==engagement['first_comment'],'comment JSON escaping invalid')
with Image.open(OUT/'thumbnail_upload.jpg') as cover:
    required(cover.size==(1080,1920),'Upload cover dimensions changed')
required(0<(OUT/'thumbnail_upload.jpg').stat().st_size<=2_000_000,'Upload cover too large')
# This marker is not human aesthetic approval: it records machine QA, explicitly.
MARKER.write_text("auto_quality_checked="+DATE+"\n",encoding="utf-8")
print("VIDEO AUTOMATED QA PASSED: Distinct licensed/CLIP-screened photos; correct 9:16, source, font, MP4 and music.")
print("VISUAL QA REMAINS AUTOMATED HEURISTIC; owner can still request review.")

