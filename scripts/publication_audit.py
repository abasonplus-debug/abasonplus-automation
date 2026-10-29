"""Conservative five-platform audit/recovery decisions. No network, uploads or credentials."""
import argparse,json
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
PLATFORMS=('website','facebook','youtube','instagram','tiktok')
HOSTS={'website':{'abasonplus.wordpress.com'},'facebook':{'facebook.com','www.facebook.com','fb.watch'},'youtube':{'youtube.com','www.youtube.com','youtu.be'},'instagram':{'instagram.com','www.instagram.com'},'tiktok':{'tiktok.com','www.tiktok.com'}}

def localday(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Evidence timestamps must include timezone')
    return dt.astimezone(ZoneInfo('Europe/Berlin')).date().isoformat()

def safe_url(platform,url):
    try:
        p=urlparse(url)
        return p.scheme=='https' and p.hostname in HOSTS[platform] and not p.username and not p.password and p.port in (None,443)
    except (ValueError,TypeError):return False

def retry_decision(evidence):
    # Only a failed pre-delivery GitHub job may be retried automatically once.
    # Never replay the full Make router or remove daily reservations.
    if evidence.get('duplicate_found') or evidence.get('published'):return 'do_not_retry'
    if evidence.get('provider_accepted') or evidence.get('delivery_attempted') is not False:return 'inspect_only'
    if evidence.get('failure_phase')!='before_delivery' or evidence.get('transient_failure') is not True:return 'inspect_only'
    if evidence.get('github_job_status')!='failure' or evidence.get('prior_retries',0)!=0:return 'inspect_only'
    if not evidence.get('current_day_verified') or not evidence.get('quota_safe'):return 'inspect_only'
    return 'retry_failed_pre_delivery_job_once'

def classify(platform,day,now,rows,context):
    valid=[];out_of_date=0
    for row in rows:
        if row.get('platform')!=platform:continue
        stamp=row.get('published_at') or row.get('observed_at')
        try:date=localday(stamp)
        except (ValueError,TypeError,AttributeError):continue
        if date!=day:out_of_date+=1;continue
        valid.append(row)
    published={}
    for row in valid:
        # A Make job status, delivery HTTP 200, draft or processing is not publication.
        if (row.get('status')=='published' and row.get('verification')=='platform_readback'
            and row.get('post_id') and row.get('published_at') and row.get('identity_matched') is True
            and safe_url(platform,row.get('url',''))):published[str(row['post_id'])]=row
    if len(published)>1:return {'status':'duplicate','posts':list(published.values()),'action':'inspect_only'}
    if published:return {'status':'published_verified','posts':list(published.values()),'action':'do_not_retry'}
    if platform=='tiktok' and not context.get('exact_tiktok_video_approved'):
        return {'status':'awaiting_video_review','posts':[],'action':'do_not_upload_without_exact_review'}
    scheduled=now.replace(hour=0,minute=30,second=0,microsecond=0)
    if now<scheduled:return {'status':'not_due','posts':[],'action':'wait_for_schedule'}
    if context.get('fresh_content_ready') is False:return {'status':'held_missing_fresh_content','posts':[],'action':'research_required'}
    if any(r.get('status') in ('publishing','processing','scheduled') for r in valid):
        return {'status':'processing','posts':[],'action':'read_status_later_no_resend'}
    if now<scheduled+timedelta(hours=2) and not valid:return {'status':'waiting_schedule_or_render','posts':[],'action':'read_status_later_no_resend'}
    if context.get('lookup_complete',{}).get(platform) is not True:
        return {'status':'unverified','posts':[],'action':'complete_platform_lookup'}
    return {'status':'failed_or_missing','posts':[],'action':'inspect_before_retry'}

def quota_report(quota):
    remaining=quota.get('remaining');used=quota.get('used');days=quota.get('days_until_reset')
    if not all(type(x) is int and x>=0 for x in (remaining,used,days)) or days<1:
        return {'status':'unverified','auto_purchase_allowed':False}
    measured=quota.get('measured_daily_credits')
    cost=measured if isinstance(measured,(int,float)) and measured>=0 else None
    needed=round(cost*days,2) if cost is not None else None
    reserve=20  # Owner stop floor, 30 October 2026
    return {'remaining':remaining,'used':used,'days_until_reset':days,'reserve':reserve,
            'projected_need':needed,'status':'insufficient' if needed is not None and remaining<needed+reserve else 'unverified_forecast' if needed is None else 'within_measured_budget',
            'auto_purchase_allowed':False}

def build(snapshot):
    now=datetime.fromisoformat(snapshot['checked_at'].replace('Z','+00:00'))
    if now.tzinfo is None:raise ValueError('Audit timestamp must include timezone')
    now=now.astimezone(ZoneInfo('Europe/Berlin'));day=now.date().isoformat()
    results={p:classify(p,day,now,snapshot.get('evidence',[]),snapshot.get('context',{})) for p in PLATFORMS}
    return {'date':day,'checked_at':now.isoformat(),'platforms':results,'quota':quota_report(snapshot.get('quota',{})),
            'recovery':retry_decision(snapshot.get('recovery',{})),
            'quality':snapshot.get('quality',{'status':'unverified'}),
            'weekly_metrics':snapshot.get('weekly_metrics',{'status':'unavailable','note':'Unavailable metrics are not zero and do not establish performance.'}),
            'no_publication_performed':True}

def markdown(report):
    ls=['# AbasonPlus publication audit — '+report['date'],'','| Platform | Verified state | Action |','|---|---|---|']
    for p,item in report['platforms'].items():ls.append(f"| {p} | {item['status']} | {item['action']} |")
    ls+=['','## Verified post links']
    for p,item in report['platforms'].items():
        for row in item['posts']:ls.append(f"- {p}: {row['url']}")
    ls+=['','## Free quota',json.dumps(report['quota'],ensure_ascii=False),'','## Recovery',report['recovery'],'','## Quality and mobile preview',json.dumps(report['quality'],ensure_ascii=False),'','## Weekly metrics and availability',json.dumps(report['weekly_metrics'],ensure_ascii=False),'','This report never publishes, deletes daily reservations or replays a Make publication.']
    return '\n'.join(ls)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('snapshot');ap.add_argument('--output',default='output/publication-audit');args=ap.parse_args()
    snapshot=json.loads(Path(args.snapshot).read_text())
    root=Path(__file__).resolve().parents[1]
    day=localday(snapshot['checked_at'])
    approval=root/'audits/tiktok-approvals'/f'{day}.json'
    publication=root/'audits/tiktok-publications'/f'{day}.json'
    if approval.is_file() and publication.is_file():
        from tiktok_approval import reconcile
        try:
            snapshot=reconcile(snapshot,json.loads(approval.read_text()),json.loads(publication.read_text()))
        except (ValueError,KeyError,TypeError):
            snapshot.setdefault('quality',{}).setdefault('findings',[]).append('Exact-video consent records could not be reconciled; inspect, never infer approval.')
    report=build(snapshot);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/'report.md').write_text(markdown(report));print(markdown(report))
if __name__=='__main__':main()
