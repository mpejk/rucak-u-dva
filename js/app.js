import { DJECA } from './obitelj.js';
import * as L from './logika.js';
import * as P from './pohrana.js';

const app = document.getElementById('app');
let RECEPTI = [];
let PO_ID = {};
let IDOVI = [];
let hrGlas = null;
let budilica = null; // Wake Lock

// ---------- pomoćno ----------
const e = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const slika = (id, klasa = '') => `<img class="slika ${klasa}" src="slike/${e(id)}.svg" alt="" width="240" height="240" loading="lazy">`;
const sada = () => Date.now();

function ruta() {
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  const [put, upit = ''] = h.split('?');
  const dijelovi = put.split('/').filter(Boolean);
  return { dijelovi, upit: new URLSearchParams(upit) };
}

function stanjeVremena(upit) {
  const u = L.parsirajSat(upit.get('u'));
  return { posluzivanje: u ?? L.ZADANO_POSLUZIVANJE, sutra: upit.get('d') === 'sutra' };
}

function upitVremena({ posluzivanje, sutra }) {
  const p = new URLSearchParams();
  if (posluzivanje !== L.ZADANO_POSLUZIVANJE) p.set('u', L.sat(posluzivanje));
  if (sutra) p.set('d', 'sutra');
  const s = p.toString();
  return s ? `?${s}` : '';
}

function datumHr(datum) {
  const [y, m, d] = datum.split('-').map(Number);
  return `${d}. ${m}. ${y}.`;
}

function rezultatiSvih() {
  const s = P.ucitaj();
  const r = {};
  for (const d of DJECA) r[d] = L.rezultatDjeteta(s.djeca[d]?.odgovori || [], IDOVI);
  return r;
}

function glavaStranice(naslov, natrag = '#/') {
  return `<header class="glava"><a class="natrag" href="${natrag}" aria-label="Natrag">‹</a><h1>${e(naslov)}</h1></header>`;
}

function kontroleVremena(vr, osnova) {
  const k = L.kontekst(sada(), vr.posluzivanje, false);
  const sutraDan = L.danUTjednu(L.dodajDane(k.sada.datum, 1));
  return `
  <div class="kontrole" data-osnova="${e(osnova)}">
    <div class="seg" role="group" aria-label="Dan">
      <button type="button" data-dan="danas" class="${vr.sutra ? '' : 'odabrano'}" aria-pressed="${!vr.sutra}">Danas</button>
      <button type="button" data-dan="sutra" class="${vr.sutra ? 'odabrano' : ''}" aria-pressed="${vr.sutra}">Sutra · ${e(L.imeDana(sutraDan))}</button>
    </div>
    <div class="vrijeme">
      <span>Ručak u</span>
      <button type="button" data-pomak="-30" aria-label="30 minuta ranije">−30</button>
      <input type="time" id="posluzivanje" value="${L.sat(vr.posluzivanje)}" step="300" aria-label="Vrijeme posluživanja">
      <button type="button" data-pomak="30" aria-label="30 minuta kasnije">+30</button>
    </div>
  </div>`;
}

function spojiKontrole(vr) {
  const k = app.querySelector('.kontrole');
  if (!k) return;
  const osnova = k.dataset.osnova;
  const idi = (nv) => { location.hash = osnova + upitVremena(nv); };
  k.querySelectorAll('[data-dan]').forEach((b) => b.addEventListener('click', () => idi({ ...vr, sutra: b.dataset.dan === 'sutra' })));
  k.querySelectorAll('[data-pomak]').forEach((b) => b.addEventListener('click', () => {
    const n = Math.min(23 * 60 + 30, Math.max(6 * 60, vr.posluzivanje + Number(b.dataset.pomak)));
    idi({ ...vr, posluzivanje: n });
  }));
  k.querySelector('#posluzivanje').addEventListener('change', (ev) => {
    const n = L.parsirajSat(ev.target.value);
    if (n != null) idi({ ...vr, posluzivanje: n });
  });
}

