#!/usr/bin/env python3
"""Narrate EXACT carousel slide text with the owner-selected Dan Mason CosyVoice3 voice.

Free public Space + CC0 voice reference only. No paid API, fallback synthetic speech,
secret, post/upload, or account connection. A synthesis or duration failure blocks release.
Slide duration follows complete spoken text, without a fixed maximum video length.
"""
from __future__ import annotations
from array import array
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import json
import math
import os
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
CONFIG = ROOT / "config" / "cosyvoice3_selected_voice.json"
REFERENCE_URL = "https://raw.githubusercontent.com/CoisLR/TTS-Reference-Voices/main/voices/dan_mason.flac"
SPACE = "kawshikbuet17/bengali-cosyvoice3-tts-demo"
MODEL_ENDPOINT = "/generate_cross_lingual_audio"
SAMPLE_RATE = 24000
MIN_SLIDE_SECONDS = 3
VOICE_GAIN = 1.0
MUSIC_GAIN = 0.20

def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("COSYVOICE3_RELEASE_BLOCKED: " + message)

def run(command, timeout=120):
    try:
        return subprocess.run(command, check=True, timeout=timeout,
                              capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("FFmpeg/tool failed: " + (exc.stderr or exc.stdout or "")[-2500:]) from exc

def probe_duration(filename: Path) -> float:
    raw = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(filename)], 25).stdout.strip()
    seconds = float(raw)
    check(math.isfinite(seconds) and seconds > 0, "invalid media duration")
    return seconds

def source_texts(story: dict) -> list[str]:
    check(isinstance(story, dict), "no daily story")
    tips = story.get("tips")
    check(isinstance(tips, list) and 4 <= len(tips) <= 15,
          "invalid number of narrated slides")
    texts = [story.get("hook")] + [tip.get("text") for tip in tips]
    check(all(isinstance(t, str) and t.strip() and t == t.strip()
              and 8 <= len(t) <= 500 for t in texts),
          "all slide texts must be literal, nonempty Bengali script")
    check(all(any("\u0980" <= c <= "\u09ff" for c in t) for t in texts),
          "a slide contains no Bengali text")
    return texts

def slide_durations(audio_durations: list[float]) -> list[float]:
    check(5 <= len(audio_durations) <= 16, "outside owner slide count limits")
    durations = []
    for seconds in audio_durations:
        check(isinstance(seconds, (float, int)) and math.isfinite(seconds)
              and seconds >= 0.55, "incomplete or abnormal TTS segment")
        # 0.30 seconds silence at end. Round up to 30fps frame boundary.
        frames = max(90, math.ceil((seconds + 0.30) * 30))
        durations.append(round(frames / 30, 6))
    return durations

def get_reference(target: Path) -> None:
    raw = target / "dan_mason_cc0.flac"
    wav = target / "dan_mason_cc0_reference.wav"
    req = Request(REFERENCE_URL, headers={"User-Agent": "AbasonPlus-CosyVoice3-CC0-Only/1.0"})
    with urlopen(req, timeout=30) as response:
        check(response.status == 200, "voice reference download rejected")
        content = response.read(3_000_001)
    check(3000 < len(content) <= 3_000_000, "missing or oversized CC0 reference")
    raw.write_bytes(content)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw),
         "-t", "8", "-ar", "16000", "-ac", "1", str(wav)], 30)
    with wave.open(str(wav), "rb") as ref:
        duration = ref.getnframes() / ref.getframerate()
        check(2 <= duration <= 8.1 and ref.getnchannels() == 1 and
              ref.getframerate() == 16000, "reference audio validation failed")
    return wav

def validate_segment(path: Path) -> float:
    with wave.open(str(path), "rb") as f:
        check(f.getnchannels() == 1 and f.getsampwidth() == 2 and
              f.getframerate() == SAMPLE_RATE, "speech is not PCM16/mono/24k")
        duration = f.getnframes() / SAMPLE_RATE
        check(duration >= 0.55, "speech missing or implausibly short")
        frames = f.readframes(f.getnframes())
    samples = array("h")
    samples.frombytes(frames)
    check(len(samples) > 10000, "no usable speech samples")
    # Reject silent or almost-silent server responses; this is not linguistic QA.
    peak = max(abs(v) for v in samples)
    check(peak >= 300, "speech is silent or too faint")
    return duration

