"""Owner-required social copy assets. No network, publishing or paid generation."""
import json,re,unicodedata
from pathlib import Path

def hashtag_tokens(text):
    return set(unicodedata.normalize('NFC',s.rstrip('.,;:!?।')).casefold() for s in re.findall(r'(?<!\S)#[^\s#]+',text))

def hashtags_for(topic):
    tags=['#AbasonPlus','#আবাসন','#RealEstateBangladesh']
    if any(x in topic for x in ('আইন','দলিল','খতিয়ান','খতিয়ান')):tags+=['#ভূমিআইন','#জমিরদলিল','#LandRecords']
    elif 'জমি' in topic or 'Land' in topic:tags+=['#জমি','#জমিকেনা','#PropertyTips']
    elif any(x in topic for x in ('নির্মাণ','সিমেন্ট','রড','ইট')):tags+=['#নির্মাণ','#BuildingMaterials','#ConstructionTips']
    else:tags+=['#ফ্ল্যাট','#HomeBuying','#PropertyTips']
    return tags

def first_comment(hook):
    return f'{hook}\nআপনার প্রশ্ন বা অভিজ্ঞতা লিখুন। বিস্তারিত: https://abasonplus.wordpress.com/'

def validate_pack(pack):
    if len(hashtag_tokens(pack['caption']))<5 or len(hashtag_tokens(pack['description']))<5:
        raise ValueError('Five DISTINCT relevant hashtags required in caption and description')
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
