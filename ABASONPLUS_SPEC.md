# AbasonPlus — Approved Production Specification (2026-10-16)

## CURRENT STATUS (updated 16 October 2026)
**WordPress Post-by-Email scheduled publishing is ACTIVE; Facebook/YouTube VIDEO publishing is PAUSED.**
GitHub WordPress scheduler: once daily 06:20 UTC, next reviewed unpublished article via Make Gmail; manual preview runs do NOT send email. Make.com scenario 7968544 ACTIVE with only its WordPress delivery branch able to publish; video Facebook/YouTube modules DISABLED.
There are **11 newly researched official-source Bengali articles** prioritized ahead of **15 older queued articles**; both are finite queues.
Read-only official-source monitoring at 05:35 UTC collects reports for editorial review, NOT automatically written breaking-news articles.
Full real-world publication verification is still required after next scheduled WordPress run.
See `ABASONPLUS_EDITORIAL_POLICY.md` for detailed sourcing/freshness standards.

## Image / Slideshow Requirements
- Individual slides: **1080×1920 pixels**, **9:16 Vertical**, 5–10 independent images.
- **No border, frame, margin, padding, letterbox, mosaic or collage.**
- Source photography must be **realistic, high-resolution, original or properly licensed**, visually relevant to the exact text. No scanned maps, archival certificates or unrelated photos masquerading as ultra-realistic subject photos. The approved Sample #2 should be checked when actually available; do not guess its identity.
- Professional photographic final touch: realistic brightness/contrast/white balance, sharp detail, natural skin and textures. Do not oversaturate or invent photo provenance.
- Bengali copy directly on images; **font >=130px, Regular/Medium, NOT Bold**; translucent/transparent with discreet shadow/outlines.
- Typography composition spans **at least 60% of frame height** per automated QA; visible quality and the user's requested 60% *area* must still be reviewed visually. Do not claim these are equivalent.
- First slide = compelling accurate **Hook Thumbnail**, not fake fear/clickbait.
- Branding: AbasonPlus; consistent style, informative captions and hashtags.

## ChatGPT Preview Format
Show one BIG real 9:16 slide, below it clickable SMALL thumbnail strip showing the same actual finished images, with slide counter. Never show a static composite simulating a carousel. Human reviews slide photos before approving video and any future publishing.

## Audio / Video
Use only original `assets/abasonplus.mp3`; no fallback. MP4 H.264/AAC, 1080×1920, 30fps, 3sec per slide with music fade-out. Each image is its own frame; no reuse of one image as multiple slides.

## Publishing and deduplication
Existing authorized destinations: AbasonPlus Facebook Page Reels, YouTube Shorts, and WordPress. Instagram/TikTok are not connected destinations.
- Video/social publishing steps remain OFF until authorization.
- When authorized to resume, use **only the single Make.com scenario**; WordPress remains a separate flow.
- Make Data Store `AbasonPlus Published Video Keys` (id 220796): unique local-day key, overwrite=false, BEFORE router; sequential execution to reduce duplicate risk. This is an at-most-once *attempt*, not guaranteed exactly-once delivery to both platforms. Review partial failures manually.
- YouTube Description = incoming `description`; Facebook caption = incoming `caption`.
- GitHub preview files: independent `slide_*.png`, `thumbnail.png`, `metadata.json`, titles/captions/descriptions, MP4, source credits.
- Preserve source attribution and license obligations. WordPress OAuth `invalid_token` remains an external account blocker until owner reauthorizes; never invent or leak credentials.

## Current QA Gate
A GitHub safe validation workflow compiles scripts, validates 18 curated topics/90 typography layouts, checks paused publishing, produces an MP4 without outbound posting and probes metadata/FFmpeg streams.
**Technical render success is NOT visual approval.** Wikimedia fallback search has chosen irrelevant items (historic maps/certificates and cityscape). The photography selection is still not production-quality. Do not reactivate publishing until the photo assets/selection are human-reviewed or a reliable photo QA pipeline is proven.

## Scheduling note (historical video / current WordPress)
Previous VIDEO generation schedule (suspended): 03:15 UTC daily, 05:15 summer / 04:15 winter Germany. WordPress ACTIVE: 06:20 UTC, 08:20 summer / 07:20 winter. GitHub Actions may start late; generation time != publication time.

**Never call this complete, nor publish, merely because a test workflow is green.**

## 2026-10-16 Photo / OAuth remediation findings
- Photo screening now includes an offline CLIP semantic relevance model. Wikimedia/Openverse broad keyword searching alone produced unrelated historical/scanned materials; automated ranking alone cannot guarantee visual fidelity.
- The `জমির নথি` topic has FIVE curated photo source URLs with photographer provenance and Pexels license recorded in `content/researched_photos.json`. The safe CI `38858152894` rendered five topic-related 1080×1920 slides and MP4 successfully. These images are **PREVIEW ONLY**; user has not approved publication.
- Other topics still need reliable vetted photographic assets; reject or hold when there is no photographic match, rather than publishing unrelated stock photos.
- WordPress site 257973809 is accessible using the connected WordPress.com app (read-only test), but separate GitHub Actions secret `WORDPRESS_ACCESS_TOKEN` failed the official token-info endpoint with HTTP 400 `invalid_request` and also failed independent WordPress REST bearer identity verification with HTTP 400. The secret exists but is not usable. This requires an owner-authorized replacement; **GitHub connector cannot create/edit Actions secrets**. Do not write or publish to WordPress until the new credential passes read-only verification.
- Previously shared OAuth app credentials appeared in chat screenshots: rotate exposed secrets/access tokens through the official provider UI; never paste tokens in chat, public repository, commits or workflow logs.

