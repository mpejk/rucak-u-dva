#!/usr/bin/env python3
"""Provjera podataka recepata (odjeljak 2 zadatka).

Pokretanje:  python3 alati/provjeri_podatke.py [putanja/do/recepti.json]
Izlazni kod 0 = sve u redu. S --samotest provjerava i da provjera hvata pokvarene zapise.
"""
import copy
import json
import re
import sys
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
OBAVEZNA_POLJA = {
    "id": str, "naziv": str, "kratkiNaziv": str, "glavno": str, "petak": bool,
    "vecerPrije": bool, "tip": str, "ukupnoMin": int, "aktivnoMin": int,
    "oprema": list, "istodobno": str, "deklaracija": str, "sastojci": list, "koraci": list,
}
SKUPINE = {"povrce", "bjelancevine", "zitarice", "mlijecno", "masnoca", "zacin", "ostalo"}
TIPOVI = {"radni", "vikend", "oboje"}

# Sastojci koji obično sadrže gluten (brašno, tjestenina, njoki, kruh, mrvice, griz,
# kuskus, ječam, raž, pivo, soja umak, gotov temeljac ili kocka) i srodni oblici.
GLUTEN = re.compile(
    r"brašn|tjesten|špaget|njok|kruh|mrvic|griz|kuskus|ječam|ječm|\braž|pivo|piva|\bsoj|"
    r"temeljac|temeljca|kock|lazanj|pecivo|peciva|tijest|mlinc|panko|zemičk|tortilj",
    re.IGNORECASE)
# Meso, suhomesnato, mast i mesni temeljac (zabranjeno u petak).
MESO = re.compile(
    r"pilet|pileć|pile\b|junet|junec|juneć|govedin|goveđ|svinj|slanin|pršut|šunk|kobasic|"
    r"salam|hrenovk|puret|pureć|purić|telet|teleć|janj|mesn|\bmast\b|svinjsk|čvarc|pancet|"
    r"špek|\bmeso|ćevap|rebr|dimljen|bunc|kulen|batak|bataci|odrez",
    re.IGNORECASE)


def provjeri_recept(r):
    g = []
    rid = r.get("id", "?")
    for polje, tip in OBAVEZNA_POLJA.items():
        if polje not in r:
            g.append(f"{rid}: nedostaje polje '{polje}'")
        elif not isinstance(r[polje], tip) or (tip in (str, list) and not r[polje]):
            g.append(f"{rid}: polje '{polje}' je prazno ili krivog tipa")
    if g:
        return g
    if r["tip"] not in TIPOVI:
        g.append(f"{rid}: nepoznat tip '{r['tip']}'")
    if r["vecerPrije"] and not (r.get("pripremaUnaprijed") or {}).get("tekst"):
        g.append(f"{rid}: recept traži pripremu večer prije, a nema 'pripremaUnaprijed'")

    # sastojci
    for s in r["sastojci"]:
        ime = s.get("naziv", "")
        if not ime or not s.get("kolicina"):
            g.append(f"{rid}: sastojak bez naziva ili količine: {s}")
        if s.get("skupina") not in SKUPINE:
            g.append(f"{rid}: sastojak '{ime}' ima nepoznatu skupinu")
        if GLUTEN.search(ime):
            if not (s.get("bg") is True and "bezglutensk" in ime.lower()):
                g.append(f"{rid}: sastojak '{ime}' obično sadrži gluten, a nije označen kao bezglutenski")
            if not s.get("deklaracija"):
                g.append(f"{rid}: sastojak '{ime}' nema napomenu o deklaraciji")
        if r["petak"] and (s.get("meso") or MESO.search(ime)):
            g.append(f"{rid}: jelo za petak sadrži meso/suhomesnato/mast/mesni temeljac: '{ime}'")
    if not any(s.get("skupina") in ("povrce", "bjelancevine", "zitarice", "mlijecno") and s.get("grama")
               for s in r["sastojci"]):
        g.append(f"{rid}: nema sastojaka s gramima za procjenu sastava obroka")

    # koraci i trajanja
    kraj = 0
    aktivni = []
    for i, k in enumerate(r["koraci"]):
        for p in ("od", "min", "tekst", "gotovo"):
            if p not in k or k[p] in ("", None):
                g.append(f"{rid}: korak {i + 1} nema '{p}'")
        if g:
            continue
        if k["min"] <= 0 or k["od"] < 0:
            g.append(f"{rid}: korak {i + 1} ima neispravno trajanje")
        kraj = max(kraj, k["od"] + k["min"])
        if k.get("aktivno"):
            aktivni.append((k["od"], k["od"] + k["min"], i + 1))
        if re.search(r"pećnic", k["tekst"], re.I) and not k.get("temperatura") and k.get("aktivno") is False:
            g.append(f"{rid}: korak {i + 1} koristi pećnicu bez temperature")
    if g:
        return g
    if kraj != r["ukupnoMin"]:
        g.append(f"{rid}: koraci završavaju u {kraj}. min, a ukupnoMin je {r['ukupnoMin']}")
    aktivni.sort()
    for a, b in zip(aktivni, aktivni[1:]):
        if b[0] < a[1]:
            g.append(f"{rid}: aktivni koraci {a[2]} i {b[2]} se preklapaju")
    zbroj = sum(b - a for a, b, _ in aktivni)
    if zbroj != r["aktivnoMin"]:
        g.append(f"{rid}: aktivni koraci traju {zbroj} min, a aktivnoMin je {r['aktivnoMin']}")
    if r["koraci"][0]["od"] != 0:
        g.append(f"{rid}: prvi korak ne počinje u nultoj minuti")
    return g


