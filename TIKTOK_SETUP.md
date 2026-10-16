# AbasonPlus TikTok publishing integration

Last checked: 2026-10-16. TikTok account and publishing connection **NOT YET AUTHORIZED**.

## What is already complete
- Original video source is the shared daily AbasonPlus editorial and high-resolution 9:16 five-slide carousel.
- The exact user-supplied music file is `assets/abasonplus.mp3`.
- The hook is the first full-bleed 1080x1920 frame and also `thumbnail.png`.
- The renderer and `scripts/verify_video_release.py` verify topic-linked photo sources, attribution, no repeated images, 130+ px Bengali typography, reserved 60% typography region, source links, 15-second H.264 MP4 with AAC soundtrack.
- `scripts/prepare_tiktok_preview.py` produces `output/tiktok_caption.txt` and `output/tiktok_preview.json`. Both are archived with the same daily generated video on the existing video workflow.
- Successful, **nonpublishing** smoke test: GitHub run 38909294406.
- No account id, password or access token is committed to the repository.

## Remaining external authorization and connection
TikTok organic posting is **not provided** by Make's official TikTok Campaign Management (ads-focused) app.
Make's `make-nodes-late:addTiktokPost` (Zernio) is the available third-party organic TikTok publisher, but no Zernio connection currently exists. TikTok account must be connected on Zernio and the related Make OAuth/API-key credential must be approved by the owner. Only then can an account id be obtained from `make-nodes-late:getSocialAccounts`, validated, and bound to a module.

Zernio's current published pricing permits up to **two connected social accounts free**, including TikTok, subject to platform restrictions. This may change; verify before subscribing or authorizing fees. If using its TikTok API, respect creator's allowed privacy levels, content preview confirmation, express consent, AI/sponsored-content disclosures and account eligibility. Never set express-consent flags without genuine owner authorization.

## Media delivery blocker
Make receives the MP4 as file bytes from GitHub, but the Make Zernio `addTiktokPost` action expects a `video` URL **string**, not a binary MP4 attachment. To make it operational, provide a correctly MIME-typed public HTTPS URL that actually returns MP4 bytes (not HTML or an authenticated Drive page), or use Zernio's authenticated media upload/presign interface and feed its resulting URL into the TikTok post module. Never silently map multipart file bytes to a URL field.

Before enabling actual TikTok delivery:
1. Verify TikTok/Zernio account connection, allowed privacy choices and whether the user's account meets all provider requirements.
2. Confirm a public or provider-hosted video URL, media copyright rights and caption/thumbnail metadata.
3. Add the TikTok delivery as its own independently idempotent route, **not** behind the shared Facebook+YouTube same-day key: an error for one platform must not prevent legitimate retries of the other platform.
4. Use the existing GitHub machine-verified MP4; no separate generation or duplicate music.
5. Check actual TikTok post status and URL (including asynchronous completion), not merely Make webhook acceptance.
6. Test with a harmless **draft** or owner-approved private/preview action and only then enable the authorized schedule.
7. Do not publish from this TikTok preparation code. TikTok remains pending until the account has authorized the workflow.

## Official reference
- TikTok Content Posting API: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- Zernio TikTok publishing requirements: https://docs.zernio.com/platforms/tiktok
- Zernio account pricing: https://docs.zernio.com/pricing

**Status: Preview rendering works. TikTok account authorization and actual media upload path remain unverified. No TikTok video was posted.**

## Confirmed new integration results — 16 October 2026
- The Zernio connection is live and returns a connected, active TikTok account `@abasonplus` with `video.publish` and `video.upload` permissions. No TikTok posts were made by ChatGPT.
- The existing authenticated Zernio Make connector successfully requested a signed temporary MP4 upload URL through `/media/presign` (no additional API key or paid hosting).
- GitHub generated an isolated 24,552-byte transport-test MP4. Make received it, then the Make HTTP v4 module uploaded it as `video/mp4` to Zernio R2 temporary storage with HTTP 200.
- Byte integrity was independently verified: uploaded R2 ETag matched the original sample's MD5 exactly. Test GitHub run: `38915481663`; Make execution: `ac35ed08ec204ce8a248f421eeccd82d`. This proves the media transport, **not** TikTok publication.
- The Make router has a separate TikTok route behind **`kind=video`, `review_approved=true`, `visual_qa_passed=true`, and `tiktok_publish_approved=true`** (a separate transport-test-only alternate).
- The TikTok route has a per-day Data Store key module after media upload using `{{1.tiktok_post_key}}` to avoid duplicate posting attempts.
- The existing GitHub scheduled video workflow maps `tiktok_caption` and a TikTok post key but ALWAYS sends `tiktok_publish_approved=false`; therefore daily video publication to TikTok **cannot trigger** yet. The existing WordPress/Facebook/YouTube routes remain unchanged.
- TikTok Zernio create-post module 14 is NOW CONNECTED to `@abasonplus`, with media URL from the successful signed-upload module and caption mapping from `tiktok_caption`, but is deliberately `disabled=true` until genuine post-specific preview/consent can be confirmed. Final platform URL/status verification remains PENDING. TikTok's Content Posting API requires creator content-preview and express-consent signals and the account's permitted privacy options. Do not fabricate creator preview confirmation.
- The user's older Zernio API key was visible in a screenshot. The authorized Make connection has been retested successfully, but a working connection alone cannot prove that the previous exposed key was revoked. Any new API key must remain private.
- Zernio's temporary uploaded media deletes after seven days unless attached to a Zernio post, and uploads may not be scheduled beyond its allowed window. No monetary paid upgrade is part of this implementation.

