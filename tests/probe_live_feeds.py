#!/usr/bin/env python3
"""Only check openly available RSS feeds. No publishing or model requests."""
import urllib.request,xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
feeds=[
("BSS RSS", "https://www.bssnews.net/rss"),
("BSS latest", "https://www.bssnews.net/rss/news"),
("Google metro", "https://news.google.com/rss/search?q=site%3Abssnews.net%20Bangladesh%20metro%20rail%20land&hl=en-BD&gl=BD&ceid=BD:en"),
("Google government projects","https://news.google.com/rss/search?q=Bangladesh%20government%20development%20project%20land%20housing%20economic%20zone&hl=en-BD&gl=BD&ceid=BD:en"),
("Google land Bangla","https://news.google.com/rss/search?q=%E0%A6%9C%E0%A6%AE%E0%A6%BF%20%E0%A6%AA%E0%A7%8D%E0%A6%B0%E0%A6%95%E0%A6%B2%E0%A7%8D%E0%A6%AA%20%E0%A6%86%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A6%A8&hl=bn&gl=BD&ceid=BD:bn"),
]
for label,url in feeds:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (AbasonPlus Education Feed Monitor)"})
  with urllib.request.urlopen(req,timeout=14) as resp:
   data=resp.read(120_000)
   print(label,"HTTP",resp.status,"TYPE",resp.headers.get("content-type"),flush=True)
  root=ET.fromstring(data)
  items=root.findall(".//item")
  for item in items[:3]:
   txt=lambda n:(item.findtext(n) or "")[:110].strip()
   print("  ",txt("title"),"|",txt("pubDate"),"|",txt("link")[:100],flush=True)
  print("  TOTAL",len(items),flush=True)
 except Exception as exc: print(label,"ERROR",type(exc).__name__,str(exc)[:140],flush=True)
