#!/usr/bin/env python3
"""Builds the static site into ./docs

Usage:  python build.py
Needs:  pip install markdown
"""
import json, re, html, shutil, datetime, secrets
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
CFG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")


def read_partial(name):
    p = ROOT / "partials" / name
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    # strip HTML comments so an "empty" banner file renders nothing
    return re.sub(r"<!--.*?-->", "", txt, flags=re.S).strip()


def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta, body = {}, raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    meta["related"] = [s.strip() for s in meta.get("related", "").split(",") if s.strip()]
    meta["order"] = int(meta.get("order", "99"))
    meta["body_html"] = markdown.markdown(body, extensions=["tables", "sane_lists", "toc"])
    return meta


def url_for(lang, slug=""):
    prefix = CFG["languages"][lang]["prefix"]
    parts = [p for p in (prefix, slug) if p]
    return "/" + "/".join(parts) + ("/" if parts else "")


def esc(s):
    return html.escape(s, quote=True)


def cap(s):
    # keep brand casing such as "eBesucher"
    return s if (len(s) > 1 and s[1].isupper()) else s[:1].upper() + s[1:]


def banner(slot):
    b = read_partial(f"banner-{slot}.html")
    return f'<div class="ad ad-{slot}">{b}</div>' if b else ""


def hreflang_tags(slug, langs_with_slug):
    tags = []
    for l in langs_with_slug:
        tags.append(f'<link rel="alternate" hreflang="{l}" href="{BASE}{url_for(l, slug)}">')
    if CFG["default_lang"] in langs_with_slug:
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{url_for(CFG["default_lang"], slug)}">')
    return "\n".join(tags) if len(langs_with_slug) > 1 else ""


def page(lang, title, description, path, body, hreflang="", jsonld=None, cats=None, image=None):
    og_img = f'<meta property="og:image" content="{BASE}{image}">\n<meta property="og:image:width" content="1000">\n<meta property="og:image:height" content="1500">' if image else ""
    head_extra = read_partial("head.html")
    year = datetime.date.today().year
    nav = "".join(f'<a href="{url_for(lang)}#{c["id"]}">{esc(c["title"])}</a>' for c in (cats or CFG["categories"]))
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE}{path}">
{hreflang}
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{BASE}{path}">
{og_img}
<link rel="stylesheet" href="/assets/style.css">
{ld}
{head_extra}
</head>
<body>
<header class="site-head">
  <div class="wrap head-row">
    <a class="logo" href="{url_for(lang)}"><span class="logo-mark">Ð</span>{esc(CFG["site_name"])}</a>
    <nav class="nav">{nav}<a href="{url_for(lang, 'about')}">About</a></nav>
  </div>
</header>
{banner("top")}
<main class="wrap">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p class="disclosure"><strong>Disclosure:</strong> this site is published by the {esc(CFG["publisher"])}. SurfFlux is our own traffic exchange, and we link to it where it fits the topic. Other services are described as they are, without payment for placement. <a href="{url_for(lang, 'about')}">More about this site</a>.</p>
    <p>© {year} {esc(CFG["site_name"])}</p>
  </div>
</footer>
</body>
</html>
"""


def insert_inline_banner(body_html):
    b = banner("inline")
    if not b:
        return body_html
    idx = [m.start() for m in re.finditer(r"<h2", body_html)]
    if len(idx) >= 2:
        i = idx[1]
        return body_html[:i] + b + body_html[i:]
    return body_html + b


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    # files from static/ go to the site root unchanged (ads.txt, verification files, ...)
    st = ROOT / "static"
    if st.exists():
        for f in st.rglob("*"):
            if f.is_file() and f.name != "README.txt":
                dest = OUT / f.relative_to(st)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)

    # IndexNow key file
    key = CFG.get("indexnow_key") or ""
    if not key:
        key = secrets.token_hex(16)
        CFG["indexnow_key"] = key
        (ROOT / "site.json").write_text(json.dumps(CFG, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / f"{key}.txt").write_text(key)

    sitemap = []
    today = datetime.date.today().isoformat()

    # which slugs exist in which languages (for hreflang)
    content = {}
    for lang in CFG["languages"]:
        d = ROOT / "content" / lang
        content[lang] = {p.stem: parse(p) for p in sorted(d.glob("*.md"))} if d.exists() else {}
    slug_langs = {}
    for lang, arts in content.items():
        for slug in arts:
            slug_langs.setdefault(slug, []).append(lang)

    for lang, arts in content.items():
        about = arts.pop("about", None)
        # ---- articles ----
        for slug, a in arts.items():
            path = url_for(lang, slug)
            rel = [arts[s] | {"slug": s} for s in a["related"] if s in arts]
            rel_html = ""
            if rel:
                rel_html = '<aside class="related"><h2>Related guides</h2><ul>' + "".join(
                    f'<li><a href="{url_for(lang, r["slug"])}">{esc(cap(r.get("anchor", r["title"])))}</a></li>' for r in rel) + "</ul></aside>"
            cat = next((c for c in CFG["categories"] if c["id"] == a.get("category")), None)
            crumb = f'<nav class="crumbs"><a href="{url_for(lang)}">Home</a> › ' + (
                f'<a href="{url_for(lang)}#{cat["id"]}">{esc(cat["title"])}</a>' if cat else "") + "</nav>"
            body = f"""
