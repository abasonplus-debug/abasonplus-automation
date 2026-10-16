#!/usr/bin/env python3
"""Read today's ChatGPT-researched GitHub editorial and prepare topic-specific 5-slide render.
No network, no social publication, no source invention.
"""
import json, pathlib, sys
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1]
out=ROOT/"output";out.mkdir(exist_ok=True)
today=datetime.now(ZoneInfo("Asia/Dhaka")).date().isoformat()
f=ROOT/"content"/f"daily_editorial_{today}.json"
if not f.exists():
    print("NO_CHATGPT_DAILY_EDITORIAL: refusing repeated static carousel")
    sys.exit(3)
data=json.loads(f.read_text(encoding="utf-8"))
story=data.get("story")
if data.get("date")!=today or data.get("verified_on")!=today:
    raise RuntimeError("Daily editorial is not verified today")
if not data.get("source_url","").startswith("https://") or data["source_url"] not in data.get("content",""):
    raise RuntimeError("Source missing or not present in daily article")
if not isinstance(story,dict) or len(story.get("tips",[]))!=4:
    raise RuntimeError("Need exactly four new, sourced carousel tips")
if story.get("source_url")!=data["source_url"] or story.get("verified_on")!=today:
    raise RuntimeError("Slide and article source/version mismatch")
for x in story["tips"]:
    if not (8<=len(x.get("text",""))<=88 and 5<=len(x.get("query",""))<=140):
        raise RuntimeError("One slide has no concise readable Bengali/visual brief")
if not 12<=len(story.get("hook",""))<=100:
    raise RuntimeError("Hook missing or unsuitable")
if not 7<=len(story.get("cover_query",""))<=140:
    raise RuntimeError("Cover photographic brief missing")
story["source_kind"]=("official_law_reference" if "bdlaws.minlaw.gov.bd" in data["source_url"] else "external_news_report")
story["expires_on"]=today
p=out/"daily_research_story.json"
p.write_text(json.dumps(story,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("VALIDATED_DAILY_VIDEO_BRIEF:",today,"source URL recorded; no posts sent")
