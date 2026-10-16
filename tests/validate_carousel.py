#!/usr/bin/env python3
"""Offline, non-publishing validation for AbasonPlus carousel source and catalog."""
import ast
import json
import pathlib
from PIL import Image, ImageDraw, ImageFont, features

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "create_carousel.py").read_text(encoding="utf-8")
ast.parse(SOURCE,filename="scripts/create_carousel.py")
catalog = json.loads((ROOT / "content" / "topics.json").read_text(encoding="utf-8"))
assert len(catalog) >= 15, "At least 15 distinct curated topics required"
assert len({x["title"] for x in catalog}) == len(catalog), "Topic duplicated"
photo_map=json.loads((ROOT/"content"/"researched_photos.json").read_text(encoding="utf-8"))
photo_urls=[]
for subject,pictures in photo_map.items():
    assert 5<=len(pictures)<=10,subject
    for entry in pictures:
        assert entry["source"].startswith("https://www.pexels.com/photo/"),subject
        assert entry["license"]=="Pexels Free License",subject
        assert entry["url"].startswith("https://images.pexels.com/photos/"),subject
        photo_urls.append(entry["url"])
assert len(photo_urls)==len(set(photo_urls)), "Exact curated photo reused across multiple videos"
assert features.check("raqm"), "Bengali shaping support missing"
fonts = [p for p in pathlib.Path("/usr/share/fonts").rglob("*.ttf") if "Bengali" in p.name and "Bold" in p.name]
assert fonts, "Bold Bengali font missing"
dummy = Image.new("RGBA",(1080,1920))
d = ImageDraw.Draw(dummy)

def wrap(value,font):
    lines=[]
    current=""
    for word in value.split():
        candidate=(current+" "+word).strip()
        if current and d.textbbox((0,0),candidate,font=font)[2]>950:
            lines.append(current)
            current=word
        else:
            current=candidate
    if current: lines.append(current)
    assert lines and all(d.textbbox((0,0),x,font=font)[2]<=950 for x in lines),f"Unfit 120px: {value}"
    return lines

checked=0
for topic in catalog:
    assert len(topic["tips"]) >= 4 and len(topic["tips"]) <= 9
    cases = [topic["hook"]] + [p["text"] for p in topic["tips"]]
    for idx,message in enumerate(cases):
        assert idx == 0 or topic["tips"][idx-1]["query"]
        assert topic["cover_query"]
        font=ImageFont.truetype(str(fonts[0]),120)
        lines=wrap(message,font)
        assert len(lines)<=3,(topic["title"],message,len(lines))
        layer=Image.new("RGBA",(1080,1920))
        dt=ImageDraw.Draw(layer)
        def drawline(t,y):
            width=dt.textbbox((0,0),t,font=font)[2]
            dt.text(((1080-width)//2,y),t,font=font,fill=(6,27,62,230))
        for j,line in enumerate(lines): drawline(line,260+j*int(font.size*1.52))
        bbox=layer.getbbox()
        assert bbox and 65<=bbox[0]<bbox[2]<=1015 and 220<=bbox[1]<bbox[3]<=1100,(topic["title"],idx,"selected style safe region")
        checked+=1

# Only scheduled and sourced, QA-passed video uploads may publish.
video_workflow=(ROOT/".github/workflows/daily-carousel.yml").read_text(encoding="utf-8")
assert "cron: '45 6 * * *'" in video_workflow,"Unexpected scheduled video time"
assert "needs.source.outputs.ready == 'true'" in video_workflow,"Video missing fresh daily editorial gate"
assert "if: ${{ github.event_name == 'schedule' }}" in video_workflow,"Manual video workflow must be preview-only"
assert "python3 scripts/select_video_story.py" in video_workflow,"Mandatory topic-and-source gate missing"
assert "Verify dimensions, original audio and visual layout" in video_workflow,"Mandatory rendering QA missing"
assert "python3 scripts/verify_video_release.py" in video_workflow,"Independent photo release gate missing"
assert '-F "visual_qa_passed=true"' in video_workflow,"Make video QA approval mapping missing"
# Owner explicitly enabled ONLY WordPress Post by Email, scheduled once daily.
wp_workflow=(ROOT/".github/workflows/wordpress-post.yml").read_text(encoding="utf-8")
assert "cron: '20 6 * * *'" in wp_workflow,"WordPress expected 06:20 UTC schedule"
assert "github.event_name == 'schedule'" in wp_workflow,"WordPress manual runs must stay preview-only"
assert (ROOT / "assets" / "abasonplus.mp3").stat().st_size > 1000, "Original audio missing"
print(f"Validated {len(catalog)} topics, {checked} dark direct-photo headline layouts at 120px+, source-gated VIDEO publishing, separately scheduled WordPress, and original audio.")