## Token-free WordPress.com publishing design — HISTORICAL setup notes; current status above supersedes older activation statements
Official WordPress.com Free-site alternative: Post by Email (Settings → Writing → Post by Email). A unique private destination email address acts as a publishing credential. Never commit it to the public repository, paste it in chat, or expose it in logs.

GitHub `wordpress_email_prepare.py` converts reviewed articles into formatted emails and checks public published slugs first (fail closed on error).
GitHub `wordpress_email_send.py` uses existing secret `MAKE_WEBHOOK_URL` and requires explicit owner permission plus confirmed Gmail/Post-by-Email readiness. GitHub `.github/workflows/wordpress-post.yml` schedules DAILY 06:20 UTC preview-only work; outbound delivery is hard-disabled. The separate `wordpress-email-preview.yml` verifies the publisher stays blocked.
Make.com scenario `7968544` is INACTIVE, with the original `kind=video` route and a new `kind=wordpress_email` route guarded by review approval. The WordPress route records key `abasonplus-wp-{{1.post_key}}` in Data Store `220796` to prevent duplicate attempts.
The Gmail sender module is not yet attached: user must authorize Make `google-email:sendAnEmail` (request currently pending), enable Post by Email on WordPress.com, and enter its special email address privately in Make. Until then, publishing cannot work; do not claim completion or activate.

## Gmail authorization completed — HISTORICAL setup notes; production recipient is now configured privately
Make Gmail connection `11995107` is authorized and OK (gmail.readonly + gmail.send). The WordPress branch in inactive scenario `7968544` now has:
- approved request filter and duplicate slug guard (module 7)
- Gmail `sendAnEmail` (module 8), subject from `{{1.subject}}`, HTML body from `{{1.html_content}}`
- SAFE STAGING destination `abasonplus@gmail.com` (owner's own inbox). NOT the WordPress publishing address.
Final activation blocked: owner must enable WordPress.com Post by Email under site Settings → Writing and put the newly generated confidential `@post.wordpress.com` destination **directly in module 8's To field** in Make. Never send this secret to chat or GitHub. Gmail module and Make scenario currently have not been run. Keep scenario inactive and GitHub sender `if: false` until explicit publishing authorization.

## Production status update — 2026-10-16
**WordPress Post-by-Email automation: ENABLED at the owner's explicit request.** Daily GitHub workflow `.github/workflows/wordpress-post.yml` runs at 06:20 UTC; the sending step is enabled ONLY for GitHub `schedule` runs, while manual dispatch remains PREVIEW-ONLY. GitHub uses the existing private Make webhook secret; it does not use or expose the invalid WordPress OAuth token.

Make.com scenario `7968544` is ACTIVE. WordPress JSON webhook fields were learned with a harmless unapproved schema sample; no message was sent from the learning run. WordPress route requires `kind=wordpress_email` and `review_approved=true`, checks unique slug key in Data Store `220796`, and sends via authorized Gmail module 8 to the configured private WordPress Post-by-Email recipient. Do not write the private email address into GitHub or chat.

**Facebook and YouTube video posting remains DISABLED** in Make.com modules 3 and 4 and in the GitHub video workflow, until visual image quality is approved. There are 15 curated WordPress articles queued, not an unlimited content generator. Real-world email-to-post delivery remains to be verified after the first scheduled publication; Make webhook acceptance alone is not proof of publication.

**Security:** the Post-by-Email address appeared in an earlier screenshot. Rotate it through WordPress Settings -> Writing and update the private Make Gmail recipient before treating the address as secure. If rotated, update Make before future scheduled sends or delivery will fail.

## Audience-oriented reporting upgrade — 16 Oct 2026
- `ABASONPLUS_EDITORIAL_POLICY.md`: authoritative-source-first content policy, project-status labels, risks vs opportunities, building-code safety rules and no guaranteed profits.
- `content/researched_wordpress_posts.json`: 11 new project, land-share, material quality, earthquake and land-service articles backed by links to government/legal sources, with `verified_on` and `expires_on` where time-sensitive. The publisher puts these before older generic articles.
- `wordpress_email_prepare.py` rejects stale researched facts, missing citations and expired government-project status rather than calling them current. Static articles are not automatic live fact research.
- `content/topics.json`: 32 video themes, including 14 new high-interest topics. Video rendering skips expired dated topics; still PAUSED from social publishing until photographs pass manual approval.
- `.github/workflows/official-source-monitor.yml`: read-only official source report at 05:35 UTC daily (saved as 7-day GitHub artifact). Monitoring is NOT independent verification and cannot create fresh researched stories by itself.
- `tests/validate_researched_posts.py` checks sources, article structure, dates and duplicate slugs without publishing.
