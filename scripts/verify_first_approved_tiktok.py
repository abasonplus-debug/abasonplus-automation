#!/usr/bin/env python3
"""Strict verification of ONE specifically owner-reviewed TikTok video.

This is read-only. It never calls Make, Zernio or TikTok. A GitHub workflow
may deliver only after a separate production-route gate is enabled by a
successful Zernio creator-compliant connection test.
"""
from datetime import date
from hashlib import sha256
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]
ART=ROOT/"output"
CONSENT=ROOT/"config"/"tiktok_first_approved_2026-10-16.json"
GATE=ROOT/"config"/"tiktok_publication_gate.json"

def need(test,msg):
    if not test: raise RuntimeError("BLOCK TIKTOK PUBLICATION: "+msg)

def sha(filepath):
    return sha256(filepath.read_bytes()).hexdigest()

def main():
    c=json.loads(CONSENT.read_text(encoding="utf-8"))
    gate=json.loads(GATE.read_text(encoding="utf-8"))
    need(c["account_handle"]=="@abasonplus" and
         c["account_id"]=="6ad22ddb280aa6cf7d25310d","target not recognized")
    need(c["content_key"]=="abasonplus-tiktok-2026-10-16","wrong video content key")
    need(c["preview_run_id"]==38923421174,"unreviewed GitHub preview")
    need(c["privacy_level"]=="PUBLIC_TO_EVERYONE","public privacy was not selected")
    need(all(c[x] is True for x in (
       "allow_comment","allow_duet","allow_stitch","content_preview_confirmed",
       "express_consent_given","media_music_rights_confirmed")),"missing consent or music ownership")
    need(c["auto_publish_future_videos"] is False,"approval must be for one video only")
    need(c["ai_generated_visual_disclosure"] is True,"AI disclosure must remain")
    need(c["commercial_content_type"]=="none","commercial disclosure not verified")
    need(date.fromisoformat(c["source_date"])<=date.today(),"future source date")
    need((date.today()-date.fromisoformat(c["source_date"])).days<=7,
         "old approved video: requires new creator review")
    require_enabled=c.get("delivery_enabled") is True and gate.get("enabled") is True
    need(require_enabled,"production route is not yet verified and enabled")
    for file,checksum_key in (("abasonplus_daily.mp4","video_sha256"),
                              ("thumbnail.png","thumbnail_sha256"),
                              ("tiktok_caption.txt","caption_sha256")):
        p=ART/file
        need(p.is_file() and sha(p)==c[checksum_key],f"reviewed file mismatch: {file}")
    m=json.loads((ART/"metadata.json").read_text(encoding="utf-8"))
    t=json.loads((ART/"tiktok_preview.json").read_text(encoding="utf-8"))
    need(m["source_url"]==c["source_url"]==t["source_url"],"source changed since review")
    need(m["date"]==c["source_date"] and t["date"]==c["source_date"],"source date changed")
    need(m["slides"]==5 and len(m["quality"])==5,"wrong number of slides")
    need(len({i["source"] for i in m["quality"]})==5,"duplicate source photo")
    for i in m["quality"]:
        need(i["photo_semantic_qa"] is True and i["font_glyph_coverage_qa"] is True,
             "relevance or typography glyph QA missing")
        need(i["font_px"]>=130 and i["typography_reserved_area_fraction"]>=.6,
             "too small or not enough text composition")
    need((ART/"thumbnail.png").read_bytes()==(ART/"slide_0.png").read_bytes(),
         "reviewed thumbnail does not match first frame")
    result=json.loads(subprocess.check_output([
      "ffprobe","-v","error","-show_streams","-show_format","-of","json",
      str(ART/"abasonplus_daily.mp4")],timeout=30))
    vids=[s for s in result["streams"] if s["codec_type"]=="video"]
    auds=[s for s in result["streams"] if s["codec_type"]=="audio"]
    need(len(vids)==1 and vids[0]["codec_name"]=="h264" and
         vids[0]["width"]==1080 and vids[0]["height"]==1920,
         "wrong TikTok video format")
    need(auds and auds[0]["codec_name"]=="aac","owner MP3 not mixed into AAC video")
    need(14.5<float(result["format"]["duration"])<16.5,"unexpected duration")
    need(t["status"]=="preview_only" and t["posting_enabled"] is False,
         "unreviewed artifact unexpectedly marked published")
    print("APPROVED ONE-VIDEO PUBLICATION VALIDATION PASSED:")
    print("VIDEO_SHA256="+c["video_sha256"])
    print("ACCOUNT="+c["account_handle"]+"; PRIVACY="+c["privacy_level"])
    print("COMMENTS/DUET/STITCH=ON; OWNER MUSIC RIGHTS=CONFIRMED")
    print("POSTING_REQUESTS_SENT=ZERO (validation only)")
if __name__=="__main__":main()
