#!/usr/bin/env python3
"""Safe, READ-ONLY WordPress.com OAuth token check; prints no credentials.

Checks the existing GitHub Actions secret without creating/editing/publishing
any WordPress content. GitHub secret content is never logged.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

client_id=os.environ.get("WPCOM_CLIENT_ID","150614")
token_raw=os.environ.get("WORDPRESS_ACCESS_TOKEN","")
has_bearer_prefix=token_raw.strip().lower().startswith("bearer ")
contains_whitespace=any(ch.isspace() for ch in token_raw.strip())
token=token_raw.strip()
if has_bearer_prefix:
    token=token[7:].strip()
if token.startswith('"') and token.endswith('"'):
    token=token[1:-1]
print("WORDPRESS_SECRET_FORMAT="
      + ("BEARER_PREFIX " if has_bearer_prefix else "")
      + ("WHITESPACE " if contains_whitespace else "")
      + ("TOKEN_PRESENT" if token else "EMPTY"),
      flush=True)
expected_blog_id=os.environ.get("WPCOM_SITE_ID","257973809")
if not token:
    print("WORDPRESS_OAUTH_STATUS=MISSING_SECRET")
    sys.exit(2)

url="https://public-api.wordpress.com/oauth2/token-info?"+urllib.parse.urlencode(
    {"client_id":client_id,"token":token})
req=urllib.request.Request(url,headers={"User-Agent":"AbasonPlus-OAuth-ReadOnly-Diagnostics/1.0"})
try:
    with urllib.request.urlopen(req,timeout=20) as response:
        payload=json.load(response)
except urllib.error.HTTPError as e:
    # Print only safe status; not the URL (which contains a secret).
    try:
        body=json.loads(e.read().decode("utf-8","replace"))
        code=str(body.get("error","invalid_token"))[:50]
    except (ValueError,TypeError):
        code="API_REJECTION"
    print(f"WORDPRESS_OAUTH_STATUS=INVALID HTTP_{e.code} ERROR_{code}")
    sys.exit(3)
except Exception:
    print("WORDPRESS_OAUTH_STATUS=NETWORK_OR_RESPONSE_ERROR")
    sys.exit(4)
if "error" in payload:
    print("WORDPRESS_OAUTH_STATUS=INVALID API_ERROR")
    sys.exit(3)
actual_blog_id=str(payload.get("blog_id",""))
scope=str(payload.get("scope",""))
has_posts=("posts" in scope.split(",")) or ("global" in scope.split(","))
if actual_blog_id not in (expected_blog_id,"0","") and "global" not in scope:
    print("WORDPRESS_OAUTH_STATUS=WRONG_SITE")
    sys.exit(5)
if not has_posts:
    print("WORDPRESS_OAUTH_STATUS=MISSING_POSTS_SCOPE")
    sys.exit(6)
print("WORDPRESS_OAUTH_STATUS=VALID_WITH_POSTS_SCOPE (read-only verification)")
