// Lokalna pohrana na uređaju: odgovori i napredak svakog djeteta, datum zadnjeg izvoza.
import { DJECA } from './obitelj.js';
import { prviKrug, sljedeciDrugiKrug, BROJ_PRVI, BROJ_DRUGI, PAUZA_NAKON } from './logika.js';

const KLJUC = 'rucak-u-dva/v1';
const VERZIJA = 1;

function prazno() { return { verzija: VERZIJA, djeca: {}, zadnjiIzvoz: null }; }

let memorija = null; // ako localStorage nije dostupan (privatni način), radi u memoriji

export function ucitaj() {
  try {
    const s = JSON.parse(localStorage.getItem(KLJUC) || 'null');
    if (s && s.verzija === VERZIJA && s.djeca) return s;
  } catch { /* oštećeno ili nedostupno */ }
  return memorija ? structuredClone(memorija) : prazno();
}

export function spremi(s) {
  memorija = structuredClone(s);
  try { localStorage.setItem(KLJUC, JSON.stringify(s)); } catch { /* ostaje u memoriji */ }
}

export async function zatraziTrajnuPohranu() {
  try {
    if (navigator.storage && navigator.storage.persist) {
      if (await navigator.storage.persisted()) return true;
      return await navigator.storage.persist();
    }
  } catch { /* nije podržano */ }
  return false;
}

// ---------- igra ----------
export function dijete(s, ime, idovi) {
  if (!DJECA.includes(ime)) throw new Error('Nepoznato ime');
  if (!s.djeca[ime]) {
    const seed = Math.floor(Math.random() * 2 ** 31);
    s.djeca[ime] = { seed, parovi: prviKrug(idovi, seed), odgovori: [], trenutni: null, pauza: false, zavrseno: false };
  }
  return s.djeca[ime];
}

/** Vraća stanje igre: {vrsta: 'par'|'pauza'|'kraj-kruga'|'gotovo', par, broj, ukupno, krug} */
export function korak(d, idovi) {
  const n = d.odgovori.length;
  const ukupno = BROJ_PRVI + BROJ_DRUGI;
  if (d.zavrseno) return { vrsta: 'gotovo', broj: n, ukupno };
  if (n === PAUZA_NAKON && !d.pauza) return { vrsta: 'pauza', broj: n, ukupno };
  if (n === BROJ_PRVI && !d.krug2) return { vrsta: 'kraj-kruga', broj: n, ukupno };
  if (n < BROJ_PRVI) return { vrsta: 'par', par: d.parovi[n], broj: n, ukupno, krug: 1 };
  if (n < ukupno) {
    if (!d.trenutni) d.trenutni = sljedeciDrugiKrug(d.odgovori, idovi);
    if (d.trenutni) return { vrsta: 'par', par: d.trenutni, broj: n, ukupno, krug: 2 };
  }
  d.zavrseno = true;
  return { vrsta: 'gotovo', broj: n, ukupno };
}

export function odgovori(d, par, odgovor, jela = []) {
  const krug = d.odgovori.length < BROJ_PRVI ? 1 : 2;
  d.odgovori.push({ a: par[0], b: par[1], odgovor, jela, krug, vrijeme: Date.now() });
  d.trenutni = null;
}

export function natrag(d) {
  const o = d.odgovori.pop();
  if (!o) return false;
  d.zavrseno = false;
  d.trenutni = o.krug === 2 ? [o.a, o.b] : null;
  if (d.odgovori.length < BROJ_PRVI) d.krug2 = false;
  if (d.odgovori.length < PAUZA_NAKON) d.pauza = false;
  return true;
}

// ---------- izvoz i uvoz ----------
export function paketZaIzvoz(s) {
  return { aplikacija: 'rucak-u-dva', verzija: VERZIJA, izvezeno: new Date().toISOString(), podaci: { djeca: s.djeca } };
}

export function procitajUvoz(tekst) {
  let p;
  try { p = JSON.parse(tekst); } catch { throw new Error('Datoteka nije ispravan JSON.'); }
  if (!p || p.aplikacija !== 'rucak-u-dva' || !p.podaci || typeof p.podaci.djeca !== 'object') {
    throw new Error('Ovo nije datoteka s rezultatima aplikacije Ručak u dva.');
  }
  const djeca = {};
  for (const [ime, d] of Object.entries(p.podaci.djeca)) {
    if (!DJECA.includes(ime)) continue;
    if (!Array.isArray(d.odgovori) || !Array.isArray(d.parovi)) throw new Error(`Neispravni podaci za ${ime}.`);
    djeca[ime] = d;
  }
  return djeca;
}

export async function izvezi(s) {
  const paket = paketZaIzvoz(s);
  const tekst = JSON.stringify(paket, null, 1);
  const ime = `rucak-u-dva-rezultati-${paket.izvezeno.slice(0, 10)}.json`;
  const blob = new Blob([tekst], { type: 'application/json' });
  let nacin = 'preuzimanje';
  try {
    const datoteka = new File([blob], ime, { type: 'application/json' });
    if (navigator.canShare && navigator.canShare({ files: [datoteka] })) {
      await navigator.share({ files: [datoteka], title: 'Ručak u dva — rezultati' });
      nacin = 'dijeljenje';
    } else throw new Error('nema dijeljenja');
  } catch (e) {
    if (e && e.name === 'AbortError') return null; // korisnik je odustao od dijeljenja
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = ime; a.rel = 'noopener';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }
  s.zadnjiIzvoz = paket.izvezeno;
  spremi(s);
  return nacin;
}
