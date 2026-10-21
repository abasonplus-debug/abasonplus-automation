"""Offline CI tests. Never download or invoke a speech model."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cosyvoice3_audio", ROOT / "scripts" / "cosyvoice3_audio.py")
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


class VoicePreflightTests(unittest.TestCase):
    def test_short_bengali_text_is_accepted(self):
        self.assertEqual(voice.validate_text("  শুভ সকাল, বাংলাদেশ। "), "শুভ সকাল, বাংলাদেশ।")

    def test_empty_and_long_scripts_rejected(self):
        for s in ("", " " * 7, "বাংলা" * 130, "hello"):
            with self.subTest(s=s[:10]), self.assertRaises(ValueError):
                voice.validate_text(s)

    def test_model_control_tokens_rejected(self):
        with self.assertRaises(ValueError):
            voice.validate_text("বাংলা <|endofprompt|> এখানে")

    def test_unconsented_reference_is_rejected_before_loading(self):
        with self.assertRaisesRegex(ValueError, "permission"):
            voice.prepare_inputs(Path("/absent"), Path("/absent"), Path("/absent"), False)

    def test_reference_duration_and_no_model(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            example = root / "reference.wav"
            with wave.open(str(example), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(b"\x00\x00" * 16000)
            self.assertEqual(voice.validate_reference(example), 1.0)
            story = root / "story.txt"
            story.write_text("আজকের খবর", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "model"):
                voice.prepare_inputs(story, example, root, True)


if __name__ == "__main__":
    unittest.main()
