#!/usr/bin/env python3
"""Cut one gameplay clip into social video shapes with ffmpeg.

Shapes: 9x16 (1080x1920), 4x5 (1080x1350), 16x9 (1920x1080) and gif (looping,
size-capped). Optional hook text for the first seconds, an end card for the last
seconds, a speed factor, loudness normalisation to about -14 LUFS, and mute.

Python 3 standard library only. Needs ffmpeg and ffprobe on PATH. Hook and end card
text need ffmpeg's drawtext filter (built with libfreetype). Some builds leave it out,
such as the default Homebrew ffmpeg on macOS; the script says so before it starts.

Examples:
  clip_cut.py footage.mp4 --start 12.5 --end 27 --shape 9x16 4x5 \\
      --hook "This boat can fly. Wait for it." --out-dir marketing/clips
  clip_cut.py footage.mp4 --start 1:02 --end 1:10 --shape gif --gif-width 640
  clip_cut.py footage.mp4 --shape 16x9 --fit blur --end-text "Wishlist on Steam" \\
      --end-url yourgame.com --dry-run
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap

SHAPES = {
    "9x16": (1080, 1920),
    "4x5": (1080, 1350),
    "16x9": (1920, 1080),
    "gif": None,  # width from --gif-width, height from the source aspect
}

# Safe area as fractions of the frame: left, right, top, bottom.
# 9:16 feeds put buttons on the right and captions, names and the progress bar at
# the bottom, so text stays out of the right edge, the top 14 and the bottom 35 percent
# (Meta's Reels safe zone, the strictest of the three apps).
SAFE = {
    "9x16": (0.07, 0.16, 0.14, 0.35),
    "4x5": (0.06, 0.08, 0.07, 0.14),
    "16x9": (0.06, 0.06, 0.08, 0.14),
    "gif": (0.05, 0.05, 0.06, 0.08),
}

# Hook font size as a fraction of the frame width.
FONT_FRAC = {"9x16": 0.066, "4x5": 0.060, "16x9": 0.036, "gif": 0.052}

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]

CHAR_W = 0.60   # average glyph width as a fraction of font size (bold sans, safe side)
LINE_H = 1.22   # line height as a fraction of font size


class CutError(Exception):
    pass


def die(msg):
    print(f"clip_cut: error: {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"clip_cut: warning: {msg}", file=sys.stderr)


def parse_time(value):
    """Accept seconds (12.5), m:ss(.s) or h:mm:ss(.s)."""
    try:
        parts = [float(p) for p in str(value).split(":")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a time: {value!r} (use 12.5 or 1:02.5)")
    if not 1 <= len(parts) <= 3 or any(p < 0 for p in parts):
        raise argparse.ArgumentTypeError(f"not a time: {value!r}")
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def need_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        die(
            f"{' and '.join(missing)} not found on PATH. Install ffmpeg "
            "(macOS: brew install ffmpeg; Debian/Ubuntu: sudo apt install ffmpeg; "
            "Windows: winget install ffmpeg) and try again."
        )


def has_drawtext():
    res = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return re.search(r"^\s*\S*\s+drawtext\s", res.stdout, re.M) is not None


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise CutError(f"ffprobe could not read {path}: {res.stderr.strip()}")
    return json.loads(res.stdout)


def video_info(path):
    data = probe(path)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if v is None:
        raise CutError(f"{path} has no video stream")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) % 180 == 90:
        w, h = h, w
    dur = float(data.get("format", {}).get("duration") or v.get("duration") or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    rates = (v.get("r_frame_rate"), v.get("avg_frame_rate"))
    return {"w": w, "h": h, "dur": dur, "audio": has_audio, "rates": rates}


def find_font(user_font):
    if user_font:
        if not os.path.isfile(user_font):
            die(f"--font {user_font!r} does not exist")
        return user_font
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    if shutil.which("fc-match"):
        res = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True)
        if res.returncode == 0 and os.path.isfile(res.stdout.strip()):
            return res.stdout.strip()
    die(
        "no font found for hook or end card text. Pass --font /path/to/Font-Bold.ttf "
        "(any .ttf or .otf file), or install DejaVu Sans or Liberation Sans."
    )


def esc(value):
    """Escape a value for a filter option inside -filter_complex (two levels)."""
    lvl1 = re.sub(r"([\\':])", r"\\\1", str(value))
    return re.sub(r"([\\'\[\],;])", r"\\\1", lvl1)


def wrap_lines(text, max_chars):
    lines = []
    for para in text.replace("\\n", "\n").split("\n"):
        para = para.strip()
        if not para:
            continue
        lines.extend(textwrap.wrap(para, width=max(4, max_chars)) or [""])
    return lines


def even(n):
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


class TextWriter:
    """Writes each text line to its own file so drawtext needs no text escaping."""

    def __init__(self, tmpdir):
        self.tmpdir = tmpdir
        self.n = 0

    def file(self, line):
        self.n += 1
        path = os.path.join(self.tmpdir, f"line{self.n:03d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(line)
        return path


def text_block(tw, font, lines, size, x0, avail_w, y0, enable, alpha=None, color="white"):
    """drawtext filters for centred lines inside [x0, x0+avail_w], starting at y0."""
    out = []
    border = max(2, round(size / 11))
    for i, line in enumerate(lines):
        y = round(y0 + i * size * LINE_H)
        parts = [
            f"fontfile={esc(font)}",
            f"textfile={esc(tw.file(line))}",
            "expansion=none",
            f"fontsize={size}",
            f"fontcolor={color}",
            f"borderw={border}",
            "bordercolor=black@0.85",
            f"x={x0}+({avail_w}-text_w)/2",
            f"y={y}",
            f"enable={esc(enable)}",
        ]
        if alpha:
            parts.append(f"alpha={esc(alpha)}")
        out.append("drawtext=" + ":".join(parts))
    return out


def fit_lines(text, size, avail_w, avail_h, min_size):
    """Shrink the font until the wrapped block fits the safe box."""
    while True:
        max_chars = int(avail_w / (size * CHAR_W))
        lines = wrap_lines(text, max_chars)
        long_word = max((len(l) for l in lines), default=0) > max_chars
        block_h = len(lines) * size * LINE_H
        if (block_h <= avail_h and not long_word) or size <= min_size:
            return lines, size
        size = max(min_size, int(size * 0.9))


def build(args, shape, src, font, tmpdir, out_path):
    in_dur = args.end - args.start
    out_dur = in_dur / args.speed
    is_gif = shape == "gif"

    if is_gif:
        W = even(args.gif_width)
        H = even(W * src["h"] / src["w"])
    else:
        W, H = SHAPES[shape]

    tw = TextWriter(tmpdir)
    inputs = ["-ss", f"{args.start:.3f}", "-t", f"{in_dur:.3f}", "-i", args.input]
    fps = args.gif_fps if is_gif else args.fps
    chain = [f"setpts=(PTS-STARTPTS)/{args.speed}", f"fps={fps}"]
    graph = []

    # Shape: crop or blurred-background fit.
    if is_gif:
        chain.append(f"scale={W}:{H}:flags=lanczos,setsar=1")
        graph.append(f"[0:v]{','.join(chain)}[base]")
    elif args.fit == "crop":
        a = W / H
        if src["w"] / src["h"] > a:
            cw, ch = min(int(src["h"] * a) // 2 * 2, src["w"]), src["h"]
            if args.crop_x is None:
                x = (src["w"] - cw) // 2
            else:
                x = int(args.crop_x)
                if x < 0 or x + cw > src["w"]:
                    clamped = max(0, min(x, src["w"] - cw))
                    warn(f"--crop-x {x} puts the {cw}px window outside the {src['w']}px frame; using {clamped}")
                    x = clamped
            chain.append(f"crop={cw}:{ch}:{x}:0")
        else:
            ch = min(int(src["w"] / a) // 2 * 2, src["h"])
            if args.crop_x is not None:
                warn("--crop-x ignored: the source is narrower than the target shape, so the crop is vertical")
            chain.append(f"crop={src['w']}:{ch}:0:{(src['h'] - ch) // 2}")
        chain.append(f"scale={W}:{H}:flags=lanczos,setsar=1")
        graph.append(f"[0:v]{','.join(chain)}[base]")
    else:  # blur
        graph.append(f"[0:v]{','.join(chain)},split[fgsrc][bgsrc]")
        graph.append(
            f"[bgsrc]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=30:2,eq=brightness=-0.08,setsar=1[bg]"
        )
        graph.append(
            f"[fgsrc]scale={W}:{H}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,setsar=1[fg]"
        )
        graph.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[base]")

    sl, sr, st, sb = SAFE[shape]
    x0, avail_w = round(W * sl), round(W * (1 - sl - sr))
    top, bottom = round(H * st), round(H * (1 - sb))
    base_size = round(W * FONT_FRAC[shape] * args.text_scale)
    min_size = max(12, round(base_size * 0.6))
    draws = []
    cur = "base"

    # Hook text: first N seconds, fades out over the last 0.25 s.
    if args.hook:
        hs = min(args.hook_seconds, out_dur)
        lines, size = fit_lines(args.hook, base_size, avail_w, (bottom - top) * 0.5, min_size)
        alpha = f"if(lt(t,{hs - 0.25:.3f}),1,max(0,({hs:.3f}-t)/0.25))"
        draws += text_block(tw, font, lines, size, x0, avail_w, top, f"between(t,0,{hs:.3f})", alpha)

    # End card: last N seconds.
    es = 0.0
    if args.end_card or args.end_text or args.end_url:
        es = min(args.end_seconds, out_dur)
        t0 = out_dur - es
        if args.hook and t0 < min(args.hook_seconds, out_dur):
            warn(f"{shape}: hook ({args.hook_seconds}s) and end card ({es}s) overlap in a {out_dur:.2f}s clip")
        enable = f"gte(t,{t0:.3f})"
        if args.end_card:
            inputs += ["-loop", "1", "-i", args.end_card]
            graph.append(
                f"[1:v]scale={W}:{H}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,format=yuva420p[card]"
            )
            graph.append(f"[{cur}][card]overlay=0:0:eof_action=repeat:enable={esc(enable)}[carded]")
            cur = "carded"
        if args.end_text or args.end_url:
            if not args.end_card:
                draws.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.72:t=fill:enable={esc(enable)}")
            blocks = []
            if args.end_text:
                blocks.append(fit_lines(args.end_text, base_size, avail_w, (bottom - top) * 0.45, min_size))
            if args.end_url:
                usize = max(min_size, round(base_size * 0.7))
                ulines, usize = fit_lines(args.end_url, usize, avail_w, (bottom - top) * 0.2, max(10, min_size // 2))
                blocks.append((ulines, usize))
            gap = round(base_size * 0.6)
            total_h = sum(len(l) * s * LINE_H for l, s in blocks) + gap * (len(blocks) - 1)
            y = round(top + ((bottom - top) - total_h) / 2)
            for i, (lines, size) in enumerate(blocks):
                color = "white" if i == 0 and args.end_text else "0xFFE27A"
                draws += text_block(tw, font, lines, size, x0, avail_w, y, enable, color=color)
                y = round(y + len(lines) * size * LINE_H + gap)

    tail = draws + ([] if is_gif else ["format=yuv420p"])
    if tail:
        graph.append(f"[{cur}]{','.join(tail)}[vout]")
    else:
        graph.append(f"[{cur}]null[vout]")

    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y"] + inputs

    if is_gif:
        graph[-1] = graph[-1][: -len("[vout]")] + ",split[g1][g2]"
        graph.append("[g1]palettegen=max_colors=256:stats_mode=diff[pal]")
        graph.append("[g2][pal]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle[vout]")
        cmd += ["-filter_complex", ";".join(graph), "-map", "[vout]", "-t", f"{out_dur:.3f}",
                "-loop", "0", out_path]
        return cmd, out_dur

    use_audio = src["audio"] and not args.mute
    if use_audio:
        afilters = []
        sp = args.speed
        while sp > 2.0:  # older ffmpeg caps atempo at 2.0 per instance
            afilters.append("atempo=2.0")
            sp /= 2.0
        while sp < 0.5:
            afilters.append("atempo=0.5")
            sp /= 0.5
        if abs(sp - 1.0) > 1e-6:
            afilters.append(f"atempo={sp:.6f}")
        afilters.append(f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11")
        afilters.append("aresample=48000")
        if out_dur > 1.0:
            afilters.append(f"afade=t=out:st={out_dur - 0.4:.3f}:d=0.4")
        graph.append(f"[0:a]{','.join(afilters)}[aout]")

    cmd += ["-filter_complex", ";".join(graph), "-map", "[vout]"]
    if use_audio:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf), "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-t", f"{out_dur:.3f}", "-movflags", "+faststart", out_path]
    return cmd, out_dur


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise CutError("ffmpeg failed:\n" + (res.stderr.strip()[-3000:] or "(no output)"))


def describe(path):
    data = probe(path)
    v = next(s for s in data["streams"] if s.get("codec_type") == "video")
    a = next((s for s in data["streams"] if s.get("codec_type") == "audio"), None)
    dur = float(data["format"].get("duration") or 0)
    size = int(data["format"].get("size") or os.path.getsize(path))
    return v["width"], v["height"], dur, a is not None, size


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="clip_cut.py",
        description="Cut a gameplay clip into 9x16, 4x5, 16x9 and GIF versions with ffmpeg, "
        "with optional hook text, end card, speed-up and loudness normalisation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Shapes: 9x16=1080x1920 (Shorts, TikTok, Reels), 4x5=1080x1350 (Reddit, X feed),
                    16x9=1920x1080 (Reddit, X, YouTube), gif=looping GIF at --gif-width.
            Times accept seconds (12.5) or m:ss (1:02.5). Hook and end card times are in the
            output clip, after --speed.
            Exit status: 0 on success, 1 on any failure, 2 on bad arguments."""
        ),
    )
    p.add_argument("input", help="source video file")
    p.add_argument("--start", type=parse_time, default=0.0, help="in point in the source (default 0)")
    p.add_argument("--end", type=parse_time, help="out point in the source (default: end of file)")
    p.add_argument("--shape", nargs="+", default=["9x16"], metavar="SHAPE",
                   help="one or more of: 9x16 4x5 16x9 gif (default 9x16)")
    p.add_argument("--fit", choices=["crop", "blur"], default="crop",
                   help="crop to fill the frame, or fit the whole picture over a blurred copy (default crop)")
    p.add_argument("--crop-x", type=int, metavar="PX",
                   help="left edge of the crop window in source pixels (default: centre)")
    p.add_argument("--hook", help='hook text for the first seconds; "\\n" forces a line break')
    p.add_argument("--hook-seconds", type=float, default=3.0, help="how long the hook shows (default 3)")
    p.add_argument("--end-card", metavar="IMAGE", help="image shown full frame for the last seconds")
    p.add_argument("--end-text", help="end card text, e.g. \"Wishlist on Steam\"")
    p.add_argument("--end-url", help="short URL shown under the end card text")
    p.add_argument("--end-seconds", type=float, default=3.0, help="end card length (default 3)")
    p.add_argument("--speed", type=float, default=1.0, help="speed factor, e.g. 1.3 (default 1)")
    p.add_argument("--mute", action="store_true", help="drop the audio")
    p.add_argument("--lufs", type=float, default=-14.0, help="loudness target in LUFS (default -14)")
    p.add_argument("--font", help="font file for text (default: first common bold sans found)")
    p.add_argument("--text-scale", type=float, default=1.0, help="multiply the text size (default 1)")
    p.add_argument("--fps", type=int, default=30, help="output frame rate for video, forces constant rate (default 30)")
    p.add_argument("--gif-width", type=int, default=720, help="GIF width in px (default 720)")
    p.add_argument("--gif-fps", type=int, default=15, help="GIF frame rate (default 15)")
    p.add_argument("--gif-max-mb", type=float, default=8.0,
                   help="shrink the GIF until it is under this size in MB (default 8)")
    p.add_argument("--crf", type=int, default=20, help="x264 quality, lower is better (default 20)")
    p.add_argument("--preset", default="medium", help="x264 preset (default medium)")
    p.add_argument("--out-dir", default=".", help="output folder (default: current folder)")
    p.add_argument("--name", help="output base name (default: <input name>-<start>s)")
    p.add_argument("--dry-run", action="store_true", help="print the ffmpeg commands, do not run them")
    args = p.parse_args(argv)

    bad = [s for s in args.shape if s not in SHAPES]
    if bad:
        p.error(f"unknown shape(s): {', '.join(bad)}. Use: {' '.join(SHAPES)}")
    if not 0.25 <= args.speed <= 4.0:
        p.error("--speed must be between 0.25 and 4")
    if args.hook_seconds <= 0 or args.end_seconds <= 0:
        p.error("--hook-seconds and --end-seconds must be above 0")

    need_tools()
    if not os.path.isfile(args.input):
        die(f"input not found: {args.input}")
    if args.end_card and not os.path.isfile(args.end_card):
        die(f"end card image not found: {args.end_card}")

    try:
        src = video_info(args.input)
    except CutError as e:
        die(str(e))
    if args.end is None:
        args.end = src["dur"]
    if src["dur"] and args.end > src["dur"] + 0.05:
        warn(f"--end {args.end:.2f}s is past the end of the source ({src['dur']:.2f}s); using the end")
        args.end = src["dur"]
    if args.end - args.start <= 0.1:
        die(f"nothing to cut: --start {args.start:.2f}s, --end {args.end:.2f}s")
    if src["rates"][0] and src["rates"][1] and src["rates"][0] != src["rates"][1]:
        warn(f"source looks like variable frame rate ({src['rates'][0]} vs {src['rates'][1]}); "
             f"output is forced to a constant {args.fps} fps")
    if not src["audio"] and not args.mute:
        warn("source has no audio stream; output will be silent")

    wants_text = bool(args.hook or args.end_text or args.end_url)
    if wants_text and not args.dry_run and not has_drawtext():
        die("this ffmpeg has no drawtext filter (it was built without libfreetype), so it "
            "cannot draw --hook, --end-text or --end-url. Install a build with it (macOS: "
            "brew install ffmpeg-full, or the homebrew-ffmpeg tap; Linux: the distro ffmpeg "
            "package), or run without text and use --end-card with an image.")
    font = find_font(args.font) if wants_text else None
    name = args.name or f"{os.path.splitext(os.path.basename(args.input))[0]}-{args.start:g}s"
    if not args.dry_run:
        os.makedirs(args.out_dir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="clip_cut_")

    failed = False
    try:
        for shape in args.shape:
            ext = "gif" if shape == "gif" else "mp4"
            out_path = os.path.join(args.out_dir, f"{name}-{shape}.{ext}")
            cmd, out_dur = build(args, shape, src, font, tmpdir, out_path)
            if args.dry_run:
                print(f"# {shape}: {out_path} ({out_dur:.2f}s)")
                print(shlex.join(cmd))
                continue
            try:
                run(cmd)
                if shape == "gif":
                    limit = args.gif_max_mb * 1024 * 1024
                    width, fps = args.gif_width, args.gif_fps
                    while os.path.getsize(out_path) > limit and width > 320:
                        width = int(width * 0.8)
                        fps = max(10, fps - 2)
                        warn(f"GIF over {args.gif_max_mb} MB; retrying at {width}px, {fps} fps")
                        sub = argparse.Namespace(**{**vars(args), "gif_width": width, "gif_fps": fps})
                        cmd, out_dur = build(sub, shape, src, font, tmpdir, out_path)
                        run(cmd)
                    if os.path.getsize(out_path) > limit:
                        warn(f"GIF is still over {args.gif_max_mb} MB; cut a shorter clip or use MP4")
                w, h, dur, has_a, size = describe(out_path)
                audio = "audio" if has_a else "no audio"
                print(f"{out_path}  {w}x{h}  {dur:.2f}s  {audio}  {size / 1024 / 1024:.2f} MB")
            except CutError as e:
                failed = True
                print(f"clip_cut: error: {shape}: {e}", file=sys.stderr)
    finally:
        if args.dry_run:
            print(f"# text files for drawtext kept in {tmpdir}")
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
