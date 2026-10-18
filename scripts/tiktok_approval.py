"""Exact-video consent reconciliation. Offline; never grants future consent."""
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import re

ACCOUNT = "6ad22ddb280aa6cf7d25310d"

def validate_approval(approval, day, video_sha256=None, caption=None, preview_run_id=None):
    if approval.get("date") != day:
        raise ValueError("Approval date mismatch")
    stamp = datetime.fromisoformat(approval["approved_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.astimezone(ZoneInfo("Europe/Berlin")).date().isoformat() != day:
        raise ValueError("Approval timestamp mismatch")
    digest = approval.get("video_sha256", "")
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Missing exact video digest")
    if video_sha256 is not None and digest != video_sha256:
        raise ValueError("Different approved video")
    if preview_run_id is not None and str(approval.get("preview_run_id")) != str(preview_run_id):
        raise ValueError("Different approved artifact run")
    if not re.fullmatch(r"[a-f0-9]{64}", approval.get("caption_sha256", "")):
        raise ValueError("Missing exact caption digest")
    if not approval.get("approval") or not approval.get("consent_scope"):
        raise ValueError("Missing owner consent evidence")
    if approval.get("account_id") != ACCOUNT or approval.get("account_username") != "abasonplus":
        raise ValueError("Wrong TikTok account")
    if approval.get("privacy_level") != "PUBLIC_TO_EVERYONE":
        raise ValueError("Privacy changed")
    if any(type(approval.get(k)) is not bool for k in ("allow_comment", "allow_duet", "allow_stitch")):
        raise ValueError("Interaction choice missing")
    if caption is not None:
        digest = hashlib.sha256(caption.strip().encode("utf-8")).hexdigest()
        if approval.get("caption_sha256") != digest:
            raise ValueError("Caption changed since approval")
    return True

def reconcile(snapshot, approval, publication):
    """Return a corrected copy only when approval and actual publication match."""
    import copy
    result = copy.deepcopy(snapshot)
    day = result["checked_at"][:10]
    validate_approval(approval, day)
    if (publication.get("date") != day or publication.get("video_sha256") != approval["video_sha256"]
        or publication.get("account_id") != ACCOUNT or publication.get("status") != "published"
        or publication.get("platform_status") != "published"
        or publication.get("verification") != "account-specific provider readback"):
        raise ValueError("Approval/publication identity mismatch")
    approved_at = datetime.fromisoformat(approval["approved_at"].replace("Z", "+00:00"))
    published_at = datetime.fromisoformat(publication["published_at"].replace("Z", "+00:00"))
    if published_at.tzinfo is None or published_at < approved_at or published_at.astimezone(ZoneInfo("Europe/Berlin")).date().isoformat() != day:
        raise ValueError("Consent must precede this day's publication")
    if publication.get("caption_sha256") != approval["caption_sha256"]:
        raise ValueError("Published caption mismatch")
    for key in ("privacy", "comments", "duet", "stitch"):
        expected = approval[{"privacy":"privacy_level","comments":"allow_comment","duet":"allow_duet","stitch":"allow_stitch"}[key]]
        if publication.get(key) != expected:
            raise ValueError("Published settings mismatch")
    rows = [r for r in result.get("evidence", []) if r.get("platform") == "tiktok"
            and str(r.get("post_id")) == str(publication.get("post_id"))
            and r.get("url") == publication.get("url") and r.get("status") == "published"
            and r.get("identity_matched") is True]
    if not rows:
        raise ValueError("No matching publication evidence")
    result.setdefault("context", {})["exact_tiktok_video_approved"] = True
    quality = result.setdefault("quality", {})
    quality["findings"] = [f for f in quality.get("findings", [])
                           if not ("No matching exact-video owner approval" in f)]
    note = "Exact-video owner OK reconciled against dated approval and publication records; preview false flags describe the earlier pre-approval state."
    if note not in quality["findings"]: quality["findings"].append(note)
    if quality.get("status") == "machine_qa_passed_with_tiktok_consent_provenance_mismatch":
        quality["status"] = "machine_qa_passed"
    result["consent_evidence"] = {"approval_file":"audits/tiktok-approvals/"+day+".json",
                                 "publication_file":"audits/tiktok-publications/"+day+".json",
                                 "video_sha256":approval["video_sha256"]}
    return result
