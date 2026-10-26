"""Shared publication date, source and safe article rules; no network or writes."""
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
from html.parser import HTMLParser
import re

TIMEZONE = "Europe/Berlin"

def publication_day(moment=None):
    return (moment or datetime.now(ZoneInfo(TIMEZONE))).astimezone(ZoneInfo(TIMEZONE)).date()

def trusted_source_url(value):
    try:
        p = urlparse(value)
        host = (p.hostname or "").lower()
        return (p.scheme == "https" and not p.username and not p.password
                and p.port in (None, 443)
                and (host.endswith(".gov.bd") or host in ("www.bssnews.net", "www.tbsnews.net")))
    except (TypeError, ValueError):
        return False

class SafeArticle(HTMLParser):
    tags = {"p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "strong", "em", "b", "i", "br", "blockquote"}
    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            raise ValueError("Unsupported article HTML tag: " + tag)
        for name, value in attrs:
            if tag != "a" or name not in {"href", "title", "rel", "target"}:
                raise ValueError("Unsupported article HTML attribute: " + name)
            if name == "href":
                p = urlparse(value or "")
                if p.scheme != "https" or not p.hostname or p.username or p.password:
                    raise ValueError("Article link must be a public HTTPS URL")
    def handle_endtag(self, tag):
        if tag not in self.tags:
            raise ValueError("Unsupported article HTML closing tag: " + tag)

def validate_article_html(body):
    if re.search(r"\[\s*(?:status|slug|title|delay|password|publicize|category|tags|end)\b", body, re.I):
        raise ValueError("Post-by-Email control directive in article content")
    parser = SafeArticle(convert_charrefs=True)
    parser.feed(body)
    parser.close()

def validate_social_copy(caption, description, title):
    if not 1 <= len(caption) <= 2200:
        raise ValueError("Instagram caption must fit 2200 characters including attribution")
    if caption.count("#") < 5:
        raise ValueError("At least five caption hashtags required")
    if not 1 <= len(description) <= 5000:
        raise ValueError("YouTube description must fit 5000 characters")
    if not 1 <= len(title) <= 100:
        raise ValueError("YouTube title must fit 100 characters")


def require_editorial_ready(entry, *, video=False):
    """Honor explicit editorial holds; never relabel a draft as approved."""
    if entry.get('publication_ready') is False or entry.get('status') in ('draft', 'held', 'pending'):
        raise ValueError('EDITORIAL_HELD: draft or explicitly not ready for publication')
    if video and entry.get('video_ready') is False:
        raise ValueError('VIDEO_HELD: illustration assets/QA or narration incomplete')
