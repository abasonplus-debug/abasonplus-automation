"""Owner-dispatched, current-day, exact-artifact recovery. No TikTok or guard bypass.

Read reservation and fixed-account feed before ONE targeted delivery. Never retry
an upload, clear a key, or replay a whole router. Keep webhook out of diagnostics.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from schedule_guard import GitHub, stamp

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
IDENTITIES={'youtube':'UCKA_4RYtC2ktoclxzWCI1Lg','facebook':'293664680487578','instagram':'6ad380c8b835331ad1563a7a'}
DELIVERY='Send ONE daily validated Reel and Short to Make on automatic schedule ONLY'

def require(ok, reason):
    if not ok: raise ValueError(reason)

def decoded(value):
    if isinstance(value,str):
        try:return json.loads(value)
        except ValueError:raise ValueError('Status receipt was not JSON') from None
    return value

def validate_receipt(receipt, platform, day):
    require(receipt.get('schema')==1 and receipt.get('platform')==platform and receipt.get('date')==day,
            'Wrong status schema/platform/Berlin date')
    require(receipt.get('identity')==IDENTITIES[platform], 'Wrong fixed account')
    require(receipt.get('reserved') is False, 'Reserved or unknown publication; never resend')
    data=decoded(receipt.get('data'))
    if platform=='youtube':
        require(isinstance(data,dict) and 'items' in data, 'YouTube feed incomplete')
        rows=data['items']
        require(not data.get('nextPageToken') or len(rows)==25,'Unexpected YouTube feed pagination')
        times=[r.get('snippet',{}).get('publishedAt') for r in rows]
        require(all(r.get('snippet',{}).get('channelId')==IDENTITIES[platform] for r in rows),'Wrong YouTube channel')
    elif platform=='facebook':
        require(isinstance(data,list),'Facebook feed incomplete')
        rows=data
        times=[r.get('created_time') for r in rows]
    else:
        require(isinstance(data,dict),'Instagram feed incomplete')
        body=decoded(data.get('body',data))
        require(isinstance(body,dict),'Instagram feed body incomplete')
        require(body.get('status') not in ('error','failed'),'Instagram feed error')
        if isinstance(body.get('data'),dict):body=body['data']
        rows=body.get('posts',body.get('data'))
        require(isinstance(rows,list),'Instagram native posts unavailable')
        times=[r.get('timestamp') or r.get('created_time') or r.get('publishedAt') or r.get('createdAt') for r in rows]
    require(isinstance(rows,list) and bool(rows),'Empty native feed cannot prove lookup complete')
    require(all(isinstance(t,str) for t in times),'Native publication timestamp unavailable')
    localdates=[stamp(t).astimezone(ZoneInfo('Europe/Berlin')).date().isoformat() for t in times]
    require(all(d<day for d in localdates),'Current-day or future own post exists; hold for reconciliation')
    return {'reserved':False,'recent_rows_checked':len(rows),'latest_observed_day':max(localdates)}

def multipart(fields, files):
    boundary='AbasonPlus'+uuid.uuid4().hex
    body=bytearray()
    for name,value in fields.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for name,path,mime in files:
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
        body.extend(path.read_bytes());body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode())
    require(len(body)<=5_000_000,'Complete multipart payload exceeds free limit; no truncation or upload')
    return bytes(body),boundary

def main():
    day=os.environ['RECOVERY_DAY'];platform=os.environ['RECOVERY_PLATFORM']
    run_id=int(os.environ['PREVIEW_RUN_ID']);expected=os.environ['VIDEO_SHA256']
    require(platform in IDENTITIES,'Only one of Facebook/YouTube/Instagram; no TikTok')
    require(os.environ.get('GITHUB_ACTOR')=='abasonplus-debug','Repository owner dispatch required')
    require(os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch' and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','No scheduled/replayed recovery')
    require(os.environ.get('RECOVERY_CONFIRMATION')=='RECOVER_ONE_PLATFORM','Explicit recovery intent missing')
    now=datetime.now(ZoneInfo('Europe/Berlin'))
    require(day==now.date().isoformat(),'Stale recovery date')
    require(re.fullmatch('[a-f0-9]{64}',expected) is not None,'Exact MP4 hash required')
    request=json.loads((ROOT/'audits/recovery-requests'/f'{day}.json').read_text())
    require(request.get('owner_authorized') is True and request.get('preview_run_id')==run_id and request.get('video_sha256')==expected,'Exact owner recovery record mismatch')
    q=request.get('quota',{})
    require(q.get('free') is True and q.get('auto_purchase') is False and q.get('remaining',0)>=150,'Fresh free quota evidence missing')
    age=now-stamp(q['observed_at'])
    require(timedelta(0)<=age<=timedelta(minutes=15),'Quota evidence older than 15 minutes; inspect before transfer')
    api=GitHub()
    source=api.request('/actions/runs/'+str(run_id))
    require(source.get('conclusion')=='success' and source.get('head_branch')=='main' and source.get('name')=='AbasonPlus Daily Source-Checked Carousel & Video','Only actual successful main preview artifact')
    require(stamp(source['created_at']).astimezone(ZoneInfo('Europe/Berlin')).date().isoformat()==day,'Preview is stale')
    editorial=ROOT/'content'/f'daily_editorial_{day}.json'
    require(hashlib.sha256(editorial.read_bytes()).hexdigest()==request.get('editorial_sha256'),'Current editorial hash changed since recovery authorization')
    article=json.loads(editorial.read_text())
    brief=json.loads((OUT/'daily_research_story.json').read_text())
    require(article.get('date')==day and article.get('verified_on')==day and article.get('source_url')==brief.get('source_url')
            and article.get('story',{}).get('hook')==brief.get('hook')
            and article.get('story',{}).get('tips')==brief.get('tips'),'Artifact does not match current exact editorial script')
    runs=api.runs('daily-carousel.yml',now.date())
    require(any(int(r['id'])==request.get('failed_run_id') and r.get('conclusion')=='failure' for r in runs),'Original failed run evidence missing')
    require(all(r.get('status')=='completed' for r in runs),'Scheduled run still active; no concurrent recovery')
    for run in runs:
        for job in api.jobs(run['id']):
            for step in job.get('steps',[]):
                if step.get('name')==DELIVERY:
                    require(step.get('status')=='completed' and step.get('conclusion')=='skipped','Prior scheduled delivery may have started; hold')
    video=OUT/'abasonplus_daily.mp4'
    require(hashlib.sha256(video.read_bytes()).hexdigest()==expected,'MP4 hash changed')
    # Reapply independent source/date/layout/license/audio/timing QA to the artifact.
    subprocess.run(['python3','scripts/verify_video_release.py'],cwd=ROOT,check=True,timeout=120)
    url=os.environ['MAKE_WEBHOOK_URL']
    payload={'kind':'publication_status_provider' if platform=='instagram' else 'publication_status_'+platform,
             'audit_date':day,'audit_platform':platform}
    try:
        req=Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=90) as response: receipt=json.load(response)
    except Exception: raise ValueError('Read-only status unavailable; no publication sent') from None
    evidence=validate_receipt(receipt,platform,day)
    report={'date':day,'platform':platform,'preview_run_id':run_id,'video_sha256':expected,'status':'checked_no_delivery',**evidence}
    out=OUT/'recovery_result.json';out.write_text(json.dumps(report,indent=2)+'\n')
    if os.environ.get('DRY_RUN','true')!='false':
        print('Recovery checks passed; NO POSTS');return
    require(datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()==day,'Midnight crossed before transfer')
    fields={'kind':'video','target_platform':platform,'review_approved':'true','visual_qa_passed':'true',
            'visual_style_id':'compact_white_gold_v2','video_sha256':expected,'tiktok_publish_approved':'false'}
    for key,name in [('title','title.txt'),('caption','caption.txt'),('description','description.txt'),('first_comment','first_comment.txt'),('first_comment_json','first_comment_json.txt')]:
        fields[key]=(OUT/name).read_text()
    body,boundary=multipart(fields,[('video',video,'video/mp4'),('thumbnail',OUT/'thumbnail_upload.jpg','image/jpeg')])
    report['status']='delivery_started_reconcile_before_any_retry';out.write_text(json.dumps(report,indent=2)+'\n')
    try:
        req=Request(url,data=body,headers={'Content-Type':'multipart/form-data; boundary='+boundary},method='POST')
        with urlopen(req,timeout=120) as response: status=response.status;response.read(4096)
        require(200<=status<300,'Delivery rejected; reservation needs reconciliation')
    except Exception:raise ValueError('Delivery response unconfirmed; never retry automatically') from None
    report['status']='request_accepted_publication_unverified';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Never emit network exception strings containing the private webhook.
        print('RECOVERY HELD:',str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        raise SystemExit(1)
