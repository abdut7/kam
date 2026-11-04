#!/usr/bin/env python3
"""Download title, channel and captions for every video listed in videos.txt.

Setup and run (from this folder):
    pip install youtube-transcript-api
    python3 fetch_transcripts.py

Writes, next to this script:
    transcripts/<video_id>.txt       "[mm:ss] caption line" per line, in the original language
    transcripts/<video_id>.en.txt    English translation, only when the original is not English
    index.json                       id, url, title, channel, language, status for every video

Videos that fail (no captions, blocked, private) are recorded in index.json with the
reason and the run continues. Re-running skips videos already downloaded.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi

HERE = Path(__file__).resolve().parent
OUT = HERE / "transcripts"
ENGLISH = ["en", "en-US", "en-GB", "en-IN"]


def video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname and parsed.hostname.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    return urllib.parse.parse_qs(parsed.query)["v"][0]


def read_urls() -> list[str]:
    lines = (HERE / "videos.txt").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def oembed(url: str) -> dict:
    """Title and channel name from YouTube's public oEmbed endpoint."""
    q = urllib.parse.urlencode({"url": url, "format": "json"})
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?{q}", timeout=20) as r:
            data = json.load(r)
        return {"title": data.get("title"), "channel": data.get("author_name")}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {"title": None, "channel": None}


def stamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def to_text(fetched) -> str:
    return "\n".join(f"[{stamp(sn.start)}] {sn.text.replace(chr(10), ' ').strip()}" for sn in fetched)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    api = YouTubeTranscriptApi()
    index_path = HERE / "index.json"
    index = {e["id"]: e for e in json.loads(index_path.read_text())} if index_path.exists() else {}
    failures = 0

    for url in read_urls():
        vid = video_id(url)
        if index.get(vid, {}).get("status") == "ok" and (OUT / f"{vid}.txt").exists():
            print(f"skip   {vid} (already downloaded)")
            continue
        entry = {"id": vid, "url": url, **oembed(url)}
        try:
            transcripts = api.list(vid)
            try:
                chosen = transcripts.find_transcript(ENGLISH)
            except NoTranscriptFound:
                chosen = next(iter(transcripts))
            entry["language"] = chosen.language_code
            entry["auto_generated"] = chosen.is_generated
            (OUT / f"{vid}.txt").write_text(to_text(chosen.fetch()), encoding="utf-8")
            if not chosen.language_code.lower().startswith("en") and chosen.is_translatable:
                (OUT / f"{vid}.en.txt").write_text(to_text(chosen.translate("en").fetch()), encoding="utf-8")
                entry["english_translation"] = True
            entry["status"] = "ok"
            print(f"ok     {vid}  [{chosen.language_code}{' auto' if chosen.is_generated else ''}]  {entry.get('title')}")
        except Exception as exc:  # keep going; the reason is recorded for the report
            entry["status"] = "failed"
            entry["error"] = f"{type(exc).__name__}: {str(exc).strip().splitlines()[0] if str(exc).strip() else ''}"
            failures += 1
            print(f"FAILED {vid}  {entry['error']}")
        index[vid] = entry
        index_path.write_text(json.dumps(list(index.values()), indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(1)  # be polite; repeated fast requests get an IP blocked

    ok = sum(1 for e in index.values() if e.get("status") == "ok")
    print(f"\n{ok} downloaded, {failures} failed this run. Details in {index_path.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