// ---------- prvi ekran ----------
function prviEkran(upit) {
  const vr = stanjeVremena(upit);
  const ktx = L.kontekst(sada(), vr.posluzivanje, vr.sutra);
  const rez = rezultatiSvih();
  const p = L.prijedlozi(RECEPTI, ktx, rez);
  const dan = vr.sutra ? `Sutra je ${L.imeDana(ktx.dan)}` : `Danas je ${L.imeDana(ktx.dan)}`;
  const naslov = p.nacin === 'prekasno'
    ? `<p class="upozorenje" data-test="prekasno">Za ručak u ${L.sat(vr.posluzivanje)} je prekasno. Ovo možeš početi kuhati odmah:</p>`
    : '';
  const kartice = p.stavke.map((s, i) => {
    const r = s.recept;
    const u = p.nacin === 'prekasno' ? s.gotovo : vr.posluzivanje;
    const veza = `#/recept/${r.id}${upitVremena({ posluzivanje: u, sutra: vr.sutra })}`;
    const pocni = p.nacin === 'prekasno'
      ? `<strong>Kreni odmah (${L.sat(s.najkasnije)})</strong> — gotovo u <strong data-test="gotovo">${L.sat(s.gotovo)}</strong>`
      : `Kreni najkasnije u <strong data-test="najkasnije">${L.sat(s.najkasnije)}</strong>`;
    return `
    <article class="prijedlog" data-id="${e(r.id)}" data-petak="${r.petak}">
      <a href="${veza}" class="prijedlog-veza">
        ${slika(r.id)}
        <div class="prijedlog-tekst">
          <h2>${e(r.naziv)}</h2>
          <p class="vremena">Ukupno <strong>${L.trajanje(r.ukupnoMin)}</strong> · u kuhinji <strong>${L.trajanje(r.aktivnoMin)}</strong></p>
          <p class="pocetak">${pocni}</p>
          <p class="razlog">${e(s.razlog)}</p>
          ${r.vecerPrije && vr.sutra ? `<p class="napomena">Večeras: ${e(r.pripremaUnaprijed.tekst.replace(/^Večer prije:\s*/, ''))}</p>` : ''}
        </div>
      </a>
    </article>`;
  }).join('');
  app.innerHTML = `
    <header class="naslovnica">
      <h1>Što danas kuhati?</h1>
      <p class="podnaslov">${e(dan)}, ${datumHr(ktx.datum)} · sada je ${L.sat(ktx.sada.min)} (Zagreb) · ručak za šestero</p>
    </header>
    ${kontroleVremena(vr, '#/')}
    ${ktx.petak ? '<p class="info">Petak: predlažu se samo jela bez mesa i mesnog temeljca.</p>' : ''}
    ${naslov}
    <section class="prijedlozi" aria-label="Prijedlozi">${kartice}</section>
    <nav class="glavni-izbornik">
      <a class="gumb" href="#/recepti">📖 Svi recepti (${RECEPTI.length})</a>
      <a class="gumb" href="#/igra">🎲 Igra za djecu</a>
      <a class="gumb sporedno" href="#/roditelji">Roditeljski pregled</a>
    </nav>`;
  spojiKontrole(vr);
}

// ---------- kuharica ----------
const FILTRI = {
  svi: ['Svi', () => true],
  petak: ['Za petak', (r) => r.petak],
  brzo: ['Do 45 min', (r) => r.ukupnoMin <= 45],
  vikend: ['Za vikend', (r) => r.tip === 'vikend'],
};

function popisRecepata(upit) {
  const f = FILTRI[upit.get('f')] ? upit.get('f') : 'svi';
  const lista = RECEPTI.filter(FILTRI[f][1]).sort((a, b) => a.naziv.localeCompare(b.naziv, 'hr'));
  app.innerHTML = `
    ${glavaStranice('Kuharica')}
    <p class="podnaslov">24 bezglutenska ručka za šestero.</p>
    <div class="filtri" role="group" aria-label="Filtar">
      ${Object.entries(FILTRI).map(([k, [n]]) => `<a class="filtar ${k === f ? 'odabrano' : ''}" href="#/recepti?f=${k}">${n}</a>`).join('')}
    </div>
    <ul class="popis">
      ${lista.map((r) => `
        <li><a href="#/recept/${r.id}" data-id="${e(r.id)}">
          ${slika(r.id, 'mala')}
          <span><strong>${e(r.naziv)}</strong>
          <small>${L.trajanje(r.ukupnoMin)} · u kuhinji ${L.trajanje(r.aktivnoMin)}${r.petak ? ' · petak' : ''}${r.vecerPrije ? ' · priprema večer prije' : ''}</small></span>
        </a></li>`).join('')}
    </ul>`;
}

function oznakaGlutena(s) {
  if (!s.deklaracija) return '';
  return `<span class="dekl">⚠ ${e(s.deklaracija)}</span>`;
}

