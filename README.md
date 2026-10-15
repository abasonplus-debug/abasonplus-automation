# AbasonPlus Automation

Automated Bengali housing-information carousel generation using GitHub Actions, Python, Pillow, Noto Bengali fonts and FFmpeg.

- Runs daily at 03:15 UTC (09:15 Bangladesh time), or manually through Actions → AbasonPlus Daily Carousel → Run workflow.
- Produces a 15-second vertical MP4 (1080×1920, five slides, three seconds each).
- Saves the video as a downloadable Actions artifact for seven days. No WordPress or Google Drive video storage.
- Optional Make integration: repository Actions secret `MAKE_WEBHOOK_URL` sends the MP4 as multipart field `video` to a Make webhook. Configure and verify the Make receiver before enabling this secret.
- Uses rotating evergreen educational topics, not real-time news.
- No paid video rendering API required. Free plan usage limits still apply.

Website: https://abasonplus.wordpress.com/
