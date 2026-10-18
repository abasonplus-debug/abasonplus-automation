"""Offline selector regression: normalize research attribution without weakening QA."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]

class PhotoSourceContract(unittest.TestCase):
    def run_selector(self, photos):
        today = datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
        source = "https://www.bssnews.net/others/435855"
        payload = {
            "date": today, "verified_on": today, "source_url": source,
            "content": '<p>Source <a href="' + source + '">news</a></p>',
            "story": {"source_url": source, "verified_on": today,
                      "hook": "আজকের প্রকল্প বিষয়ে কী যাচাই করবেন?",
                      "cover_query": "professional photograph of a modern road tunnel",
                      "tips": [{"text": "প্রকল্পের সরকারি নথি যাচাই করুন।", "query": "professional construction photograph"} for _ in range(4)],
                      "photos": photos}}
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "scripts").mkdir()
            (root / "content").mkdir()
            for name in ("select_video_story.py", "publication_policy.py"):
                (root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
            (root / "content" / ("daily_editorial_" + today + ".json")).write_text(json.dumps(payload))
            result = subprocess.run([sys.executable, str(root / "scripts/select_video_story.py")], capture_output=True, text=True)
            output = root / "output/daily_research_story.json"
            return result, json.loads(output.read_text()) if output.exists() else None

    def photos(self, key):
        return [{key: "https://www.pexels.com/photo/tunnel-" + str(i) + "/",
                 "url": "https://images.pexels.com/photos/" + str(i) + "/photo.jpeg",
                 "license": "Pexels Free License", "creator": "Fixture", "scene": "Road tunnel"} for i in range(5)]

    def test_research_source_page_normalized_for_renderer(self):
        result, story = self.run_selector(self.photos("source_page"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(p["source"] == p["source_page"] for p in story["photos"]))

    def test_legacy_source_still_supported(self):
        result, story = self.run_selector(self.photos("source"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(story["photos"][0]["source"], self.photos("source")[0]["source"])

    def test_conflicting_attributions_rejected(self):
        photos = self.photos("source")
        photos[0]["source_page"] = "https://www.pexels.com/photo/different/"
        result, story = self.run_selector(photos)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Conflicting photographic source", result.stderr)
        self.assertIsNone(story)

    def test_missing_or_wrong_source_and_license_rejected(self):
        for field, value in (("source_page", ""), ("source_page", "https://example.org/photo/test/"), ("license", "Unknown")):
            with self.subTest(field=field, value=value):
                photos = self.photos("source_page")
                photos[0][field] = value
                result, story = self.run_selector(photos)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(story)

if __name__ == "__main__":
    unittest.main()
