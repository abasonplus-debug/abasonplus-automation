#!/usr/bin/env python3
"""Free 15-second Bengali housing tips carousel."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FONT = next((str(p) for p in Path("/usr/share/fonts").rglob("*Bengali*Regular.ttf")), None)
if not FONT:
    raise RuntimeError("Noto Bengali font missing")
title_font = ImageFont.truetype(FONT, 72)
body_font = ImageFont.truetype(FONT, 56)
small_font = ImageFont.truetype(FONT, 35)
topics = [
    ("জমি কেনার আগে", ["মালিকানার কাগজ যাচাই করুন", "দলিল ও খতিয়ান মিলিয়ে দেখুন", "দাগ নম্বর ও সীমানা পরীক্ষা করুন", "বিরোধ বা দায় আছে কি না জানুন"]),
    ("ফ্ল্যাট কেনার আগে", ["প্রকল্পের অনুমোদন যাচাই করুন", "চুক্তির শর্ত ভালোভাবে পড়ুন", "হস্তান্তরের সময় জেনে নিন", "বিশেষজ্ঞের পরামর্শ নিন"]),
    ("বাড়ি নির্মাণের আগে", ["অনুমোদিত নকশা যাচাই করুন", "মাটির পরীক্ষা সম্পর্কে জানুন", "উপকরণের মান যাচাই করুন", "প্রকৌশলীর পরামর্শ নিন"]),
]
today = datetime.now(timezone(timedelta(hours=6))).date()
heading, tips = topics[today.toordinal() % len(topics)]
slides = [(heading, "আবাসন+ | আজকের চারটি পরামর্শ")] + [(tip, f"পরামর্শ {i}/৪") for i, tip in enumerate(tips, 1)]
def center(draw, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((1080-(bbox[2]-bbox[0]))/2, y), text, font=font, fill=fill, stroke_width=0)
for i,(main,sub) in enumerate(slides):
    im=Image.new("RGB",(1080,1920),(11,31,54))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((65,100,1015,1820),radius=65,fill=(21,58,84),outline=(59,186,169),width=6)
    center(d,"আবাসন+",250,title_font,(126,240,211))
    d.line((150,420,930,420),fill=(59,186,169),width=4)
    center(d,main,760,title_font,(255,255,255))
    center(d,sub,1040,body_font,(194,220,230))
    center(d,"abasonplus.wordpress.com",1650,small_font,(126,240,211))
    im.save(OUT/f"slide_{i}.png")
playlist=OUT/"slides.txt"
playlist.write_text("".join(f"file 'slide_{i}.png'\nduration 3\n" for i in range(5))+"file 'slide_4.png'\n",encoding="utf-8")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(playlist),"-t","15","-r","25","-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","28","-movflags","+faststart",str(OUT/"abasonplus_daily.mp4")],cwd=OUT,check=True)
print("Created",OUT/"abasonplus_daily.mp4")