function prikazRecepta(id, upit) {
  const r = PO_ID[id];
  if (!r) return nijePronadeno();
  const vr = stanjeVremena(upit);
  const ktx = L.kontekst(sada(), vr.posluzivanje, vr.sutra);
  const izv = L.izvedivost(r, ktx);
  const sas = L.sastav(r);
  const koraci = L.satnica(r, vr.posluzivanje);
  const start = L.najkasnijiPocetak(r, vr.posluzivanje);
  app.innerHTML = `
    ${glavaStranice(r.kratkiNaziv, '#/recepti')}
    <article class="recept" data-id="${e(r.id)}">
      ${slika(r.id, 'velika')}
      <h2 class="naziv-jela">${e(r.naziv)}</h2>
      <p class="vremena">Ukupno <strong data-test="ukupno">${L.trajanje(r.ukupnoMin)}</strong> · aktivno u kuhinji <strong>${L.trajanje(r.aktivnoMin)}</strong> · za šestero</p>
      ${kontroleVremena(vr, `#/recept/${r.id}`)}
      <p class="pocetak">Za ručak u <strong>${L.sat(vr.posluzivanje)}</strong> kreni najkasnije u <strong data-test="start">${L.sat(start)}</strong>.</p>
      ${izv.ok ? '' : `<p class="upozorenje" data-test="neizvedivo">Za ${vr.sutra ? 'sutra' : 'danas'} nije izvedivo: ${e(izv.zasto)}.</p>`}
      <a class="gumb glavni" href="#/kuhanje/${r.id}${upitVremena(vr)}">▶ Kuhaj korak po korak</a>
      <section class="sastav"><h3>Na tanjuru</h3><p>${e(sas.opis[0].toUpperCase() + sas.opis.slice(1))}.</p><p>${e(sas.tekst)}</p>
        ${sas.neobavezno.length ? `<p class="sitno">Neobavezni dodatak (${e(sas.neobavezno.join(', '))}) nije uračunat u sastav obroka.</p>` : ''}
        <p class="sitno"><a href="#/o-aplikaciji">Kako se procjenjuje sastav?</a></p></section>
      ${r.vecerPrije ? `<section class="unaprijed"><h3>Priprema večer prije</h3><p>${e(r.pripremaUnaprijed.tekst)}</p><p class="sitno">Rad: ${L.trajanje(r.pripremaUnaprijed.min)}, zatim ${e(r.pripremaUnaprijed.odlezavanje)}. Bez toga se jelo ne može skuhati isti dan.</p></section>` : ''}
      <section><h3>Sastojci za šestero</h3>
        <ul class="sastojci">${r.sastojci.map((s) => `<li><span class="kol">${e(s.kolicina)}</span> <span>${e(s.naziv)}${oznakaGlutena(s)}</span></li>`).join('')}</ul>
      </section>
      <section class="gluten"><h3>Bez glutena — provjeri deklaraciju</h3><p>${e(r.deklaracija)}</p></section>
      <section><h3>Oprema</h3><ul class="oprema">${r.oprema.map((o) => `<li>${e(o)}</li>`).join('')}</ul></section>
      <section><h3>Satnica</h3><p class="sitno">${e(r.istodobno)}</p>
        <ol class="satnica">${koraci.map((k) => `
          <li class="${k.aktivno ? 'aktivno' : 'pasivno'}" data-test="korak">
            <div class="sat"><strong>${L.sat(k.pocetak)}</strong><small>–${L.sat(k.kraj)}</small></div>
            <div><p>${e(k.tekst)}</p>
            <p class="detalji">${k.aktivno ? '👩‍🍳 radiš' : '⏳ samo se kuha'} · ${L.trajanje(k.min)}${k.temperatura ? ` · ${e(k.temperatura)}` : ''}${k.toplina ? ` · ${e(k.toplina)}` : ''}</p>
            <p class="gotovo">Gotovo kad: ${e(k.gotovo)}</p></div>
          </li>`).join('')}</ol>
      </section>
    </article>`;
  spojiKontrole(vr);
}

async function zadrziZaslon() {
  try {
    if ('wakeLock' in navigator && document.visibilityState === 'visible') {
      budilica = await navigator.wakeLock.request('screen');
      const z = document.getElementById('budilica');
      if (z) z.textContent = '☀ Zaslon ostaje upaljen dok je ovaj prikaz otvoren.';
    }
  } catch { /* nije dopušteno */ }
}

function pustiZaslon() {
  if (budilica) { budilica.release().catch(() => {}); budilica = null; }
}

function kuhanje(id, upit) {
  const r = PO_ID[id];
  if (!r) return nijePronadeno();
  const vr = stanjeVremena(upit);
  const koraci = L.satnica(r, vr.posluzivanje);
  let i = Math.min(Math.max(0, Number(upit.get('k') || 0)), koraci.length - 1);
  const crtaj = () => {
    const k = koraci[i];
    app.innerHTML = `
      ${glavaStranice(r.kratkiNaziv, `#/recept/${r.id}${upitVremena(vr)}`)}
      <section class="kuhanje" data-korak="${i + 1}">
        <p class="kuhanje-sat"><strong>${L.sat(k.pocetak)}</strong> – ${L.sat(k.kraj)} · korak ${i + 1} od ${koraci.length}</p>
        <p class="kuhanje-tekst">${e(k.tekst)}</p>
        <p class="kuhanje-detalji">${k.aktivno ? 'Radiš' : 'Samo se kuha'} · ${L.trajanje(k.min)}${k.temperatura ? ` · ${e(k.temperatura)}` : ''}${k.toplina ? ` · ${e(k.toplina)}` : ''}</p>
        <p class="kuhanje-gotovo">Gotovo kad: ${e(k.gotovo)}</p>
        <div class="kuhanje-gumbi">
          <button type="button" class="gumb" id="prethodni" ${i === 0 ? 'disabled' : ''}>‹ Prethodni</button>
          <button type="button" class="gumb glavni" id="sljedeci" ${i === koraci.length - 1 ? 'disabled' : ''}>Sljedeći ›</button>
        </div>
        <p class="sitno" id="budilica"></p>
      </section>
      <ol class="satnica sazeto">${koraci.map((x, j) => `<li class="${j === i ? 'trenutni' : ''} ${x.aktivno ? 'aktivno' : 'pasivno'}"><strong>${L.sat(x.pocetak)}</strong> ${e(x.tekst.split('. ')[0])}</li>`).join('')}</ol>`;
    app.querySelector('#prethodni').onclick = () => { i--; crtaj(); };
    app.querySelector('#sljedeci').onclick = () => { i++; crtaj(); };
    if (budilica) document.getElementById('budilica').textContent = '☀ Zaslon ostaje upaljen dok je ovaj prikaz otvoren.';
  };
  crtaj();
  zadrziZaslon();
}

// ---------- igra ----------
function odabirIgraca() {
  const s = P.ucitaj();
  app.innerHTML = `
    ${glavaStranice('Što bi radije sutra za ručak?')}
    <p class="podnaslov">Tko igra? Dodirni svoje ime.</p>
    <div class="igraci">
      ${DJECA.map((d) => {
        const n = s.djeca[d]?.odgovori.length || 0;
        const gotovo = s.djeca[d]?.zavrseno;
        return `<a class="igrac" href="#/igra/${encodeURIComponent(d)}" data-ime="${e(d)}"><span class="ime">${e(d)}</span>
          <small>${gotovo ? 'gotovo ✓' : n ? `nastavi (${n}/20)` : 'kreni'}</small></a>`;
      }).join('')}
    </div>`;
  P.zatraziTrajnuPohranu();
}

function procitaj(tekst) {
  if (!hrGlas || !('speechSynthesis' in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(tekst);
  u.voice = hrGlas; u.lang = hrGlas.lang;
  speechSynthesis.speak(u);
}

function igra(ime) {
  if (!DJECA.includes(ime)) return nijePronadeno();
  const s = P.ucitaj();
  const d = P.dijete(s, ime, IDOVI);
  const k = P.korak(d, IDOVI);
  P.spremi(s);
  const glava = glavaStranice(ime, '#/igra');
  const napredak = `<div class="napredak" aria-label="Napredak"><div style="width:${Math.round((k.broj / k.ukupno) * 100)}%"></div></div>`;

  if (k.vrsta === 'pauza' || k.vrsta === 'kraj-kruga') {
    const pauza = k.vrsta === 'pauza';
    app.innerHTML = `${glava}${napredak}
      <section class="pauza" data-test="${pauza ? 'pauza' : 'kraj-kruga'}">
        <p class="velik">${pauza ? '🌟 Bravo! Pola prvog kruga je gotovo.' : '🎉 Prvi krug je gotov!'}</p>
        <p>${pauza ? 'Možeš se odmoriti i nastaviti kasnije — sve je spremljeno.' : 'Još 8 pitanja da saznamo što ti je najdraže.'}</p>
        <button type="button" class="gumb glavni" id="nastavi">Nastavi</button>
        <a class="gumb sporedno" href="#/igra">Pauza — igra netko drugi</a>
        <button type="button" class="gumb sporedno" id="natrag-odg">↩ Vrati zadnji odgovor</button>
      </section>`;
    app.querySelector('#nastavi').onclick = () => {
      const s2 = P.ucitaj(); const d2 = P.dijete(s2, ime, IDOVI);
      if (pauza) d2.pauza = true; else d2.krug2 = true;
      P.spremi(s2); igra(ime);
    };
    app.querySelector('#natrag-odg').onclick = () => { const s2 = P.ucitaj(); P.natrag(P.dijete(s2, ime, IDOVI)); P.spremi(s2); igra(ime); };
    return;
  }
  if (k.vrsta === 'gotovo') { location.hash = `#/rezultati/${encodeURIComponent(ime)}?kraj=1`; return; }

  const [a, b] = k.par;
  const ra = PO_ID[a], rb = PO_ID[b];
  const kartica = (r, strana) => `
    <div class="izbor-omot">
      <button type="button" class="izbor" data-strana="${strana}" data-id="${e(r.id)}" aria-label="${e(r.kratkiNaziv)}">
        ${slika(r.id)}
        <span class="izbor-naziv">${e(r.kratkiNaziv)}</span>
      </button>
      ${hrGlas ? `<button type="button" class="citaj" data-tekst="${e(r.kratkiNaziv)}" aria-label="Pročitaj naglas">🔊</button>` : ''}
    </div>`;
  app.innerHTML = `${glava}${napredak}
    <section class="igra" data-broj="${k.broj}" data-krug="${k.krug}">
      <p class="pitanje">Što bi radije sutra za ručak?
        ${hrGlas ? '<button type="button" class="citaj" data-tekst="Što bi radije sutra za ručak?" aria-label="Pročitaj pitanje">🔊</button>' : ''}</p>
      <div class="par">${kartica(ra, 'a')}${kartica(rb, 'b')}</div>
      <div class="dodatni" id="dodatni">
        <button type="button" class="gumb" data-odg="oboje">😋 Oboje mi je dobro</button>
        <button type="button" class="gumb" data-odg="ne">🙅 Ovo ne bih jeo/jela</button>
        <button type="button" class="gumb" data-odg="neprobano">🤔 Ovo još nisam probao/probala</button>
      </div>
      <div class="koje" id="koje" hidden>
        <p id="koje-pitanje"></p>
        <button type="button" class="gumb" data-jela="a">${e(ra.kratkiNaziv)}</button>
        <button type="button" class="gumb" data-jela="b">${e(rb.kratkiNaziv)}</button>
        <button type="button" class="gumb" data-jela="oba">Oba</button>
        <button type="button" class="gumb sporedno" data-jela="odustani">Odustani</button>
      </div>
      <div class="igra-dno">
        <button type="button" class="gumb sporedno" id="natrag-odg" ${k.broj === 0 ? 'disabled' : ''}>↩ Natrag</button>
        <a class="gumb sporedno" href="#/igra">Promijeni igrača</a>
      </div>
      <p class="sitno">${k.krug === 1 ? `Prvi krug: ${k.broj + 1}/12` : `Drugi krug: ${k.broj - 11}/8`}</p>
    </section>`;

  const zabiljezi = (odgovor, jela = []) => {
    const s2 = P.ucitaj(); const d2 = P.dijete(s2, ime, IDOVI);
    P.odgovori(d2, [a, b], odgovor, jela);
    P.spremi(s2);
    igra(ime);
  };
  app.querySelectorAll('.izbor').forEach((btn) => btn.addEventListener('click', () => zabiljezi(btn.dataset.strana)));
  app.querySelectorAll('.citaj').forEach((btn) => btn.addEventListener('click', () => procitaj(btn.dataset.tekst)));
  let nacin = null;
  app.querySelectorAll('[data-odg]').forEach((btn) => btn.addEventListener('click', () => {
    if (btn.dataset.odg === 'oboje') return zabiljezi('oboje');
    nacin = btn.dataset.odg;
    app.querySelector('#koje-pitanje').textContent = nacin === 'ne' ? 'Koje jelo ne bi jeo/jela?' : 'Koje jelo još nisi probao/probala?';
    app.querySelector('#koje').hidden = false;
    app.querySelector('#dodatni').hidden = true;
  }));
  app.querySelectorAll('[data-jela]').forEach((btn) => btn.addEventListener('click', () => {
    const v = btn.dataset.jela;
    if (v === 'odustani') { app.querySelector('#koje').hidden = true; app.querySelector('#dodatni').hidden = false; return; }
    zabiljezi(nacin, v === 'oba' ? [a, b] : [v === 'a' ? a : b]);
  }));
  app.querySelector('#natrag-odg').onclick = () => { const s2 = P.ucitaj(); P.natrag(P.dijete(s2, ime, IDOVI)); P.spremi(s2); igra(ime); };
}

