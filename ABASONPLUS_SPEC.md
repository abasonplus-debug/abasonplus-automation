# AbasonPlus — Approved Production Specification (2026-10-16)

## Status: PUBLISHING PAUSED
**No Facebook, YouTube or WordPress publishing until the owner explicitly reauthorizes it.**
GitHub video workflow: manual preview only, publish step `if: false`.
GitHub WordPress workflow: publishing step `if: false`.
Make.com scenario 7968544 must remain inactive. Do not silently reactivate.

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
- Vimeo/social publishing steps remain OFF until authorization.
- When authorized to resume, use **only the single Make.com scenario**; WordPress remains a separate flow.
- Make Data Store `AbasonPlus Published Video Keys` (id 220796): unique local-day key, overwrite=false, BEFORE router; sequential execution to reduce duplicate risk. This is an at-most-once *attempt*, not guaranteed exactly-once delivery to both platforms. Review partial failures manually.
- YouTube Description = incoming `description`; Facebook caption = incoming `caption`.
- GitHub preview files: independent `slide_*.png`, `thumbnail.png`, `metadata.json`, titles/captions/descriptions, MP4, source credits.
- Preserve source attribution and license obligations. WordPress OAuth `invalid_token` remains an external account blocker until owner reauthorizes; never invent or leak credentials.

## Current QA Gate
A GitHub safe validation workflow compiles scripts, validates 18 curated topics/90 typography layouts, checks paused publishing, produces an MP4 without outbound posting and probes metadata/FFmpeg streams.
**Technical render success is NOT visual approval.** Wikimedia fallback search has chosen irrelevant items (historic maps/certificates and cityscape). The photography selection is still not production-quality. Do not reactivate publishing until the photo assets/selection are human-reviewed or a reliable photo QA pipeline is proven.

## Scheduled times — only when explicitly reenabled
Previous (now suspended) generation: 03:15 UTC daily, 05:15 summer / 04:15 winter Germany. WordPress: 06:20 UTC, 08:20 summer / 07:20 winter. GitHub Actions may start late; generation time != publication time.

**Never call this complete, nor publish, merely because a test workflow is green.**
