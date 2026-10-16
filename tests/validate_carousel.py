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
assert features.check("raqm"), "Bengali shaping support missing"
fonts = [p for p in pathlib.Path("/usr/share/fonts").rglob("*.ttf") if "Bengali" in p.name and "Regular" in p.name]
assert fonts, "Regular Bengali font missing"
font = ImageFont.truetype(str(fonts[0]),130)
dummy = Image.new("RGBA",(1080,1920))
d = ImageDraw.Draw(dummy)

def wrap(value):
    lines=[]
    current=""
    for word in value.split():
        candidate=(current+" "+word).strip()
        if current and d.textbbox((0,0),candidate,font=font)[2]>940:
            lines.append(current)
            current=word
        else:
            current=candidate
    if current: lines.append(current)
    assert lines and all(d.textbbox((0,0),x,font=font)[2]<=940 for x in lines),f"Unfit 130px: {value}"
    return lines

checked=0
for topic in catalog:
    assert len(topic["tips"]) >= 4 and len(topic["tips"]) <= 9
    cases = [(topic["hook"],"জরুরি তথ্য")] + [(p["text"],f"পরামর্শ {i}/{len(topic['tips'])}") for i,p in enumerate(topic["tips"],1)]
    for idx,(message,sub) in enumerate(cases):
        assert idx == 0 or topic["tips"][idx-1]["query"]
        assert topic["cover_query"]
        top=wrap(topic["title"] if idx else "আবাসনপ্লাস")
        middle=wrap(message)
        bottom=wrap(sub)
        assert len(top)<=2 and len(middle)<=4 and len(bottom)==1,(topic["title"],message,len(top),len(middle),len(bottom))
        layer=Image.new("RGBA",(1080,1920))
        dt=ImageDraw.Draw(layer)
        def drawline(t,y):
            width=dt.textbbox((0,0),t,font=font)[2]
            dt.text(((1080-width)//2,y),t,font=font,fill=(255,255,255,205),stroke_width=2,stroke_fill=(0,0,0,185))
        for j,line in enumerate(top): drawline(line,265+j*170)
        start=960-((len(middle)-1)*170)//2
        for j,line in enumerate(middle): drawline(line,start+j*170)
        drawline(bottom[0],1500)
        bbox=layer.getbbox()
        assert bbox and bbox[3]-bbox[1]>=1152,(topic["title"],idx,"<60% vertical composition")
        assert bbox[3]<1750,(topic["title"],idx,"UI safe region overflow")
        checked+=1

for path in [".github/workflows/daily-carousel.yml",".github/workflows/wordpress-post.yml"]:
    workflow=(ROOT/path).read_text(encoding="utf-8")
    assert "if: ${{ false }}" in workflow,f"Unexpected enabled publisher: {path}"
    assert "  schedule:" not in workflow,f"Unexpected automatic publishing: {path}"
assert 'root / "assets"' not in SOURCE.lower()
assert (ROOT / "assets" / "abasonplus.mp3").stat().st_size > 1000, "Original audio missing"
print(f"Validated {len(catalog)} topics, {checked} frame layouts, 130px font, >=60% vertical text composition, paused publishing and original audio.")
