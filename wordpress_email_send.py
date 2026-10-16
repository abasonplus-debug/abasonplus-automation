#!/usr/bin/env python3
"""Delivery adapter for GitHub -> Make Gmail -> WordPress post-by-email.

Security: requires 3 independent gates; cannot run in current paused workflow.
No WordPress OAuth, SMTP password, email recipient, or Gmail token is stored here.
"""
import json,os,pathlib,sys
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=pathlib.Path(__file__).resolve().parent
path=ROOT/"output"/"wordpress_email_preview.json"
if not path.is_file():
    sys.exit("No prepared reviewed email. STOPPED.")
payload=json.loads(path.read_text(encoding="utf-8"))
if os.environ.get("ABASONPLUS_PUBLISH")!="OWNER_APPROVED":
    sys.exit("Publication disabled: owner approval required. STOPPED.")
if os.environ.get("ABASONPLUS_POST_BY_EMAIL_READY")!="CONFIRMED":
    sys.exit("Publication disabled: Gmail and private WordPress mail address not verified. STOPPED.")
webhook=os.environ.get("MAKE_WEBHOOK_URL","")
if not webhook.startswith("https://hook.eu1.make.com/"):
    sys.exit("Missing or unexpected Make webhook. STOPPED.")
if payload.get("kind")!="wordpress_email" or not payload.get("post_key"):
    sys.exit("Invalid WordPress message. STOPPED.")
payload["review_approved"]="true"
payload["status"]="publish"
data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
req=Request(webhook,data=data,method="POST",headers={"Content-Type":"application/json; charset=utf-8","User-Agent":"AbasonPlusGitHubEmailPosting/1.0"})
try:
    with urlopen(req,timeout=40) as response:
        if response.status>=300:
            sys.exit(f"Make delivery failed HTTP {response.status}")
except (HTTPError,URLError,TimeoutError) as error:
    sys.exit(f"Make delivery failed: {type(error).__name__}; manual review before retry.")
receipt={"status":"make_accepted","post_key":payload["post_key"],"sent_utc":datetime.now(timezone.utc).isoformat()}
(ROOT/"output"/"wordpress_send_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print("Make webhook accepted one email-publish request.")
print("This is NOT a WordPress publish confirmation; verify WordPress URL before marking published.")
