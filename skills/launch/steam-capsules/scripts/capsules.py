#!/usr/bin/env python3
"""Check, make and preview Steam capsule and library art with ffmpeg.

Commands:
  check <folder>     Name each image by its exact size (ffprobe), then list missing
                     required assets, wrong sizes, wrong file types, opaque logos and,
                     with --max-mb, files over a size you set.
  make               Crop and scale one key art to every size, overlay the logo at a
                     safe width per size (never on the library hero or page background),
                     and write correctly named files.
  preview <small>    Contact sheet of the small capsule at 120x45, 184x69 and 231x87 on
                     Steam's list background, plus a blurred copy for a squint test.

Sizes come from Valve's Steamworks Graphical Assets pages (see references/sizes.md).
Python 3 standard library only. Needs ffmpeg and ffprobe on PATH.

Examples:
  capsules.py check marketing/capsules
  capsules.py make --art key.png --logo logo.png --out marketing/capsules
  capsules.py make --art key.png --logo logo.png --out out --focus 0.3,0.5 --only small header
  capsules.py preview marketing/capsules/store/small_462x174.png --out squint.png

Exit codes: 0 ok, 1 problems found, 2 usage or tool error.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# id: (name, group, width, height, required, file types Valve names or None, logo layout)
# Logo layout: None = no logo; (scale, y) = logo fits inside scale x frame, centred at x 0.5, y.
# Layouts follow the Manalens capsule maker defaults, except the small capsule, where Valve says
# the logo "should nearly fill" it, so the logo gets 0.9 of the frame.
ASSETS = {
    "header": ("Header capsule", "store", 920, 430, True, None, (0.7, 0.62)),
    "small": ("Small capsule", "store", 462, 174, True, None, (0.9, 0.5)),
    "main": ("Main capsule", "store", 1232, 706, True, None, (0.7, 0.62)),
    "vertical": ("Vertical capsule", "store", 748, 896, True, None, (0.8, 0.78)),
    "background": ("Page background", "store", 1438, 810, False, None, None),
    "bundle": ("Bundle header", "store", 707, 232, False, None, (0.7, 0.5)),
    "library-capsule": ("Library capsule", "library", 600, 900, True, None, (0.8, 0.78)),
    "library-header": ("Library header", "library", 920, 430, False, None, (0.7, 0.62)),
    "library-hero": ("Library hero", "library", 3840, 1240, True, ["png"], None),
    "library-logo": ("Library logo", "library", 1280, 720, True, ["png"], "logo"),
    "shortcut-icon": ("Shortcut icon", "community", 256, 256, True, ["png", "ico"], (0.8, 0.5)),
    "app-icon": ("App icon", "community", 184, 184, True, ["jpg"], (0.8, 0.5)),
    "event-cover": ("Event cover", "event", 800, 450, True, None, (0.6, 0.5)),
    "event-header": ("Event header", "event", 1920, 622, False, None, (0.5, 0.5)),
}
NOTES = {
    "library-header": "optional in practice: Steam uses the store header capsule if it is empty",
    "background": "optional: Steam uses your last screenshot if it is empty",
    "bundle": "only needed for a bundle",
    "event-header": "suggested, not required",
}
DEFAULT_MAKE = [a for a in ASSETS if a != "bundle"]
SAFE_INSET = 0.05  # our practice: keep the logo 5% in from every edge
HERO_SAFE = (860, 380)  # Valve: safe area at the centre of the library hero
SMALL_COPIES = [(120, 45), (184, 69), (231, 87)]  # Steam makes 120x45 and 184x69; 231x87 seen in store lists
STORE_BG = "0x1b2838"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".ico", ".webp", ".bmp"}
ALPHA_FMTS = ("rgba", "ya8", "argb", "bgra", "abgr", "pal8", "rgba64", "ya16", "yuva")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def need_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        die(f"error: {', '.join(missing)} not found on PATH. Install ffmpeg (https://ffmpeg.org) and retry.")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,pix_fmt,codec_name", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    streams = json.loads(r.stdout or "{}").get("streams") or []
    return streams[0] if streams else None


def ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        die(f"error: ffmpeg failed:\n{r.stderr.strip()}")


def file_type(path, codec):
    ext = path.suffix.lower().lstrip(".")
    return {"jpeg": "jpg", "mjpeg": "jpg"}.get(ext, ext) if ext else {"mjpeg": "jpg"}.get(codec, codec)


def fits(asset_id, w, h):
    if asset_id == "library-logo":
        return (w == 1280 and h <= 720) or (h == 720 and w <= 1280)
    if asset_id == "shortcut-icon":
        return (w, h) in ((256, 256), (512, 512))
    a = ASSETS[asset_id]
    return (w, h) == (a[2], a[3])


def identify(path, w, h):
    """Return the asset id for this file: by exact size, using the file name to break ties."""
    name = path.stem.lower().replace("_", "-")
    by_size = [a for a in ASSETS if fits(a, w, h)]
    for a in sorted(ASSETS, key=len, reverse=True):  # "library-header" before "header"
        if a in name and (a in by_size or not by_size):
            return a, a in by_size
    if len(by_size) > 1:  # 920x430: header unless the name says library
        by_size = ["library-header"] if "library" in name else ["header"]
    if by_size:
        return by_size[0], True
    for a in sorted(ASSETS, key=len, reverse=True):
        if a in name:
            return a, False
    return None, False


def cmd_check(args):
    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"error: {folder} is not a folder", file=sys.stderr)
        return 2
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXT)
    found, problems, warnings, rows = {}, [], [], []
    for p in files:
        info = probe(p)
        if not info:
            warnings.append(f"{p}: ffprobe could not read it")
            continue
        w, h = int(info.get("width", 0)), int(info.get("height", 0))
        asset, size_ok = identify(p, w, h)
        ftype = file_type(p, info.get("codec_name", ""))
        mb = p.stat().st_size / 1024 / 1024
        rows.append((str(p.relative_to(folder)), f"{w}x{h}", asset or "?", f"{mb:.2f} MB"))
        if asset is None:
            warnings.append(f"{p.name}: {w}x{h} matches no Steam asset size")
            continue
        a = ASSETS[asset]
        if not size_ok:
            want = "1280 wide and/or 720 tall" if asset == "library-logo" else (
                "256x256 or 512x512" if asset == "shortcut-icon" else f"{a[2]}x{a[3]}")
            problems.append(f"{p.name}: named like {a[0]} but is {w}x{h}; Valve asks for {want}")
        else:
            found.setdefault(asset, []).append(p)
        if a[5] and ftype not in a[5]:
            problems.append(f"{p.name}: {a[0]} is {ftype.upper()}; Valve asks for {' or '.join(t.upper() for t in a[5])}")
        elif not a[5] and ftype not in ("png", "jpg"):
            warnings.append(f"{p.name}: {ftype.upper()}; Valve names no type here, PNG or JPG is the safe choice")
        if asset == "library-logo" and not str(info.get("pix_fmt", "")).startswith(ALPHA_FMTS):
            problems.append(f"{p.name}: library logo has no alpha channel ({info.get('pix_fmt')}); Valve asks for a transparent background")
        if args.max_mb and mb > args.max_mb:
            problems.append(f"{p.name}: {mb:.2f} MB is over your --max-mb {args.max_mb}")
    for asset, (name, _g, w, h, required, _t, _l) in ASSETS.items():
        if asset in found:
            if len(found[asset]) > 1:
                warnings.append(f"{name}: {len(found[asset])} files at this size ({', '.join(x.name for x in found[asset])}); upload one")
            continue
        if required and (not args.store_only or ASSETS[asset][1] == "store"):
            problems.append(f"missing: {name} {w}x{h}")
        elif asset in NOTES and not args.store_only:
            warnings.append(f"not found: {name} {w}x{h} ({NOTES[asset]})")

    if args.json:
        print(json.dumps({"files": rows, "problems": problems, "warnings": warnings}, indent=2))
    else:
        print(f"{len(files)} image(s) in {folder}")
        for r in rows:
            print(f"  {r[0]:<44} {r[1]:>10}  {r[2]:<16} {r[3]}")
        for w_ in warnings:
            print(f"WARN  {w_}")
        for pr in problems:
            print(f"FAIL  {pr}")
        print("ok: every required asset is present at the right size" if not problems else f"{len(problems)} problem(s)")
        print("Valve lists no file size limit for these assets; --max-mb is your own cap.")
    return 1 if problems else 0


def parse_focus(text):
    try:
        x, y = (float(v) for v in text.split(","))
    except ValueError:
        die("error: --focus takes two numbers from 0 to 1, like 0.5,0.4")
    if not (0 <= x <= 1 and 0 <= y <= 1):
        die("error: --focus values must be between 0 and 1")
    return x, y


def logo_box(lw, lh, fw, fh, scale, ycentre):
    """Logo size and position inside the frame: fit scale of the frame, kept inside a 5% inset."""
    s = min(fw * scale / lw, fh * scale / lh)
    s = min(s, fw * (1 - 2 * SAFE_INSET) / lw, fh * (1 - 2 * SAFE_INSET) / lh)
    w, h = max(2, int(lw * s) // 2 * 2), max(2, int(lh * s) // 2 * 2)
    x = (fw - w) // 2
    y = int(fh * ycentre - h / 2)
    y = max(int(fh * SAFE_INSET), min(y, int(fh * (1 - SAFE_INSET)) - h))
    return w, h, x, y


def cmd_make(args):
    art, logo, out = Path(args.art), Path(args.logo) if args.logo else None, Path(args.out)
    ai = probe(art)
    if not ai:
        die(f"error: cannot read key art {art}")
    aw, ah = int(ai["width"]), int(ai["height"])
    li = None
    if logo:
        li = probe(logo)
        if not li:
            die(f"error: cannot read logo {logo}")
        if not str(li.get("pix_fmt", "")).startswith(ALPHA_FMTS):
            print(f"WARN  logo {logo.name} has no alpha channel ({li.get('pix_fmt')}); use a transparent PNG")
    if not logo and not args.no_logo:
        print("WARN  no --logo: Valve says capsules must contain a readable product logo or name")
    fx, fy = parse_focus(args.focus)
    only = args.only or DEFAULT_MAKE
    bad = [a for a in only if a not in ASSETS]
    if bad:
        die(f"error: unknown asset id(s) {bad}. Use: {' '.join(ASSETS)}")
    written = []
    for aid in only:
        name, group, fw, fh, _req, types, layout = ASSETS[aid]
        ext = (types or ["png"])[0]
        if aid == "library-logo":
            if not li:
                print(f"skip  {name}: no --logo given")
                continue
            lw, lh = int(li["width"]), int(li["height"])
            fw, fh = (1280, max(1, round(1280 * lh / lw))) if lw / lh >= 1280 / 720 else (max(1, round(720 * lw / lh)), 720)
            dest = out / group / f"{aid}_{fw}x{fh}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ffmpeg(["-i", str(logo), "-vf", f"scale={fw}:{fh}:flags=lanczos,format=rgba", "-frames:v", "1", str(dest)])
            written.append(dest)
            print(f"wrote {dest}  ({name}, logo only, transparent)")
            continue
        up = max(fw / aw, fh / ah)
        if up > 1.01:
            print(f"WARN  {name}: key art is enlarged {up:.1f}x and may look soft; supply art at least {fw}x{fh}")
        crop = (f"scale={fw}:{fh}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={fw}:{fh}:(iw-{fw})*{fx}:(ih-{fh})*{fy},setsar=1")
        dest = out / group / f"{aid}_{fw}x{fh}.{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if layout and li and not args.no_logo:
            scale, yc = layout
            w, h, x, y = logo_box(int(li["width"]), int(li["height"]), fw, fh, scale, yc)
            graph = (f"[0:v]{crop}[bg];[1:v]scale={w}:{h}:flags=lanczos,format=rgba[lg];"
                     f"[bg][lg]overlay={x}:{y}:format=auto")
            fmt = ",format=rgb24" if ext == "jpg" else ""
            ffmpeg(["-i", str(art), "-i", str(logo), "-filter_complex", graph + fmt, "-frames:v", "1",
                    *(["-q:v", "2"] if ext == "jpg" else []), str(dest)])
            fill = max(w / fw, h / fh)
            note = f"logo {w}x{h} at {x},{y}, fills {fill:.0%}"
        else:
            ffmpeg(["-i", str(art), "-vf", crop + (",format=rgb24" if ext == "jpg" else ""), "-frames:v", "1",
                    *(["-q:v", "2"] if ext == "jpg" else []), str(dest)])
            note = {"library-hero": "no logo: Valve wants no words at all here",
                    "background": "no logo: art only, behind the page"}.get(aid, "no logo")
        if aid == "library-hero":
            note += f"; keep the subject inside the centred {HERO_SAFE[0]}x{HERO_SAFE[1]} safe area"
        written.append(dest)
        print(f"wrote {dest}  ({name}, {note})")
    print(f"{len(written)} file(s) in {out}. Draft only: review each one, then upload in Steamworks yourself.")
    return 0


def cmd_preview(args):
    src = Path(args.small)
    info = probe(src)
    if not info:
        die(f"error: cannot read {src}")
    if (int(info["width"]), int(info["height"])) != (462, 174):
        print(f"WARN  {src.name} is {info['width']}x{info['height']}, not 462x174; previewing anyway")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pad, sizes = 24, SMALL_COPIES
    # Row 1: the three list sizes at 1:1. Row 2: the 231x87 copy blurred (squint) and the
    # 120x45 copy blown up 4x with hard pixels, so you see what a 120 pixel logo really keeps.
    sheet_w = max(pad * (len(sizes) + 1) + sum(w for w, _ in sizes), pad * 3 + 231 + 480)
    sheet_h = pad * 3 + 87 + 180
    parts = []
    for i, (w, h) in enumerate(sizes):
        parts.append(f"[0:v]scale={w}:{h}:flags=area[s{i}]")
    parts.append("[0:v]scale=231:87:flags=area,gblur=sigma=2.5[blur]")
    parts.append("[0:v]scale=120:45:flags=area,scale=480:180:flags=neighbor[big]")
    parts.append(f"color=c={STORE_BG}:s={sheet_w}x{sheet_h}:d=1[bg]")
    x, chain, last = pad, [], "bg"
    for i, (w, h) in enumerate(sizes):
        chain.append(f"[{last}][s{i}]overlay={x}:{pad}[o{i}]")
        last, x = f"o{i}", x + w + pad
    chain.append(f"[{last}][blur]overlay={pad}:{pad * 2 + 87}[ob]")
    chain.append(f"[ob][big]overlay={pad * 2 + 231}:{pad * 2 + 87}")
    ffmpeg(["-i", str(src), "-filter_complex", ";".join(parts + chain), "-frames:v", "1", str(out)])
    print(f"wrote {out}")
    print("Top row: 120x45, 184x69 and 231x87 on Steam's list colour. Bottom: 231x87 blurred (squint), 120x45 at 4x.")
    print("Pass if you can read the name in the blurred copy and the 120x45 copy, and tell the genre.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a folder of capsule images")
    c.add_argument("folder")
    c.add_argument("--max-mb", type=float, default=0, help="flag files larger than this (Valve names no limit)")
    c.add_argument("--store-only", action="store_true", help="only require the four store capsules")
    c.add_argument("--json", action="store_true", help="print JSON")
    m = sub.add_parser("make", help="make every size from key art and a logo")
    m.add_argument("--art", required=True, help="key art, ideally 3840x1240 or larger")
    m.add_argument("--logo", help="logo as a transparent PNG, trimmed to its edges")
    m.add_argument("--out", required=True, help="output folder (store/, library/, community/, event/)")
    m.add_argument("--focus", default="0.5,0.5", help="crop focus x,y from 0 to 1 (default centre)")
    m.add_argument("--only", nargs="+", metavar="ID", help=f"asset ids: {' '.join(ASSETS)}")
    m.add_argument("--no-logo", action="store_true", help="art only, no logo anywhere")
    v = sub.add_parser("preview", help="squint-test sheet for the small capsule")
    v.add_argument("small", help="the 462x174 small capsule")
    v.add_argument("--out", default="capsule-preview.png", help="output PNG (default capsule-preview.png)")
    args = p.parse_args()
    need_tools()
    return {"check": cmd_check, "make": cmd_make, "preview": cmd_preview}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
