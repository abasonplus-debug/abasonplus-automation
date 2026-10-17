# AbasonPlus video automation

Bangla housing-information carousel, Facebook Reel, YouTube Short, and creator-reviewed TikTok video. Source: a fresh, cited `content/daily_editorial_YYYY-MM-DD.json` for the current Asia/Dhaka date. Without that file, the daily workflow skips the video.

## Each carousel image: locked visual direction

Apply these directions independently to the hook and all four tips. The `text` and `query` fields in the daily editorial brief are the slide-specific copy and matching photographic subject.

1. Use a distinct, relevant, rights-checked real photograph filling a **1080 × 1920** portrait frame. The scene must match that slide's `query`; never imply a stock photograph depicts a specific real project. Record photo source and license.
2. Place that slide's exact Bengali `text` directly over naturally light space in the image, in the upper portion. Prefer two lines; allow up to three only if needed. Use Noto Sans Bengali Bold at **120 px or larger**, with a real Latin bold fallback where English words occur. Keep the text large, dark navy `#061B3E`, about 90% opacity.
3. Use **no text box, border, stroke, shadow, gradient, or dark overlay**. Every headline line needs its own measured light/contrast check against the photograph. If no relevant licensed photo passes, stop the release instead of shrinking the type or using an unrelated picture.
4. A logo, if available, is small in the **bottom-right corner**. Make each slide a separate frame; never reuse a photo or silently replace the owner's music.

The source, exact text, photo brief, license, 120 px minimum, line contrast, glyph support, MP4 dimensions, music, and duration are release checks in `scripts/create_carousel.py` and `scripts/verify_video_release.py`. Machine semantic screening is a heuristic, not a human aesthetic review.

## Facebook and YouTube

`.github/workflows/daily-carousel.yml` is scheduled daily at **08:45 Europe/Berlin**, after the WordPress job at **08:20 Europe/Berlin**. GitHub Actions can start scheduled runs late, so these are target trigger times rather than guaranteed publish minutes. It first requires today's verified editorial file; then renders five slides and a 15-second H.264/AAC MP4, runs release QA, and saves `abasonplus-source-checked-video` as a GitHub Actions artifact for seven days. A scheduled run only sends the QA-passed video and its SHA-256 through the private `MAKE_WEBHOOK_URL`. A manual `workflow_dispatch` is **preview-only**.

Make scenario [7968544](https://eu1.make.com/3161815/scenarios/7968544) routes this video to YouTube upload and Facebook Pages Reel. Each branch has its own SHA-256 duplicate key, so one platform's key does not suppress the other's route. The `review_approved` webhook field records this pre-authorized scheduled release after machine QA; it is not evidence of human review. A platform upload failure after its key is reserved needs inspection before retrying that same branch.

## TikTok: review each exact video

The daily job also writes `tiktok_preview.json` and `tiktok_caption.txt` into the same artifact. It never publishes to TikTok on a schedule.

1. Run or inspect **AbasonPlus Daily Source-Checked Carousel & Video** and watch its completed MP4. Record the successful run ID for the exact video.
2. The repository owner starts **AbasonPlus TikTok – Publish One Reviewed Video** with that `preview_run_id`, the exact preview and post consent phrases, rights confirmation, public privacy selection, and individual true/false comment, Duet, and Stitch choices.
3. That workflow checks today's source, image typography, visual metadata, MP4 and caption; computes the file's SHA-256; then sends only that file to Make. Make checks the same-day key, SHA shape and consent fields, uploads temporary media, prevents a duplicate key, and submits the reviewed TikTok post. Confirm the resulting platform status and URL separately; webhook acceptance alone is not proof of publication.

The TikTok workflow has **no cron trigger**. Do not reuse an older video's approval for a new MP4. The previous first-video record is archival and grants no future consent.

## Setup and verification

Keep `MAKE_WEBHOOK_URL` in GitHub Actions secrets. Use **AbasonPlus Safe Code Validation** or a manual preview to check code without a social post. The signed-in Make connections for Facebook, YouTube and the TikTok posting provider must remain healthy. The daily source research task targets 05:00 Europe/Berlin and must create today's editorial JSON before the 08:45 Europe/Berlin video workflow; otherwise the video intentionally skips publication. The schedule can start late or be skipped by GitHub Actions, so verify actual publications in the daily audit.

The WordPress job currently uses Post by Email through Make. If WordPress.com or the mail service stops accepting that feature on the free site, the job fails closed and the daily audit reports the failure; do not activate a paid plan. No step is allowed to purchase services or consume a paid trial. TikTok requires review and consent for each exact video; the general standing authorization does not turn that workflow into unattended scheduled posting.

Website: https://abasonplus.wordpress.com/