function popisJela(ids, prazno) {
  if (!ids.length) return `<p class="sitno">${prazno}</p>`;
  return `<ul class="mini">${ids.map((id) => `<li data-id="${e(id)}">${slika(id, 'mini')}<span>${e(PO_ID[id].kratkiNaziv)}</span></li>`).join('')}</ul>`;
}

function rezultati(ime, upit, roditelj = false) {
  if (!DJECA.includes(ime)) return nijePronadeno();
  const s = P.ucitaj();
  const d = s.djeca[ime];
  const rez = L.rezultatDjeteta(d?.odgovori || [], IDOVI);
  const naslovFav = rez.precizno ? 'Najdraže jelo' : 'Mogući favoriti';
  app.innerHTML = `
    ${glavaStranice(roditelj ? `Poredak: ${ime}` : `Bravo, ${ime}!`, roditelj ? '#/roditelji' : '#/igra')}
    ${upit.get('kraj') ? '<p class="velik">🎉 Igra je gotova. Hvala!</p>' : ''}
    <p class="podnaslov">${rez.odgovora} odgovora${rez.odgovora < 20 ? ' — igra još nije gotova' : ''}.</p>
    <section class="rezultat" data-test="favoriti"><h2>${naslovFav}</h2>
      ${!rez.precizno && rez.favoriti.length > 1 ? '<p class="sitno">Još nema dovoljno odgovora za točan poredak, pa je ovo skupina jela koja su najčešće pobjeđivala.</p>' : ''}
      ${popisJela(rez.favoriti, 'Još nema odgovora.')}</section>
    <section class="rezultat" data-test="odbijena"><h2>Ovo ne bi jeo/jela</h2>${popisJela(rez.odbijena, 'Nijedno jelo.')}</section>
    <section class="rezultat" data-test="neprobana"><h2>Još nije probao/probala</h2>${popisJela(rez.neprobana, 'Nijedno jelo.')}</section>
    <section class="rezultat"><h2>Cijeli poredak</h2>
      <p class="sitno">Poraz u usporedbi znači samo da je drugo jelo bilo draže.</p>
      <ol class="poredak" data-test="poredak">${rez.poredak.map((x) => `<li data-id="${e(x.id)}">${e(PO_ID[x.id].kratkiNaziv)} <small>${x.w} pob. · ${x.l} por.${x.t ? ` · ${x.t}× oboje` : ''}</small></li>`).join('')}</ol>
    </section>
    ${roditelj ? '' : `<a class="gumb" href="#/igra">Sljedeći igrač</a>`}`;
}

