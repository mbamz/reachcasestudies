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
- `render_post.py` — renders one post + rebuilds all derived surfaces.
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
     `dek`, `date_iso`, `date_human`, `read_time`, `keywords` (array),
     `cta_pre`, `llms_summary`. Optional: `excerpt` (defaults to `dek`),
     `card_alt` (defaults to `og_title`), `author` (defaults to `Jackie He`).
   - `<slug>.body.html` — the article body, Reach Social company voice. Real
     numbers only, client names anonymized to category descriptors.

2. Generate the two images with the shared brand-kit generator
   (`~/.amzadvisers/image-gen/gen_images.py`), writing into `blog/assets/`:

   ```sh
   G=~/.amzadvisers/image-gen/gen_images.py
   # clean, TEXT-FREE thumbnail — logo + category eyebrow only (NO headline, NO stat)
   python "$G" --brand reach --slug <slug> --out blog/assets --types card \
       --eyebrow "<Category>"
   # OG share card — headline baked in is fine here
   python "$G" --brand reach --slug <slug> --out blog/assets --types og \
       --eyebrow "Reach Social · <Category>" --headline "<short headline>" \
       --impact "<one real stat>"
   ```

   Never generate a `-hero.png`. The in-body hero image is gone by design.

3. Render:

   ```sh
   python blog/_generator/render_post.py <slug>
   ```

   This writes `blog/<slug>/index.html`, promotes the post to the index
   `featured` slot, demotes the previously featured post to the top of the
   grid, and rebuilds `blog/sitemap.xml`, `blog/llms.txt`, and the index
   JSON-LD. It is idempotent: re-running a slug updates it in place; new slugs
   go to the front (newest → featured).

4. Re-render everything (e.g. after a template change):

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
