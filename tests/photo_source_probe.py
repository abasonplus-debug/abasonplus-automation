#!/usr/bin/env python3
"""Read-only Wikimedia Commons query diagnosis; never publishes content."""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
tests=[
 "filetype:bitmap cadastral land records papers",
 "filetype:bitmap land survey",
 "filetype:bitmap farm",
 "filetype:bitmap house",
 "filetype:bitmap documents",
 "cadastral",
 "agricultural land",
 "landscape",
 "residential building",
 "surveying"
]
for term in tests:
    q={"action":"query","generator":"search","gsrsearch":term,
       "gsrnamespace":6,"gsrlimit":6,"prop":"imageinfo",
       "iiprop":"url|extmetadata","iiurlwidth":1800,"format":"json"}
    try:
        url="https://commons.wikimedia.org/w/api.php?"+urlencode(q)
        with urlopen(Request(url,headers={"User-Agent":"AbasonPlusEducationBot/2.0 (https://abasonplus.wordpress.com/)"}),timeout=15) as r:
            result=json.load(r)
        pages=list(result.get("query",{}).get("pages",{}).values())
        print(term,"->",len(pages),"candidate(s)",[(p.get("title","")[:35],(p.get("imageinfo") or [{}])[0].get("width")) for p in pages[:2]],flush=True)
    except Exception as e:
        print(term,"ERROR",str(e)[:140],flush=True)
