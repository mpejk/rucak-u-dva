# Odluke

- Node nije instaliran; testovi idu kroz python3 venv (.venv) i Playwright za Python, preglednici u .radno/browsers.
- Git identitet postavljen lokalno na neutralno ime (repo je javni); vlasnik ga može promijeniti prije pusha.
- Recepti su u jednoj datoteci podaci/recepti.json (jedan zapis po receptu); provjera podataka je alati/provjeri_podatke.py (Python, bez ovisnosti).
- Količine su izračunate za oko 5 odraslih porcija (dvoje odraslih + četvero djece); dob se nigdje u kodu ne sprema.
- Polje "grama" je približna masa namirnice na tanjurima (kuhano), koristi se samo za procjenu sastava prema „Mom tanjuru”.
- Korak ima "od" (minuta od početka) i "min"; ukupno = kraj zadnjeg koraka, aktivno = zbroj aktivnih koraka koji se ne smiju preklapati.
- Riječ „kocka” u nazivu sastojka provjera tretira kao temeljac, pa se meso ne opisuje kao „na kocke”.
- Za petak: provjera traži i oznaku "meso": true i ključne riječi (meso, suhomesnato, mast, mesni temeljac).
- Pizza: umak od rajčice računat je kao ukuhan (manja masa), pa pizza ima malo povrća na tanjuru.
