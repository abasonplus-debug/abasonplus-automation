# AbasonPlus: publication checks and limited recovery

Applies to website, Facebook, YouTube, Instagram and TikTok. The owner's fixed compact white/gold design and real logo apply. New voiced media uses 5–16 slides, each covering its complete measured narration (minimum three seconds); no fixed total duration or 50-second ceiling. Historical artifacts retain their recorded timing and are never resent merely for this update.

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
No purchases, paid plans, paid APIs or paid trials. Keep 20 Make credits as the remaining-credit stop floor (owner update 30 October 2026), superseding older percentage/50/100-credit reserves. Stop credit-consuming calls at remaining <=20. Check each bounded action's defensible maximum cost will leave at least 20; do not cross the floor. Forecast only from observed complete-day usage and disclose missing measurements. Batch GET reads and avoid repeated polling. Insufficient quota means hold optional work, never buy more credits.

## Weekly review
During Sunday's existing daily audit, review the preceding seven days. Use real available reach/watch time/completion/save/share/click metrics with dates and platform sources. Missing metrics are unavailable, never zero. Different platforms' view definitions are not directly comparable. If analytics access is absent, report the gap and use verified publication/duplicate/error counts only. Do not add paid analytics services or invent virality claims.

## TikTok
The integration is connected, but exact content preview, creator settings and explicit upload consent still apply. General standing permission is not evidence that a future video was previewed. Official guidance: https://developers.tiktok.com/docs/en/content-sharing-guidelines . Keep the reviewed workflow and no unattended TikTok cron. Daily reporting and post-status reconciliation DO include TikTok.

## Hook, caption, first brand comment, hashtags, cover and music
Owner instruction 18 October: every video needs a factual compelling hook, useful fuller caption/description, a prepared first brand comment, exactly five distinct hashtags: two topic-specific and three broad Bangladesh-audience tags, an attractive matching hook cover and ONLY the owner's assets/abasonplus.mp3. scripts/engagement_pack.py validates and stores first_comment.txt, its JSON-escaped form and engagement_pack.json. These are archived with the preview. Do not claim hashtag popularity, viral reach or increased views as guaranteed.

Facebook uses native CreateComment after the new Reel upload. YouTube attempts the actual hook-cover thumbnail and a top-level comment on separate branches; errors must not stop other destinations. Instagram uses the first frame as cover (thumbOffset=0), TikTok cover offset=0. YouTube Shorts can handle cover display differently; do not claim a successful API write proves that every Shorts surface uses that image.

For Instagram/TikTok first comments, confirm the exact post is published, read existing own comments, verify account capability and preserve one stable per-post comment key. A dedicated comment route accepts only fixed connected accounts and numeric native post IDs. No DMs, replies to other people, likes, paid features or pinning. TikTok's exact-video preview must also include the prepared comment. A timeout is not permission to post again; preserve the key and reconcile. Other viewers can comment before the automation, so this is the first BRAND comment, not a promise of first chronological position. Write capability is not tested by a GET; report first live comment result after it occurs.

Resolved 18 October 22:30 Europe/Berlin: comment GETs require accountId in the query. Both connected Instagram and TikTok reads succeeded. Gate 45 is enabled; each exact post has datastore reservation and stable idempotency. One owner-approved comment on each current-day post was written and read back with isOwner=true: Instagram 18111358733267412, TikTok 7697943343510160161. Use GET-only checker comments/meta/status outputs and config/engagement_comment_routes.json. Never repeat installation comments or repost a video.

## Failure visibility and consent evidence
### Missing-trigger protection — installed 21 October 2026

Primary WordPress and video triggers are 01:00 Europe/Berlin. The same workflows
also have backup targets at 01:23 (WordPress) and 01:31 (video). Both primary and
backup pass scripts/schedule_guard.py under the existing workflow concurrency
group. Only the first scheduled first-attempt run for that Berlin date proceeds.
Any earlier run, including failed, cancelled, queued or ambiguous delivery, blocks
a second attempt. This is missing-trigger recovery, not failed-publication recovery.
The existing independent Make/platform reservations remain authoritative and are
never removed. A delayed primary created after the backup cannot deliver again.
Manual dispatch remains preview only. Scheduled reruns are held for reconciliation.
The elected Berlin date is checked again immediately before any transfer; crossing
midnight holds release. DST changes preserve the same Berlin-day election.

publication-watchdog.yml checks both publishing workflows separately at 02:07
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

Read audits/tiktok-approvals/YYYY-MM-DD.json and audits/tiktok-publications/YYYY-MM-DD.json before diagnosing missing consent. scripts/tiktok_approval.py validates exact date, account, hash and settings. Preview false flags describe the pre-approval state and do not override a later matching real owner OK. Future approvals must include caption_sha256, preview_run_id, preview_head_sha and the complete immutable format object (including voiceover and slide_durations); changing media, caption or settings invalidates approval. Never infer consent for another date/video.

For first brand comments, after verified current-day publication read GET /inbox/comments/<native-id>?accountId=<fixed-id>. Require status success, matching meta account/post and no matching own comment; if pagination hasMore=true finish checking before writing. Then use bounded kind publish_first_comment once, verify returned ID and own-comment readback, and save evidence. Preserve reservations after ambiguous errors; no blind retries, no DMs or other people's replies. Schedule/audit or the interactive TikTok OK handler performs this once; do not claim comments are instant.


