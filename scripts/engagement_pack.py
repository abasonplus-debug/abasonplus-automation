"""Owner-required social copy assets. No network, publishing or paid generation."""
import json,re,unicodedata
from pathlib import Path

def hashtag_tokens(text):
    return set(unicodedata.normalize('NFC',s.rstrip('.,;:!?।')).casefold() for s in re.findall(r'(?<!\S)#[^\s#]+',text))

BROAD_TAGS = {
    "facebook": ["#Bangladesh", "#বাংলাদেশ", "#ReelsBD"],
    "youtube": ["#Bangladesh", "#বাংলাদেশ", "#Bangla", "#Shorts"],
    "instagram": ["#Bangladesh", "#Bangla", "#Reels"],
    "tiktok": ["#Bangladesh", "#বাংলাদেশ", "#BanglaTikTok"],
}

def hashtags_for(topic, platform=None):
    topic=unicodedata.normalize('NFC',str(topic)).casefold()
    if any(x in topic for x in ('নামজারি','নামজারী','mutation')): specific=['#নামজারি','#ভূমিসেবা']
    elif any(x in topic for x in ('bds','ডিজিটাল জরিপ')): specific=['#ডিজিটালজরিপ','#ভূমিরেকর্ড']
    elif any(x in topic for x in ('land share','ল্যান্ড শেয়ার','ল্যান্ড শেয়ার')): specific=['#LandShare','#জমিরঅংশীদারত্ব']
    elif any(x in topic for x in ('অগ্নি','fire safety','fire-safety')): specific=['#অগ্নিনিরাপত্তা','#ভবননিরাপত্তা']
    elif any(x in topic for x in ('জলাধার','কৃষিজমি')): specific=['#কৃষিজমি','#নির্মাণঅনুমতি']
    elif any(x in topic for x in ('টানেল','সেতু','মেট্রো','সড়ক','সড়ক','অবকাঠামো','bridge','tunnel')): specific=['#অবকাঠামো','#সরকারিপ্রকল্প']
    elif any(x in topic for x in ('আইন','দলিল','খতিয়ান','খতিয়ান','law','deed')): specific=['#ভূমিআইন','#জমিরদলিল']
    elif 'জমি' in topic or 'land' in topic: specific=['#জমি','#জমিকেনা']
    elif any(x in topic for x in ('নির্মাণ','সিমেন্ট','রড','ইট')): specific=['#নির্মাণ','#নির্মাণসামগ্রী']
    elif any(x in topic for x in ('ফ্ল্যাট','বাড়ি','বাড়ি','home')): specific=['#ফ্ল্যাট','#বাড়ি']
    else: specific=['#জনসচেতনতা','#গুরুত্বপূর্ণতথ্য']
    # Owner-selected broad audience tags; no measured popularity/reach claim.
    if platform is not None and platform not in BROAD_TAGS: raise ValueError('Unknown social platform')
    return specific+(BROAD_TAGS[platform] if platform else ['#Bangladesh','#বাংলাদেশ','#Bangla'])

def first_comment(hook):
    return f'{hook}\nআপনার প্রশ্ন বা অভিজ্ঞতা লিখুন। বিস্তারিত: https://abasonplus.wordpress.com/'

def validate_pack(pack):
    for field in ('caption','description'):
        platform=pack.get('field_platforms',{}).get(field)
        broad=hashtag_tokens(' '.join(BROAD_TAGS[platform])) if platform else hashtag_tokens('#Bangladesh #বাংলাদেশ #Bangla')
        tokens=hashtag_tokens(pack[field])
        raw=re.findall(r'(?<!\S)#[^\s#]+',pack[field])
        if len(raw)!=len(broad)+2 or len(tokens)!=len(broad)+2 or not broad.issubset(tokens):
            raise ValueError('Exactly two topic tags and three broad audience tags required; no duplicates')
    if not pack['hook'].strip() or not 1<=len(pack['first_comment'])<=500:
        raise ValueError('Hook or first comment missing/too long')
    if pack['music']!='assets/abasonplus.mp3':raise ValueError('Owner music must not be substituted')
    if pack['thumbnail']!='output/thumbnail.png':raise ValueError('Hook cover missing')
    if pack.get('thumbnail_source')!='slide_0':raise ValueError('Cover must match approved first slide')
    return True

def write_pack(out,hook,caption,description):
    legacy='#Bangladesh #বাংলাদেশ #Bangla'
    caption=caption.replace(legacy,' '.join(BROAD_TAGS['facebook']))
    description=description.replace(legacy,' '.join(BROAD_TAGS['youtube']))
    pack=dict(hook=hook,caption=caption,description=description,first_comment=first_comment(hook),music='assets/abasonplus.mp3',thumbnail='output/thumbnail.png',thumbnail_source='slide_0',view_growth_guaranteed=False)
    pack['field_platforms']={'caption':'facebook','description':'youtube'}
    validate_pack(pack)
    instagram_caption=caption.replace(' '.join(BROAD_TAGS['facebook']), ' '.join(BROAD_TAGS['instagram']))
    if len(instagram_caption)>2200: raise ValueError('Instagram caption overflow')
    (out/'instagram_caption.txt').write_text(instagram_caption,encoding='utf-8')
    pack['instagram_caption']=instagram_caption
    (out/'first_comment.txt').write_text(pack['first_comment'],encoding='utf-8')
    (out/'first_comment_json.txt').write_text(json.dumps(pack['first_comment'],ensure_ascii=False),encoding='utf-8')
    (out/'engagement_pack.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return pack
