#!/usr/bin/env python3
"""Generates Pinterest pin images (1000x1500) and a bulk-upload CSV.

Usage:  pip install playwright && playwright install chromium
        python scripts/make_pins.py
Output: assets/pins/<slug>.png  and  pins.csv (Pinterest "Create Pins in bulk")
Then run python build.py so the images are copied into docs/ and used as og:image.
"""
import csv, json, html, datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
data = json.loads((ROOT / "scripts" / "pins.json").read_text(encoding="utf-8"))
base = cfg["base_url"].rstrip("/")
host = base.split("//", 1)[1]
out = ROOT / "assets" / "pins"
out.mkdir(parents=True, exist_ok=True)

ACCENT = {"traffic-exchange": "#e0b84a", "traffic": "#5cc8b8", "earn": "#f08a6c", "faucetpay-doge": "#e0b84a"}


def category_of(slug):
    md = (ROOT / "content" / "en" / f"{slug}.md").read_text(encoding="utf-8")
    for line in md.splitlines():
        if line.startswith("category:"):
            return line.split(":", 1)[1].strip()
    return "traffic-exchange"


TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:#07162e;color:#fff;font-family:'Inter Display','Inter',sans-serif;position:relative;overflow:hidden}}
.glow{{position:absolute;width:900px;height:900px;border-radius:50%;right:-380px;top:-300px;background:radial-gradient(circle,{acc}33 0%,transparent 65%)}}
.mark{{position:absolute;right:-60px;bottom:170px;font-size:760px;font-weight:800;line-height:1;color:{acc};opacity:.07}}
.inner{{position:absolute;inset:90px 84px 84px 84px;display:flex;flex-direction:column}}
.pill{{align-self:flex-start;background:{acc};color:#07162e;font-weight:700;font-size:30px;letter-spacing:.04em;text-transform:uppercase;padding:14px 26px;border-radius:999px}}
h1{{margin-top:auto;font-size:{size}px;line-height:1.04;font-weight:800;letter-spacing:-.02em}}
.rule{{width:120px;height:10px;background:{acc};border-radius:5px;margin:48px 0 36px}}
.sub{{font-size:42px;line-height:1.3;color:#c9d2e3;font-weight:500;margin-bottom:auto}}
.foot{{display:flex;align-items:center;gap:20px;border-top:2px solid #ffffff22;padding-top:34px;margin-top:60px}}
.logo{{width:64px;height:64px;border-radius:50%;background:#e0b84a;color:#07162e;display:grid;place-items:center;font-weight:800;font-size:38px}}
.name{{font-size:34px;font-weight:700}} .url{{font-size:26px;color:#9aa4b5;margin-top:4px}}
</style></head><body><div class="glow"></div><div class="mark">Ð</div>
<div class="inner"><div class="pill">{label}</div><h1>{headline}</h1><div class="rule"></div><div class="sub">{sub}</div>
<div class="foot"><div class="logo">Ð</div><div><div class="name">{site}</div><div class="url">{host}</div></div></div></div></body></html>"""

rows = []
start = datetime.date.today() + datetime.timedelta(days=1)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1000, "height": 1500})
    for i, pin in enumerate(data["pins"]):
        cat = category_of(pin["slug"])
        n = len(pin["headline"])
        size = 112 if n <= 28 else 98 if n <= 40 else 88
        page.set_content(TEMPLATE.format(acc=ACCENT[cat], label=html.escape(data["labels"][cat]),
                                         headline=html.escape(pin["headline"]), sub=html.escape(pin["sub"]),
                                         size=size, site=html.escape(cfg["site_name"]), host=host))
        page.wait_for_timeout(100)
        page.screenshot(path=str(out / f"{pin['slug']}.png"))
        # two pins a day, 09:00 and 18:00, starting tomorrow (Pinterest accepts dates up to 14 days ahead)
        day = start + datetime.timedelta(days=i // 2)
        when = f"{day.isoformat()}T{'09' if i % 2 == 0 else '18'}:00:00"
        rows.append({"Title": pin["title"][:100], "Media URL": f"{base}/assets/pins/{pin['slug']}.png",
                     "Pinterest board": data["boards"][cat], "Thumbnail": "", "Description": pin["desc"][:500],
                     "Link": f"{base}/{pin['slug']}/", "Publish date": when, "Keywords": pin["keywords"]})
    browser.close()

with open(ROOT / "pins.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} pins -> {out} and pins.csv")