def provjeri_sve(recepti):
    g = []
    if len(recepti) != 24:
        g.append(f"očekivana su 24 recepta, a ima ih {len(recepti)}")
    idovi = [r.get("id") for r in recepti]
    if len(set(idovi)) != len(idovi):
        g.append("id-ovi recepata nisu jedinstveni")
    for r in recepti:
        g += provjeri_recept(r)
        if not (KORIJEN / "slike" / f"{r.get('id')}.svg").exists():
            g.append(f"{r.get('id')}: nedostaje slike/{r.get('id')}.svg")
    if sum(1 for r in recepti if r.get("petak")) < 8:
        g.append("manje od osam jela prikladnih za petak")
    return g


def samotest(recepti):
    """Pokvari ispravne zapise i potvrdi da ih provjera odbija."""
    r0 = next(r for r in recepti if r["petak"])
    kvarovi = {
        "bez polja": lambda r: r.pop("koraci"),
        "trajanje": lambda r: r.__setitem__("ukupnoMin", r["ukupnoMin"] + 5),
        "gluten": lambda r: r["sastojci"].append({"naziv": "pšenično brašno", "kolicina": "1 žlica", "skupina": "ostalo"}),
        "deklaracija": lambda r: r["sastojci"].append({"naziv": "bezglutenska tjestenina", "kolicina": "1 g", "skupina": "zitarice", "bg": True}),
        "petak": lambda r: r["sastojci"].append({"naziv": "slanina", "kolicina": "50 g", "skupina": "bjelancevine"}),
        "petak temeljac": lambda r: r["sastojci"].append({"naziv": "bezglutenski pileći temeljac", "kolicina": "1 l", "skupina": "ostalo", "bg": True, "deklaracija": "x"}),
    }
    neuhvaceni = []
    for ime, kvar in kvarovi.items():
        r = copy.deepcopy(r0)
        kvar(r)
        if not provjeri_recept(r):
            neuhvaceni.append(ime)
    return neuhvaceni


def main():
    argumenti = [a for a in sys.argv[1:] if not a.startswith("--")]
    put = Path(argumenti[0]) if argumenti else KORIJEN / "podaci" / "recepti.json"
    recepti = json.loads(put.read_text(encoding="utf-8"))
    greske = provjeri_sve(recepti) if "--skupina" not in sys.argv else sum((provjeri_recept(r) for r in recepti), [])
    if "--samotest" in sys.argv:
        n = samotest(recepti)
        if n:
            greske.append("samotest: provjera nije uhvatila kvarove: " + ", ".join(n))
    for x in greske:
        print("GREŠKA:", x)
    print(f"Provjera podataka: {len(recepti)} recepata, {len(greske)} grešaka")
    return 1 if greske else 0


if __name__ == "__main__":
    sys.exit(main())
