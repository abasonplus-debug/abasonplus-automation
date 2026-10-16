#!/usr/bin/env python3
"""Publish one reviewed Bengali AbasonPlus post via WordPress.com OAuth API.

Required secrets: WPCOM_ACCESS_TOKEN and WPCOM_SITE_ID (site id defaults to AbasonPlus).
Posts are read from wordpress_posts.json. No paid AI API is called.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SITE_ID=os.environ.get("WPCOM_SITE_ID","257973809")
TOKEN=os.environ.get("WPCOM_ACCESS_TOKEN","")
POSTS=Path(__file__).with_name("wordpress_posts.json")
API=f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts/new"

def main():
    if not TOKEN:
        sys.exit("WPCOM_ACCESS_TOKEN missing: no publication attempted")
    items=json.loads(POSTS.read_text(encoding="utf-8"))
    if not isinstance(items,list) or not items:
        sys.exit("No reviewed posts available: no publication attempted")
    today=datetime.now(timezone.utc).date()
    # Day-based selection; a remote slug lookup prevents accidental repeats.
    for post in items:
        if not all(post.get(k) for k in ("title","content","slug")):
            continue
        slug=post["slug"]
        check=f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts/slug:{slug}"
        req=urllib.request.Request(check,headers={"Authorization":f"Bearer {TOKEN}"})
        try:
            with urllib.request.urlopen(req,timeout=25) as response:
                existing=json.load(response)
            if existing.get("ID"):
                continue
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                sys.exit(f"WordPress lookup failed: HTTP {exc.code}; stopped safely")
        payload={"title":post["title"],"content":post["content"],"slug":slug,
                 "status":"publish","tags":",".join(post.get("tags",[]))}
        req=urllib.request.Request(API,data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
              headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"},
              method="POST")
        try:
            with urllib.request.urlopen(req,timeout=40) as response:
                created=json.load(response)
        except urllib.error.HTTPError as exc:
            sys.exit(f"Publish failed: HTTP {exc.code}; check OAuth permission and site settings")
        if not created.get("ID") or created.get("status")!="publish":
            sys.exit("Publish response did not confirm published status")
        print("Published:",created.get("URL","(URL missing)"))
        return
    sys.exit("No unpublished reviewed posts left; add more to wordpress_posts.json")

if __name__=="__main__":
    main()