def concat_with_padding(files: list[Path], durations: list[float], output: Path) -> None:
    check(len(files) == len(durations), "voice and slide count mismatch")
    with wave.open(str(output), "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(2)
        dst.setframerate(SAMPLE_RATE)
        for audio, length in zip(files, durations):
            with wave.open(str(audio), "rb") as src:
                frames = src.readframes(src.getnframes())
            target_frames = round(length * SAMPLE_RATE)
            got_frames = len(frames) // 2
            check(got_frames + round(0.15 * SAMPLE_RATE) <= target_frames,
                  "voice would be cut when slide advances")
            dst.writeframesraw(frames + bytes((target_frames-got_frames)*2))
        dst.writeframes(b"")
    check(abs(validate_segment(output) - sum(durations)) < .003,
          "narration concatenation duration mismatch")

def write_slides_playlist(count: int, durations: list[float], dest: Path) -> None:
    check(count == len(durations), "slide playlist count differs from speech")
    value = "".join(f"file 'slide_{i}.png'\nduration {durations[i]:.6f}\n"
                    for i in range(count))
    value += f"file 'slide_{count-1}.png'\n"
    dest.write_text(value, encoding="utf-8")

def render_with_narration(voice_track: Path, music: Path, durations: list[float],
                          target: Path) -> float:
    duration = sum(durations)
    check(music.is_file() and music.stat().st_size > 1000,
          "owner's original music not found")
    check(voice_track.is_file(), "original CosyVoice3 narration track missing")
    playlist = target.parent / "narrated_slides.txt"
    write_slides_playlist(len(durations), durations, playlist)
    # Explicit linear gains: narration at unity (100%), original music at 0.20 (20%).
    # normalize=0 prevents amix from unexpectedly halving the voice.
    # The limiter avoids digital clipping if the mastered music and voice peaks coincide.
    filters = (f"[1:a]aresample=24000,volume={VOICE_GAIN:.2f}[spoken];"
               f"[2:a]aresample=24000,volume={MUSIC_GAIN:.2f}[bed];"
               f"[spoken][bed]amix=inputs=2:duration=first:"
               f"dropout_transition=0:normalize=0,"
               f"alimiter=limit=0.98,"
               f"afade=t=out:st={max(0,duration-0.35):.3f}:d=0.35[mixed]")
    candidate = target.parent / "voiced_candidate.mp4"
    candidate.unlink(missing_ok=True)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(playlist),
         "-i", str(voice_track), "-stream_loop", "-1", "-i", str(music),
         "-filter_complex", filters, "-map", "0:v:0", "-map", "[mixed]",
         "-t", f"{duration:.6f}", "-r", "30", "-vf", "fps=30,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         str(candidate)], max(270, int(duration * 8 + 120)))
    check(candidate.is_file() and candidate.stat().st_size > 500_000,
          "narrated video missing or incomplete")
    # Deliberately do not cap duration to fit Make's 5MB free webhook.
    # The scheduled upload checks the free-plan size separately and must block
    # delivery without spending money if the transport rejects the large file.
    checked = probe_duration(candidate)
    check(abs(checked - duration) < .15, "rendered video out of sync with voice")
    ffinfo = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                             "-of", "json", str(candidate)], 25).stdout)
    check(any(x.get("codec_type") == "video" and x.get("codec_name") == "h264"
              for x in ffinfo.get("streams", [])), "rendered H264 video missing")
    check(any(x.get("codec_type") == "audio" and x.get("codec_name") == "aac"
              for x in ffinfo.get("streams", [])), "mixed AAC audio missing")
    os.replace(candidate, target)
    return checked

def verify_voiceover(out: Path, story: dict, metadata: dict) -> None:
    from carousel_timing import validate_timing
    texts = source_texts(story)
    report = json.loads((out / "voiceover_manifest.json").read_text(encoding="utf-8"))
    voice = metadata.get("voiceover")
    check(isinstance(voice, dict) and voice.get("engine") == "CosyVoice3"
          and voice.get("reference") == "Dan Mason" and voice.get("complete") is True,
          "not using the owner-selected real CosyVoice3 voice")
    check(voice.get("reference_url") == REFERENCE_URL and
          report.get("source_url") == story.get("source_url") and
          report.get("verified_on") == story.get("verified_on"),
          "voice source provenance mismatch")
    check(report.get("model") == SPACE and report.get("reference_url") == REFERENCE_URL,
          "unapproved TTS backend or reference voice")
    parts = report.get("segments")
    check(isinstance(parts, list) and len(parts) == len(texts), "not every slide was narrated")
    durations = []
    for i, (text, part) in enumerate(zip(texts, parts)):
        check(part.get("slide") == i + 1 and part.get("text_sha256") ==
              sha256(text.encode("utf-8")).hexdigest(), "narration does not match visible slide text")
        file = out / "narration_segments" / f"slide_{i:02}.wav"
        check(file.is_file() and sha256(file.read_bytes()).hexdigest() ==
              part.get("audio_sha256"), "narration segment missing or altered")
        duration = validate_segment(file)
        check(abs(duration - float(part["seconds"])) < .015,
              "narration duration not verified")
        durations.append(duration)
    check(slide_durations(durations) == metadata.get("slide_durations"),
          "slide timing not derived from full speech")
    narration = out / "cosyvoice3_narration.wav"
    check(narration.is_file(), "combined voice track missing")
    combined = validate_segment(narration)
    check(abs(combined - sum(metadata["slide_durations"])) < .02,
          "narration and slides not synchronized")
    validate_timing(metadata)
    check(voice.get("script_sha256") ==
          sha256("\n".join(texts).encode("utf-8")).hexdigest(),
          "narration script proof invalid")