Official references:
https://docs.zernio.com/guides/media-uploads
https://docs.zernio.com/platforms/tiktok

**TikTok AUTO-PUBLISH STATUS: CONFIGURED BUT DISABLED PENDING PER-VIDEO CREATOR PREVIEW/CONSENT. No public TikTok video posted.**

## 16 Oct 2026 — Final test result
- GitHub run `38915481663` sent an isolated 24,552-byte test video. The Make temporary Zernio upload (module 12) returned HTTP 200 with ETag exactly matching the original MP4 MD5 `fbc82b4334fb174f5f3ce51fe9d484cf`.
- The Zernio account `@abasonplus` is authorized and has `video.publish` and `video.upload` scopes. The Make Zernio posting module is number 14 and is **disabled**. The GitHub video publisher currently sends `tiktok_publish_approved=false` by design.
- Distinct TikTok daily key goes to the Make Data Store only when video source and post-specific owner permission checks pass. Machine-generated TikTok caption includes image-source and content disclosures where relevant.
- Don't claim TikTok auto publishing is active until a creator-reviewed sample is genuinely approved and a private test/publishing status confirms the correct TikTok account and privacy settings. Zernio Free accounts quota and Make free credits must stay below applicable limits.

## Final direct-post compliance and visual findings — 16 Oct 2026
- Confirmed live account `@abasonplus`, display name "আবাসন প্লাস", canPostMore=true, and ONLY `PUBLIC_TO_EVERYONE` allowed for direct video posts. Creator interaction options (comment, duet and stitch) are available, but TikTok requires them to be individually selected by the creator. Zernio creator endpoint: `GET /v1/accounts/{accountId}/tiktok/creator-info?mediaType=video`.
- Official TikTok + Zernio direct posting requires **per-video preview confirmation** and **express user consent**. Do not blindly set these flags from a daily schedule or from the earlier broad "auto publishing on" instruction.
- Added manual, individual-video approval GitHub workflow `.github/workflows/tiktok-publish-reviewed.yml`, requiring a viewed preview run ID, an exact preview statement, post-specific consent, creator privacy choice, three interaction choices and soundtrack/image rights. This does not run automatically.
- Introduced `config/tiktok_publication_gate.json` with `enabled=false`. The GitHub consent workflow fails closed until the Zernio direct-post route accepts the full required consent settings and publishes a real test successfully. The Make connector temporarily returned internal errors during this final step, so no TikTok configuration changes should be assumed.
- Audited actual first video, discovered Bengali-only Noto font produced `□` for English `Land Share?` even though previous machine QA returned success. Corrected with fontTools Unicode cmap checks, mixed Latin/Bengali shaping fallback and thinner transparent regular font; GitHub end-to-end preview run `38923421174` is successful. This proves the rendering error is repaired, **not** that the visuals meet the owner's aesthetic standards.
- The updated source-checked five-slide, 1080×1920 H264/AAC 15-second video is a **PREVIEW ONLY** of the 2026-10-16 Land Share landowner due-diligence tips, not a published TikTok post.
- GitHub daily video workflow `daily-carousel.yml` still sets `tiktok_publish_approved=false`; TikTok direct-post remains unverified and disabled. Existing WordPress, Facebook and YouTube schedules were not changed.
- Unreviewed static photos, unproven music publication rights, and creator-mandated per-post privacy/consent are remaining blockers. Keep new videos offline until approved.

TikTok reference: https://docs.zernio.com/platforms/tiktok
