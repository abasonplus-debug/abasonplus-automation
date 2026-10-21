#!/usr/bin/env python3
"""Mix approved generated voice with the original music from an existing MP4.

Never overwrites the source video. Does not publish, post, or transmit data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

MAX_VIDEO_SECONDS = 50
MAX_MAKE_BYTES = 5_000_000


def probe(filename: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type",
        "-of", "json", str(filename)], timeout=20))


def validate_media(video: Path, speech: Path) -> float:
    if not video.is_file() or not speech.is_file():
        raise FileNotFoundError("Existing MP4 and generated WAV are both required")
    v, s = probe(video), probe(speech)
    if not any(track.get("codec_type") == "video" for track in v.get("streams", [])):
        raise ValueError("Original video stream is missing")
    if not any(track.get("codec_type") == "audio" for track in v.get("streams", [])):
        raise ValueError("Original background music is missing")
    if not any(track.get("codec_type") == "audio" for track in s.get("streams", [])):
        raise ValueError("Generated voice audio is missing")
    video_sec = float(v["format"]["duration"])
    speech_sec = float(s["format"]["duration"])
    if not 1 <= speech_sec <= video_sec + 0.15:
        raise ValueError("Voice longer than the video: shorten the script, do not cut words")
    if not 1 <= video_sec <= MAX_VIDEO_SECONDS:
        raise ValueError("Video duration must be 1–50 seconds")
    return video_sec


def mix(video: Path, speech: Path, output: Path) -> None:
    duration = validate_media(video, speech)
    if output.resolve() == video.resolve():
        raise ValueError("Original MP4 must never be overwritten")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="abasonplus-audio-") as tmp:
        tmp_out = Path(tmp) / "mixed.mp4"
        mix_filter = "[0:a]volume=0.12[bg];[1:a]volume=1.0[voice];[bg][voice]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(video),
                        "-i", str(speech), "-filter_complex", mix_filter,
                        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "96k", "-t", str(duration), "-movflags", "+faststart",
                        str(tmp_out)], check=True, timeout=180)
        check = probe(tmp_out)
        if abs(float(check["format"]["duration"]) - duration) > 0.20:
            raise RuntimeError("Output MP4 duration changed unexpectedly")
        if tmp_out.stat().st_size > MAX_MAKE_BYTES:
            raise RuntimeError("Mixed video exceeds existing Make webhook free-plan 5MB limit")
        tmp_out.replace(output)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--speech", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mix(args.video, args.speech, args.output)
    except (ValueError, FileNotFoundError, RuntimeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print(f"AUDIO MIX BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"MIXED PREVIEW CREATED: {args.output}. No posting performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
