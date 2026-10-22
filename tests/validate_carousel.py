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
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from carousel_style import layout, paint, STYLE_ID
latin=next(pathlib.Path('/usr/share/fonts').rglob('NotoSans-Bold.ttf'))
checked=0
for topic in catalog:
    assert 4<=len(topic['tips'])<=9
    for idx,message in enumerate([topic['hook']]+[p['text'] for p in topic['tips']]):
        font=ImageFont.truetype(str(fonts[0]),132 if idx==0 else 120)
        lf=ImageFont.truetype(str(latin),font.size)
        def tokens(value,f):
            import re
            for token in re.findall(r'\s+|\S+',value):
                yield token,f if any(0x0980<=ord(c)<=0x09ff for c in token) else lf
        rows=layout(message,font,tokens)
        layer,boxes=paint(rows,tokens)
        assert layer.getbbox() and boxes
        checked+=1

# Semantic models can mistake the NASA "Surveyor" probe for a land surveyor.
# Verify title checks independently without importing the renderer or downloading photos.
import re
tree=ast.parse(SOURCE)
guard_node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="subject_guard")
scope={}
exec(compile(ast.Module(body=[guard_node],type_ignores=[]),"subject_guard","exec"),{"re":re},scope)
guard=scope["subject_guard"]
assert not guard("land surveyor in a field","Surface of the Moon as seen by Surveyor 3.jpg")
assert not guard("property paperwork","Document concerning an unrelated historical record.jpg")
assert guard("land surveyor in a field","Land surveyor using a total station.jpg")
assert guard("property paperwork","Real estate property agreement documents.jpg")

# Only scheduled and sourced, QA-passed video uploads may publish.
video_workflow=(ROOT/".github/workflows/daily-carousel.yml").read_text(encoding="utf-8")
assert "cron: '0 1 * * *'" in video_workflow,"Unexpected scheduled video time"
assert "timezone: 'Europe/Berlin'" in video_workflow
assert "needs.source.outputs.ready == 'true'" in video_workflow,"Video missing fresh daily editorial gate"
assert "if: ${{ github.event_name == 'schedule' }}" in video_workflow,"Manual video workflow must be preview-only"
assert "python3 scripts/select_video_story.py" in video_workflow,"Mandatory topic-and-source gate missing"
assert "validate_timing(meta," in video_workflow and "validate_style(quality_record)" in video_workflow and "verify_voiceover(out, news, meta)" in video_workflow,"Mandatory visual/timing/voice QA missing"
assert "python3 scripts/verify_video_release.py" in video_workflow,"Independent photo release gate missing"
assert '-F "visual_qa_passed=true"' in video_workflow,"Make video QA approval mapping missing"
# Owner explicitly enabled ONLY WordPress Post by Email, scheduled once daily.
wp_workflow=(ROOT/".github/workflows/wordpress-post.yml").read_text(encoding="utf-8")
assert "cron: '0 1 * * *'" in wp_workflow,"WordPress expected 02:00 Berlin schedule"
assert "timezone: 'Europe/Berlin'" in wp_workflow
assert "github.event_name == 'schedule'" in wp_workflow,"WordPress manual runs must stay preview-only"
assert (ROOT / "assets" / "abasonplus.mp3").stat().st_size > 1000, "Original audio missing"
print(f"Validated {len(catalog)} topics, {checked} compact white/gold outlined layouts at 120px+, source-gated VIDEO publishing, separately scheduled WordPress, and original audio.")

