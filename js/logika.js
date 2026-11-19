// Čista logika bez DOM-a: vrijeme (Europe/Zagreb), satnica, sastav obroka,
// prijedlozi ručka, rezultati igre i obiteljska preporuka.
import { DJECA } from './obitelj.js';

export const ZONA = 'Europe/Zagreb';
export const ZADANO_POSLUZIVANJE = 14 * 60;
const DANI = ['nedjelja', 'ponedjeljak', 'utorak', 'srijeda', 'četvrtak', 'petak', 'subota'];
const DANI_U_KOJEM = ['u nedjelju', 'u ponedjeljak', 'u utorak', 'u srijedu', 'u četvrtak', 'u petak', 'u subotu'];

// ---------- vrijeme ----------
const fmt = new Intl.DateTimeFormat('en-GB', {
  timeZone: ZONA, year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

/** Trenutak u Zagrebu: datum (YYYY-MM-DD), minute od ponoći i dan u tjednu (0 = nedjelja). */
export function zagreb(ms = Date.now()) {
  const d = {};
  for (const p of fmt.formatToParts(new Date(ms))) d[p.type] = p.value;
  const datum = `${d.year}-${d.month}-${d.day}`;
  return { datum, min: Number(d.hour) * 60 + Number(d.minute), dan: danUTjednu(datum) };
}

export function danUTjednu(datum) {
  const [y, m, d] = datum.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay();
}

export function dodajDane(datum, n) {
  const [y, m, d] = datum.split('-').map(Number);
  const t = new Date(Date.UTC(y, m - 1, d + n));
  return t.toISOString().slice(0, 10);
}

export const imeDana = (dan) => DANI[dan];
export const uDan = (dan) => DANI_U_KOJEM[dan];

export function sat(min) {
  const m = ((Math.round(min) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
}

export function parsirajSat(t) {
  const m = /^(\d{1,2}):(\d{2})$/.exec(t || '');
  if (!m) return null;
  const h = Number(m[1]), mi = Number(m[2]);
  return h < 24 && mi < 60 ? h * 60 + mi : null;
}

export function trajanje(min) {
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60), m = min % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}

// ---------- satnica ----------
export function najkasnijiPocetak(recept, posluzivanje) {
  return posluzivanje - recept.ukupnoMin;
}

/** Koraci s točnim satom početka i kraja za zadano vrijeme posluživanja. */
export function satnica(recept, posluzivanje) {
  const pocetak = najkasnijiPocetak(recept, posluzivanje);
  return recept.koraci
    .map((k, i) => ({ ...k, broj: i + 1, pocetak: pocetak + k.od, kraj: pocetak + k.od + k.min }))
    .sort((a, b) => a.pocetak - b.pocetak || a.broj - b.broj);
}

// ---------- sastav obroka („Moj tanjur”) ----------
const SKUPINA_TANJURA = { povrce: 'povrce', bjelancevine: 'bjelancevine', mlijecno: 'bjelancevine', zitarice: 'zitarice' };

export function spoji(rijeci) {
  if (rijeci.length <= 1) return rijeci.join('');
  return `${rijeci.slice(0, -1).join(', ')} i ${rijeci[rijeci.length - 1]}`;
}

export function sastav(recept) {
  const g = { povrce: 0, bjelancevine: 0, zitarice: 0 };
  const opisi = { bjelancevine: [], zitarice: [], povrce: [] };
  for (const s of recept.sastojci) {
    if (s.neobavezno) continue;
    const k = SKUPINA_TANJURA[s.skupina];
    if (!k) continue;
    g[k] += s.grama || 0;
    if (s.opis && !opisi[k].includes(s.opis)) opisi[k].push(s.opis);
  }
  const ukupno = g.povrce + g.bjelancevine + g.zitarice || 1;
  const udio = g.povrce / ukupno;
  const opis = `sadrži ${spoji([...opisi.bjelancevine, ...opisi.zitarice, ...opisi.povrce])}`;
  let razina, tekst;
  if (udio >= 0.4 && g.bjelancevine && g.zitarice) {
    razina = 2; tekst = 'Povrće čini gotovo pola tanjura, uz bjelančevine i prilog — blizu „Mog tanjura”.';
  } else if (udio >= 0.3) {
    razina = 1; tekst = 'Povrće čini otprilike trećinu tanjura — manje od preporučene polovice.';
  } else {
    razina = 0; tekst = 'Povrće čini manje od trećine tanjura; prevladavaju prilog i bjelančevine.';
  }
  const neobavezno = recept.sastojci.filter((s) => s.neobavezno).map((s) => s.naziv);
  return { ...g, udio, razina, opis, tekst, neobavezno };
}

export const NAZIV_RAZINE = ['malo povrća', 'povrće oko trećine tanjura', 'uravnotežen tanjur'];

// ---------- rezultati igre jednog djeteta ----------
/**
 * Odgovor: {a, b, odgovor: 'a'|'b'|'oboje'|'ne'|'neprobano', jela: [id...], krug}
 * Poraz znači samo „drugo jelo mi je draže”; nepoznato jelo nije odbijeno.
 */
export function rezultatDjeteta(odgovori, idovi) {
  const s = {};
  for (const id of idovi) s[id] = { id, w: 0, l: 0, t: 0, status: null, viđeno: 0 };
  const pobjeda = (x, y) => { if (s[x] && s[y]) { s[x].w++; s[y].l++; } };
  for (const o of odgovori) {
    if (s[o.a]) s[o.a].viđeno++;
    if (s[o.b]) s[o.b].viđeno++;
    if (o.odgovor === 'a') { pobjeda(o.a, o.b); oznaci(s, o.a, 'voli'); }
    else if (o.odgovor === 'b') { pobjeda(o.b, o.a); oznaci(s, o.b, 'voli'); }
    else if (o.odgovor === 'oboje') { for (const x of [o.a, o.b]) if (s[x]) { s[x].t++; oznaci(s, x, 'voli'); } }
    else if (o.odgovor === 'ne') {
      for (const x of o.jela) oznaci(s, x, 'odbijeno');
      if (o.jela.length === 1) {
        const drugo = o.jela[0] === o.a ? o.b : o.a;
        pobjeda(drugo, o.jela[0]);
      }
    } else if (o.odgovor === 'neprobano') {
      for (const x of o.jela) oznaci(s, x, 'neprobano');
    }
  }
  const sva = Object.values(s);
  for (const x of sva) {
    const n = x.w + x.l + x.t;
    x.n = n;
    x.ocjena = (x.w + 0.5 * x.t + 1) / (n + 2);
  }
  const aktivna = sva.filter((x) => x.status !== 'odbijeno' && x.status !== 'neprobano' && x.n > 0);
  aktivna.sort((a, b) => b.ocjena - a.ocjena || b.w - a.w || b.n - a.n || a.id.localeCompare(b.id));
  const max = aktivna.length ? aktivna[0].ocjena : 0;
  let favoriti = aktivna.filter((x) => x.ocjena >= max - 0.001 && x.w + x.t > 0);
  const precizno = favoriti.length === 1 && favoriti[0].w >= 2;
  if (!precizno) favoriti = aktivna.filter((x) => x.ocjena >= max - 0.09 && x.w + x.t > 0).slice(0, 6);
  return {
    odgovora: odgovori.length,
    poredak: aktivna,
    favoriti: favoriti.map((x) => x.id),
    precizno,
    odbijena: sva.filter((x) => x.status === 'odbijeno').map((x) => x.id),
    neprobana: sva.filter((x) => x.status === 'neprobano').map((x) => x.id),
    jela: s,
  };
}

function oznaci(s, id, st) { if (s[id]) s[id].status = st; }

/** Što dijete misli o jelu: favorit | rado | manje | odbijeno | neprobano | nema */
export function stavDjeteta(rez, id) {
  const x = rez.jela[id];
  if (!x || (x.n === 0 && !x.status)) return 'nema';
  if (x.status === 'odbijeno') return 'odbijeno';
  if (x.status === 'neprobano') return 'neprobano';
  if (rez.favoriti.includes(id)) return 'favorit';
  if (x.n === 0) return 'nema';
  return x.ocjena >= 0.5 ? 'rado' : 'manje';
}

// ---------- obiteljska ocjena ----------
const BROJ = ['nijedno dijete', 'jedno dijete', 'dva djeteta', 'tri djeteta', 'sva četiri djeteta'];
export const brojDjece = (n) => BROJ[n] || `${n} djece`;

export function obiteljskiStav(id, rezultati) {
  const glasala = DJECA.filter((d) => rezultati[d] && rezultati[d].odgovora > 0);
  const stavovi = {};
  for (const d of DJECA) stavovi[d] = rezultati[d] ? stavDjeteta(rezultati[d], id) : 'nema';
  const rado = glasala.filter((d) => ['favorit', 'rado'].includes(stavovi[d]));
  const favorit = glasala.filter((d) => stavovi[d] === 'favorit');
  const odbili = glasala.filter((d) => stavovi[d] === 'odbijeno');
  const neprobali = glasala.filter((d) => stavovi[d] === 'neprobano');
  const ocjene = glasala.map((d) => rezultati[d].jela[id]).filter((x) => x && x.n > 0).map((x) => x.ocjena);
  const prosjek = ocjene.length ? ocjene.reduce((a, b) => a + b, 0) / ocjene.length : 0.5;
  let razred = 0; // 3 = svi koji su glasali rado jedu (i glasala su barem tri), 2 = većina, 1 = nitko protiv, 0 = netko odbija
  if (odbili.length) razred = 0;
  else if (glasala.length >= 3 && rado.length === glasala.length) razred = 3;
  else if (rado.length > glasala.length / 2) razred = 2;
  else razred = 1;
  return { glasala, stavovi, rado, favorit, odbili, neprobali, prosjek, razred };
}

function imena(lista) { return spoji(lista); }

export function zasadGlasala(n) {
  return n === 1 ? 'Zasad je glasalo jedno dijete' : `Zasad su glasala ${brojDjece(n)}`;
}

export function razlogObitelji(recept, st, sas) {
  const n = st.glasala.length;
  if (!n) return `Još nitko nije igrao; ${sas.opis}.`;
  const pocetak = n < 4 ? zasadGlasala(n) : '';
  let dio;
  if (st.odbili.length) dio = `${imena(st.odbili)} ${st.odbili.length > 1 ? 'su rekli' : 'je rekao/rekla'} da ga ne bi ${st.odbili.length > 1 ? 'jeli' : 'jeo/jela'}`;
  else if (st.razred === 3) dio = n === 4 ? 'svih četvero ga rado jede' : `svi koji su glasali (${imena(st.glasala)}) ga rado jedu`;
  else if (st.rado.length) dio = `rado ga jede ${imena(st.rado)}`;
  else if (st.neprobali.length) dio = `${imena(st.neprobali)} ga još nije probao/probala`;
  else dio = 'djeci su draža druga jela';
  const tanjur = sas.razina === 2 ? `uravnotežen je tanjur (${sas.opis})`
    : sas.razina === 1 ? `povrća je oko trećine tanjura (${sas.opis})`
      : `na tanjuru je malo povrća (${sas.opis})`;
  const r = `${dio}, a ${tanjur}.`;
  return pocetak ? `${pocetak}: ${r}` : r.charAt(0).toUpperCase() + r.slice(1);
}

// ---------- izvedivost ----------
export function kontekst(sadaMs, posluzivanje = ZADANO_POSLUZIVANJE, sutra = false) {
  const sada = zagreb(sadaMs);
  const datum = sutra ? dodajDane(sada.datum, 1) : sada.datum;
  const dan = danUTjednu(datum);
  return { sada, datum, dan, sutra, posluzivanje, petak: dan === 5, vikend: dan === 0 || dan === 6 };
}

/** Može li se jelo poslužiti u zadano vrijeme zadanog dana, kad se kreće od nule sada. */
export function izvedivost(recept, ktx) {
  if (ktx.petak && !recept.petak) return { ok: false, zasto: 'petak je, a jelo sadrži meso' };
  if (!ktx.sutra) {
    if (recept.vecerPrije) return { ok: false, zasto: 'traži pripremu večer prije' };
    const start = najkasnijiPocetak(recept, ktx.posluzivanje);
    if (start < ktx.sada.min) return { ok: false, zasto: `trebalo je krenuti u ${sat(start)}` };
  }
  return { ok: true };
}

// ---------- prijedlozi za prvi ekran ----------
function hash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 1000) / 1000;
}

function ocjenaPrijedloga(r, ktx, sas, st, slobodno) {
  let o = hash(ktx.datum + r.id) * 1.2; // dnevna raznolikost kad nema drugih razloga
  if (ktx.vikend) o += r.tip === 'vikend' ? 1.2 : r.tip === 'oboje' ? 0.4 : 0;
  else o += r.ukupnoMin <= 60 ? 1 : r.tip === 'vikend' ? -1 : 0;
  o += sas.razina * 0.5;
  if (slobodno != null && slobodno < 15) o += 0.3; // taman stiže
  if (st && st.glasala.length) {
    o += st.razred * 1.2 + (st.prosjek - 0.5) * 2;
    if (st.odbili.length) o -= 3;
  }
  return o;
}

export function razlogPrijedloga(r, ktx, sas, st, nacin) {
  const dijelovi = [];
  if (nacin === 'prekasno') dijelovi.push(`Za ${sat(ktx.posluzivanje)} je kasno, a ovo je gotovo za ${trajanje(r.ukupnoMin)} ako kreneš odmah`);
  else if (ktx.petak) dijelovi.push(`Petak je, a ovo je jelo bez mesa`);
  else if (ktx.vikend && r.tip === 'vikend') dijelovi.push(`${imeDana(ktx.dan)[0].toUpperCase() + imeDana(ktx.dan).slice(1)} je, ima vremena za sporije jelo`);
  else if (!ktx.vikend && r.ukupnoMin <= 45) dijelovi.push(`Brz ručak za radni dan: u kuhinji si ${trajanje(r.aktivnoMin)}`);
  else if (!ktx.vikend && r.aktivnoMin <= 30) dijelovi.push(`Većinu vremena se kuha samo — aktivno si u kuhinji ${trajanje(r.aktivnoMin)}`);
  else dijelovi.push(`Stiže na vrijeme za ${sat(ktx.posluzivanje)}`);
  if (st && st.glasala.length) {
    if (st.odbili.length) dijelovi.push(`ali ${imena(st.odbili)} ga ne bi jeo/jela`);
    else if (st.razred === 3) dijelovi.push(st.glasala.length === 4 ? 'svih četvero ga rado jede' : `rado ga jedu svi koji su glasali (${zasadGlasala(st.glasala.length).toLowerCase()})`);
    else if (st.rado.length) dijelovi.push(`${imena(st.rado)} ga ${st.rado.length > 1 ? 'rado jedu' : 'rado jede'}`);
  } else if (sas.razina === 2) dijelovi.push(`a tanjur je uravnotežen (${sas.opis})`);
  else dijelovi.push(sas.opis);
  return dijelovi.join('; ') + '.';
}

/**
 * Tri prijedloga za ručak.
 * Ako za zadano vrijeme nema barem tri izvediva jela (danas), vraća tri jela
 * koja se mogu početi kuhati odmah, sa stvarnim vremenom kad su gotova.
 */
export function prijedlozi(recepti, ktx, rezultati = {}) {
  const imaGlasova = DJECA.some((d) => rezultati[d] && rezultati[d].odgovora > 0);
  const ocijeni = (r, nacin) => {
    const sas = sastav(r);
    const st = imaGlasova ? obiteljskiStav(r.id, rezultati) : null;
    const najkasnije = najkasnijiPocetak(r, ktx.posluzivanje);
    const slobodno = ktx.sutra ? null : najkasnije - ktx.sada.min;
    return { recept: r, sas, st, najkasnije, ocjena: ocjenaPrijedloga(r, ktx, sas, st, slobodno), nacin };
  };
  let nacin = 'normalno';
  let kandidati = recepti.filter((r) => izvedivost(r, ktx).ok).map((r) => ocijeni(r, nacin));
  if (kandidati.length < 3 && !ktx.sutra) {
    nacin = 'prekasno';
    const odmah = Math.ceil(ktx.sada.min / 5) * 5;
    kandidati = recepti
      .filter((r) => !r.vecerPrije && (!ktx.petak || r.petak))
      .map((r) => {
        const x = ocijeni(r, nacin);
        x.najkasnije = odmah;
        x.gotovo = odmah + r.ukupnoMin;
        x.ocjena += -r.ukupnoMin / 20; // što prije gotovo
        return x;
      });
  }
  kandidati.sort((a, b) => b.ocjena - a.ocjena || a.recept.id.localeCompare(b.recept.id));
  const izabrani = [];
  const glavna = new Set();
  for (const k of kandidati) { // raznolikost: različita glavna namirnica
    if (izabrani.length === 3) break;
    if (glavna.has(k.recept.glavno)) continue;
    izabrani.push(k); glavna.add(k.recept.glavno);
  }
  for (const k of kandidati) { if (izabrani.length === 3) break; if (!izabrani.includes(k)) izabrani.push(k); }
  for (const k of izabrani) {
    if (k.gotovo == null) k.gotovo = ktx.posluzivanje;
    k.razlog = razlogPrijedloga(k.recept, ktx, k.sas, k.st, nacin);
  }
  return { nacin, ktx, stavke: izabrani };
}

/** Obiteljska preporuka: djeca (stav), sastav obroka i izvedivost danas — tri zasebne stvari. */
export function obiteljskiPoredak(recepti, rezultati, ktx) {
  const redovi = recepti.map((r) => {
    const st = obiteljskiStav(r.id, rezultati);
    const sas = sastav(r);
    const izv = izvedivost(r, ktx);
    return { recept: r, st, sas, izv, razlog: razlogObitelji(r, st, sas) };
  });
  redovi.sort((a, b) =>
    (b.izv.ok - a.izv.ok)
    || (b.st.razred - a.st.razred)
    || (b.sas.razina - a.sas.razina)
    || (b.st.prosjek - a.st.prosjek)
    || a.recept.naziv.localeCompare(b.recept.naziv, 'hr'));
  return redovi;
}

// ---------- parovi za igru ----------
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Prvi krug: 12 parova u kojima se svih 24 jela pojavljuju točno jednom. */
export function prviKrug(idovi, seed) {
  const r = rng(seed);
  const a = [...idovi];
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  const parovi = [];
  for (let i = 0; i < a.length; i += 2) parovi.push([a[i], a[i + 1]]);
  return parovi;
}

export const BROJ_PRVI = 12;
export const BROJ_DRUGI = 8;
export const PAUZA_NAKON = 6;

/** Sljedeći par drugog kruga: najjači kandidati za favorita koji se još nisu susreli. */
export function sljedeciDrugiKrug(odgovori, idovi) {
  const rez = rezultatDjeteta(odgovori, idovi);
  const vidjeni = new Set(odgovori.map((o) => [o.a, o.b].sort().join('|')));
  const lijevo = {};
  for (const o of odgovori) { lijevo[o.a] = (lijevo[o.a] || 0) + 1; lijevo[o.b] = (lijevo[o.b] || 0) - 1; }
  const kand = rez.poredak.filter((x) => x.w + x.t > 0).slice(0, 10);
  let najbolji = null;
  for (let i = 0; i < kand.length; i++) {
    for (let j = i + 1; j < kand.length; j++) {
      const x = kand[i], y = kand[j];
      if (vidjeni.has([x.id, y.id].sort().join('|'))) continue;
      const v = Math.min(x.ocjena, y.ocjena) * 10 - Math.abs(x.ocjena - y.ocjena) * 4 - (x.n + y.n) * 0.15;
      if (!najbolji || v > najbolji.v) najbolji = { v, x: x.id, y: y.id };
    }
  }
  if (!najbolji) return null;
  // izmjenjuj strane: jelo koje je češće bilo lijevo ide desno
  return (lijevo[najbolji.x] || 0) > (lijevo[najbolji.y] || 0) ? [najbolji.y, najbolji.x] : [najbolji.x, najbolji.y];
}
