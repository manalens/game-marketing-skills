#!/usr/bin/env python3
"""Check an exported game trailer against Steam, YouTube or social targets with ffprobe and ffmpeg.

Checks: container, video and audio codec, resolution and aspect ratio, frame rate, video bit
rate, audio sample rate, length, loudness (ffmpeg ebur128: integrated LUFS and true peak),
black frames at the start and anywhere (blackdetect), and silence at the start (silencedetect).

Profiles (targets in references/export-specs.md):
  steam    Valve's Trailers page: .mov/.wmv/.mp4, H.264 + AAC preferred, up to 1920x1080,
           30/29.97 or 60/59.94 fps, 5,000 Kbps or more, 44.1 or 48 kHz audio.
  youtube  YouTube's recommended upload settings: MP4, H.264, AAC-LC 48 kHz, 1080p at
           8 Mbps (24 to 30 fps) or 12 Mbps (48 to 60 fps).
  social   Steam's file rules plus a length cap: pass --max-seconds 15 or 30.

Python 3 standard library only. Needs ffmpeg and ffprobe on PATH.

Examples:
  check_trailer.py launch/trailer/announce_1080p.mp4
  check_trailer.py cut30.mp4 --profile social --max-seconds 30
  check_trailer.py yt.mp4 --profile youtube --json

Exit codes: 0 pass (warnings allowed unless --strict), 1 a check failed, 2 usage or tool error.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

STEAM_FPS = (29.97, 30.0, 59.94, 60.0)
YT_FPS = (23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0)
LUFS_TARGET, LUFS_TOL, TRUE_PEAK_MAX = -14.0, 2.0, -1.0  # our practice, same as clip-cut
START_SILENCE = 1.0  # seconds of silence at the start before we warn


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def need_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        die(f"error: {', '.join(missing)} not found on PATH. Install ffmpeg (https://ffmpeg.org) and retry.")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die(f"error: ffprobe cannot read {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def rate(text):
    try:
        num, den = (float(x) for x in str(text).split("/"))
        return num / den if den else 0.0
    except ValueError:
        return 0.0


def near(value, targets, tol=0.02):
    return any(abs(value - t) <= tol for t in targets)


def analyse(path, has_audio):
    """One decode pass: blackdetect on a small copy of the video, ebur128 and silencedetect on audio."""
    graph = "[0:v]scale=320:-2,blackdetect=d=0.2:pix_th=0.10[v]"
    maps = ["-map", "[v]"]
    if has_audio:
        graph += ";[0:a]silencedetect=n=-50dB:d=0.5,ebur128=peak=true:framelog=quiet[a]"
        maps += ["-map", "[a]"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", graph,
                        *maps, "-f", "null", "-"], capture_output=True, text=True)
    if r.returncode != 0:
        die(f"error: ffmpeg analysis failed:\n{r.stderr[-2000:]}")
    err = r.stderr
    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    silence_starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    silence_ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    silence = list(zip(silence_starts, silence_ends + [None] * (len(silence_starts) - len(silence_ends))))
    summary = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    lufs = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
    return {
        "black": black,
        "silence": silence,
        "lufs": float(lufs.group(1)) if lufs and lufs.group(1) != "-inf" else None,
        "true_peak": float(peak.group(1)) if peak and peak.group(1) != "-inf" else None,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video", help="exported trailer file")
    p.add_argument("--profile", choices=["steam", "youtube", "social"], default="steam")
    p.add_argument("--max-seconds", type=float, help="fail if longer (social cuts: 15 or 30)")
    p.add_argument("--min-seconds", type=float, help="fail if shorter")
    p.add_argument("--lufs", type=float, default=LUFS_TARGET, help=f"loudness target (default {LUFS_TARGET})")
    p.add_argument("--no-loudness", action="store_true", help="skip the decode pass (faster)")
    p.add_argument("--strict", action="store_true", help="warnings also fail")
    p.add_argument("--json", action="store_true", help="print JSON")
    args = p.parse_args()
    if args.profile == "social" and not args.max_seconds:
        die("error: --profile social needs --max-seconds (15 or 30)")
    need_tools()
    path = Path(args.video)
    if not path.is_file():
        die(f"error: {path} not found")

    info = probe(path)
    fmt = info.get("format", {})
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        die(f"error: {path} has no video stream")
    results = []  # (level, check, detail) with level PASS, WARN or FAIL

    def add(ok, check, detail, level="FAIL"):
        results.append(("PASS" if ok else level, check, detail))

    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    fps = rate(v.get("avg_frame_rate") or v.get("r_frame_rate"))
    dur = float(fmt.get("duration") or v.get("duration") or 0)
    vbr = int(v.get("bit_rate") or 0) or max(0, int(fmt.get("bit_rate") or 0) - int((a or {}).get("bit_rate") or 0))
    kbps = vbr / 1000
    ext = path.suffix.lower()
    vcodec, acodec = v.get("codec_name", "?"), (a or {}).get("codec_name")
    sr = int((a or {}).get("sample_rate") or 0)
    ratio = w / h if h else 0

    if args.profile in ("steam", "social"):
        add(ext in (".mov", ".wmv", ".mp4"), "container", f"{ext}; Valve accepts .mov, .wmv or .mp4")
        add(vcodec == "h264", "video codec", f"{vcodec}; Valve prefers H.264", "WARN")
        add(w <= 1920 and h <= 1080, "resolution", f"{w}x{h}; Valve asks for up to 1920x1080", "WARN")
        add(w >= 1280 and h >= 720, "resolution floor", f"{w}x{h}; export the highest you have, ideally 1920x1080", "WARN")
        add(abs(ratio - 16 / 9) < 0.01 or abs(ratio - 4 / 3) < 0.01, "aspect ratio",
            f"{ratio:.3f}; Valve prefers 16:9, accepts 4:3", "FAIL" if args.profile == "steam" else "WARN")
        add(near(fps, STEAM_FPS), "frame rate", f"{fps:.3f} fps; Valve asks for 30/29.97 or 60/59.94")
        add(kbps >= 5000, "video bit rate", f"{kbps:.0f} Kbps; Valve asks for 5,000 Kbps or more")
        if a:
            add(acodec == "aac", "audio codec", f"{acodec}; Valve prefers AAC", "WARN")
            add(sr in (44100, 48000), "audio sample rate", f"{sr} Hz; use 44.1 or 48 kHz (odd rates fail Steam processing)")
    else:
        add(ext == ".mp4", "container", f"{ext}; YouTube recommends MP4", "WARN")
        add(vcodec == "h264", "video codec", f"{vcodec}; YouTube recommends H.264", "WARN")
        add(abs(ratio - 16 / 9) < 0.01, "aspect ratio", f"{ratio:.3f}; 16:9 is YouTube's standard", "WARN")
        add(near(fps, YT_FPS), "frame rate", f"{fps:.3f} fps; upload at the frame rate you recorded", "WARN")
        need = (12000 if fps > 31 else 8000) if h >= 1080 else 5000
        add(kbps >= need, "video bit rate", f"{kbps:.0f} Kbps; YouTube recommends {need:,} Kbps for {h}p at {fps:.0f} fps", "WARN")
        if a:
            add(acodec == "aac", "audio codec", f"{acodec}; YouTube recommends AAC-LC", "WARN")
            add(sr == 48000, "audio sample rate", f"{sr} Hz; YouTube recommends 48 kHz", "WARN")
    if not a:
        add(False, "audio", "no audio stream; a trailer without sound is rare, check the export", "WARN")
    if args.max_seconds:
        add(dur <= args.max_seconds + 0.05, "length", f"{dur:.1f} s; target at most {args.max_seconds:g} s")
    if args.min_seconds:
        add(dur >= args.min_seconds - 0.05, "length", f"{dur:.1f} s; target at least {args.min_seconds:g} s")
    if not args.max_seconds and not args.min_seconds:
        add(True, "length", f"{dur:.1f} s; no platform limit set (90 to 180 s is a common Steam page trailer)")

    found = {}
    if not args.no_loudness:
        found = analyse(path, a is not None)
        start_black = [(s, e) for s, e in found["black"] if s <= 0.1]
        add(not start_black, "black at start",
            f"black from 0 to {start_black[0][1]:.2f} s; open on gameplay" if start_black else "no black frames in the first frames")
        long_black = [(s, e) for s, e in found["black"] if s > 0.1 and e - s >= 1.0 and e < dur - 0.5]
        add(not long_black, "black mid-trailer",
            ", ".join(f"{s:.1f}-{e:.1f} s" for s, e in long_black) + "; Steam cuts its microtrailer from points across the first trailer"
            if long_black else "no black gap of 1 s or more", "WARN")
        if a:
            start_sil = [(s, e) for s, e in found["silence"] if s <= 0.1]
            end = start_sil[0][1] if start_sil else None
            add(not start_sil or (end is not None and end < START_SILENCE), "silence at start",
                f"silent until {end if end is not None else dur:.2f} s; start sound with the first shot" if start_sil else "sound from the start", "WARN")
            if found["lufs"] is not None:
                add(abs(found["lufs"] - args.lufs) <= LUFS_TOL, "loudness",
                    f"{found['lufs']:.1f} LUFS integrated; aim for {args.lufs:g} +/- {LUFS_TOL:g}", "WARN")
            else:
                add(False, "loudness", "could not measure (silent?)", "WARN")
            if found["true_peak"] is not None:
                add(found["true_peak"] <= TRUE_PEAK_MAX, "true peak", f"{found['true_peak']:.1f} dBTP; keep at or under {TRUE_PEAK_MAX:g}", "WARN")

    fails = [r for r in results if r[0] == "FAIL"]
    warns = [r for r in results if r[0] == "WARN"]
    bad = bool(fails) or (args.strict and bool(warns))
    if args.json:
        print(json.dumps({"file": str(path), "profile": args.profile, "width": w, "height": h, "fps": round(fps, 3),
                          "seconds": round(dur, 2), "video_kbps": round(kbps), "audio": acodec, "sample_rate": sr,
                          "lufs": found.get("lufs"), "true_peak": found.get("true_peak"),
                          "checks": [{"level": l, "check": c, "detail": d} for l, c, d in results],
                          "pass": not bad}, indent=2))
    else:
        print(f"{path}  [{args.profile}]  {w}x{h}  {fps:.2f} fps  {dur:.1f} s  {kbps:.0f} Kbps  {vcodec}/{acodec or 'no audio'}")
        for level, check, detail in results:
            print(f"{level:<5} {check:<18} {detail}")
        print(f"{'FAIL' if bad else 'ok'}: {len(fails)} failed, {len(warns)} warning(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