def main() -> None:
    from gradio_client import Client, handle_file
    from carousel_timing import validate_timing
    OUT.mkdir(exist_ok=True)
    story = json.loads((OUT/"daily_research_story.json").read_text(encoding="utf-8"))
    meta_file = OUT/"metadata.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    texts = source_texts(story)
    check(meta.get("slides") == len(texts), "daily story and rendered slides differ")
    check(meta.get("source_url") == story.get("source_url") and
          meta.get("verified_on") == story.get("verified_on"),
          "stale or different visual narration source")
    today = datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
    check(meta.get("date") == today and story.get("verified_on") == today,
          "not a freshly verified story")
    preset = json.loads(CONFIG.read_text(encoding="utf-8"))
    check(preset.get("reference_source_url") == REFERENCE_URL and
          preset.get("engine") == "CosyVoice3" and
          preset.get("reference_voice") == "Dan Mason" and
          preset.get("free_only") is True, "voice preset not owner approved")
    for i in range(len(texts)):
        check((OUT/f"slide_{i}.png").is_file(), "slide image unavailable before narration")
    temp = OUT / "narration_segments"
    temp.mkdir(exist_ok=True)
    ref = get_reference(temp)
    client = Client(SPACE, verbose=False)
    files = []
    durations = []
    for i, text in enumerate(texts):
        # Public demo has no SLA. Any timeout, quota or failure => NO publication.
        print(f"CosyVoice3 owner-selected male speech {i+1}/{len(texts)}", flush=True)
        result = client.predict(text, handle_file(str(ref)), 0, 1.0,
                                api_name=MODEL_ENDPOINT)
        value = result[0] if isinstance(result, (list, tuple)) else result
        model_audio = (value.get("path") or value.get("name")) if isinstance(value, dict) else value
        check(isinstance(model_audio, str) and Path(model_audio).is_file(),
              f"no real CosyVoice3 result for slide {i+1}")
        dest = temp/f"slide_{i:02}.wav"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(model_audio), "-ac", "1", "-ar", "24000",
             "-c:a", "pcm_s16le", str(dest)], 50)
        durations.append(validate_segment(dest))
        files.append(dest)
        slide_durations(durations + [0.55]*(len(texts)-len(durations)))
    display_times = slide_durations(durations)
    narration = OUT/"cosyvoice3_narration.wav"
    concat_with_padding(files, display_times, narration)
    segments = [
        {"slide": i+1,
         "text_sha256": sha256(texts[i].encode("utf-8")).hexdigest(),
         "audio_sha256": sha256(files[i].read_bytes()).hexdigest(),
         "seconds": round(durations[i], 6)}
        for i in range(len(texts))
    ]
    manifest = {"engine": "CosyVoice3", "model": SPACE, "reference": "Dan Mason",
                "reference_url": REFERENCE_URL, "source_url": story["source_url"],
                "verified_on": story["verified_on"], "segments": segments}
    (OUT/"voiceover_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    duration = render_with_narration(narration, ROOT/"assets"/"abasonplus.mp3",
                                      display_times, OUT/"abasonplus_daily.mp4")
    meta["slide_durations"] = display_times
    meta["voiceover"] = {
        "engine": "CosyVoice3", "reference": "Dan Mason",
        "reference_url": REFERENCE_URL, "complete": True,
        "script_sha256": sha256("\n".join(texts).encode("utf-8")).hexdigest(),
        "mix": "narration_100_music_20_no_amix_normalization",
        "voice_gain": VOICE_GAIN,
        "music_gain": MUSIC_GAIN,
        "narrated_slide_count": len(texts)}
    validate_timing(meta, duration)
    verify_voiceover(OUT, story, meta)
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    print(f"COSYVOICE3_DAILY_VOICE_SUCCESS {len(texts)} slides, {duration:.2f}s, "
          f"{(OUT/'abasonplus_daily.mp4').stat().st_size} bytes; NO POSTS", flush=True)

if __name__ == "__main__":
    main()
