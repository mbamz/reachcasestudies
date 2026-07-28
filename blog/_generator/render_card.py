#!/usr/bin/env python3
"""
render_card.py - Reach blog cover-card renderer (the blog owns its card art).

Renders a branded 1200x675 "cover" thumbnail for a blog post: the Reach mark
large and centered on a dark panel with a subtle lime radial glow, the uppercase
lime category eyebrow beneath it, and a small "Reach Social" wordline. NO post
headline, NO stat pill — so it never duplicates the H1 and never crops weirdly
in the 160px-tall index grid (all content is vertically centered inside the
safe zone).

Technique mirrors ~/.amzadvisers/image-gen/gen_images.py: fill a self-contained
HTML template (card_template.html), screenshot with headless Chrome at 2x, then
downscale with Pillow to an exact 1200x675 PNG.

Usage:
  python render_card.py <slug> "<Category>"     # e.g. what-is-gmv-max-tiktok-shop "GMV Max"

Or import:  from render_card import render_card ;  render_card(slug, category)
"""
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
KIT = Path.home() / ".amzadvisers" / "brand-kits" / "reach" / "assets"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1200, 675


def fileurl(p: Path) -> str:
    return "file:///" + str(Path(p).resolve()).replace("\\", "/")


def build_html(category: str) -> str:
    tmpl = (GEN / "card_template.html").read_text(encoding="utf-8")
    mark = (ASSETS / "rs-mark.svg").read_text(encoding="utf-8")
    css = KIT / "brand.css"
    css_url = fileurl(css) if css.exists() else ""
    return (tmpl
            .replace("{{BRAND_CSS}}", css_url)
            .replace("<!--MARK-->", mark)
            .replace("{{EYEBROW}}", _html.escape(category)))


def render_card(slug: str, category: str) -> Path:
    work = Path(tempfile.mkdtemp(prefix="reachcard_"))
    try:
        hp = work / "card.html"
        hp.write_text(build_html(category), encoding="utf-8")
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
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print("wrote", render_card(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
