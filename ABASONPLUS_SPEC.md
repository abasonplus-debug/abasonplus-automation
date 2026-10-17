# AbasonPlus production rules — verified 17 October 2026

This is the current production specification. README.md describes the live routes. Historical setup statements are superseded by this file.

## Daily flow and date
- Use Europe/Berlin for the publication day, filenames, dedupe and schedules, including daylight saving changes.
- ChatGPT Daily Research targets 05:00; source monitor 07:35; WordPress 08:20; Facebook/YouTube/Instagram video workflow 08:45.
- These are trigger targets. GitHub may delay or drop scheduled runs; rendering and provider processing take additional time.
- Today's verified editorial is required for both WordPress and video; static article catalogs are available only through an explicit preview flag. Missing or invalid content is held and reported, never invented or relabeled as breaking news.

## Exact visual style
- Five independent, full-frame 1080×1920 photographs; 9:16, no frame, panel, border, dark overlay, gradient, outline or shadow.
- Each photograph must match that slide's specific topic and have recorded source, creator and license. Stock imagery must not be presented as an actual named government project.
- Bengali and Latin text: actual font size at least 120 px, bold dark navy #061B3E, alpha 230/255, directly over naturally light space. Two lines preferred; at most three. Font fallback must cover all glyphs.
- Each text line is checked for background brightness/contrast. Metadata records actual ink bounding area; no claim that this equals 60% opaque text coverage.
- If a logo is available, use it small at the bottom right within the platform safe area; otherwise omit it.
- CLIP relevance checks are heuristic. They cannot guarantee human aesthetic judgment or prove that a photograph depicts a real event.

## Media and copy
- Use only assets/abasonplus.mp3 supplied by the owner. The owner's claim of usage rights is not an independent copyright clearance.
- H.264/AAC MP4, 1080×1920, 30 fps, yuv420p, fast start, five 3-second slides, about 15 seconds, fade-out.
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
