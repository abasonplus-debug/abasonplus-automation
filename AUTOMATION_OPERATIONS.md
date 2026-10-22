# AbasonPlus: publication checks and limited recovery

Applies to website, Facebook, YouTube, Instagram and TikTok. The owner's fixed compact white/gold design, real logo and exactly three seconds per image apply (owner update 20 October 2026); keep 5–16 slides and the 50-second ceiling. Historical artifacts retain their recorded timing and are never resent merely for this update.

## Daily evidence
The task performs lightweight GitHub checks at 09:00 and 10:00 Europe/Berlin and the full audit at 11:00. Early checks do not repeat Make/platform reads; notify on actual failure/hold, or hand over a ready exact TikTok preview once. Execution time and phone push delivery are not guaranteed. The full audit collects platform evidence into audits/daily/YYYY-MM-DD.json. The publication-audit-report workflow produces an artifact and workflow summary using scripts/publication_audit.py. It never uploads content. Platform status must come from the destination/provider readback, with matched identity, real post ID, publication time and HTTPS destination URL. Make acceptance, job success and provider processing are not publication. Older-day posts never satisfy today's slot. Before the scheduled time a slot is not overdue. TikTok awaiting exact video review is reported separately from missing/failed publication.

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

## Hook, caption, first brand comment, hashtags, cover and music
Owner instruction 18 October: every video needs a factual compelling hook, useful fuller caption/description, a prepared first brand comment, at least five distinct topic-relevant hashtags, an attractive matching hook cover and ONLY the owner's assets/abasonplus.mp3. scripts/engagement_pack.py validates and stores first_comment.txt, its JSON-escaped form and engagement_pack.json. These are archived with the preview. Do not claim hashtag popularity, viral reach or increased views as guaranteed.

Facebook uses native CreateComment after the new Reel upload. YouTube attempts the actual hook-cover thumbnail and a top-level comment on separate branches; errors must not stop other destinations. Instagram uses the first frame as cover (thumbOffset=0), TikTok cover offset=0. YouTube Shorts can handle cover display differently; do not claim a successful API write proves that every Shorts surface uses that image.

For Instagram/TikTok first comments, confirm the exact post is published, read existing own comments, verify account capability and preserve one stable per-post comment key. A dedicated comment route accepts only fixed connected accounts and numeric native post IDs. No DMs, replies to other people, likes, paid features or pinning. TikTok's exact-video preview must also include the prepared comment. A timeout is not permission to post again; preserve the key and reconcile. Other viewers can comment before the automation, so this is the first BRAND comment, not a promise of first chronological position. Write capability is not tested by a GET; report first live comment result after it occurs.

Resolved 18 October 22:30 Europe/Berlin: comment GETs require accountId in the query. Both connected Instagram and TikTok reads succeeded. Gate 45 is enabled; each exact post has datastore reservation and stable idempotency. One owner-approved comment on each current-day post was written and read back with isOwner=true: Instagram 18111358733267412, TikTok 7697943343510160161. Use GET-only checker comments/meta/status outputs and config/engagement_comment_routes.json. Never repeat installation comments or repost a video.

## Failure visibility and consent evidence
### Missing-trigger protection — installed 21 October 2026

Primary WordPress and video triggers remain 02:00 Europe/Berlin. The same workflows
also have backup targets at 02:23 (WordPress) and 02:31 (video). Both primary and
backup pass scripts/schedule_guard.py under the existing workflow concurrency
group. Only the first scheduled first-attempt run for that Berlin date proceeds.
Any earlier run, including failed, cancelled, queued or ambiguous delivery, blocks
a second attempt. This is missing-trigger recovery, not failed-publication recovery.
The existing independent Make/platform reservations remain authoritative and are
never removed. A delayed primary created after the backup cannot deliver again.
Manual dispatch remains preview only. Scheduled reruns are held for reconciliation.
The elected Berlin date is checked again immediately before any transfer; crossing
midnight holds release. DST repeated 02:00 hours share the same daily election.

publication-watchdog.yml checks both publishing workflows separately at 03:07
Europe/Berlin and after either workflow completes. It distinguishes no trigger,
queued/running, held/skipped delivery, failed delivery and completed transfer.
It never treats a successful source job or Make receipt as published. Missing
editorial now raises an error in WordPress preparation instead of silently ending
green. The watchdog only reads workflow evidence and upserts one GitHub alert
issue per date, including actual run links. Identical alerts do not create repeat
issues/comments. Manual and push watchdog checks are read-only. It never invokes
Make, uploads media, clears keys, reruns jobs or publishes to TikTok.

The default alert destination is a GitHub issue in this repository. GitHub email
delivery depends on the owner's notification/subscription settings and is not
verified by creating an issue. Optional Telegram needs GitHub Actions secrets
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID; values must never enter source/logs.
Telegram sends only when the daily issue is created/updated, with no ambiguous
send retry. Telegram is not active until these secrets are configured and a real
message is verified. No Make credits or paid service is required by the watchdog.

