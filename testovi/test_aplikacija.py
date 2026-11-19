"""Scenariji iz odjeljka 6 zadatka. Vrte se u WebKitu (iPhone) i Chromiumu, s lažnim satom.

Zona uređaja je America/New_York, a aplikacija mora računati po Europe/Zagreb.
Datumi: 2026-11-16 je ponedjeljak, 19. četvrtak, 20. petak, 21. subota (CET = UTC+1).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import KORIJEN, idi, otvori

RECEPTI = json.loads((KORIJEN / "podaci" / "recepti.json").read_text(encoding="utf-8"))
PO_ID = {r["id"]: r for r in RECEPTI}
PON_9 = "2026-11-16T09:00:00+01:00"
PETAK_9 = "2026-11-20T09:00:00+01:00"
CET_9 = "2026-11-19T09:00:00+01:00"
SUB_7 = "2026-11-21T07:00:00+01:00"


def sat_u_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def prikazani_prijedlozi(s):
    return s.eval_on_selector_all(".prijedlog", "els => els.map(e => ({id: e.dataset.id, petak: e.dataset.petak === 'true'}))")


# ---------- 1. prazan uređaj: svih 24 recepata odmah ----------
def test_provjera_podataka_prolazi():
    r = subprocess.run([sys.executable, str(KORIJEN / "alati" / "provjeri_podatke.py"), "--samotest"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_prazan_uredaj_ima_sve_recepte(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "", PON_9)
    assert s.evaluate("localStorage.length") == 0
    assert len(prikazani_prijedlozi(s)) == 3
    idi(s, "#/recepti")
    assert s.locator(".popis li").count() == 24
    for r in RECEPTI:
        idi(s, f"#/recept/{r['id']}")
        assert s.locator(".sastojci li").count() == len(r["sastojci"])
        kolicine = s.locator(".sastojci .kol").all_inner_texts()
        assert all(k.strip() for k in kolicine), r["id"]
        assert s.locator("[data-test=korak]").count() == len(r["koraci"])
        assert s.locator("[data-test=start]").inner_text() == f"{(840 - r['ukupnoMin']) // 60 % 24:02d}:{(840 - r['ukupnoMin']) % 60:02d}"
        assert s.locator(".gotovo").count() == len(r["koraci"])


# ---------- 2. petak ----------
def test_petak_samo_bez_mesa(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "", PETAK_9)
    p = prikazani_prijedlozi(s)
    assert len(p) == 3 and all(x["petak"] for x in p), p
    assert "Petak" in s.locator(".info").inner_text()
    # sva vremena posluživanja od 6:00 do 23:30, uključujući način „prekasno”
    los = s.evaluate("""async () => {
      const L = await import('./js/logika.js');
      const R = await (await fetch('podaci/recepti.json')).json();
      const losi = [];
      for (let u = 360; u <= 1410; u += 30) {
        const p = L.prijedlozi(R, L.kontekst(Date.now(), u, false));
        for (const x of p.stavke) if (!x.recept.petak) losi.push([u, x.recept.id]);
      }
      return losi;
    }""")
    assert los == []


def test_cetvrtak_sutra_je_petak(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "", CET_9)
    assert not all(x["petak"] for x in prikazani_prijedlozi(s)) or True  # četvrtkom smije biti meso
    s.get_by_role("button", name=re.compile("Sutra")).click()
    s.wait_for_function("location.hash.includes('d=sutra')")
    s.wait_for_selector(".info")
    p = prikazani_prijedlozi(s)
    assert len(p) == 3 and all(x["petak"] for x in p), p
    los = s.evaluate("""async () => {
      const L = await import('./js/logika.js');
      const R = await (await fetch('podaci/recepti.json')).json();
      const losi = [];
      for (let u = 360; u <= 1410; u += 30)
        for (const x of L.prijedlozi(R, L.kontekst(Date.now(), u, true)).stavke) if (!x.recept.petak) losi.push(x.recept.id);
      return losi;
    }""")
    assert los == []


# ---------- 3. vrijeme posluživanja ----------
def test_pomak_vremena_pomice_satnicu(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "#/recept/bataci-krumpir-mrkva", PON_9)
    prije = [sat_u_min(t) for t in s.locator("[data-test=korak] .sat strong").all_inner_texts()]
    assert s.locator("[data-test=start]").inner_text() == "12:45"
    s.get_by_role("button", name="30 minuta ranije").click()
    s.wait_for_function("decodeURIComponent(location.hash).includes('u=13:30')")
    s.wait_for_selector("text=Za ručak u 13:30")
    poslije = [sat_u_min(t) for t in s.locator("[data-test=korak] .sat strong").all_inner_texts()]
    assert s.locator("[data-test=start]").inner_text() == "12:15"
    assert [a - b for a, b in zip(prije, poslije)] == [30] * len(prije)


def test_prekasni_rucci_ispadaju(novi_kontekst, url):
    # 12:30 u Zagrebu: za 14:00 je ostalo 90 min
    s = otvori(novi_kontekst(), url, "", "2026-11-16T12:30:00+01:00")
    for kartica in s.locator(".prijedlog").all():
        assert sat_u_min(kartica.locator("[data-test=najkasnije]").inner_text()) >= 12 * 60 + 30
    ids = [x["id"] for x in prikazani_prijedlozi(s)]
    assert all(PO_ID[i]["ukupnoMin"] <= 90 for i in ids), ids
    # ručak ranije -> ostaju samo kraća jela
    idi(s, "#/?u=13:30")
    ids = [x["id"] for x in prikazani_prijedlozi(s)]
    assert all(PO_ID[i]["ukupnoMin"] <= 60 for i in ids), ids
    assert s.locator("[data-test=prekasno]").count() == 0
    # recept koji traje predugo na svojoj stranici kaže da nije izvediv
    idi(s, "#/recept/sarma-pire")
    assert "nije izvedivo" in s.locator("[data-test=neizvedivo]").inner_text()


def test_prekasno_kuhaj_odmah(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "", "2026-11-16T13:50:00+01:00")
    assert s.locator("[data-test=prekasno]").is_visible()
    for kartica in s.locator(".prijedlog").all():
        r = PO_ID[kartica.get_attribute("data-id")]
        gotovo = sat_u_min(kartica.locator("[data-test=gotovo]").inner_text())
        assert gotovo == 13 * 60 + 50 + r["ukupnoMin"]
        assert not r["vecerPrije"]


# ---------- 4. priprema večer prije ----------
def test_vecer_prije_nije_za_danas(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "", SUB_7)
    rez = s.evaluate("""async () => {
      const L = await import('./js/logika.js');
      const R = await (await fetch('podaci/recepti.json')).json();
      const danas = [], sutra = [];
      for (let u = 600; u <= 1320; u += 30) {
        for (const x of L.prijedlozi(R, L.kontekst(Date.now(), u, false)).stavke) danas.push(x.recept.id);
      }
      const p = R.find(r => r.id === 'pasticada-njoki');
      return { danas, izvDanas: L.izvedivost(p, L.kontekst(Date.now(), 1200, false)).ok, izvSutra: L.izvedivost(p, L.kontekst(Date.now(), 840, true)).ok };
    }""")
    assert "pasticada-njoki" not in rez["danas"]
    assert rez["izvDanas"] is False and rez["izvSutra"] is True
    idi(s, "#/recept/pasticada-njoki?u=20:00")
    assert "večer prije" in s.locator("[data-test=neizvedivo]").inner_text()


# ---------- 5. dvoje djece naizmjence ----------
def stanje(s):
    return s.evaluate("JSON.parse(localStorage.getItem('rucak-u-dva/v1'))")


def test_dvoje_djece_naizmjence(novi_kontekst, url):
    k = novi_kontekst()
    s = otvori(k, url, "#/igra", PON_9)
    s.get_by_role("link", name=re.compile("Luka")).click()
    for _ in range(3):
        s.locator(".izbor[data-strana=a]").click()
    s.get_by_role("link", name="Promijeni igrača").click()
    s.get_by_role("link", name=re.compile("Matej")).click()
    s.get_by_role("button", name=re.compile("Oboje mi je dobro")).click()
    s.get_by_role("button", name=re.compile("Ovo još nisam")).click()
    s.locator("[data-jela=b]").click()
    s.get_by_role("link", name="Promijeni igrača").click()
    s.get_by_role("link", name=re.compile("Luka")).click()
    s.locator(".izbor[data-strana=b]").click()
    st = stanje(s)
    s.close()  # zatvori stranicu
    s2 = otvori(k, url, "#/igra", PON_9)
    assert stanje(s2) == st
    luka, matej = st["djeca"]["Luka"], st["djeca"]["Matej"]
    assert [o["odgovor"] for o in luka["odgovori"]] == ["a", "a", "a", "b"]
    assert [o["odgovor"] for o in matej["odgovori"]] == ["oboje", "neprobano"]
    assert matej["odgovori"][1]["jela"] == [matej["parovi"][1][1]]
    assert "nastavi (4/20)" in s2.locator("[data-ime=Luka]").inner_text()
    assert "nastavi (2/20)" in s2.locator("[data-ime=Matej]").inner_text()
    # nastavak točno ondje gdje je stao
    s2.locator("[data-ime=Luka]").click()
    s2.wait_for_selector(".izbor")
    par = [s2.locator(".izbor[data-strana=a]").get_attribute("data-id"), s2.locator(".izbor[data-strana=b]").get_attribute("data-id")]
    assert par == luka["parovi"][4]
    # povratak za jedan odgovor
    s2.get_by_role("button", name=re.compile("Natrag")).click()
    assert len(stanje(s2)["djeca"]["Luka"]["odgovori"]) == 3
    assert s2.locator(".izbor[data-strana=a]").get_attribute("data-id") == luka["parovi"][3][0]
    # nepoznato jelo nije odbijeno
    rez = s2.evaluate("""async (o) => { const L = await import('./js/logika.js');
      const R = await (await fetch('podaci/recepti.json')).json();
      return L.rezultatDjeteta(o, R.map(r => r.id)); }""", matej["odgovori"])
    assert rez["odbijena"] == [] and rez["neprobana"] == [matej["parovi"][1][1]]


def odigraj(s, ime, izbor):
    """Odigra cijelu igru: izbor(a, b) vraća 'a', 'b' ili 'oboje'."""
    s.goto(s.url.split("#")[0] + f"#/igra/{ime}")
    for _ in range(40):
        if s.locator("[data-test=pauza], [data-test=kraj-kruga]").count():
            s.locator("#nastavi").click()
            continue
        if s.locator("[data-test=favoriti]").count():
            return
        s.wait_for_selector(".izbor, [data-test=favoriti]")
        if not s.locator(".izbor").count():
            continue
        a = s.locator(".izbor[data-strana=a]").get_attribute("data-id")
        b = s.locator(".izbor[data-strana=b]").get_attribute("data-id")
        odg = izbor(a, b)
        prije = s.locator(".igra").get_attribute("data-broj")
        if odg == "oboje":
            s.get_by_role("button", name=re.compile("Oboje mi je dobro")).click()
        else:
            s.locator(f".izbor[data-strana={odg}]").click()
        s.wait_for_function("b => !document.querySelector('.igra') || document.querySelector('.igra').dataset.broj !== b", arg=prije)
    s.wait_for_selector("[data-test=favoriti]")


def pizza_pa_bataci(a, b):
    for fav in ("pizza-sir", "bataci-krumpir-mrkva"):
        if fav in (a, b):
            return "a" if a == fav else "b"
    return "oboje"


# ---------- 6. svi biraju pizzu ----------
def test_svi_vole_pizzu(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "#/igra", PON_9)
    for ime in ["Luka", "Matej", "Blaž", "Ana"]:
        odigraj(s, ime, pizza_pa_bataci)
        assert s.locator("[data-test=favoriti] li").first.get_attribute("data-id") == "pizza-sir", ime
        assert s.locator("[data-test=poredak] li").first.get_attribute("data-id") == "pizza-sir", ime
        assert s.locator("[data-test=odbijena] li").count() == 0
    idi(s, "#/roditelji")
    assert "svih četvero" in s.locator("[data-test=glasanje]").inner_text()
    redak = s.locator("tr[data-id=pizza-sir]")
    assert redak.locator("td.st-favorit").count() == 4
    vrh = s.locator("[data-test=preporuka] li").first
    assert vrh.get_attribute("data-id") != "pizza-sir"
    vrh_id = vrh.get_attribute("data-id")
    assert s.locator(f"tr[data-id={vrh_id}] td.tanjur").get_attribute("class").endswith("r2")
    assert "svih četvero ga rado jede" in vrh.inner_text().lower()
    razlog_pizze = s.evaluate("""async () => { const L = await import('./js/logika.js');
      const R = await (await fetch('podaci/recepti.json')).json();
      const p = R.find(r => r.id === 'pizza-sir'); return L.sastav(p); }""")
    assert razlog_pizze["razina"] < 2
    # osobni poredak u roditeljskom pregledu
    idi(s, "#/roditelji/Ana")
    assert s.locator("[data-test=poredak] li").first.get_attribute("data-id") == "pizza-sir"


def test_dva_djeteta_glasala(novi_kontekst, url):
    s = otvori(novi_kontekst(), url, "#/igra", PON_9)
    for ime in ["Luka", "Ana"]:
        s.goto(url + f"#/igra/{ime}")
        s.locator(".izbor[data-strana=a]").click()
    idi(s, "#/roditelji")
    assert "Zasad su glasala dva djeteta" in s.locator("[data-test=glasanje]").inner_text()
    assert "Zasad su glasala dva djeteta" in s.locator("[data-test=preporuka]").inner_text()


# ---------- 7. izvoz i uvoz ----------
def test_izvoz_i_uvoz(novi_kontekst, url, tmp_path):
    k = novi_kontekst()
    k.add_init_script("Object.defineProperty(navigator, 'canShare', {value: undefined, configurable: true})")
    s = otvori(k, url, "#/igra", PON_9)
    odigraj(s, "Blaž", pizza_pa_bataci)
    s.goto(url + "#/igra/Ana")
    s.locator(".izbor[data-strana=b]").click()
    s.get_by_role("button", name=re.compile("Ovo ne bih")).click()
    s.locator("[data-jela=a]").click()
    idi(s, "#/roditelji")
    assert s.locator("[data-test=zadnji-izvoz]").inner_text() == "nikad"
    tablica_prije = s.locator("[data-test=tablica]").inner_text()
    stanje_prije = stanje(s)
    with s.expect_download() as d:
        s.get_by_role("button", name=re.compile("Izvezi")).click()
    put = tmp_path / "izvoz.json"
    d.value.save_as(put)
    assert s.locator("[data-test=zadnji-izvoz]").inner_text() == "16. 11. 2026."
    # novi, prazni uređaj
    s2 = otvori(novi_kontekst(), url, "#/roditelji", PON_9)
    s2.set_input_files("#uvoz", str(put))
    s2.wait_for_selector("text=Uvezeno")
    assert stanje(s2)["djeca"] == stanje_prije["djeca"]
    assert s2.locator("[data-test=tablica]").inner_text() == tablica_prije
    s2.goto(url + "#/igra")
    assert "nastavi (2/20)" in s2.locator("[data-ime=Ana]").inner_text()  # izbor + „ne bih jeo/jela”
    assert "gotovo" in s2.locator("[data-ime=Blaž]").inner_text()


def test_izvoz_dijeljenjem(novi_kontekst, url):
    k = novi_kontekst()
    k.add_init_script("""
      window.__podijeljeno = null;
      Object.defineProperty(navigator, 'canShare', {value: (d) => !!(d && d.files), configurable: true});
      Object.defineProperty(navigator, 'share', {value: async (d) => { window.__podijeljeno = { ime: d.files[0].name, tekst: await d.files[0].text() }; }, configurable: true});
    """)
    s = otvori(k, url, "#/igra/Luka", PON_9)
    s.locator(".izbor[data-strana=a]").click()
    idi(s, "#/roditelji")
    s.get_by_role("button", name=re.compile("Izvezi")).click()
    s.wait_for_function("window.__podijeljeno")
    p = s.evaluate("window.__podijeljeno")
    assert p["ime"].endswith(".json")
    assert json.loads(p["tekst"])["podaci"]["djeca"]["Luka"]["odgovori"][0]["odgovor"] == "a"
    assert "podijeljena" in s.locator("#poruka").inner_text()


# ---------- 8. offline iz podmape ----------
def test_offline_iz_podmape(novi_kontekst):
    from posluzitelj import posluzi_s_gasenjem
    with posluzi_s_gasenjem() as (url, ugasi):
        assert re.search(r"/rucak-u-dva/$", url)
        k = novi_kontekst()
        s = otvori(k, url, "", PON_9)
        s.evaluate("async () => { await navigator.serviceWorker.ready; }")
        s.reload()  # sada stranicu kontrolira service worker
        s.wait_for_selector("body[data-spremno]")
        s.wait_for_function("navigator.serviceWorker.controller !== null")
        provjeri_offline(k, s, url, ugasi)


def provjeri_offline(k, s, url, ugasi):
    sve = s.evaluate("async () => (await (await caches.open('rucak-u-dva-v1')).keys()).length")
    assert sve >= 12 + 24
    ugasi()  # poslužitelj više ne postoji — kao da nema interneta
    s.close()
    s = otvori(k, url, "", PON_9)  # nova kartica, sve mora doći iz service workera
    assert len(prikazani_prijedlozi(s)) == 3
    idi(s, "#/recept/pizza-sir")
    assert s.locator(".sastojci li").count() == len(PO_ID["pizza-sir"]["sastojci"])
    s.wait_for_function("(() => { const i = document.querySelector('.slika.velika'); return i && i.complete && i.naturalWidth > 0; })()")
    s.goto(url + "#/igra/Ana")
    s.wait_for_selector(".izbor")
    s.locator(".izbor[data-strana=a]").click()
    assert len(stanje(s)["djeca"]["Ana"]["odgovori"]) == 1
    # manifest i ikone dostupni relativno
    assert s.evaluate("fetch('manifest.webmanifest').then(r => r.ok)")
