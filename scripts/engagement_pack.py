"""Owner-required social copy assets. No network, publishing or paid generation."""
import json,re,unicodedata
from pathlib import Path

def hashtag_tokens(text):
    return set(unicodedata.normalize('NFC',s.rstrip('.,;:!?।')).casefold() for s in re.findall(r'(?<!\S)#[^\s#]+',text))

def hashtags_for(topic):
    topic=unicodedata.normalize('NFC',str(topic)).casefold()
    if any(x in topic for x in ('অগ্নি','fire safety','fire-safety')): specific=['#অগ্নিনিরাপত্তা','#ভবননিরাপত্তা']
    elif any(x in topic for x in ('জলাধার','কৃষিজমি')): specific=['#কৃষিজমি','#নির্মাণঅনুমতি']
    elif any(x in topic for x in ('টানেল','সেতু','মেট্রো','সড়ক','সড়ক','অবকাঠামো','bridge','tunnel')): specific=['#অবকাঠামো','#সরকারিপ্রকল্প']
    elif any(x in topic for x in ('আইন','দলিল','খতিয়ান','খতিয়ান','law','deed')): specific=['#ভূমিআইন','#জমিরদলিল']
    elif 'জমি' in topic or 'land' in topic: specific=['#জমি','#জমিকেনা']
    elif any(x in topic for x in ('নির্মাণ','সিমেন্ট','রড','ইট')): specific=['#নির্মাণ','#নির্মাণসামগ্রী']
    elif any(x in topic for x in ('ফ্ল্যাট','বাড়ি','বাড়ি','home')): specific=['#ফ্ল্যাট','#বাড়ি']
    else: specific=['#জনসচেতনতা','#গুরুত্বপূর্ণতথ্য']
    # Owner-selected broad audience tags; no measured popularity/reach claim.
    return specific+['#Bangladesh','#বাংলাদেশ','#Bangla']

def first_comment(hook):
    return f'{hook}\nআপনার প্রশ্ন বা অভিজ্ঞতা লিখুন। বিস্তারিত: https://abasonplus.wordpress.com/'

def validate_pack(pack):
    broad=hashtag_tokens('#Bangladesh #বাংলাদেশ #Bangla')
    for field in ('caption','description'):
        tokens=hashtag_tokens(pack[field])
        raw=re.findall(r'(?<!\S)#[^\s#]+',pack[field])
        if len(raw)!=5 or len(tokens)!=5 or not broad.issubset(tokens):
            raise ValueError('Exactly two topic tags and three broad audience tags required; no duplicates')
    if not pack['hook'].strip() or not 1<=len(pack['first_comment'])<=500:
        raise ValueError('Hook or first comment missing/too long')
    if pack['music']!='assets/abasonplus.mp3':raise ValueError('Owner music must not be substituted')
    if pack['thumbnail']!='output/thumbnail.png':raise ValueError('Hook cover missing')
    if pack.get('thumbnail_source')!='slide_0':raise ValueError('Cover must match approved first slide')
    return True

def write_pack(out,hook,caption,description):
    pack=dict(hook=hook,caption=caption,description=description,first_comment=first_comment(hook),music='assets/abasonplus.mp3',thumbnail='output/thumbnail.png',thumbnail_source='slide_0',view_growth_guaranteed=False)
    validate_pack(pack)
    (out/'first_comment.txt').write_text(pack['first_comment'],encoding='utf-8')
    (out/'first_comment_json.txt').write_text(json.dumps(pack['first_comment'],ensure_ascii=False),encoding='utf-8')
    (out/'engagement_pack.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return pack
