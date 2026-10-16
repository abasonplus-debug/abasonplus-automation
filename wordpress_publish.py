#!/usr/bin/env python3
"""Publish one reviewed Bengali AbasonPlus post via WordPress.com OAuth API.

Required secret: WORDPRESS_ACCESS_TOKEN (site id defaults to AbasonPlus).
Posts are read from wordpress_posts.json. No paid AI API is called.
"""
import json, os, sys, urllib.request, urllib.error, urllib.parse
from pathlib import Path

SITE_ID=os.environ.get("WPCOM_SITE_ID","257973809")
TOKEN=os.environ.get("WORDPRESS_ACCESS_TOKEN","")
POSTS=Path(__file__).with_name("wordpress_posts.json")
API=f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts/new"

def main():
    if not TOKEN:
        sys.exit("WORDPRESS_ACCESS_TOKEN missing: no publication attempted")
    items=json.loads(POSTS.read_text(encoding="utf-8"))
    if not isinstance(items,list) or not items:
        sys.exit("No reviewed posts available: no publication attempted")
    # List existing slugs before publishing; stop safely if lookup fails.
    existing_slugs=set()
    for page in range(1, 101):
        query=urllib.parse.urlencode({"number":100,"page":page,"fields":"ID,slug,status"})
        url=f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts/?{query}"
        req=urllib.request.Request(url,headers={"Authorization":f"Bearer {TOKEN}"})
        try:
            with urllib.request.urlopen(req,timeout=25) as response:
                result=json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                details=json.loads(exc.read().decode("utf-8",errors="replace"))
                reason=str(details.get("error",""))+": "+str(details.get("message",""))
            except (ValueError, AttributeError):
                reason="unavailable"
            sys.exit(f"WordPress posts-list lookup failed: HTTP {exc.code}; API reason: {reason[:350]}; stopped safely")
        posts=result.get("posts",[])
        if not isinstance(posts,list):
            sys.exit("Unexpected WordPress posts-list response; stopped safely")
        existing_slugs.update(p.get("slug") for p in posts if p.get("slug"))
        if len(posts)<100:
            break
    else:
        sys.exit("Too many posts to check safely; stopped")
    for post in items:
        if not all(post.get(k) for k in ("title","content","slug")):
            continue
        slug=post["slug"]
        if slug in existing_slugs:
            continue
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
