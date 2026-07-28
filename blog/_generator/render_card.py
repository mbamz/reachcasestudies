#!/usr/bin/env python3
"""
render_card.py - Reach blog cover-card renderer (the blog owns its card art).

Renders a per-post branded 1200x675 "cover" thumbnail. Every card is one visual
family — dark Reach panel, inset frame, uppercase lime category eyebrow, and a
"Reach Social" wordline — but each post looks DISTINCT via two per-post levers,
both set in posts/<slug>.json so future posts just declare them:

  1. card_icon  -> a topical glyph (card_icons/<name>.svg), large + centered in
                   the lime accent. Defaults to the RS mark if unset/missing.
  2. slug seed  -> the background (lime-family accent hue, glow size/position,
                   dotted-grid density, gradient angle) is derived deterministic-
                   ally from the slug, so no two cards share a background and the
                   same slug always renders the same card.

There is NO headline and NO stat on the card (that would duplicate the H1 and
crop badly); all content is vertically centered so it survives the 160px-tall
index-grid center-crop.

Technique mirrors ~/.amzadvisers/image-gen/gen_images.py: fill the self-contained
card_template.html, screenshot with headless Chrome at 2x, downscale with Pillow
to an exact 1200x675 PNG.

Usage:
  python render_card.py <slug> "<Category>" [card_icon]
Or import:
  from render_card import render_card ;  render_card(slug, category, card_icon)
"""
import colorsys
import hashlib
import html as _html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

GEN = Path(__file__).resolve().parent          # blog/_generator
BLOG = GEN.parent                               # blog/
ASSETS = BLOG / "assets"
ICONS = GEN / "card_icons"
KIT = Path.home() / ".amzadvisers" / "brand-kits" / "reach" / "assets"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1200, 675


def fileurl(p: Path) -> str:
    return "file:///" + str(Path(p).resolve()).replace("\\", "/")


def seed_params(slug: str) -> dict:
    """Deterministic, lime-family background variation derived from the slug."""
    h = int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16)
    hue = (63 + h % 30) / 360.0          # 63..92 deg — yellow-green .. green (lime family)
    r, g, b = colorsys.hls_to_rgb(hue, 0.67, 0.92)
    R, G, B = round(r * 255), round(g * 255), round(b * 255)

    def rgba(a):
        return f"rgba({R},{G},{B},{a})"

    return {
        "ACCENT": f"#{R:02X}{G:02X}{B:02X}",
        "GLOW_STRONG": rgba(0.18),
        "GLOW_SOFT": rgba(0.05),
        "GLOW_DROP": rgba(0.42),
        "FRAME": rgba(0.16),
        "GLOW_X": 28 + (h >> 7) % 44,     # 28..71 %
        "GLOW_Y": 30 + (h >> 13) % 30,    # 30..59 %
        "GLOW_SIZE": 98 + (h >> 33) % 44, # 98..141 %
        "GRID": 22 + (h >> 19) % 12,      # 22..33 px
        "ANGLE": 150 + (h >> 25) % 64,    # 150..213 deg
    }


def icon_svg(card_icon: str) -> str:
    p = ICONS / f"{card_icon}.svg"
    if card_icon and p.exists():
        return p.read_text(encoding="utf-8")
    return (ASSETS / "rs-mark.svg").read_text(encoding="utf-8")   # brand-mark fallback


def build_html(slug: str, category: str, card_icon: str) -> str:
    tmpl = (GEN / "card_template.html").read_text(encoding="utf-8")
    css = KIT / "brand.css"
    out = (tmpl
           .replace("{{BRAND_CSS}}", fileurl(css) if css.exists() else "")
           .replace("<!--ICON-->", icon_svg(card_icon))
           .replace("{{EYEBROW}}", _html.escape(category)))
    for k, v in seed_params(slug).items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def render_card(slug: str, category: str, card_icon: str = "mark") -> Path:
    work = Path(tempfile.mkdtemp(prefix="reachcard_"))
    try:
        hp = work / "card.html"
        hp.write_text(build_html(slug, category, card_icon), encoding="utf-8")
        raw = work / "raw.png"
        cmd = [
            CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={work / 'prof'}",
            "--force-device-scale-factor=2", f"--window-size={W},{H}",
            "--virtual-time-budget=3000", "--run-all-compositor-stages-before-draw",
            f"--screenshot={raw}", fileurl(hp),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not raw.exists():
            raise RuntimeError(f"chrome screenshot failed: {r.stderr[-500:]}")
        ASSETS.mkdir(parents=True, exist_ok=True)
        out = ASSETS / f"{slug}-card.png"
        img = Image.open(raw).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        img.save(out, "PNG")
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    print("wrote", render_card(a[0], a[1], a[2] if len(a) > 2 else "mark"))


if __name__ == "__main__":
    main()
