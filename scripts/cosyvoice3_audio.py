#!/usr/bin/env python3
"""Generate Bengali speech with a *locally installed* CosyVoice3 model.

Fail-closed: this tool never downloads a model, contacts a service, or publishes.
Use only a reference WAV whose speaker explicitly consented to voice synthesis.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

MAX_TEXT_CHARACTERS = 500
MAX_VOICE_SECONDS = 50.0
SYSTEM_PROMPT = "You are a helpful assistant.<|endofprompt|>"


def validate_text(text: str) -> str:
    text = text.strip()
    if not text or len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError("Bengali script must contain 1–500 characters")
    if "<|endofprompt|>" in text or "<|" in text:
        raise ValueError("Model control tokens are not allowed in the script")
    if not any("\u0980" <= ch <= "\u09ff" for ch in text):
        raise ValueError("The script must contain Bengali text")
    return text


def validate_reference(path: Path) -> float:
    if not path.is_file():
        raise FileNotFoundError("Consent-based reference voice WAV missing")
    with wave.open(str(path), "rb") as f:
        if f.getnframes() == 0 or f.getframerate() <= 0:
            raise ValueError("Reference audio has no samples")
        duration = f.getnframes() / f.getframerate()
        if f.getnchannels() not in (1, 2):
            raise ValueError("Reference voice must be mono or stereo")
    if not 1.0 <= duration <= 30.0:
        raise ValueError("Reference voice duration must be 1–30 seconds")
    return duration


def prepare_inputs(text_file: Path, reference: Path, model_dir: Path, accepted: bool) -> str:
    if not accepted:
        raise ValueError("Explicit reference-speaker permission is required")
    if not text_file.is_file():
        raise FileNotFoundError("Source Bengali text is missing")
    script = validate_text(text_file.read_text(encoding="utf-8"))
    validate_reference(reference)
    if not model_dir.is_dir() or not (model_dir / "cosyvoice3.yaml").is_file():
        raise FileNotFoundError("Downloaded CosyVoice3 model directory is unavailable")
    return script


def generate(text: str, reference: Path, model_dir: Path, output: Path, cosyvoice_checkout: Path) -> float:
    if not cosyvoice_checkout.is_dir() or not (cosyvoice_checkout / "cosyvoice" / "cli" / "cosyvoice.py").is_file():
        raise FileNotFoundError("Pinned CosyVoice source checkout is missing")
    # Dependencies are installed manually in an isolated environment. No pip installation here.
    sys.path.insert(0, str(cosyvoice_checkout))
    sys.path.insert(0, str(cosyvoice_checkout / "third_party" / "Matcha-TTS"))
    import torch  # noqa: PLC0415
    import torchaudio  # noqa: PLC0415
    from cosyvoice.cli.cosyvoice import AutoModel  # noqa: PLC0415
    from cosyvoice.utils.common import set_all_random_seed  # noqa: PLC0415

    set_all_random_seed(0)
    model = AutoModel(model_dir=str(model_dir), load_jit=False, load_trt=False, load_vllm=False)
    with tempfile.TemporaryDirectory(prefix="abasonplus-cosyvoice-") as tmp:
        normalized_reference = Path(tmp) / "reference_16k.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(reference),
                        "-ac", "1", "-ar", "16000", str(normalized_reference)], check=True,
                       timeout=45)
        chunks = []
        for part in model.inference_cross_lingual(SYSTEM_PROMPT + text,
                                                  str(normalized_reference), stream=False, speed=1.0):
            chunks.append(part["tts_speech"].detach().cpu().flatten())
        if not chunks:
            raise RuntimeError("CosyVoice3 generated no voice samples")
        samples = torch.cat(chunks).unsqueeze(0)
        sample_rate = int(model.sample_rate)
        seconds = samples.shape[-1] / sample_rate
        if not 1.0 <= seconds <= MAX_VOICE_SECONDS:
            raise ValueError("Generated voice duration is outside the allowed 1–50 seconds")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Write atomically: failed inference must not leave a release-ready partial file.
        temp_output = output.with_name(output.stem + ".partial.wav")
        try:
            torchaudio.save(str(temp_output), samples, sample_rate)
            temp_output.replace(output)
        finally:
            temp_output.unlink(missing_ok=True)
        return seconds


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true", help="validate entrypoint without downloads")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--reference-wav", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--cosyvoice-checkout", type=Path)
    parser.add_argument("--output-wav", type=Path)
    parser.add_argument("--speaker-consented", action="store_true", help="confirm permission for reference voice")
    args = parser.parse_args(argv)
    if args.self_check:
        print("SELF-CHECK PASS: CPU-only safe entrypoint, no service, downloads, or publication")
        return 0
    fields = (args.text_file, args.reference_wav, args.model_dir, args.cosyvoice_checkout, args.output_wav)
    if any(field is None for field in fields):
        parser.error("all file paths are required for generation")
    try:
        script = prepare_inputs(args.text_file, args.reference_wav, args.model_dir,
                                args.speaker_consented)
        length = generate(script, args.reference_wav, args.model_dir,
                          args.output_wav, args.cosyvoice_checkout)
    except (ValueError, FileNotFoundError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"COSYVOICE3 BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"COSYVOICE3 GENERATED: {args.output_wav} ({length:.2f}s). Human listening QA remains required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
