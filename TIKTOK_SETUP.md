# TikTok production status — 17 October 2026

@abasonplus is connected through Zernio account 6ad22ddb280aa6cf7d25310d. Provider reads confirmed published videos, including https://www.tiktok.com/@abasonplus/video/7697624320675302688 .

The daily video workflow prepares a TikTok caption and preview package but does not schedule a TikTok post. The owner reviews the exact completed video and selects privacy, comments, Duet and Stitch and confirms usage rights and explicit upload consent. The current per-video workflow is .github/workflows/tiktok-publish-reviewed.yml; it validates the successful artifact, current Europe/Berlin date, five slides, 120 px minimum type, photo QA, caption and MP4 before delivery.

Make modules 9/12 upload temporary media, 13 prevents duplicate daily attempts, and 15 submits the individually approved post. Creator-supported options and current posting availability must be checked before each approved upload. The general standing authorization must not be substituted for the post-specific preview/consent fields.

The original one-video workflow and manifest are retired audit records, not a source of consent for new videos. No cron is enabled. A successful webhook response is not proof of a published TikTok; confirm the provider platform status and public URL.

All visual, audio, source, cost and security rules are in ABASONPLUS_SPEC.md. No new payment, trial or third provider account may be enabled.
