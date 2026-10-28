"""Verify and deliver ONE owner-approved immutable preview; no media synthesis or TikTok post.

Only the 28 October original-resolution exception is accepted, bound to the exact
MP4 and original-background hashes. All other source/layout/audio/semantic,
free-quota, same-day and duplicate checks remain mandatory. No request retries.
"""
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import argparse,json,hashlib,sys,subprocess,math,shutil,os,re,wave
from urllib.request import Request,urlopen
from PIL import Image,ImageFont,ImageOps,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'assets/editorial/2026-10-28-reviewed'
OUT=ROOT/'output';DAY='2026-10-28'
SHA='56c921431c655997993dcecb5f2e3a7da3de97078a7b88960552112e82d4397e'
BERLIN=ZoneInfo('Europe/Berlin')

def need(ok,why):
    if not ok:raise ValueError(why)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def current():need(datetime.now(BERLIN).date().isoformat()==DAY,'Stale one-time request')
def request():
    current();r=read(ROOT/'audits/approved-media/2026-10-28.json')
    need(r['video_sha256']==SHA and r['owner_authorized'] is True and r['date']==DAY,'Wrong exact owner request')
    need(r['owner_evidence'][0]['text']=='Post করো 5 জায়গায়' and r['owner_evidence'][1]['text']=='সম্পূর্ণ করো কাজ','Missing actual owner instructions')
    need(r['native_resolution_exception']['video_sha256']==SHA and r['native_resolution_exception']['one_time_only'] is True,'No artifact-bound exception')
    return r

