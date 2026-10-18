# AbasonPlus video automation

Bangla housing-information carousel, Facebook Reel, YouTube Short, and creator-reviewed TikTok video. Source: a fresh, cited `content/daily_editorial_YYYY-MM-DD.json` for the current Europe/Berlin date. Without that file, both daily publication workflows hold. Static article catalogs are explicit preview material only.

## Each carousel image: locked visual direction

Apply these directions independently to the hook and all four tips. The `text` and `query` fields in the daily editorial brief are the slide-specific copy and matching photographic subject.

Use **CAROUSEL_STYLE_PROMPT_BN.md** and **config/carousel_style.json** for every image, including the hook. The owner-selected style is **compact_white_gold_v2**: centered compact Bengali text block; 120 px Bold body, 132 px Bold hook; white/gold semantic emphasis; 4 px black outline and close subtle shadow. The no-panel/no-border/no-gradient rules remain. The old navy/no-outline style is retired.

The renderer measures actual visible ink/outline/shadow spacing (4 px within a sentence; 10 px between sentences), checks each photograph for readable line regions, and refuses overflow instead of shrinking the font. Each photograph must be distinct, licensed, precisely topic-matched and professionally finished. This remains a free licensed-stock workflow; “final director cut” is visual direction, not a claim of daily AI-generated photography.

Use the actual small logo at bottom right (70–90 px width, 28 px margins), report omission if unavailable, and never invent a wordmark. Aesthetic judgments and automatic subject matching are not guaranteed by machine checks. The renderer, shared style validator, release gate, TikTok packaging and Make gates all enforce the same version. Publishing permissions and schedules remain unchanged.

## Facebook and YouTube

`.github/workflows/daily-carousel.yml` is scheduled daily at **02:00 Europe/Berlin**, alongside the independent WordPress job at **02:00 Europe/Berlin**. GitHub Actions can start scheduled runs late, so these are target trigger times rather than guaranteed publish minutes. It first requires today's verified editorial file; then renders the story’s 5–25 slides at exactly two seconds each into an H.264/AAC MP4, runs release QA, and saves `abasonplus-source-checked-video` as a GitHub Actions artifact for seven days. A scheduled run only sends the QA-passed video and its SHA-256 through the private `MAKE_WEBHOOK_URL`. A manual `workflow_dispatch` is **preview-only**.

Make scenario [7968544](https://eu1.make.com/3161815/scenarios/7968544) routes this video to YouTube upload and Facebook Pages Reel. Each platform has its own Europe/Berlin daily key and a check-before-reserve guard. A duplicate stops only its own branch. The new Facebook/YouTube/WordPress daily guards take effect on 2026-10-18; all three were already published on 2026-10-17, which is held during migration. The `review_approved` webhook field records this pre-authorized scheduled release after machine QA; it is not evidence of human review. A platform upload failure after its key is reserved needs inspection before retrying that same branch.

## Instagram

Instagram @abasonplus is connected through Zernio account `6ad380c8b835331ad1563a7a`. Make scenario 7968544 modules 17–23 receive the same QA-passed daily MP4 from the 02:00 Europe/Berlin GitHub workflow and publish it as a Reel with share-to-Feed enabled, the first frame as cover, and comments enabled. The original soundtrack remains embedded in the video.

The route checks caption length (1–2,200 characters), visual QA, style, SHA-256 shape and video presence. It checks the independent `abasonplus-instagram-YYYY-MM-DD` record using the Europe/Berlin date, sends the same key as the provider Idempotency-Key, and records accepted publication requests. Provider failure responses raise a Make error. Accepted/processing requests are not proof of publication; the daily audit checks the actual provider platform status and public URL. A failed or ambiguous request needs inspection before retrying.

The first complete transport/publication test reused the exact existing QA-passed artifact from run 39029928876; no new video was generated. Delivery run 39039712606 and Make execution b8523af132154e59a0320809b01834fd succeeded. Provider post `6ad38233fa35a96b9d6d9601` was read back as published on 2026-10-17 at 16:12 Europe/Berlin: https://www.instagram.com/reel/DemS0nVkciB/ . Its daily dedupe record was stored. Tomorrow's unattended run has not yet occurred.

The provider currently holds exactly two social accounts (TikTok and Instagram), within its published two-account free allowance. Do not add a third account or enable paid features. Existing Make/GitHub free limits still apply.

Read-only status checker scenario 8007397 accepts `path` with GET only. Use `/posts/<observed-id>` for output `data`, `/posts` for output `posts`, and `/accounts` for output `accounts`. Its default preserves the previous approved TikTok lookup. The scheduled publication audit includes Instagram.

## TikTok: review each exact video

The daily job also writes `tiktok_preview.json` and `tiktok_caption.txt` into the same artifact. It never publishes to TikTok on a schedule.

1. Run or inspect **AbasonPlus Daily Source-Checked Carousel & Video** and watch its completed MP4. Record the successful run ID for the exact video.
2. The repository owner starts **AbasonPlus TikTok – Publish One Reviewed Video** with that `preview_run_id`, the exact preview and post consent phrases, rights confirmation, public privacy selection, and individual true/false comment, Duet, and Stitch choices.
3. That workflow checks today's source, image typography, visual metadata, MP4 and caption; computes the file's SHA-256; then sends only that file to Make. Make checks the same-day key, SHA shape and consent fields, uploads temporary media, prevents a duplicate key, and submits the reviewed TikTok post. Confirm the resulting platform status and URL separately; webhook acceptance alone is not proof of publication.

The TikTok workflow has **no cron trigger**. Do not reuse an older video's approval for a new MP4. The previous first-video record is archival and grants no future consent.

## Setup and verification

Keep `MAKE_WEBHOOK_URL` in GitHub Actions secrets. Use **AbasonPlus Safe Code Validation** or a manual preview to check code without a social post. The signed-in Make connections for Facebook, YouTube and the TikTok posting provider must remain healthy. The daily source research task targets 00:30 Europe/Berlin and must create today's editorial JSON before the 02:00 Europe/Berlin video workflow; otherwise the video intentionally skips publication. The schedule can start late or be skipped by GitHub Actions, so verify actual publications in the daily audit.

The WordPress job uses Post by Email on the current free site without plugins. Keep all services within their free limits; the audit reports delivery failures and no paid plan may be activated. No step is allowed to purchase services or consume a paid trial. TikTok requires review and consent for each exact video; the general standing authorization does not turn that workflow into unattended scheduled posting.

Website: https://abasonplus.wordpress.com/


Timing correction (owner, 2026-10-18): every image is exactly 2 seconds, never 3 or 1.5. Multiple sentences per image are allowed; increase slide count as needed within the existing 50-second maximum. Dense text can be difficult to read in two seconds; do not mislabel readability as guaranteed.

## Five-platform operations
See AUTOMATION_OPERATIONS.md for the daily evidence report, narrow pre-delivery retry ceiling, mobile preview guides, freshness review, Free credit reserve and Sunday performance review. TikTok is included in monitoring but still requires exact-video review before uploading.

## Social copy and cover contract
config/engagement_rules.json locks hook, substantial useful captions/descriptions, one prepared first brand comment, at least five distinct relevant hashtags, the actual hook cover and only the owner-provided MP3. Packaging is verified before release. First-comment/custom-thumbnail writes are new configuration, not a claim of a successful live write; inspect destination results.
