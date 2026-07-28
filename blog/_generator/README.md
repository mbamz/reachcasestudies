# Reach Social blog generator

A real, re-runnable generator so the blog chrome stops drifting. One template,
one script, one registry. Every post page and every derived surface (index,
sitemap, llms.txt, JSON-LD) is produced from the same source of truth.

## Files

- `template.html` — the canonical post shell, extracted verbatim from the good
  reachsocial.co chrome (header `rs-site-header`, topbar, newsletter, footer
  `rs-site-footer`, styles, scripts). It has **no** in-body hero `<figure>`
  (that was the double-header bug). Placeholders: `{{PAGE_TITLE}}`,
  `{{OG_TITLE}}`, `{{TITLE_HTML}}`, `{{DESCRIPTION}}`, `{{EYEBROW}}`, `{{DEK}}`,
  `{{DATE_ISO}}`, `{{DATE_HUMAN}}`, `{{READ_TIME}}`, `{{KEYWORDS_JSON}}`,
  `{{CTA_PRE}}`, `{{SLUG}}`, `{{BODY_HTML}}`. The OG image is derived as
  `/blog/assets/{{SLUG}}-og.png`; every canonical/og/JSON-LD URL and both CTA
  `utm_campaign` values are derived from `{{SLUG}}`.
- `render_post.py` — renders one post + rebuilds all derived surfaces, and (by
  default) regenerates the post's cover card.
- `render_card.py` + `card_template.html` + `card_icons/` — the blog's **own**
  cover-card renderer. Produces a **per-post distinct** `blog/assets/<slug>-card.png`
  that still reads as one family (dark panel, inset frame, uppercase lime category
  eyebrow, "Reach Social" wordline). Each card differs via two per-post levers:
  - **`card_icon`** (json field): a topical glyph from `card_icons/<name>.svg`,
    large + centered in the lime accent. Shipped icons: `growth`, `network`,
    `checklist`, `storefront`. Add more by dropping a `<name>.svg` (viewBox
    `0 0 100 100`, `stroke`/`fill` = `currentColor`) into `card_icons/` and
    referencing it from the post json. Unset/unknown → falls back to the RS mark.
  - **slug seed**: the background (lime-family accent hue, glow size/position,
    dotted-grid density, gradient angle) is derived deterministically from the
    slug — no two backgrounds match, and the same slug always renders the same
    card.
  NO headline, NO stat; everything is vertically centered so it never crops
  weirdly in the 160px grid (verified against a simulated center-crop). Same
  technique as gen_images (self-contained template → headless Chrome screenshot
  at 2x → Pillow downscale to 1200x675). The blog owns its card art; the shared
  `gen_images.py` is used only for the OG share image now.
- `posts/<slug>.json` — per-post metadata (fields documented in the script
  header).
- `posts/<slug>.body.html` — the inner HTML of `<article class="rs-post-body">`
  (h2/h3/p/ul/`rs-callout`/`rs-kpiband`). No `<article>` wrapper, no hero
  `<figure>`, no `rs-mark-ornament` (the template appends it). Indent 4 spaces.
- `posts/registry.json` — ordered newest-first list of all posts. Source of
  truth for the index featured slot + grid, sitemap, llms.txt, and the index
  JSON-LD `blogPost` array. Generated; do not hand-edit.

## How the Reach Blog Writer publishes a post

1. Author the two input files in `blog/_generator/posts/`:
   - `<slug>.json` — set `slug`, `page_title`, `og_title` (plain, **no
     double-quotes**), `title_html` (may contain one `<em>...</em>`),
     `description` (<=160 chars, no double-quotes), `eyebrow`, `category`,
     `card_icon` (one of `card_icons/` — `growth`/`network`/`checklist`/
     `storefront`, or a new one you add; picks the cover glyph), `dek`,
     `date_iso`, `date_human`, `read_time`, `keywords` (array), `cta_pre`,
     `llms_summary`. Optional: `excerpt` (defaults to `dek`), `card_alt`
     (defaults to `og_title`), `author` (defaults to `Jackie He`).
   - `<slug>.body.html` — the article body, Reach Social company voice. Real
     numbers only, client names anonymized to category descriptors.

2. Generate the OG share image with the shared brand-kit generator
   (`~/.amzadvisers/image-gen/gen_images.py`), writing into `blog/assets/`.
   The cover **card** is produced by `render_post.py` (step 3) — do NOT make a
   card with gen_images, and never make a `-hero.png` (the in-body hero is gone
   by design):

   ```sh
   G=~/.amzadvisers/image-gen/gen_images.py
   # OG share card — headline baked in is fine here
   python "$G" --brand reach --slug <slug> --out blog/assets --types og \
       --eyebrow "Reach Social · <Category>" --headline "<short headline>" \
       --impact "<one real stat>"
   ```

3. Render (writes the page, regenerates the cover card, rebuilds every surface):

   ```sh
   python blog/_generator/render_post.py <slug>
   ```

   This writes `blog/<slug>/index.html`, regenerates `blog/assets/<slug>-card.png`
   via `render_card.py`, promotes the post to the index `featured` slot, demotes
   the previously featured post to the top of the grid, and rebuilds
   `blog/sitemap.xml`, `blog/llms.txt`, and the index JSON-LD. It is idempotent:
   re-running a slug updates it in place; new slugs go to the front (newest →
   featured). Pass `--no-card` to skip card regeneration (e.g. no Chrome). The
   card can also be made on its own:

   ```sh
   python blog/_generator/render_card.py <slug> "<Category>"
   ```

4. Re-render everything (e.g. after a template or card-design change):

   ```sh
   python blog/_generator/render_post.py --all
   ```

## Preview locally

```sh
cd C:/dev/reachcasestudies
python -m http.server 8000
# then open http://localhost:8000/blog/  (paths are root-absolute, so serve the repo root)
```

## Notes

- All outputs are written with LF newlines.
- Do not reintroduce `<slug>-hero.png` or the `rs-post-figure` in-body image.
- `template.html` is byte-faithful to the live chrome: two of the three
  pre-existing posts round-trip identically through the generator; the third
  (`tiktok-shop-strategy-retail-not-social`) only changes where it had drifted
  (its three description variants get unified, and its CTA `utm` params get
  normalized to the canonical pattern).