<div class="layout">
<article class="article">
{crumb}
<h1>{esc(a["h1"] if a.get("h1") else a["title"])}</h1>
<p class="meta">By the {esc(CFG["publisher"])} · Updated {esc(a.get("updated", today))}</p>
{insert_inline_banner(a["body_html"])}
{rel_html}
</article>
<aside class="side">{banner("side")}</aside>
</div>"""
            jsonld = [{
                "@context": "https://schema.org", "@type": "Article", "headline": a["title"],
                "description": a.get("description", ""), "dateModified": a.get("updated", today),
                "author": {"@type": "Organization", "name": CFG["publisher"]},
                "publisher": {"@type": "Organization", "name": CFG["publisher"]},
                "mainEntityOfPage": BASE + path}, {
                "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + url_for(lang)},
                    {"@type": "ListItem", "position": 2, "name": a["title"], "item": BASE + path}]}]
            img = f"/assets/pins/{slug}.png" if (ROOT / "assets" / "pins" / f"{slug}.png").exists() else None
            if img:
                jsonld[0]["image"] = BASE + img
            html_out = page(lang, a["title"], a.get("description", ""), path, body,
                            hreflang_tags(slug, slug_langs.get(slug, [])), jsonld, image=img)
            dest = OUT / path.strip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html_out, encoding="utf-8")
            sitemap.append((BASE + path, a.get("updated", today)))

        # ---- catalog (home) ----
        intro_p = ROOT / "content" / lang / "_home.md.txt"
        intro = markdown.markdown(intro_p.read_text(encoding="utf-8")) if intro_p.exists() else ""
        sections = []
        for c in CFG["categories"]:
            items = sorted([(s, a) for s, a in arts.items() if a.get("category") == c["id"]], key=lambda x: x[1]["order"])
            if not items:
                continue
            cards = "".join(
                f'<li class="card"><a href="{url_for(lang, s)}"><span class="card-title">{esc(cap(a.get("anchor", a["title"])))}</span>'
                f'<span class="card-desc">{esc(a.get("description", ""))}</span></a></li>' for s, a in items)
            sections.append(f'<section class="cat" id="{c["id"]}"><h2>{esc(c["title"])}</h2><p>{esc(c["intro"])}</p><ul class="cards">{cards}</ul></section>')
        home_body = f'<div class="hero">{intro}</div>{banner("inline")}' + "".join(sections)
        home_path = url_for(lang)
        home_title = f'{CFG["site_name"]}: Traffic Exchange, PTC & DOGE Faucet Guides'
        jsonld = {"@context": "https://schema.org", "@type": "WebSite", "name": CFG["site_name"], "url": BASE + home_path}
        (OUT / home_path.strip("/")).mkdir(parents=True, exist_ok=True)
        (OUT / home_path.strip("/") / "index.html").write_text(
            page(lang, home_title, CFG["tagline"], home_path, home_body, "", jsonld), encoding="utf-8")
        sitemap.insert(0, (BASE + home_path, today))

        # ---- about ----
        if about:
            path = url_for(lang, "about")
            body = f'<article class="article narrow"><h1>{esc(about["title"])}</h1>{about["body_html"]}</article>'
            dest = OUT / path.strip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(page(lang, about["title"], about.get("description", ""), path, body), encoding="utf-8")
            sitemap.append((BASE + path, about.get("updated", today)))

    # 404
    (OUT / "404.html").write_text(page(CFG["default_lang"], "Page not found", "Page not found", "/404.html",
        f'<article class="article narrow"><h1>Page not found</h1><p>That page does not exist. <a href="/">Back to all guides</a>.</p></article>'), encoding="utf-8")

    # sitemap + robots
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in sitemap:
        sm.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    print(f"Built {len(sitemap)} pages into {OUT}")


if __name__ == "__main__":
    build()