## 22 October photo recovery and voice integration
New primary render attempts use bounded natural crop repair with unchanged
readability thresholds and semantic checks of the resulting crop. Up to two
optional alternatives per slide require independently verified Pexels source,
creator, license, scene and topic match. No fabricated or arbitrary substitute.
Photo GET retries are restricted to transient network/408/429/5xx errors, three
attempts with 1s/2s backoff. Permanent 403 is not repeatedly requested. Exhausted
candidates hold release and archive sanitized diagnostics. No send retry or
reservation removal is introduced.

Editorial pushes and 00:45 Berlin run photo/layout preflight without composing
slides, synthesizing voice or generating MP4. The existing watchdog includes
preflight failures before 01:00 and upserts the existing daily issue. Telegram
still needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID; actual delivery remains
unverified until configured. Preflight is not a substitute for final media QA.

Preserve the newly installed CosyVoice3 Dan Mason owner-selected voice, full
slide script, narration at 100%, original music at 20%, and measured speech-aligned
duration. No fixed 15/50-second cap applies to new voiced media. The public free
TTS demo has no uptime guarantee; synthesis failure must hold and alert rather
than silently publishing unvoiced media or switching voice. The Make total 5 MB
payload gate remains. Historical media/approvals are unchanged, and a changed
video/voice requires a new exact TikTok preview/OK. No platform-specific resend
route or guaranteed publication is supplied by this correction.


## Owner schedule update — 23 October 2026
Daily WordPress and Facebook/YouTube/Instagram video trigger target is now 01:00 Europe/Berlin, superseding older 02:00 targets. Research remains 00:30; source monitor and photo preflight are 00:45. Missing-trigger-only backups are WordPress 01:23 and video 01:31; watchdog 02:07. Existing Berlin-day reservations, no replay after an earlier attempt, QA and exact-video TikTok preview/OK remain unchanged. Trigger time is not guaranteed publication completion time.

## Exact owner OK record and retired workflows — 24 October 2026
After the exact preview/OK, use scripts/build_tiktok_approval.py build_approval to assemble the dated record from the actual MP4 hash, original preview JSON, successful source-run metadata, current reviewed creator settings and explicit owner evidence. Copy the complete format object; do not reconstruct voice metadata or omit preview_head_sha. This offline helper cannot publish or grant consent. Save and validate the record before dispatching tiktok-publish-reviewed.yml. No generic or future OK.

Completed historical delivery workflows are archived under archive/workflows, outside GitHub Actions. They cannot be dispatched there; publication/approval evidence remains intact. Keep the current reviewed TikTok workflow, daily publishers, preflight, watchdog, report and bounded recovery workflow. Never delete daily reservations or historical approval/publication records.


## Owner superseding schedule — 26 October 2026
Primary WordPress/Facebook/YouTube/Instagram release trigger: 00:30 Europe/Berlin daily. Research target 00:00; source/photo preflight 00:15. This overrides older times above. Backups remain missing-trigger-only, no replay. TikTok requires exact preview/OK. Trigger time is not a guaranteed publication completion time.

## Owner-approved reference — 26 October 2026
Future creative target: the owner-approved 1.1x cartoon land-share explainer (Library libfile_42824ac934d881919829065642e17271). Use information-rich Bengali explanations: problem, risks, checks and practical remedy; coherent cartoon characters and matching illustrative scenes, substantial readable text, actual small bottom-right logo. Do not imply these illustrations depict real projects or events. New CosyVoice3 narration is processed with FFmpeg atempo=1.1 before measuring full speech and setting slide durations; unity voice / 20% owner music remain. Record playback_speed in voice metadata/manifests. Historical 1.0x manifests remain valid under their original approval; never reuse that approval for new media. Short useful captions; two topic + three broad tags per destination, YouTube adds #Shorts as a sixth EXTRA tag. AI label ON where supported; owner does not want additional AI prose in social copy.
Implementation status: 1.1x narration is implemented. Cartoon asset ingestion, evidence and QA are not integrated into the current photo-only daily selector/release checks. This is a real release hold, not permission to spoof photo/license QA or weaken guards. Research records the new creative brief but must report the integration hold. Existing free-only, source verification, exact TikTok preview/OK and dedupe protections remain.

## Cartoon pipeline implementation — 27 October 2026
Commit 4b6e532 implements story.illustrations inputs through selector, preflight, renderer, independent release gate and reviewed TikTok validation. Each background asset requires repository assets/editorial path, actual SHA-256, creator/origin reference, rights evidence/confirmation, scene/scene_match, contains_text=false and illustrative_not_real_event=true. Minimum original 1080x1920; repeated hashes/path escapes/altered bytes fail closed. CLIP uses illustration prompts; generic photo flags are never forged. Original glyph bounds, readability, source, exact consent, transport and duplicate checks remain. Local complete suite: 127 tests passed; 160 typography layouts passed. Watchdog due boundary and tests now match owner 00:30 release. No real new artwork/voice/video was generated or published during this repair. Earlier text saying asset ingestion is unimplemented is superseded; actual artwork creation and the first complete real render remain unverified. These code changes do not themselves grant creative-generation or publishing consent.