// ---------- roditelji ----------
const ZNAK = {
  favorit: ['★', 'favorit'], rado: ['✓', 'rado jede'], manje: ['·', 'manje drago'],
  odbijeno: ['✗', 'ne bi jeo/jela'], neprobano: ['?', 'nije probao/probala'], nema: ['–', 'bez odgovora'],
};

function roditelji() {
  const s = P.ucitaj();
  const rez = rezultatiSvih();
  const ktx = L.kontekst(sada(), L.ZADANO_POSLUZIVANJE, false);
  const redovi = L.obiteljskiPoredak(RECEPTI, rez, ktx);
  const glasala = DJECA.filter((d) => rez[d].odgovora > 0);
  const vrh = redovi.filter((r) => r.izv.ok).slice(0, 3);
  const stanjeGlasanja = glasala.length === 0 ? 'Još nitko nije igrao.'
    : glasala.length === 4 ? 'Glasalo je svih četvero djece.' : `${L.zasadGlasala(glasala.length)} (${L.spoji(glasala)}).`;
  app.innerHTML = `
    ${glavaStranice('Roditeljski pregled')}
    <p class="podnaslov" data-test="glasanje">${e(stanjeGlasanja)}</p>
    <section class="preporuka"><h2>Preporuka za redoviti ručak</h2>
      <p class="sitno">Za danas u ${L.sat(ktx.posluzivanje)}: uzima u obzir što djeca vole, sastav obroka i stiže li se skuhati${ktx.petak ? ' (petak — bez mesa)' : ''}.</p>
      <ol class="vrh" data-test="preporuka">${vrh.map((r) => `
        <li data-id="${e(r.recept.id)}"><a href="#/recept/${r.recept.id}"><strong>${e(r.recept.naziv)}</strong></a>
        <p>${e(r.razlog)}</p></li>`).join('')}</ol>
    </section>
    <section><h2>Što djeca misle</h2>
      <p class="legenda">${Object.values(ZNAK).map(([z, t]) => `<span><b>${z}</b> ${t}</span>`).join(' ')}</p>
      <div class="tablica-omot"><table class="pregled" data-test="tablica">
        <thead><tr><th>Jelo</th>${DJECA.map((d) => `<th><a href="#/roditelji/${encodeURIComponent(d)}">${e(d)}</a></th>`).join('')}<th>Tanjur</th></tr></thead>
        <tbody>${redovi.map((r) => `
          <tr data-id="${e(r.recept.id)}" class="${r.izv.ok ? '' : 'neizvedivo'}">
            <th scope="row"><a href="#/recept/${r.recept.id}">${e(r.recept.kratkiNaziv)}</a>${r.izv.ok ? '' : `<small>danas ne: ${e(r.izv.zasto)}</small>`}</th>
            ${DJECA.map((d) => { const [z, t] = ZNAK[r.st.stavovi[d]]; return `<td class="st-${r.st.stavovi[d]}" title="${e(d)}: ${t}" data-dijete="${e(d)}"><span aria-label="${t}">${z}</span></td>`; }).join('')}
            <td class="tanjur r${r.sas.razina}">${e(L.NAZIV_RAZINE[r.sas.razina])}</td>
          </tr>`).join('')}</tbody>
      </table></div>
    </section>
    <section><h2>Osobni poredak</h2>
      <div class="igraci mali">${DJECA.map((d) => `<a class="igrac" href="#/roditelji/${encodeURIComponent(d)}"><span class="ime">${e(d)}</span><small>${rez[d].odgovora}/20</small></a>`).join('')}</div>
    </section>
    <section class="sigurnosna"><h2>Prijenos i sigurnosna kopija</h2>
      <p>Zadnji izvoz: <strong data-test="zadnji-izvoz">${s.zadnjiIzvoz ? datumHr(L.zagreb(Date.parse(s.zadnjiIzvoz)).datum) : 'nikad'}</strong></p>
      <p class="sitno">Odgovori su spremljeni samo na ovom uređaju. Safari briše podatke stranice koja se tjedan dana ne koristi — zato aplikaciju dodaj na početni zaslon i povremeno izvezi rezultate.</p>
      <button type="button" class="gumb" id="izvoz">⬆ Izvezi rezultate</button>
      <label class="gumb" for="uvoz">⬇ Uvezi datoteku</label>
      <input type="file" id="uvoz" accept="application/json,.json" hidden>
      <p id="poruka" class="poruka" role="status"></p>
      <details><summary>Obriši sve odgovore</summary>
        <button type="button" class="gumb opasno" id="brisi">Obriši odgovore sve djece na ovom uređaju</button></details>
    </section>
    <p><a href="#/o-aplikaciji">Kako aplikacija odlučuje?</a></p>`;
  const poruka = app.querySelector('#poruka');
  app.querySelector('#izvoz').onclick = async () => {
    const nacin = await P.izvezi(P.ucitaj());
    if (nacin) { roditelji(); app.querySelector('#poruka').textContent = nacin === 'dijeljenje' ? 'Datoteka je podijeljena.' : 'Datoteka je preuzeta.'; }
  };
  app.querySelector('#uvoz').onchange = async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    try {
      const djeca = P.procitajUvoz(await f.text());
      const s2 = P.ucitaj();
      s2.djeca = djeca;
      P.spremi(s2);
      roditelji();
      app.querySelector('#poruka').textContent = `Uvezeno: ${Object.keys(djeca).join(', ') || 'nema podataka'}.`;
    } catch (err) { poruka.textContent = err.message; }
  };
  app.querySelector('#brisi').onclick = () => {
    if (!confirm('Sigurno obrisati sve odgovore na ovom uređaju?')) return;
    const s2 = P.ucitaj(); s2.djeca = {}; P.spremi(s2); roditelji();
  };
}

