#!/usr/bin/env python3
"""
render_post.py - Reach Social blog generator.

Renders a single blog post from its input files, then regenerates every
derived surface (blog index featured slot + grid, sitemap.xml, llms.txt,
and the index JSON-LD blogPost array) from a registry of all posts.

INPUT (per post), living in blog/_generator/posts/:
  <slug>.json        metadata (see FIELDS below)
  <slug>.body.html   the inner HTML of <article class="rs-post-body"> — h2/h3/p/
                     ul/callout/kpiband etc. NO surrounding <article> tag, NO
                     hero <figure> (the double-header bug), NO rs-mark-ornament
                     (the template appends it). Indent content with 4 spaces to
                     match the existing posts.

<slug>.json FIELDS (all strings unless noted):
  slug           url slug == folder name == image basename
  page_title     <title> text, e.g. "GMV Max on TikTok Shop | Reach Social"
  og_title       full headline, PLAIN text (no HTML, no double-quotes). Used in
                 og/twitter/JSON-LD/breadcrumb + as the clean card image alt.
  title_html     h1 / index headline, may contain a single <em>...</em>
  description    meta/og/twitter/JSON-LD description (<=160 chars, no dbl-quotes)
  eyebrow        hero eyebrow after "Reach Social &middot; " (e.g. "GMV Max")
  category       index card category label (usually == eyebrow)
  dek            hero sub-headline paragraph (HTML entities ok)
  excerpt        index card excerpt (defaults to dek if omitted)
  author         byline author (e.g. "Jackie He")
  date_iso       YYYY-MM-DD
  date_human     e.g. "July 28, 2026"
  read_time      e.g. "7 min read"
  keywords       JSON array of strings -> JSON-LD "about"
  cta_pre        bottom CTA band pre line, may contain <em>...</em>
  card_alt       alt text for the clean card thumbnail (defaults to og_title)
  llms_summary   one-line summary for llms.txt (defaults to description)

Usage:
  python render_post.py <slug>            # render one post + rebuild index/sitemap/llms
  python render_post.py --all             # re-render every post in the registry (idempotent)

Images are generated separately via ~/.amzadvisers/image-gen/gen_images.py
(see README.md). This script never touches PNGs.
"""
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent          # blog/_generator
BLOG = GEN.parent                               # blog/
POSTS = GEN / "posts"
REGISTRY = POSTS / "registry.json"
TEMPLATE = GEN / "template.html"
SITE = "https://reachsocial.co"


