#!/usr/bin/env python3
"""Sends every URL from docs/sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver and others).

Run it AFTER the site is live, so the key file can be verified:
    python scripts/indexnow.py
Optional: pass specific URLs to submit only those:
    python scripts/indexnow.py https://example.github.io/some-page/

Note: Google does not use IndexNow. For Google, submit the sitemap in Search Console.
"""
import json, sys, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
key = cfg.get("indexnow_key")
if not key:
    sys.exit("No indexnow_key in site.json. Run build.py first.")
base = cfg["base_url"].rstrip("/")
host = urlparse(base).netloc

if len(sys.argv) > 1:
    urls = sys.argv[1:]
else:
    sm = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>(.*?)</loc>", sm)

payload = {"host": host, "key": key, "keyLocation": f"{base}/{key}.txt", "urlList": urls}
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs (200/202 = accepted)")
except urllib.error.HTTPError as e:
    print(f"IndexNow error HTTP {e.code}: {e.read().decode(errors='ignore')[:300]}")
    print("403 = key file not reachable yet (deploy first); 422 = URLs do not match the host.")
