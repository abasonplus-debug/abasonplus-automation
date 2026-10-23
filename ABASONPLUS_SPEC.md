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


## Owner schedule update — 23 October 2026
Daily WordPress and Facebook/YouTube/Instagram video trigger target is now 01:00 Europe/Berlin, superseding older 02:00 targets. Research remains 00:30; source monitor and photo preflight are 00:45. Missing-trigger-only backups are WordPress 01:23 and video 01:31; watchdog 02:07. Existing Berlin-day reservations, no replay after an earlier attempt, QA and exact-video TikTok preview/OK remain unchanged. Trigger time is not guaranteed publication completion time.

## Owner production contract — 24 October 2026 (supersedes older copy/timing rules)
- Every post needs an attractive factual hook, substantial useful Bengali caption and fuller description within each platform limit; a natural follow/subscribe invitation, without guaranteed reach claims.
- Exactly FIVE distinct hashtags: TWO selected for the actual subject, THREE broad Bangladesh/Bangla audience tags (#Bangladesh #বাংলাদেশ #Bangla). These audience choices are not verified as the world's most-used tags. No irrelevant trending bait.
- Prioritise verified current useful news; clearly label useful evergreen guides. Do not repeat an unchanged topic or source.
- Real licensed professional, topic-matched 9:16 photographs, distinct per slide, with restrained finishing; “premium/final director cut” is an aesthetic target, not a substitute for QA. Original small bottom-right logo, compact white/gold outlined Bold text remains locked.
- Detailed multi-sentence slide copy is allowed. Use as much useful exact text as fits measured glyph/outline/shadow bounds at the existing minimum font size; hold or split during editorial preparation on overflow, never shrink or omit conditions. Do not add filler merely to make slides dense.
- Full selected CosyVoice3 Dan Mason narration determines each slide duration (minimum three seconds). NO fixed 15-second target or 50-second overall cap; keep 5–16 images, voice 100%, owner assets/abasonplus.mp3 music 20%, 5MB Make payload and actual provider limits.
- AI disclosure defaults ON for new media: YouTube containsSyntheticMedia=true; Instagram isAiGenerated=true; TikTok video_made_with_ai=true. Current native Make Facebook upload module exposes no AI-label input; public copy discloses AI narration, and native label status remains unverified. Do not invent a flag.
- Primary release trigger remains 01:00 Europe/Berlin, missing-trigger-only backups 01:23 WordPress/01:31 video, watchdog 02:07. Rendering/provider processing may finish later; GitHub cron is not an exact-minute SLA.
- Keep free-only operation, QA, dated source/license evidence, per-platform duplicate reservations, no ambiguous replay and exact-video TikTok preview/OK. Labels and future settings do not retroactively approve or republish existing media.
