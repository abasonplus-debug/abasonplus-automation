# AbasonPlus: CosyVoice3 Bengali TTS — isolated preview experiment

**NOT PRODUCTION READY. Do not merge or enable daily publishing until real Bengali listening QA passes.**

## Non-negotiable safeguards

- 100% zero-payment only. Uses no paid runners, GPU rental, free trials, paid API, or recurring subscriptions.
- This branch's workflow is **manual only** and never runs when the daily carousel runs.
- No extra credentials, MP3 uploads, paid service calls, or auto-posting are used.
- Never clone any real person's voice without express permission from the speaker.
- Do not commit someone's voice to this **public** repository without their informed agreement to public redistribution; use a private local folder instead.
- The official Bengali CosyVoice3 model is around **9.75 GB** and its demo uses a CUDA-based build. Feasibility on a 4-CPU/16 GB RAM standard GitHub-hosted runner with 14 GB disk is **NOT TESTED** and may be infeasible. The manual workflow only validates the code's safety gates and does not download the model.

## Read-only/zero-cost check

1. From this experiment branch, run `.github/workflows/cosyvoice3-safe-preview.yml` manually.
2. It runs a Python self-check and tests only. Nothing is uploaded, downloaded, or published by the TTS scripts.

## Manual local inference (only after independent setup)

Requirements: a locally installed, compatible CosyVoice checkout and Bengali model, Python `torch`/`torchaudio`, `ffmpeg`/`ffprobe`, and an explicitly permissioned 1–30 second WAV voice sample. The owner must obtain that permission first. Use the model author's official setup instructions and inspect upstream dependency licenses; do not pay for GPU or storage.

```bash
python3 scripts/cosyvoice3_audio.py \
  --text-file path/to/bengali_script.txt \
  --reference-wav /private/consented_reference.wav \
  --speaker-consented \
  --model-dir /models/bengali-cosyvoice3-tts \
  --cosyvoice-checkout /local/CosyVoice \
  --output-wav output/cosyvoice3_bangla.wav

python3 scripts/mix_cosyvoice3_audio.py \
  --video output/abasonplus_daily.mp4 \
  --speech output/cosyvoice3_bangla.wav \
  --output output/abasonplus_daily_voiced_preview.mp4
```

The mix command keeps the original music low, keeps the video timing, checks MP4 length, and blocks output over 5,000,000 bytes. It never overwrites the original video and never posts anything.

## Blocking production requirements

- One **legitimately permissioned** reference voice, provided once, stored outside public GitHub.
- Offline local model dependencies and disk/memory feasibility demonstrated on **standard free** GitHub runner, not GPU or larger runner.
- A real spoken Bengali WAV and mixed MP4 exported and listened to by a human.
- Final audio duration and spoken words fit 3 seconds per slide or the script is shortened with owner's approval.
- Human voice quality QA, video regression QA, and explicit owner approval **before** enabling automatic daily use.

Models: <https://huggingface.co/kawshikbuet17/bengali-cosyvoice3-tts>; demo source: <https://huggingface.co/spaces/kawshikbuet17/bengali-cosyvoice3-tts-demo/tree/main>.
