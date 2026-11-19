import os
import sys
from pathlib import Path

import pytest

KORIJEN = Path(__file__).resolve().parent.parent
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(KORIJEN / ".radno" / "browsers"))
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright  # noqa: E402
from posluzitelj import posluzi  # noqa: E402


@pytest.fixture(scope="session")
def url():
    with posluzi() as u:
        yield u


@pytest.fixture(scope="session")
def pw():
    with sync_playwright() as p:
        yield p


PREGLEDNICI = ["webkit-iphone", "chromium"]


@pytest.fixture(scope="session", params=PREGLEDNICI)
def preglednik(request, pw):
    ime = request.param
    b = (pw.webkit if ime.startswith("webkit") else pw.chromium).launch()
    b.ime = ime
    yield b
    b.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    izvjestaj = (yield).get_result()
    if izvjestaj.when == "call":
        item.pao = izvjestaj.failed


@pytest.fixture
def novi_kontekst(request, preglednik, pw, url):
    """Tvornica praznih „uređaja”. Zona uređaja namjerno NIJE Zagreb."""
    otvoreni = []

    def napravi(**dodatno):
        opcije = dict(pw.devices["iPhone 13"]) if preglednik.ime.startswith("webkit") else {"viewport": {"width": 1280, "height": 900}}
        opcije.pop("default_browser_type", None)
        opcije.update({"timezone_id": "America/New_York", "locale": "hr-HR", "accept_downloads": True})
        opcije.update(dodatno)
        k = preglednik.new_context(**opcije)
        otvoreni.append(k)
        return k

    yield napravi
    if getattr(request.node, "pao", False):  # snimka zaslona za dijagnozu
        for i, k in enumerate(otvoreni):
            for j, s in enumerate(k.pages):
                try:
                    s.screenshot(path=str(KORIJEN / ".radno" / f"neuspjeh-{request.node.name}-{i}-{j}.png"))
                    (KORIJEN / ".radno" / f"neuspjeh-{request.node.name}-{i}-{j}.txt").write_text(s.url + "\n" + s.content()[:3000])
                except Exception:
                    pass
    for k in otvoreni:
        k.close()


def otvori(kontekst, url, put="", vrijeme=None):
    """Nova stranica s lažnim satom (ISO vrijeme sa zonom)."""
    s = kontekst.new_page()
    if vrijeme:
        s.clock.set_fixed_time(vrijeme)
    s.goto(url + put)
    s.wait_for_selector("body[data-spremno]")
    return s


def idi(s, put):
    s.evaluate("p => { document.body.removeAttribute('data-spremno'); location.hash = p; }", put)
    s.wait_for_selector("body[data-spremno]")