Limitations: all GitHub schedules, including backups/watchdog, can be delayed or
dropped during a GitHub outage. Workflow-run checks cannot detect an event that
never started. The separate ChatGPT audit must have an enabled task and a verified
linked chat destination for an independent notification path. At installation its
new audit task was found paused with conversation_id=null; an update/resume did
not restore a destination, so it was paused again to avoid wrong-chat delivery.
Do not describe that notification path as repaired or create duplicate tasks.

Source selection errors now fail the daily workflow before rendering; green success is not used for a blocked source. Manual dispatch stays preview-only. Do not force a held photo/source into publication. GitHub schedule delay remains possible.

Read audits/tiktok-approvals/YYYY-MM-DD.json and audits/tiktok-publications/YYYY-MM-DD.json before diagnosing missing consent. scripts/tiktok_approval.py validates exact date, account, hash and settings. Preview false flags describe the pre-approval state and do not override a later matching real owner OK. Future approvals must include caption_sha256 and preview_run_id; changing media, caption or settings invalidates approval. Never infer consent for another date/video.

For first brand comments, after verified current-day publication read GET /inbox/comments/<native-id>?accountId=<fixed-id>. Require status success, matching meta account/post and no matching own comment; if pagination hasMore=true finish checking before writing. Then use bounded kind publish_first_comment once, verify returned ID and own-comment readback, and save evidence. Preserve reservations after ambiguous errors; no blind retries, no DMs or other people's replies. Schedule/audit or the interactive TikTok OK handler performs this once; do not claim comments are instant.

## 22 October reliability correction

The actual 22 October incident was a readable-headline-area failure, not HTTP
403. The scheduled run started and stopped before every delivery step.

`photo_preflight.py` tests the same exact text/font bounds and each verified photo
before release, without composing a slide, generating MP4 or calling Make. The
preflight runs on a daily editorial push and targets 01:15 Berlin. This is photo
and layout QA only, not completed-media QA. The scheduled release still performs
all existing final video, audio, source, license, date and duplicate checks.

Recovery is bounded: try seven natural crop positions; require the resulting
crop itself to pass subject and unchanged readability checks. Up to two optional
`alternatives` per photograph must have independently researched HTTPS Pexels
source/creator/license/scene and explicit scene_match. No web search, invented
attribution or unrelated substitute is used. Exact copy, fonts, logo, duration
and TikTok consent are unchanged. No alternatives are invented or backfilled
into already-published editorials by this installation.

Photo GET retries apply only to network errors, 408/429/5xx: three attempts with
1s/2s backoff. Permanent 403, unsafe redirect, missing license and failed quality
checks cannot be approved by retry. Exhausted candidates hold release with a
sanitized per-slide diagnostic artifact. No delivery/send retry was added.
The Make reservation remains authoritative after transfer or uncertainty.

The existing watchdog observes preflight completion and creates/updates the same
per-day GitHub issue, including failures before 02:00. Optional Telegram still
requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID; missing credentials mean no
Telegram delivery. Never claim message delivery based on issue creation.

Remaining limitations: preflight schedules can be late, semantic matching is
heuristic, final MP4 QA may fail, no platform-specific resend route is installed
by this change, and no future TikTok approval is inferred. Photo repair cannot
promise publication when every researched candidate is unsuitable. The owner
must see exact-video preview/caption/comment/settings and approve each TikTok.


## Owner superseding update — 22 October 2026

New renders use `narration_v1`, superseding every fixed two/three-second and
15/50-second editorial rule above. Exact hook plus slide texts are narrated in
Bengali; each slide lasts its measured WAV segment plus a short pause. Total
video length is the sum of those segments, not an arbitrary target or truncation.
The operational bound is 5–64 source-checked slides, with existing caption,
font/layout, file-size, provider and free quota limits checked separately.

The default voice is local GPL eSpeak NG (`bn`), offline and subscription-free.
This is synthetic speech, not a promise of natural human narration. The original
assets/abasonplus.mp3 loops quietly underneath (10% gain); no catalog music is
substituted. Narration script and WAV SHA-256, measured segment durations and
padding are independently checked before release and archived with the preview.

Historical media retain their recorded policy. New TikTok exact approval must
match narration hash, timing_mode and slide_durations as well as MP4/caption,
source run/commit, settings and rights; changing voice invalidates an earlier OK.
There is no unattended TikTok upload. No creative is generated merely by a code
validation run. Make's current 5 MB transport remains fail-closed: a longer
video that exceeds it needs an independently reviewed transport solution, never
a blind resend, reduced QA, arbitrary audio cutoff or paid upgrade.