def verify(semantic=True):
    r=request();OUT.mkdir(exist_ok=True)
    for x in r['files']:
        p=ROOT/x['path'];need(p.is_file() and digest(p)==x['sha256'],'Altered asset '+x['path'])
    video=B/'video.mp4';need(digest(video)==SHA,'Changed approved MP4')
    texts=read(B/'script.json');voice=read(B/'voice_manifest.json');quality=read(B/'visual_qa.json')['slides']
    need(len(texts)==len(quality)==len(voice['segments'])==7,'Slide/voice mismatch')
    need(voice['complete'] is True and voice['engine']=='CosyVoice3' and voice['reference']=='Dan Mason' and voice['playback_speed']==1.2,'Wrong exact voice')
    need(voice['voice_gain']==1 and voice['music_gain']==.2,'Changed mix')
    need(digest(ROOT/'assets/abasonplus.mp3')==r['owner_music_sha256'],'Wrong music')
    from publication_policy import validate_article_html,trusted_source_url
    article=read(ROOT/'content/daily_editorial_2026-10-28.json')
    need(article['date']==article['verified_on']==DAY and article['source_url']==r['source_url'],'Wrong editorial/source/date')
    need(trusted_source_url(article['source_url']) and article['source_url'] in article['content'],'Untrusted/missing article source')
    validate_article_html(article['content']);need(len(article['content'])>=1700 and article['content'].count('<h2>')>=3,'Incomplete article')
    sys.path.insert(0,str(B/'scripts'))
    import importlib.util
    spec=importlib.util.spec_from_file_location('approved_exact_style',B/'scripts/carousel_style.py');style=importlib.util.module_from_spec(spec);spec.loader.exec_module(style)
    from bilingual_text import BilingualText
    tokens=BilingualText(B/'Bengali-Bold.ttf',B/'Latin-Bold.ttf').tokens
    from fontTools.ttLib import TTFont
    cmap=set()
    for fontfile in (B/'Bengali-Bold.ttf',B/'Latin-Bold.ttf'):
        for table in TTFont(fontfile)['cmap'].tables:cmap.update(table.cmap)
    need(all(ch.isspace() or ord(ch) in cmap for text in texts for ch in text),'Missing glyph coverage')
    if semantic:
        from photo_relevance import PhotoRelevanceGuard
        guard=PhotoRelevanceGuard()
    logo=Image.open(B/'logo.png').convert('RGBA');logo.thumbnail((90,90));pos=(1080-logo.width-28,1920-logo.height-28)
    from cosyvoice3_daily_voiceover import validate_segment,concat_with_padding
    voice.update(narrated_slide_count=7,script_sha256=hashlib.sha256('\n'.join(texts).encode()).hexdigest(),mix='narration_100_music_20_no_amix_normalization');times=voice['slide_durations'];need(len(times)==7,'Timing absent');sources=set();semantic_rows=[];now=0
    for i,(text,part,seconds) in enumerate(zip(texts,voice['segments'],times)):
        bgfile=B/f'background_{i}.png';sha=digest(bgfile);need(sha not in sources,'Repeated background');sources.add(sha)
        a=r['illustrations'][i];need(a['sha256']==sha and a['contains_text'] is False and a['rights_confirmed'] is True and a['illustrative_not_real_event'] is True,'Missing real asset evidence')
        need(bgfile.resolve().is_relative_to(ROOT/'assets/editorial'),'Asset escaped repository')
        im=Image.open(bgfile).convert('RGB');need(list(im.size)==a['original_dimensions'],'Altered source dimensions')
        if im.width<1080 or im.height<1920:need(sha in r['native_resolution_exception']['background_sha256'],'Exception does not cover this background')
        crop=ImageOps.fit(im,(1080,1920),method=Image.Resampling.LANCZOS)
        if semantic:
            good,bad=guard.score(crop,a['scene'],visual_kind='illustration');need(good>=.22 and good-bad>=.025,'Semantic scene mismatch '+str(i+1));semantic_rows.append({'slide':i+1,'matching':good,'negative':bad,'passed':True})
        else:need(read(B/'semantic_qa.json')[i]['passed'] is True,'No local semantic check')
        f=ImageFont.truetype(str(B/'Bengali-Bold.ttf'),132 if i==0 else 120,layout_engine=ImageFont.Layout.RAQM)
        rows=style.layout(text,f,tokens);layer,boxes=style.paint(rows,tokens);stats=style.photo_stats(crop,boxes);need(style.readable_photo(stats),'Background clutter')
        rendered=crop.convert('RGBA');rendered.alpha_composite(logo,pos);rendered=Image.alpha_composite(rendered,layer).convert('RGB');rendered.save(OUT/f'slide_{i}.png')
        need(part['text']==text and part['audio_sha256']==digest(B/f'voice_{i}.wav'),'Voice/script altered')
        speech=validate_segment(B/f'voice_{i}.wav');need(abs(speech-part['seconds'])<.015 and seconds>=speech+.15 and seconds>=3,'Incomplete speech timing')
        sample=OUT/f'decoded_{i}.jpg';subprocess.run(['ffmpeg','-y','-v','error','-ss',str(now+seconds/2),'-i',str(video),'-frames:v','1','-update','1',str(sample)],check=True,capture_output=True)
        difference=sum(ImageStat.Stat(ImageChops.difference(Image.open(sample).convert('RGB'),rendered)).mean)/3;need(difference<10,'MP4 slide differs '+str(i+1));now+=seconds
        quality[i].update(size=[1080,1920],asset_type='illustration',source='illustration-sha256:'+sha,origin_reference=a['origin_reference'],rights_evidence=a['rights_evidence'],visual_semantic_qa=True,photo_semantic_qa=False,font_glyph_coverage_qa=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));v=[x for x in info['streams'] if x['codec_type']=='video'];au=[x for x in info['streams'] if x['codec_type']=='audio']
    need(len(v)==1 and v[0]['codec_name']=='h264' and v[0]['width']==1080 and v[0]['height']==1920 and len(au)==1 and au[0]['codec_name']=='aac','Wrong H264/AAC video')
    need(abs(float(info['format']['duration'])-now)<.15,'Video duration mismatch');subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True,capture_output=True)
    concat_with_padding([B/f'voice_{i}.wav' for i in range(7)],times,OUT/'cosyvoice3_narration.wav')
    shutil.copy2(video,OUT/'abasonplus_daily.mp4');shutil.copy2(OUT/'slide_0.png',OUT/'thumbnail.png');Image.open(OUT/'slide_0.png').save(OUT/'thumbnail_upload.jpg',quality=90,optimize=True)
    need((OUT/'thumbnail_upload.jpg').stat().st_size<2_000_000,'Cover too large')
    copy=r['copy'];need(len(copy['title'])<=100,'Title overflow')
    for field,n in [('caption',5),('instagram_caption',5),('description',6),('tiktok_caption',5)]:
        tags=re.findall(r'(?<!\S)#[^\s#]+',copy[field]);need(len(tags)==len(set(t.casefold() for t in tags))==n,'Wrong distinct hashtags '+field);need(len(copy[field])<=(5000 if field=='description' else 2200),'Copy overflow');(OUT/(field+'.txt')).write_text(copy[field],encoding='utf-8')
    need('#Shorts' in copy['description'],'Shorts missing');(OUT/'title.txt').write_text(copy['title']);(OUT/'first_comment.txt').write_text(copy['first_comment']);(OUT/'first_comment_json.txt').write_text(json.dumps(copy['first_comment'],ensure_ascii=False))
    meta={'date':DAY,'verified_on':DAY,'source_url':r['source_url'],'slides':7,'slide_seconds':3,'style_id':'compact_white_gold_v2','slide_durations':times,'voiceover':voice,'quality':quality,'release_policy':'owner_approved_exact_artifact_20261028','owner_exception_record':'audits/approved-media/2026-10-28.json','native_resolution_gate':'owner_waived_for_exact_hash_only','all_other_checks_passed':True}
    (OUT/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(OUT/'release_qa.json').write_text(json.dumps({'video_sha256':SHA,'status':'passed_with_explicit_exact_artifact_native_resolution_exception','semantic':semantic_rows,'real_device_review':False},indent=2));(OUT/'video_qa_passed.txt').write_text('exact_owner_exception_quality_checked='+DAY+'\n')
    tt={'date':DAY,'status':'preview_only','posting_enabled':False,'source_url':r['source_url'],'video_sha256':SHA,'caption':copy['tiktok_caption'],'caption_sha256':hashlib.sha256(copy['tiktok_caption'].strip().encode()).hexdigest(),'first_comment':copy['first_comment'],'format':{'slides':7,'slide_seconds':3,'slide_durations':times,'voiceover':voice},'settings':{'privacy_level':'PUBLIC_TO_EVERYONE','allow_comment':True,'allow_duet':True,'allow_stitch':True,'video_made_with_ai':True,'commercialContentType':'brand_organic'},'creator_info_reference':'Make checker execution 3585208520be460d98dee9f1a36a8337','owner_exact_caption_settings_approval':False}
    (OUT/'tiktok_preview.json').write_text(json.dumps(tt,ensure_ascii=False,indent=2))
    (OUT/'daily_research_story.json').write_text(json.dumps({'date':DAY,'verified_on':DAY,'expires_on':DAY,'source_url':r['source_url'],'source_kind':'external_news_report','hook':texts[0],'tips':[{'text':t} for t in texts[1:]],'illustrations':r['illustrations']},ensure_ascii=False,indent=2))
    print('EXACT IMMUTABLE APPROVED VIDEO: ALL APPLICABLE QA PASSED',SHA,flush=True)
    return r

def preflight():
    r=request();need((OUT/'video_qa_passed.txt').is_file(),'No independent QA marker')
    q=r['quota'];need(q['free'] is True and q['auto_purchase'] is False and q['remaining']>=150,'Free quota unsafe');need(datetime.now(BERLIN)-datetime.fromisoformat(q['observed_at'])<=timedelta(minutes=15),'Quota evidence stale')
    from recover_one_platform import validate_receipt
    for p in ('youtube','facebook','instagram'):
        e=read(ROOT/f'audits/approved-media/status-2026-10-28/{p}.json');ref=e['source_reference'];need(ref['scenario_id']==7968544 and ref['cycle']==1 and re.fullmatch('[a-f0-9]{32}',ref['execution_id']) and e['lookup_scope']=='latest_native_entry_in_descending_date_feed','Unverified status source');age=datetime.now(BERLIN)-datetime.fromisoformat(e['observed_at']);need(timedelta(0)<=age<=timedelta(minutes=5),'Duplicate evidence stale '+p);validate_receipt(e['receipt'],p,DAY)
    need(os.environ.get('GITHUB_RUN_ATTEMPT','1')=='1','No unattended rerun')
    print('FRESH NATIVE FEEDS AND DAILY RESERVATIONS CLEAR; NO POSTS YET')

def publish():
    preflight();current();r=request();need(digest(OUT/'abasonplus_daily.mp4')==SHA,'Changed MP4 after QA')
    from recover_one_platform import multipart
    c=r['copy'];fields={'kind':'video','target_platform':'all','review_approved':'true','visual_qa_passed':'true','visual_style_id':'compact_white_gold_v2','video_sha256':SHA,'tiktok_publish_approved':'false','title':c['title'],'caption':c['caption'],'description':c['description'],'instagram_caption':c['instagram_caption'],'first_comment':c['first_comment'],'first_comment_json':json.dumps(c['first_comment'],ensure_ascii=False)}
    body,boundary=multipart(fields,[('video',OUT/'abasonplus_daily.mp4','video/mp4'),('thumbnail',OUT/'thumbnail_upload.jpg','image/jpeg')]);need(len(body)<5_000_000,'Free transport exceeded')
    receipt={'date':DAY,'video_sha256':SHA,'status':'delivery_started_reconcile_before_any_retry','targets':['youtube','facebook','instagram'],'payload_bytes':len(body)};path=OUT/'approved_delivery_receipt.json';path.write_text(json.dumps(receipt,indent=2))
    try:
        req=Request(os.environ['MAKE_WEBHOOK_URL'],data=body,headers={'Content-Type':'multipart/form-data; boundary='+boundary},method='POST')
        with urlopen(req,timeout=120) as response:code=response.status;response.read(4096)
        need(200<=code<300,'Delivery response rejected')
    except Exception:raise ValueError('Delivery outcome unconfirmed; never resend') from None
    receipt['status']='request_accepted_publication_unverified';path.write_text(json.dumps(receipt,indent=2));print('Accepted transfer only; reconcile actual platform publication before claiming success.')

def website_preflight():
    r=request();need((OUT/'video_qa_passed.txt').is_file(),'No exact video QA')
    q=r['quota'];need(q['free'] is True and q['auto_purchase'] is False and q['remaining']>=150,'Free quota unsafe');need(datetime.now(BERLIN)-datetime.fromisoformat(q['observed_at'])<=timedelta(minutes=15),'Quota evidence stale')
    d=read(ROOT/'audits/approved-media/website-2026-10-28.json');e=d['reservation'];ref=e['source_reference']
    need(ref['scenario_id']==7968544 and ref['reservation_module']==66 and ref['cycle']==1 and re.fullmatch('[a-f0-9]{32}',ref['execution_id']),'Missing actual website reservation read')
    need(e['reserved'] is False and timedelta(0)<=datetime.now(BERLIN)-datetime.fromisoformat(e['observed_at'])<=timedelta(minutes=5),'WordPress reservation exists, unknown or stale')
    yt=d['youtube'];need(yt['status']=='published' and yt['identity_matched'] is True and yt['video_sha256']==SHA and yt['channel_id']=='UCKA_4RYtC2ktoclxzWCI1Lg','YouTube publication not independently verified')
    need(re.fullmatch(r'https://www.youtube.com/watch\?v=[A-Za-z0-9_-]{11}',yt['url']) is not None,'Wrong video link')
    from verify_wordpress_publication import lookup
    posts=lookup()
    for post in posts:
        stamp=datetime.fromisoformat(post['date'].replace('Z','+00:00'))
        if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=__import__('datetime').timezone.utc)
        need(stamp.astimezone(BERLIN).date().isoformat()!=DAY,'Current-day website post already exists; no resend')
    sys.path.insert(0,str(ROOT))
    from wordpress_email_prepare import prepare
    article=read(ROOT/'content/daily_editorial_2026-10-28.json');article['content']+='<p>ভিডিও: <a href="'+yt['url']+'">সম্পূর্ণ ভিডিও দেখুন</a></p>'
    payload=prepare(article);(OUT/'wordpress_email_preview.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    print('EXACT WEBSITE ARTICLE, YOUTUBE LINK AND DAILY RESERVATION VERIFIED; NO EMAIL SENT')

def website_publish():
    website_preflight();current();payload=read(OUT/'wordpress_email_preview.json');payload.update(review_approved='true',status='publish');path=OUT/'wordpress_send_receipt.json'
    receipt={'status':'delivery_started_reconcile_before_any_retry','post_key':payload['post_key'],'sent_utc':datetime.now(__import__('datetime').timezone.utc).isoformat()};path.write_text(json.dumps(receipt,indent=2))
    try:
        req=Request(os.environ['MAKE_WEBHOOK_URL'],data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=60) as response:code=response.status;response.read(4096)
        need(200<=code<300,'Website transfer rejected')
    except Exception:raise ValueError('Website delivery response unconfirmed; never resend') from None
    receipt['status']='make_accepted';path.write_text(json.dumps(receipt,indent=2));print('Website transfer accepted, checking real public post next.')
    subprocess.run([sys.executable,'scripts/verify_wordpress_publication.py','--attempts','5','--interval','10'],cwd=ROOT,check=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['verify','preflight','publish','preflight-website','publish-website']);ap.add_argument('--reuse-local-semantic',action='store_true');a=ap.parse_args()
    try:
        if a.mode=='verify':verify(not a.reuse_local_semantic)
        elif a.mode=='preflight':preflight()
        elif a.mode=='preflight-website':website_preflight()
        elif a.mode=='publish-website':website_publish()
        else:publish()
    except Exception as exc:
        print('APPROVED PUBLICATION HELD:',str(exc) if isinstance(exc,ValueError) else type(exc).__name__);raise SystemExit(1)
