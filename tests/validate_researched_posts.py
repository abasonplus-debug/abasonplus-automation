#!/usr/bin/env python3
"""Offline source/expiry/uniqueness test; cannot publish anything."""
from datetime import date
from urllib.parse import urlparse
from pathlib import Path
import json, re

root=Path(__file__).resolve().parents[1]
research=json.loads((root/"content"/"researched_wordpress_posts.json").read_text(encoding="utf-8"))
older=json.loads((root/"wordpress_posts.json").read_text(encoding="utf-8"))
assert len(research)>=10, "Need a substantial source-backed pipeline"
assert len(older)>=15, "Original queued articles must remain available"
slugs=[x["slug"] for x in research+older]
assert len(slugs)==len(set(slugs)), "Duplicate WordPress slugs in queue"
allowed={
    "investbangladesh.gov.bd","www.bssnews.net","dmtcl.gov.bd",
    "nsez.gov.bd","bdlaws.minlaw.gov.bd","hbri.gov.bd",
    "ss.pwd.gov.bd","mutation.land.gov.bd","www.eprocure.gov.bd",
    "coastguard.gov.bd"
}
for p in research:
    assert p["editorial_review"]=="verified_primary_sources"
    assert 1200<=len(p["content"])<=13000, p["slug"]
    assert len(p["title"])>24 and "হ2>" not in p["content"]
    assert len(re.findall(r"<h2>",p["content"]))>=3
    assert "যাচাইযোগ্য উৎস" in p["content"]
    assert "নিশ্চিত লাভ নয়" in p["content"],p["slug"]
    checked=date.fromisoformat(p["verified_on"])
    assert checked<=date.today(),p["slug"]
    if p["time_sensitive"]:
        expires=date.fromisoformat(p["expires_on"])
        assert expires>checked,p["slug"]
        assert (expires-checked).days<=90,p["slug"]
    links=p["sources"]
    assert links and len(links)==len(set(links))
    for link in links:
        assert link.startswith("https://") and urlparse(link).hostname in allowed,link
        assert link in p["content"],p["slug"]
print(f"Validated {len(research)} sourced articles + {len(older)} older articles; unique slugs, citations and expiry metadata.")
