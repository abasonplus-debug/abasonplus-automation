"""Locked owner-selected compact white/gold style. No network or publishing."""
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageStat

POLICY=json.loads((Path(__file__).resolve().parents[1]/'config/carousel_style.json').read_text())
STYLE_ID=POLICY['style_id']
WHITE='#FFFFFF'
GOLD='#FFD24A'
OUTLINE='#101010'
KEYWORDS=('মেট্রোরেল','চুক্তি','প্রমাণ','মালিকানা','যাচাই','সীমানা','সতর্ক','আগে','দলিল','খতিয়ান','খতিয়ান','ঝুঁকি','নথি','মূল্য','খরচ','নিরাপত্তা','পরামর্শ')

def photo_stats(photo,regions):
    result=[]
    for box in regions:
        area=photo.crop(box).convert('L')
        edge=area.filter(ImageFilter.FIND_EDGES)
        if min(edge.size)>4: edge=edge.crop((2,2,edge.width-2,edge.height-2))
        result.append([round(ImageStat.Stat(area).mean[0],2),round(ImageStat.Stat(area).stddev[0],2),round(ImageStat.Stat(edge).mean[0],2)])
    return result

def readable_photo(stats):
    # Outlined white/gold works on light or dark photos. Still reject chaotic backgrounds.
    return bool(stats) and all(len(r)==3 and r[1]<=80 and r[2]<=45 for r in stats)

def layout(text,font,tokens):
    measure=ImageDraw.Draw(Image.new('RGBA',(1080,1920)))
    def width(s): return sum(measure.textlength(t,font=f) for t,f in tokens(s,font))
    groups=re.findall(r'[^।!?\n]+[।!?]?|[^\n]+$',text)
    lines=[]
    for group in groups:
        current=''
        separator=''
        # A dash between scripts is a legal line-break opportunity, not one
        # unbreakable word. Preserve every non-whitespace character and size.
        for word in re.findall(r'\s+|[^\s—–]+[—–]?|[—–]',group):
            if word.isspace():
                separator=' '
                continue
            candidate=current+separator+word if current else word
            if current and width(candidate)>928:
                lines.append((current,False));current=word
            else: current=candidate
            separator=''
        if current: lines.append((current,True))
    if not lines or len(lines)>10: raise RuntimeError('Exact text does not fit compact 120px+ block; split or shorten only with permission')
    rows=[];cursor=0
    for line,end in lines:
        w=width(line)
        if w>928: raise RuntimeError('Unbreakable word exceeds safe width')
        x=(1080-w)/2
        boxes=[];parts=[]
        for token,f in tokens(line,font):
            if not token.isspace():
                boxes.append(measure.textbbox((x,0),token,font=f,anchor='ls',stroke_width=4))
                parts.append((x,token,f))
            x+=measure.textlength(token,font=f)
        b=[min(a[0] for a in boxes),min(a[1] for a in boxes),max(a[2] for a in boxes)+2,max(a[3] for a in boxes)+3]
        baseline=cursor-b[1]
        box=[b[0],cursor,b[2],cursor+b[3]-b[1]]
        rows.append({'text':line,'parts':parts,'baseline':baseline,'bbox':box,'sentence_end':end})
        cursor=box[3]+(10 if end else 4)
    height=rows[-1]['bbox'][3]
    if height>1450: raise RuntimeError('Compact block exceeds safe height at minimum font size')
    offset=round((1920-height)/2)
    for row in rows:
        row['baseline']+=offset
        row['bbox']=[round(row['bbox'][0]),round(row['bbox'][1]+offset),round(row['bbox'][2]),round(row['bbox'][3]+offset)]
    return rows

def paint(rows,tokens):
    layer=Image.new('RGBA',(1080,1920))
    d=ImageDraw.Draw(layer)
    ink_boxes=[]
    for row in rows:
        line_layer=Image.new('RGBA',layer.size);p=ImageDraw.Draw(line_layer)
        for x,token,font in row['parts']:
            color=GOLD if any(k in token for k in KEYWORDS) else WHITE
            y=row['baseline']
            p.text((x+2,y+3),token,font=font,anchor='ls',fill=OUTLINE,stroke_width=5,stroke_fill=OUTLINE)
            p.text((x,y),token,font=font,anchor='ls',fill=color,stroke_width=4,stroke_fill=OUTLINE)
        box=line_layer.getbbox()
        if not box or not(64<=box[0]<box[2]<=1016 and 200<=box[1]<box[3]<=1720):
            raise RuntimeError(f'Text effects outside safe block: {box}, {row["text"]}')
        if ink_boxes and ink_boxes[-1][3]>=box[1]:raise RuntimeError('Rendered lines collide including shadow')
        ink_boxes.append(list(box));layer=Image.alpha_composite(layer,line_layer)
    return layer,ink_boxes

def validate_style(info):
    if info.get('style_id')!=STYLE_ID:raise ValueError('Old or unknown style')
    if info.get('main_font_px',0)<120 or info.get('font_px',0)<120:raise ValueError('Small font')
    if info.get('slide')==1 and info.get('font_px',0)<132:raise ValueError('Small hook')
    if info.get('text_colors')!=[WHITE,GOLD] or info.get('stroke_px')!=4 or info.get('text_stroke') is not True or info.get('text_shadow') is not True:raise ValueError('Wrong typography')
    if info.get('text_background') is not False or info.get('photo_overlay') is not False:raise ValueError('Panel/overlay forbidden')
    boxes=info.get('line_ink_boxes',[])
    if len(boxes)!=info.get('text_lines') or not 1<=len(boxes)<=10:raise ValueError('Line QA absent')
    for i,b in enumerate(boxes):
        if len(b)!=4 or not(64<=b[0]<b[2]<=1016 and 200<=b[1]<b[3]<=1720):raise ValueError('Unsafe text bounds')
        if i and boxes[i-1][3]>=b[1]:raise ValueError('Line collision')
    if info.get('alignment')!='center' or info.get('compact_spacing_qa') is not True:raise ValueError('Compact layout missing')
    if not readable_photo(info.get('line_background_stats',[])) or len(info['line_background_stats'])!=len(boxes):raise ValueError('Photo readability failed')
    logo=info.get('logo_box')
    if info.get('logo_position')=='bottom_right':
        if not logo or not(70<=logo[2]-logo[0]<=90 and 24<=1080-logo[2]<=32 and 24<=1920-logo[3]<=32):raise ValueError('Logo placement wrong')
    elif info.get('logo_position')!='omitted_unavailable':raise ValueError('Invented logo')
    return True

