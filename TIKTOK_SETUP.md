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
