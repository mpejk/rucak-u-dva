#!/usr/bin/env python3
"""Snima kontrolnu stranicu ilustracija i izrađuje PNG ikone.
Pokretanje: .venv/bin/python alati/snimi.py [stranica-za-snimiti ...]
"""
import os
import sys
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORIJEN / "testovi"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(KORIJEN / ".radno" / "browsers"))
from playwright.sync_api import sync_playwright  # noqa: E402
from posluzitelj import posluzi  # noqa: E402

with posluzi() as url, sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 900})
    pg.goto(url + "slike.html")
    pg.wait_for_selector("body[data-spremno]")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(KORIJEN / ".radno" / "slike.png"), full_page=True)
    for vel in (180, 512):
        pg2 = b.new_page(viewport={"width": vel, "height": vel})
        pg2.set_content(f'<style>html,body{{margin:0}}</style><img src="{url}ikone/ikona.svg" width="{vel}" height="{vel}">')
        pg2.wait_for_timeout(200)
        pg2.screenshot(path=str(KORIJEN / "ikone" / f"ikona-{vel}.png"))
    for put in sys.argv[1:]:
        pg3 = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        pg3.goto(url + put)
        pg3.wait_for_timeout(600)
        ime = put.replace("/", "_").replace("#", "").replace("?", "_") or "pocetna"
        pg3.screenshot(path=str(KORIJEN / ".radno" / f"zaslon-{ime}.png"), full_page=True)
    b.close()
print("Snimljeno.")