function oAplikaciji() {
  app.innerHTML = `
    ${glavaStranice('Kako aplikacija odlučuje')}
    <section class="tekst">
      <h2>Prijedlozi na prvom ekranu</h2>
      <p>Sva vremena računaju se po zagrebačkom vremenu. Jelo se predlaže samo ako ga se, krenuvši sada, stigne skuhati do odabranog vremena. Jela koja traže pripremu večer prije ne nude se za danas. Za ručak koji pada u petak nude se samo jela bez mesa, suhomesnatih proizvoda, masti i mesnog temeljca (riba i jaja su u redu). Ako za odabrano vrijeme nema dovoljno jela, aplikacija pokazuje tri jela koja možeš početi odmah i kada će biti gotova.</p>
      <h2>Igra</h2>
      <p>Svako dijete u prvom krugu vidi svih 24 jela po jednom (12 parova), s pauzom nakon šest parova. U drugom krugu ima osam usporedbi između jela koja su dotad najčešće pobjeđivala. Izbor jednog jela znači samo „drugo mi je manje drago”, a ne da dijete drugo jelo ne voli. „Nisam probao/probala” nikad se ne računa kao odbijanje.</p>
      <h2>Obiteljska preporuka</h2>
      <p>Tri zasebne stvari: (1) koliko jelo vole djeca koja su o njemu glasala i je li ga netko izričito odbio, (2) koliko je obrok uravnotežen u obliku u kojem je recept napisan i (3) može li se danas skuhati na vrijeme i odgovara li pravilu za petak. Dječji osobni poredak ovisi samo o njihovim odgovorima.</p>
      <h2>Sastav obroka</h2>
      <p>Procjena se oslanja na smjernicu „Moj tanjur”: polovicu tanjura čine povrće i voće, a drugu polovicu namirnice bogate bjelančevinama i žitarice (ili krumpir). Za svaki recept zbrojena je približna masa povrća, bjelančevina (meso, riba, jaja, mahunarke, sir) i priloga na tanjurima. Opis je riječima — bez bodova. Neobavezna salata koju recept samo predlaže nije uračunata.</p>
      <p class="izvor">Izvor: Hrvatski zavod za javno zdravstvo, <cite>Prehrambene smjernice za 5. – 8. razrede osnovnih škola</cite>, <a href="https://www.hzjz.hr/wp-content/uploads/2018/06/Brosura-OSNOVNA-SKOLA.pdf" rel="noopener">https://www.hzjz.hr/wp-content/uploads/2018/06/Brosura-OSNOVNA-SKOLA.pdf</a></p>
      <h2>Privatnost</h2>
      <p>Nema računa, analitike ni slanja podataka. Odgovori djece ostaju na ovom uređaju dok ih sam ne izvezeš.</p>
    </section>`;
}

