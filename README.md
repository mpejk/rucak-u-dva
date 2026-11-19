# Ručak u dva

Obiteljska web-aplikacija na hrvatskom: gotova **bezglutenska kuharica s 24 ručka za šestero** i kratka **igra „Što bi radije sutra za ručak?”** iz koje roditelji saznaju što djeca vole. Čisti HTML, CSS i JavaScript, bez frameworka, bez koraka izgradnje, bez backenda, bez vanjskih resursa. Radi offline nakon prvog učitavanja i može se dodati na početni zaslon.

## Važno za iPhone: prije prve igre

**U Safariju otvori stranicu → Dijeli → „Dodaj na početni zaslon”, i igrajte iz te ikone.** Safari sam briše lokalne podatke stranice koja se tjedan dana ne koristi, a aplikacije s početnog zaslona ne. Odgovori djece spremaju se samo na uređaju; u roditeljskom pregledu vidi se datum zadnjeg izvoza — povremeno izvezi rezultate (dijeljenje datoteke ili preuzimanje) i uvezi ih na Macu.

## Lokalno pokretanje

Aplikacija mora biti poslužena preko HTTP-a (zbog `fetch` i service workera), ne kao `file://`:

```sh
python3 -m http.server 8000
# otvori http://localhost:8000/
```

## Provjera

```sh
./provjeri
```

Skripta vraća 0 samo ako sve prolazi. Pokreće:

1. `alati/provjeri_podatke.py --samotest` — provjera podataka recepata (obavezna polja, trajanja koraka, sastojci s glutenom bez oznake/deklaracije, meso u jelima za petak) i samotest koji potvrđuje da provjera hvata pokvarene zapise;
2. `pytest testovi` — Playwright scenariji u **WebKitu s iPhone prikazom** i u **Chromiumu**, s lažiranim satom i zonom uređaja `America/New_York` (aplikacija mora računati po Europe/Zagreb). Aplikacija se poslužuje iz podmape `/rucak-u-dva/` kao na GitHub Pagesu.

Prva priprema (jednom; Node nije potreban — Playwright za Python):

```sh
python3 -m venv .venv
.venv/bin/pip install playwright pytest
PLAYWRIGHT_BROWSERS_PATH=$PWD/.radno/browsers .venv/bin/python -m playwright install chromium webkit
# ako preuzimanje javi „unable to get local issuer certificate”, dodaj NODE_OPTIONS="--use-system-ca"
```

## Objava na GitHub Pages

1. Napravi repozitorij (npr. `rucak-u-dva`) i pushaj granu `main`.
2. Settings → Pages → Source: „Deploy from a branch”, grana `main`, mapa `/ (root)`.
3. Stranica je na `https://<korisnik>.github.io/rucak-u-dva/`. Sve putanje su relativne, pa radi iz podmape.

Stranica ima `noindex`. U repozitorij se nikad ne spremaju stvarni odgovori djece (oni postoje samo u pregledniku i u datotekama izvoza koje ne treba commitati).

## Struktura

- `index.html`, `css/stil.css`, `js/app.js` (sučelje), `js/logika.js` (vrijeme, satnica, prijedlozi, sastav obroka, rezultati igre, obiteljska preporuka), `js/pohrana.js` (lokalna pohrana, izvoz/uvoz), `js/obitelj.js` (jedino mjesto s imenima djece)
- `podaci/recepti.json` — 24 recepta, jedan zapis po receptu. Iz istog zapisa nastaju prikaz, satnica, filtri i opis sastava. Ključna polja: `ukupnoMin`, `aktivnoMin`, `petak`, `vecerPrije` (+ `pripremaUnaprijed`), `sastojci[]` (`skupina`, `grama` = približna masa na tanjuru, `bg`/`deklaracija`, `meso`, `neobavezno`), `koraci[]` (`od` = minuta od početka, `min`, `aktivno`, `temperatura`/`toplina`, `gotovo` = znak da je korak gotov).
- `slike/<id>.svg` — 24 autorske ilustracije (generira `alati/crtaj_slike.py`); kontrolna stranica `slike.html`.
- `sw.js`, `manifest.webmanifest`, `ikone/` — offline rad i početni zaslon.
- `ODLUKE.md` — samostalno donesene odluke; `NAPREDAK.md` — faze rada.

Izvor za procjenu sastava obroka: Hrvatski zavod za javno zdravstvo, *Prehrambene smjernice za 5. – 8. razrede osnovnih škola*, https://www.hzjz.hr/wp-content/uploads/2018/06/Brosura-OSNOVNA-SKOLA.pdf
