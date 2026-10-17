# AbasonPlus: publication checks and limited recovery

Applies to website, Facebook, YouTube, Instagram and TikTok. The owner's fixed compact white/gold design, real logo and exactly two seconds per image remain unchanged.

## Daily evidence
The 11:00 Europe/Berlin task collects platform evidence into audits/daily/YYYY-MM-DD.json. The publication-audit-report workflow produces an artifact and workflow summary using scripts/publication_audit.py. It never uploads content. Platform status must come from the destination/provider readback, with matched identity, real post ID, publication time and HTTPS destination URL. Make acceptance, job success and provider processing are not publication. Older-day posts never satisfy today's slot. Before the scheduled time a slot is not overdue. TikTok awaiting exact video review is reported separately from missing/failed publication.

For Facebook and YouTube, first inspect Make uploader modules 4 and 3 for returned IDs, then verify destination status/public URL using bounded read-only branches in config/publication_read_routes.json: JSON kind audit_youtube_read or audit_facebook_read, audit_video_id from actual uploader. The private webhook accepts asynchronously; inspect matching execution and module 33/34 output. HTTP Accepted is not provider data or publication. Both GET reads were live-tested without invoking publishing modules. For Instagram/TikTok use the existing GET-only checker 8007397 /posts and exact /posts/<id>; compare account IDs. Inspect warning/error cycles, including handled errors. Never expose the private posting email, webhook, tokens, binary payloads or signed media URLs in reports.

## Retry ceiling
Automatic recovery is limited to ONE failed GitHub job retry BEFORE ANY delivery step began, with verified current-day input, a demonstrated transient infrastructure/network failure, sufficient quota and no prior retry. Read job steps/logs and run_attempt. A content/quality/permission failure is not transient. Do not rerun a successful job, unknown/cancelled delivery, timeout after transfer, or failed/processing provider post. Never replay the whole Make router, delete daily keys or automatically resend a reserved publication. Ambiguous states need reconciliation first. scripts/publication_audit.py returns a recovery decision; the scheduled task may call the existing GitHub rerun_workflow_job tool only when the narrow decision is satisfied. No retry was performed while installing these rules.

## Visual QA
Every slide keeps source/license, distinct photo, matched topic, font size, glyph and line bounds, compact spacing and final MP4 timing checks. Machine subject matching remains heuristic. A mobile-scale QA contact sheet is generated with approximate interface exclusion guides; it is never a publishing asset. Fixed bottom-right logos can be hidden by platform UI. Guides warn and do not silently relocate the owner's selected design or claim a real-device review.

## Freshness
Research compares the preceding 30 days' available editorial topics/headlines and source URLs before choosing a new subject. A repeat requires a clearly identified new development. Keep source publication/effective dates separate from check dates. Corrections to already-published material are reported with proposed corrected text, not silently edited or removed.

## Free quota
No purchases, paid plans, paid APIs or paid trials. Reserve at least 10% (minimum 50 Make credits) for error handling. Forecast only from observed complete-day usage and disclose missing measurements. Batch GET reads and avoid repeated polling. Insufficient quota means hold optional work, never buy more credits.

## Weekly review
During Sunday's existing daily audit, review the preceding seven days. Use real available reach/watch time/completion/save/share/click metrics with dates and platform sources. Missing metrics are unavailable, never zero. Different platforms' view definitions are not directly comparable. If analytics access is absent, report the gap and use verified publication/duplicate/error counts only. Do not add paid analytics services or invent virality claims.

## TikTok
The integration is connected, but exact content preview, creator settings and explicit upload consent still apply. General standing permission is not evidence that a future video was previewed. Official guidance: https://developers.tiktok.com/docs/en/content-sharing-guidelines . Keep the reviewed workflow and no unattended TikTok cron. Daily reporting and post-status reconciliation DO include TikTok.
