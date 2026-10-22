#!/usr/bin/env python3
from carousel_style import STYLE_ID, validate_style
from carousel_timing import validate_timing, MIN_SLIDES, MAX_SLIDES
from engagement_pack import hashtags_for, first_comment, hashtag_tokens
"""Generate and validate a TikTok-ready preview package from AbasonPlus slides.

NO TikTok API, publishing, scheduling, Make webhook, or credentials.
TikTok account authorization, creator-supported privacy options, lawful media
rights, and actual post-specific consent must be verified separately.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
VIDEO=OUT/"abasonplus_daily.mp4"
META=OUT/"metadata.json"
STORY=OUT/"daily_research_story.json"
PASS=OUT/"video_qa_passed.txt"
AUDIO=ROOT/"assets"/"abasonplus.mp3"

def require(ok, message):
    if not ok:raise RuntimeError("TIKTOK_PREVIEW_BLOCKED: "+message)

require(META.is_file() and STORY.is_file() and PASS.is_file(),"source and photo QA must pass before TikTok packaging")
require(VIDEO.is_file() and VIDEO.stat().st_size>10_000,"MP4 missing or too small")
require(AUDIO.is_file() and AUDIO.stat().st_size>1000,"original user-supplied music missing")
info=json.loads(META.read_text(encoding="utf-8"))
story=json.loads(STORY.read_text(encoding="utf-8"))
local_day=datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
require(info.get("date")==local_day and story.get("verified_on")==local_day,"story is stale")
require(info.get("source_url")==story.get("source_url"),"source provenance mismatch")
require(story.get("source_url","").startswith("https://"),"not grounded in a cited link")
require(MIN_SLIDES<=info.get("slides",0)<=MAX_SLIDES and len(story.get("tips",[]))==info["slides"]-1,"slide count and story must match")
require(info.get("visual_approval")=="automated_semantic_qa_only","machine QA provenance not recorded")
quality=info.get("quality",[])
require(info.get("style_id")==STYLE_ID,"selected visual style missing")
require(len(quality)==info["slides"], "Quality record required for each slide")
for x in quality:
    require(x.get('photo_semantic_qa') is True, 'Photo semantic screening missing')
    validate_style(x)
require((OUT/"thumbnail.png").read_bytes()==(OUT/"slide_0.png").read_bytes(),
        "hook thumbnail not same as first slide")
probe=json.loads(subprocess.check_output([
 "ffprobe","-v","error","-show_streams","-show_format","-of","json",str(VIDEO)],timeout=20))
video=[s for s in probe["streams"] if s.get("codec_type")=="video"]
audio=[s for s in probe["streams"] if s.get("codec_type")=="audio"]
require(len(video)==1 and video[0].get("codec_name")=="h264" and
        video[0].get("width")==1080 and video[0].get("height")==1920,
        "not a 1080x1920 H264 TikTok video")
require(len(audio)>0 and audio[0].get("codec_name")=="aac","missing audio track")
validate_timing(info, float(probe["format"]["duration"]))
from cosyvoice3_daily_voiceover import verify_voiceover
verify_voiceover(OUT,story,info)
hook=re.sub(r"\s+"," ",str(story.get("hook",""))).strip()
require(12<=len(hook)<=110,"no readable catchy hook")
tips=[re.sub(r"\s+"," ",x.get("text","")).strip() for x in story["tips"]]
require(all(8<=len(t)<=500 for t in tips),"tips are unreadable")
hashtags=hashtags_for(story.get("title",hook))
body=hook+"\n"+"\n".join(f"✅ {tip}" for tip in tips)
caption=body+"\n\n"+(" ".join(hashtags))
require(len(caption)<=2200,"TikTok caption above 2200 characters")
(OUT/"tiktok_caption.txt").write_text(caption+"\n",encoding="utf-8")
status={
 "platform":"tiktok","status":"preview_only",
 "date":local_day,"content_key":"abasonplus-tiktok-"+local_day,
 "title":hook,"caption":caption,"first_comment":first_comment(hook),
 "hashtags":hashtags,"video_file":"output/abasonplus_daily.mp4",
 "thumbnail_file":"output/thumbnail.png",
 "source_url":story["source_url"],
 "verification":"machine_qa_passed_not_human_approved",
 "video_sha256":hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
 "caption_sha256":hashlib.sha256(caption.encode("utf-8")).hexdigest(),
 "format":{"width":1080,"height":1920,"fps":30,"codec":"H264","audio":"AAC","slides":info["slides"],"slide_durations":info["slide_durations"],"voiceover":info["voiceover"],"duration_seconds":round(float(probe["format"]["duration"]),2)},
 "no_extra_watermark":True,"soundtrack":"owner_music_mixed_under_cosyvoice3_deep_male",
 "license_and_music_rights_must_be_held_by_owner":True,
 "tiktok_oauth_connected":None,
 "recipient_account_verified":None,
 "express_consent_given":False,
 "content_preview_confirmed":False,
 "posting_enabled":False
}
(OUT/"tiktok_preview.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("TIKTOK READY-TO-REVIEW:",local_day,"1080x1920, MP4/AAC, variable real-photo slides, source, caption and hashtags.")
print("TIKTOK POSTING=DISABLED; user/account and post-specific authorization required.")

