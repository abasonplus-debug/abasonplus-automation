# AbasonPlus production rules — verified 17 October 2026

This is the current production specification. README.md describes the live routes. Historical setup statements are superseded by this file.

## Daily flow and date
- Use Europe/Berlin for the publication day, filenames, dedupe and schedules, including daylight saving changes.
- ChatGPT Daily Research targets 00:30; source monitor 01:15; WordPress 02:00; Facebook/YouTube/Instagram video workflow 02:00.
- These are trigger targets. GitHub may delay or drop scheduled runs; rendering and provider processing take additional time.
- Today's verified editorial is required for both WordPress and video; static article catalogs are available only through an explicit preview flag. Missing or invalid content is held and reported, never invented or relabeled as breaking news.

## Exact visual style — updated 18 October 2026
- Every hook/tip image uses the locked `compact_white_gold_v2` contract in config/carousel_style.json and CAROUSEL_STYLE_PROMPT_BN.md. This replaces the old navy, no-outline, upper-zone style.
- Five independent topic-matched licensed 1080×1920 full-bleed photographs, no frame, panel, border, dark overlay or gradient. Professional restrained photographic finishing; no paid AI generation or fabricated real-event photographs.
- Centered compact text block, exact copy, Noto Sans Bengali Bold with genuine Latin fallback: body 120 px, hook 132 px. White #FFFFFF with semantic gold #FFD24A keyword emphasis, 4 px black outline, close subtle shadow (2,3 px offset).
- Measure visible glyph/outline/shadow bounds: target 4 px gaps within a sentence, 10 px between sentences. Never collide, clip or shrink below minimum; overflow holds release. A long legal paragraph is not automatically suitable for the fixed three-second slide duration.
- Photo readability now accounts for outlined text, measuring local clutter for each line. Font, glyph coverage, actual line bounds, centered placement, no overlap, color/outline contract and photo statistics are independently checked. Machine QA is a heuristic, not human aesthetic approval.
- Use the original logo, width 70–90 px, 28 px from bottom/right. If unavailable, report omission; never invent a replacement. Platform UI can cover a logo this close to the edge.

## Media and copy
- Use only assets/abasonplus.mp3 supplied by the owner. The owner's claim of usage rights is not an independent copyright clearance.
- H.264/AAC MP4, 1080×1920, 30 fps, yuv420p, fast start, variable 5–16 slides, exactly 3 seconds EACH, total 15–48 seconds, fade-out.
- Hook, useful caption, five or more relevant hashtags, source attribution; YouTube title <=100 characters, description <=5000, Instagram caption <=2200 including credits. Hold on overflow rather than silently deleting attribution.
- Verify source/date, fonts, no repeated photos, line contrast, original music, dimensions and duration before delivery. Machine QA is recorded as machine QA.

## Publication and fault handling
- Active Make scenario 7968544 publishes WordPress, Facebook Page Reels, YouTube Shorts and Instagram @abasonplus.
- Each destination has an independent per-Berlin-day duplicate guard. Reserve at most one attempt per day for WordPress/Facebook/YouTube; inspect ambiguous failures before retrying. The new guards take effect 18 October after the already-published 17 October cycle.
- Instagram also sends a stable per-day provider Idempotency-Key. Accepted/processing is not published; verify the platform status and URL.
- A provider exception must be visible in execution history and the daily audit; isolated uploader error handlers allow later platform branches to run.
- WordPress publication verification requires the exact slug and title, a recent publication timestamp, publish status and the expected public site URL.
- TikTok is connected and individually approved videos have been published. Each new TikTok video still requires its own preview and creator consent/settings. No TikTok daily cron is enabled.
- Manual daily workflows are preview only. Completed one-time publishing workflows are retired and retained as audit records.

## Security and costs
- No paid plan, trial, credit purchase or paid API. Make Free limits and the provider's two-account free allowance apply. Only TikTok and Instagram use the posting provider.
- Keep the Make webhook and WordPress secret posting email private. Never log them or commit them. Do not expose tokens.
- Article HTML uses a safe tag/attribute allowlist and HTTPS links, and must not contain Post-by-Email control directives.
- Static regression checks run on code changes without rendering new creative content or posting. A full preview render requires an explicit authorized request.
- The daily audit is read only and reports failed/missing/processing posts. It does not automatically resend ambiguous attempts.

Timing update (owner, 2026-10-20): every image is exactly 3 seconds. This supersedes the former 2-second rule. Keep the 50-second maximum: 5–16 slides, total 15–48 seconds; never make 17 slides (51 seconds). Multiple sentences per image remain allowed. Dense text is not guaranteed readable in three seconds. Historical rendered/published artifacts retain their recorded timing; this change does not authorize re-rendering, resending or approving a different TikTok video.