function nijePronadeno() {
  app.innerHTML = `${glavaStranice('Nije pronađeno')}<p>Ova stranica ne postoji. <a href="#/">Na početak</a></p>`;
}

// ---------- usmjeravanje ----------
function prikazi() {
  pustiZaslon();
  const { dijelovi, upit } = ruta();
  const [a, b] = dijelovi;
  document.body.dataset.stranica = a || 'pocetna';
  if (!a) prviEkran(upit);
  else if (a === 'recepti') popisRecepata(upit);
  else if (a === 'recept') prikazRecepta(b, upit);
  else if (a === 'kuhanje') kuhanje(b, upit);
  else if (a === 'igra' && b) igra(b);
  else if (a === 'igra') odabirIgraca();
  else if (a === 'rezultati') rezultati(b, upit);
  else if (a === 'roditelji' && b) rezultati(b, upit, true);
  else if (a === 'roditelji') roditelji();
  else if (a === 'o-aplikaciji') oAplikaciji();
  else nijePronadeno();
  window.scrollTo(0, 0);
  document.body.dataset.spremno = '1';
}

function nadjiGlas() {
  if (!('speechSynthesis' in window)) return;
  const prije = hrGlas;
  hrGlas = speechSynthesis.getVoices().find((v) => /^hr\b|^hr-/i.test(v.lang)) || null;
  if (!prije && hrGlas && ruta().dijelovi[0] === 'igra') prikazi();
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && ruta().dijelovi[0] === 'kuhanje') zadrziZaslon();
});

async function pokreni() {
  try {
    const odg = await fetch('podaci/recepti.json');
    RECEPTI = await odg.json();
  } catch {
    app.innerHTML = '<p class="upozorenje">Recepti se nisu učitali. Otvori aplikaciju jednom s internetom.</p>';
    return;
  }
  IDOVI = RECEPTI.map((r) => r.id);
  PO_ID = Object.fromEntries(RECEPTI.map((r) => [r.id, r]));
  window.addEventListener('hashchange', prikazi);
  if ('speechSynthesis' in window) { nadjiGlas(); speechSynthesis.addEventListener?.('voiceschanged', nadjiGlas); }
  prikazi();
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

pokreni();
