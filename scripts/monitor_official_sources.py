#!/usr/bin/env python3
"""Daily source-check report for Bangladesh housing content. READ-ONLY.

Never writes/posts to WordPress, Facebook, YouTube, or Make.
HTTP availability and source-page headings are NOT proof that a project progressed.
An editor must review and date-stamp any newly added claims.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from pathlib import Path
import json, hashlib, re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output";OUT.mkdir(exist_ok=True)

SOURCES=[
("বিনিয়োগ/অর্থনৈতিক অঞ্চল", "Invest Bangladesh 180-day progress (Sep 2026)",
 "https://investbangladesh.gov.bd/press-release/invest-bangladesh-reports-progress-under-180-day-plan"),
("মেট্রোরেল", "DMTCL MRT Line-1 project progress",
 "https://dmtcl.gov.bd/pages/static-pages/6922e0a9933eb65569e28131"),
("মেট্রোরেল", "BSS MRT Line-1 tender/status Sep 2026",
 "https://www.bssnews.net/news/422295"),
("শিল্পাঞ্চল", "NSEZ official project information",
 "https://nsez.gov.bd/?page_id=639"),
("Land Share", "Bangladesh Real Estate Development Act 2010",
 "https://bdlaws.minlaw.gov.bd/act-1055/act-chapter-print-1694.html"),
("ভূমিকম্প/নকশা", "HBRI BNBC 2020 document index",
 "https://hbri.gov.bd/site/page/a5c13d7e-212d-4a16-bbf9-3e1ad937ba56/"),
("ভূমিকম্প/নকশা", "PWD seismic manuals",
 "https://ss.pwd.gov.bd/download"),
("ভূমি সেবা", "Ministry of Land mutation instructions",
 "https://mutation.land.gov.bd/nirdeshika"),
]
ALLOWED={
"investbangladesh.gov.bd","dmtcl.gov.bd","www.bssnews.net","nsez.gov.bd",
"bdlaws.minlaw.gov.bd","hbri.gov.bd","ss.pwd.gov.bd","mutation.land.gov.bd"
}

class Headings(HTMLParser):
    def __init__(self): super().__init__();self.title=[];self.headlines=[];self.current=None
    def handle_starttag(self,tag,attrs):
        if tag in ("title","h1","h2"):self.current=tag
    def handle_endtag(self,tag):
        if tag==self.current:self.current=None
    def handle_data(self,data):
        value=re.sub(r"\s+"," ",data).strip()
        if not value:return
        if self.current=="title":self.title.append(value)
        if self.current in ("h1","h2") and len(self.headlines)<8:self.headlines.append(value[:130])

def run():
    checked=datetime.now(timezone.utc).isoformat(timespec="seconds")
    findings=[]
    for topic,label,url in SOURCES:
        host=urlparse(url).hostname
        if host not in ALLOWED:raise RuntimeError("Unexpected source host")
        item={"category":topic,"label":label,"url":url,"checked_utc":checked}
        try:
            req=Request(url,headers={"User-Agent":"AbasonPlusSourceResearch/1.0","Accept":"text/html"})
            with urlopen(req,timeout=18) as response:
                data=response.read(800_000)
                item["http_status"]=response.status
                item["last_modified_header"]=response.headers.get("Last-Modified")
            parser=Headings()
            parser.feed(data.decode("utf-8","replace"))
            item["page_title"]=" ".join(parser.title)[:160]
            item["headings"]=parser.headlines[:5]
            item["content_sha256"]=hashlib.sha256(data).hexdigest()
            item["review_required"]=True
            print("CHECKED:",topic,label,"HTTP",item["http_status"],flush=True)
        except (HTTPError,URLError,TimeoutError,ValueError) as exc:
            item["error"]=type(exc).__name__
            item["review_required"]=True
            print("UNAVAILABLE:",topic,label,type(exc).__name__,flush=True)
        findings.append(item)
    report={"checked_utc":checked,"automatically_published":False,
            "note":"Source monitoring only, not verification of current project status or financial gain.",
            "sources":findings}
    (OUT/"official_source_monitor.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    md=["# AbasonPlus official sources: read-only daily monitoring",f"Checked UTC: {checked}",
        "This is a HEADLINE / ACCESSIBILITY monitor. It cannot independently verify a project stage, safety claim, land value, or official approval.",
        "Never republish unsupported automatic summaries. Revisit the original official announcement before writing.", ""]
    for x in findings:
        md.append(f"## {x['category']}: {x['label']}")
        md.append(f"Source: {x['url']}")
        md.append(f"HTTP: {x.get('http_status','UNAVAILABLE')}; Last-Modified: {x.get('last_modified_header','unknown')}")
        md.append(f"Page heading: {x.get('page_title','Unavailable')}")
        md.extend("- "+h for h in x.get("headings",[])[:4])
        md.append("")
    (OUT/"official_source_monitor.md").write_text("\n".join(md),encoding="utf-8")
    print(f"Sources checked: {len(findings)}. Publication requests sent: ZERO.",flush=True)

if __name__=="__main__":run()
