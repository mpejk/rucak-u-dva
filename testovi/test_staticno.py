"""Statičke provjere: relativne putanje, bez CDN-a, noindex, imena samo na jednom mjestu, bez dobi."""
import re
import subprocess

from conftest import KORIJEN

def datoteke_u_repo():
    izlaz = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=KORIJEN, capture_output=True, text=True).stdout
    return [KORIJEN / p for p in izlaz.split() if p]


def test_relativne_putanje_i_bez_cdn():
    for p in ["index.html", "slike.html", "sw.js", "manifest.webmanifest", *[f"js/{x}" for x in ("app.js", "logika.js", "pohrana.js", "obitelj.js")], "css/stil.css"]:
        t = (KORIJEN / p).read_text(encoding="utf-8")
        assert not re.search(r'(src|href)="/', t), p
        assert not re.search(r"<script[^>]+src=\"https?:", t), p
        assert "fonts.googleapis" not in t and "@import" not in t, p
        assert not re.search(r"""import .* from ['"](https?:|/)""", t), p


def test_noindex():
    for p in ("index.html", "slike.html"):
        assert 'name="robots" content="noindex' in (KORIJEN / p).read_text(encoding="utf-8")


def test_imena_samo_na_jednom_mjestu_i_bez_dobi():
    imena = ["Luka", "Matej", "Blaž", "Ana"]
    for p in datoteke_u_repo():
        if p.suffix not in {".html", ".js", ".css", ".json", ".md", ".py", ".webmanifest", ".svg"} or "testovi" in p.parts:
            continue
        t = p.read_text(encoding="utf-8")
        if p.name == "obitelj.js":
            assert all(i in t for i in imena)
            continue
        for i in imena:
            assert not re.search(rf"\b{i}\b", t), f"{i} u {p}"
        assert not re.search(r"14,\s*11,\s*8\s*i\s*6|\b(14|11|8|6)\s*godin", t), f"dob u {p}"


def test_ilustracije():
    import json
    recepti = json.loads((KORIJEN / "podaci" / "recepti.json").read_text(encoding="utf-8"))
    for r in recepti:
        t = (KORIJEN / "slike" / f"{r['id']}.svg").read_text(encoding="utf-8")
        assert t.startswith("<svg") and 'viewBox="0 0 240 240"' in t and "<image" not in t