def wlf(path: Path, text: str):
    """Write text with LF newlines (never CRLF) regardless of platform."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --------------------------------------------------------------------------- #
# Post page
# --------------------------------------------------------------------------- #
def load_meta(slug: str) -> dict:
    m = json.loads((POSTS / f"{slug}.json").read_text(encoding="utf-8"))
    m["slug"] = slug
    m.setdefault("excerpt", m["dek"])
    m.setdefault("card_alt", m["og_title"])
    m.setdefault("llms_summary", m["description"])
    m.setdefault("author", "Jackie He")
    return m


def render_page(meta: dict) -> str:
    body = (POSTS / f"{meta['slug']}.body.html").read_text(encoding="utf-8").rstrip("\n")
    kw = ",".join(json.dumps(k, ensure_ascii=False) for k in meta["keywords"])
    t = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{SLUG}}": meta["slug"],
        "{{PAGE_TITLE}}": meta["page_title"],
        "{{OG_TITLE}}": meta["og_title"],
        "{{TITLE_HTML}}": meta["title_html"],
        "{{DESCRIPTION}}": meta["description"],
        "{{EYEBROW}}": meta["eyebrow"],
        "{{DEK}}": meta["dek"],
        "{{DATE_ISO}}": meta["date_iso"],
        "{{DATE_HUMAN}}": meta["date_human"],
        "{{READ_TIME}}": meta["read_time"],
        "{{KEYWORDS_JSON}}": kw,
        "{{CTA_PRE}}": meta["cta_pre"],
        "{{BODY_HTML}}": body,
    }
    for k, v in repl.items():
        t = t.replace(k, v)
    left = re.findall(r"{{[A-Z_]+}}", t)
    if left:
        raise SystemExit(f"unfilled placeholders: {sorted(set(left))}")
    return t


def write_page(meta: dict) -> Path:
    out = BLOG / meta["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    wlf(out, render_page(meta))
    return out


# --------------------------------------------------------------------------- #
# Registry (source of truth for all derived surfaces, newest first)
# --------------------------------------------------------------------------- #
def load_registry() -> list:
    return json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else []


def save_registry(reg: list):
    wlf(REGISTRY, json.dumps(reg, indent=2, ensure_ascii=False) + "\n")


def upsert(reg: list, meta: dict) -> list:
    idx = next((i for i, p in enumerate(reg) if p["slug"] == meta["slug"]), None)
    if idx is None:
        reg.insert(0, meta)          # new post -> newest -> featured
    else:
        reg[idx] = meta              # existing -> update in place, keep order
    return reg


# --------------------------------------------------------------------------- #
# Derived surfaces
# --------------------------------------------------------------------------- #
def url_for(slug: str) -> str:
    return f"{SITE}/blog/{slug}/"


def featured_html(p: dict) -> str:
    return (
        '<section class="featured-wrap">\n'
        '  <span class="featured-label">Latest post</span>\n'
        f'  <a class="featured" href="{url_for(p["slug"])}">\n'
        f'    <span class="img"><img src="/blog/assets/{p["slug"]}-card.png" alt="{p["card_alt"]}" loading="eager"></span>\n'
        '    <span class="txt">\n'
        f'      <span class="cat">{p["category"]}</span>\n'
        f'      <h2>{p["title_html"]}</h2>\n'
        f'      <span class="excerpt">{p["excerpt"]}</span>\n'
        f'      <span class="meta"><span class="author">{p["author"]}</span> &middot; <time datetime="{p["date_iso"]}">{p["date_human"]}</time> &middot; {p["read_time"]}</span>\n'
        '      <span class="read">Read the post &rarr;</span>\n'
        '    </span>\n'
        '  </a>\n'
        '</section>'
    )


def card_html(p: dict) -> str:
    return (
        f'  <a class="post-card" href="{url_for(p["slug"])}">\n'
        f'    <img class="thumb" src="/blog/assets/{p["slug"]}-card.png" alt="{p["card_alt"]}" loading="lazy">\n'
        '    <span class="body">\n'
        f'      <span class="cat">{p["category"]}</span>\n'
        f'      <h3>{p["title_html"]}</h3>\n'
        f'      <span class="excerpt">{p["excerpt"]}</span>\n'
        f'      <span class="meta"><span class="author">{p["author"]}</span> &middot; <time datetime="{p["date_iso"]}">{p["date_human"]}</time> &middot; {p["read_time"]}</span>\n'
        '      <span class="read">Read the post &rarr;</span>\n'
        '    </span>\n'
        '  </a>'
    )


def blogpost_json(p: dict) -> str:
    obj = {
        "@type": "BlogPosting",
        "headline": p["og_title"],
        "url": url_for(p["slug"]),
        "datePublished": p["date_iso"],
        "author": {"@type": "Person", "name": p["author"]},
        "image": f"{SITE}/blog/assets/{p['slug']}-og.png",
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def rebuild_index(reg: list):
    idx = BLOG / "index.html"
    html = idx.read_text(encoding="utf-8")
    feat, rest = reg[0], reg[1:]

    html = re.sub(r'<section class="featured-wrap">.*?</section>',
                  lambda _: featured_html(feat), html, count=1, flags=re.DOTALL)

    grid_inner = ('\n  <!-- New post cards get inserted at the TOP of this grid '
                  '(previous featured post moves here on each publish). -->\n'
                  + "\n".join(card_html(p) for p in rest) + "\n")
    html = re.sub(r'(<main class="post-grid" id="post-grid">).*?(</main>)',
                  lambda m: m.group(1) + grid_inner + m.group(2), html, count=1, flags=re.DOTALL)

    arr = "[" + ",".join(blogpost_json(p) for p in reg) + "]"
    html = re.sub(r'"blogPost":\[.*?\]', lambda _: '"blogPost":' + arr, html, count=1, flags=re.DOTALL)

    wlf(idx, html)


def rebuild_sitemap(reg: list):
    newest = reg[0]["date_iso"]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             '  <url>', f'    <loc>{SITE}/blog/</loc>', f'    <lastmod>{newest}</lastmod>',
             '    <changefreq>weekly</changefreq>', '    <priority>0.8</priority>', '  </url>']
    for p in reg:
        parts += ['  <url>', f'    <loc>{url_for(p["slug"])}</loc>',
                  f'    <lastmod>{p["date_iso"]}</lastmod>',
                  '    <changefreq>monthly</changefreq>', '    <priority>0.7</priority>', '  </url>']
    parts += ['</urlset>', '']
    wlf(BLOG / "sitemap.xml", "\n".join(parts))


def rebuild_llms(reg: list):
    f = BLOG / "llms.txt"
    txt = f.read_text(encoding="utf-8")
    lines = [f'- [{p["og_title"]}]({url_for(p["slug"])}): {p["llms_summary"]} Published {p["date_iso"]}.'
             for p in reg]
    block = "## Posts\n\n" + "\n".join(lines) + "\n\n## Related"
    txt = re.sub(r'## Posts\n\n.*?\n\n## Related', lambda _: block, txt, count=1, flags=re.DOTALL)
    wlf(f, txt)


# --------------------------------------------------------------------------- #
def render(slug: str):
    meta = load_meta(slug)
    page = write_page(meta)
    reg = upsert(load_registry(), meta)
    save_registry(reg)
    rebuild_index(reg)
    rebuild_sitemap(reg)
    rebuild_llms(reg)
    print(f"rendered {page}  |  registry={len(reg)} posts  |  featured={reg[0]['slug']}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--all":
        for p in load_registry():
            meta = load_meta(p["slug"])
            write_page(meta)
        reg = load_registry()
        rebuild_index(reg); rebuild_sitemap(reg); rebuild_llms(reg)
        print(f"re-rendered {len(reg)} posts")
    else:
        render(sys.argv[1])


if __name__ == "__main__":
    main()
