#!/usr/bin/env python3
"""Check that WordPress REALLY published a scheduled Post-by-Email article.

Read-only; never sends content. Make webhook HTTP 200 only confirms delivery
acceptance, not publication. Delayed publication is reported as unverified.
"""
import argparse
from datetime import datetime,timezone,timedelta
import html,json,pathlib,re,sys,time
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
UA={"User-Agent":"AbasonPlus-Independent-WordPress-Post-Audit/1.0"}
SITE="257973809"

def canonical(value):
    text=html.unescape(str(value))
    text=re.sub(r"<[^>]+>","",text).replace("\u00a0"," ")
    return re.sub(r"\s+"," ",text).strip().casefold()

def lookup():
    args=urlencode({"number":100,"fields":"ID,slug,title,date,status,URL"})
    request=Request(f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE}/posts/?{args}",headers=UA)
    with urlopen(request,timeout=23) as reply:
        result=json.load(reply)
    if not isinstance(result.get("posts"),list):
        raise RuntimeError("Invalid WordPress public post index")
    return result["posts"]

def verify(expected, posts, sending_time):
    wanted_title=canonical(expected["subject"])
    wanted_slug=expected["post_key"]
    for p in posts:
        title=canonical(p.get("title",""))
        slug=str(p.get("slug",""))
        if title!=wanted_title and slug!=wanted_slug:
            continue
        # Avoid a previous-day post with the same headline being mistaken for today's.
        created=str(p.get("date",""))[:10]
        sending_day=sending_time.date()
        acceptable={(sending_day+timedelta(days=shift)).isoformat() for shift in (-1,0,1)}
        if created not in acceptable:
            continue
        if p.get("status") and p["status"]!="publish":
            continue
        return {"id":p.get("ID"),"slug":slug,"title":p.get("title"),
                "url":p.get("URL") or p.get("url"),
                "published_date":p.get("date"),"verified":True}
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--attempts",type=int,default=5)
    ap.add_argument("--interval",type=int,default=25)
    args=ap.parse_args()
    expected=json.loads((OUT/"wordpress_email_preview.json").read_text(encoding="utf-8"))
    receipt=json.loads((OUT/"wordpress_send_receipt.json").read_text(encoding="utf-8"))
    if receipt.get("status")!="make_accepted" or receipt.get("post_key")!=expected.get("post_key"):
        raise RuntimeError("Wrong or missing send receipt")
    sent=datetime.fromisoformat(receipt["sent_utc"].replace("Z","+00:00")).astimezone(timezone.utc)
    for attempt in range(args.attempts):
        try:
            match=verify(expected,lookup(),sent)
            if match:
                (OUT/"wordpress_published_verified.json").write_text(
                    json.dumps(match,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                print("WORDPRESS POST VERIFIED:",match["slug"],match["url"],flush=True)
                return
        except Exception as e:
            print(f"Public WP read check #{attempt+1}: {type(e).__name__}",flush=True)
        if attempt+1<args.attempts:
            time.sleep(args.interval)
    raise RuntimeError("PUBLICATION NOT VERIFIED: Make accepted the webhook but WordPress has not confirmed a published post. Manual review required; do NOT blindly resend (duplicate risk).")
if __name__=="__main__":
    main()
