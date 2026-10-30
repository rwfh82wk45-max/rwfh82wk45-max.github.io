# Traffic & DOGE Guide

Static guide site (catalog + articles) that links to SurfFlux. Built with a small Python script, served by GitHub Pages from the `docs/` folder.

## Build

```bash
pip install markdown
python build.py
```

The finished site is written to `docs/`. Commit and push `docs/` together with the sources.

## GitHub Pages setup (one time)

Repository → Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, folder: **/docs** → Save.
The site appears at https://rwfh82wk45-max.github.io/ after a minute or two.

## Banners

Three banner slots, each in its own file in `partials/`:

| File | Where it shows |
|---|---|
| `banner-top.html` | under the header on every page |
| `banner-inline.html` | inside every article (before the 2nd heading) and on the home page |
| `banner-side.html` | right sidebar on articles, desktop only (300×250 or 300×600) |

Paste any HTML (image link, ad network code) into the file, then run `python build.py` again.
A file that contains only the comment is treated as empty and the slot is hidden.
Put banner images in `assets/banners/`.

## Articles

Articles are Markdown files in `content/en/`. The header (front matter) controls:

- `title` – `<title>` tag; `h1` – visible heading (optional)
- `description` – meta description and catalog card text
- `keyword` – main phrase from the keyword map
- `anchor` – link text used in the catalog and in "Related guides"
- `category` – one of the ids in `site.json`
- `order` – position in the catalog section
- `related` – comma-separated slugs (file names without `.md`)

The file name is the URL: `content/en/paid-to-click.md` → `/paid-to-click/`.
The home page intro is in `content/en/_home.md.txt`; the About page is `content/en/about.md`.

## Sitemap and IndexNow

`build.py` writes `docs/sitemap.xml`, `docs/robots.txt` and the IndexNow key file automatically.

After the site is live:

```bash
python scripts/indexnow.py        # submit all URLs from the sitemap
python scripts/indexnow.py URL    # submit one or more URLs
```

IndexNow covers Bing and other participating engines. Google does not use it: add the site in Google Search Console and submit `https://rwfh82wk45-max.github.io/sitemap.xml` there.

## Adding a language later

1. Add it to `languages` in `site.json`, e.g. `"es": {"name": "Español", "prefix": "es"}`.
2. Create `content/es/` with articles using the same file names as the English ones where they are translations. Matching file names get `hreflang` links automatically.
3. Do keyword research for that language first; do not just translate the English phrases.

## Note on GitHub Pages

GitHub's terms restrict get-rich-quick content on Pages. If the site is ever taken down, the same `docs/` folder can be deployed unchanged to Cloudflare Pages or Netlify.
