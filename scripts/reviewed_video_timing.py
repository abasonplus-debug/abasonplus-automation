"""Check a reviewed artifact against its immutable render-time timing policy."""
import ast
from datetime import datetime
from zoneinfo import ZoneInfo

TIMING_UPDATED_AT = datetime.fromisoformat("2026-10-20T00:31:03+00:00")

def validate_reviewed_timing(meta, duration, approval, source_run, source_policy):
    if (str(source_run.get("id")) != str(approval.get("preview_run_id"))
            or source_run.get("head_sha") != approval.get("preview_head_sha")
            or not approval.get("preview_head_sha")
            or source_run.get("conclusion") != "success"
            or source_run.get("head_branch") != "main"):
        raise ValueError("Reviewed timing: source run/commit does not match approval")
    created = datetime.fromisoformat(source_run["created_at"].replace("Z", "+00:00"))
    if (created.tzinfo is None
            or created.astimezone(ZoneInfo("Europe/Berlin")).date().isoformat() != approval["date"]):
        raise ValueError("Reviewed timing: source run is not from the approved Berlin date")
    voice = meta.get('voiceover')
    if isinstance(voice, dict) and voice.get('complete') is True:
        # The immutable render-time source must actually support CosyVoice3 timing.
        constants = {n.value for n in ast.walk(ast.parse(source_policy)) if isinstance(n, ast.Constant) and isinstance(n.value,str)}
        if 'CosyVoice3' not in constants:
            raise ValueError('Source policy did not support narrated video')
        expected = approval.get('format', {})
        if (expected.get('voiceover') != voice or expected.get('slide_durations') != meta.get('slide_durations')
                or expected.get('slides') != meta.get('slides')):
            raise ValueError('Exact narrated timing/voice differs from owner approval')
        try:
            from .carousel_timing import validate_timing
        except ImportError:
            from carousel_timing import validate_timing
        return validate_timing(meta, duration)
    values = [node.value.value for node in ast.parse(source_policy).body
              if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
              and any(isinstance(t, ast.Name) and t.id == "SLIDE_SECONDS" for t in node.targets)]
    if len(values) != 1 or type(values[0]) is not int or values[0] not in (2, 3):
        raise ValueError("Reviewed timing: unsupported source timing policy")
    seconds = values[0]
    if seconds == 2 and created >= TIMING_UPDATED_AT:
        raise ValueError("Reviewed timing: two-second exception is historical only")
    count = meta.get("slides")
    expected = approval.get("format", {})
    if (type(count) is not int or not 5 <= count <= 50 // seconds
            or meta.get("slide_seconds") != seconds
            or meta.get("slide_durations") != [seconds] * count
            or expected.get("slide_seconds") != seconds
            or expected.get("slides") != count
            or abs(float(duration) - count * seconds) > 0.12):
        raise ValueError("Reviewed timing: MP4, metadata or approved timing mismatch")
    return count * seconds
