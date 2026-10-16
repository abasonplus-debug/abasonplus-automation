#!/usr/bin/env python3
"""Build a reviewed WordPress.com Post-by-Email payload. NEVER sends email/posts.
GitHub -> existing Make webhook -> Gmail OAuth -> WordPress secret Post-by-Email address.
"""
import argparse, html, json, pathlib, re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT=pathlib.Path(__file__).resolve().parent
SITE="257973809"
WEBSITE="https://abasonplus.wordpress.com/"

class TextContent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in ("h1","h2","h3","h4","p","div","li","br","ol","ul"): self.parts.append("\n")
        if tag=="li":self.parts.append("• ")
    def handle_endtag(self,tag):
        if tag in ("h1","h2","h3","h4","p","div","li","ol","ul"):self.parts.append("\n")
    def handle_data(self,data):self.parts.append(data)
    def text(self):
        x=html.unescape("".join(self.parts))
        x=re.sub(r"[ \t]+"," ",x)
        return re.sub(r"\n{3,}","\n\n",x).strip()

def slugs_already_published():
    found=set()
    for page in range(1,5):
        query=urlencode({"number":100,"page":page,"fields":"ID,slug,status"})
        address=f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE}/posts/?{query}"
        request=Request(address,headers={"User-Agent":"AbasonPlusReadOnly/1.0"})
        try:
            with urlopen(request,timeout=20) as response:
                result=json.load(response)
        except (HTTPError,URLError,TimeoutError,ValueError) as e:
            raise RuntimeError(f"Public posts lookup failed: {type(e).__name__}; delivery BLOCKED") from e
        posts=result.get("posts")
        if not isinstance(posts,list):raise RuntimeError("Unexpected posts lookup; delivery BLOCKED")
        found.update(p["slug"] for p in posts if p.get("slug"))
        if len(posts)<100:return found
    raise RuntimeError("More than 400 posts: review required; delivery BLOCKED")

def prepare(post):
    for name in ("slug","title","content"):
        if not isinstance(post.get(name),str) or not post[name].strip():
            raise RuntimeError(f"Missing required post field: {name}")
    slug=post["slug"].strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{3,100}",slug):
        raise RuntimeError("Invalid slug; delivery BLOCKED")
    title=re.sub(r"[\r\n]"," ",post["title"]).strip()
    document=TextContent()
    document.feed(post["content"])
    plain=document.text()
    if len(plain)<250:raise RuntimeError("Article is too short; delivery BLOCKED")
    tags=[re.sub(r"[\[\],\r\n]"," ",str(x)).strip() for x in post.get("tags",[])][:8]
    directives=f"[slug {slug}]\n[status publish]\n[publicize off]\n[tags {', '.join(tags)}]"
    email_body=directives+"\n\n"+plain+"\n\nআরও তথ্য: "+WEBSITE
    html_body="<p>"+html.escape(directives).replace("\n","</p><p>")+"</p>"
    # Keep original reviewed headings and lists for readable SEO-friendly articles.
    if re.search(r"<\\s*(?:script|iframe|form|object|embed)\\b",post["content"],re.I):
        raise RuntimeError("Unsafe article markup blocked")
    html_body+=post["content"]
    html_body+="<p>আরও তথ্য: <a href='"+WEBSITE+"'>AbasonPlus</a></p>"
    return {"kind":"wordpress_email","post_key":slug,"subject":title,
            "content":email_body,"html_content":html_body,
            "review_approved":"false","status":"preview_only"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--skip-public-lookup",action="store_true",help="Offline QA only")
    ap.add_argument("--output",default="output/wordpress_email_preview.json")
    args=ap.parse_args()
    # Research-backed timely articles take priority over the older generic queue.
    researched=json.loads((ROOT/"content"/"researched_wordpress_posts.json").read_text(encoding="utf-8"))
    evergreen=json.loads((ROOT/"wordpress_posts.json").read_text(encoding="utf-8"))
    if not isinstance(researched,list) or not isinstance(evergreen,list):
        raise RuntimeError("Article catalogs must be JSON arrays")
    generated_file=ROOT/"output"/"daily_research_post.json"
    generated=[]
    if generated_file.is_file():
        candidate=json.loads(generated_file.read_text(encoding="utf-8"))
        if candidate.get("editorial_review")!="automated_source_grounded_checks":
            raise RuntimeError("Generated article missing source-grounded QA status")
        if candidate.get("kind")!="fresh_independent_source":
            raise RuntimeError("AI article is not labeled as current source reporting")
        src=candidate.get("source_url","")
        if not src.startswith("https://www.tbsnews.net/") or src not in candidate.get("sources",[]):
            raise RuntimeError("Generated article lacks recognized primary publication source")
        if date.fromisoformat(candidate.get("verified_on"))!=datetime.now(ZoneInfo("Asia/Dhaka")).date():
            raise RuntimeError("Generated article is not freshly verified today")
        generated=[candidate]
    known=set() if args.skip_public_lookup else slugs_already_published()
    today=datetime.now(ZoneInfo("Asia/Dhaka")).date()
    items=[]
    queued=set()
    for post in generated+researched+evergreen:
        slug=post.get("slug","")
        if not slug or slug in known or slug in queued:
            continue
        queued.add(slug)
        if "verified_on" in post:
            verified=date.fromisoformat(post["verified_on"])
            if verified>today or (today-verified).days>180:
                print(f"SKIP outdated research: {slug} (last verified {verified})")
                continue
            if post.get("time_sensitive",False):
                if not post.get("expires_on"):
                    print(f"SKIP missing project expiry: {slug}")
                    continue
                if today>date.fromisoformat(post["expires_on"]):
                    print(f"SKIP expired project status: {slug}")
                    continue
            if post.get("editorial_review") not in ("verified_primary_sources","automated_source_grounded_checks"):
                print(f"SKIP unreviewed article: {slug}")
                continue
            if post.get("editorial_review")=="automated_source_grounded_checks":
                if verified!=today or not post["slug"].startswith("ap-"):
                    print(f"SKIP unverified current news item: {slug}")
                    continue
            sources=post.get("sources",[])
            if not sources or not all(u.startswith("https://") and u in post.get("content","") for u in sources):
                print(f"SKIP missing article source citations: {slug}")
                continue
        items.append(post)
    item=items[0] if items else None
    if item is None:
        print("No unpublished reviewed articles; NO email sent")
        return
    payload=prepare(item)
    output=ROOT/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PREVIEW ONLY: {payload['post_key']} -> {args.output}")
    print("No WordPress OAuth. No Make webhook. No email. No publication.")

if __name__=="__main__":
    main()
