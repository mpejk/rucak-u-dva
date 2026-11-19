#!/usr/bin/env python3
"""Crta 24 autorske SVG ilustracije jela u istom stilu (tanjur odozgo, ista paleta).

Pokretanje: python3 alati/crtaj_slike.py  -> slike/<id>.svg i ikone/ikona.svg
"""
import math
import random
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent

C = {  # zajednička paleta
    "tanjur": "#fbf8f2", "rub": "#e9e1d3", "sjena": "#d8cfbf",
    "krumpir": "#efcd6e", "krumpir2": "#d9ae48", "pire": "#f5e4b0", "riza": "#f8f4ea", "riza2": "#e6dcc6",
    "tijesto": "#f0cf7e", "tijesto2": "#d8ad55", "umak": "#c8452f", "umak2": "#a8331f",
    "smede": "#8a5636", "smede2": "#6d3f25", "zlatno": "#d99a4e", "zlatno2": "#b97a31",
    "losos": "#ef8a5c", "losos2": "#f6b28d", "bijelo": "#ffffff", "zumanjak": "#f5b52e",
    "zeleno": "#5f9e45", "zeleno2": "#3e7a33", "svjetlozeleno": "#a9cf72", "grasak": "#7db446",
    "mrkva": "#ef8a2a", "mrkva2": "#f6ac5a", "rajcica": "#e04a3c", "paprika": "#d63c2a", "zuto": "#f3c73f",
    "sir": "#f6d870", "kupus": "#dfe8bf", "kupus2": "#c3d496", "kozica": "#f39c84", "kozica2": "#e47b62",
    "gljiva": "#c9a47e", "gljiva2": "#a9825c", "grah": "#8d3b2c", "kruh": "#e2b768", "kruh2": "#c9964a",
    "palenta": "#f4c64a", "ljubicasto": "#9b4f7a", "limun": "#f7e06b",
}

R = None  # random po jelu, deterministički


def tanjur():
    return (f'<circle cx="120" cy="124" r="112" fill="{C["sjena"]}" opacity=".55"/>'
            f'<circle cx="120" cy="120" r="112" fill="{C["rub"]}"/>'
            f'<circle cx="120" cy="120" r="96" fill="{C["tanjur"]}"/>'
            f'<circle cx="120" cy="120" r="96" fill="none" stroke="{C["rub"]}" stroke-width="2" opacity=".8"/>')


def blob(cx, cy, r, boja, n=9, nep=0.18, extra=""):
    t = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + R.uniform(-nep, nep))
        t.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{(t[0][0] + t[-1][0]) / 2:.1f},{(t[0][1] + t[-1][1]) / 2:.1f} "
    for i in range(n):
        p, q = t[i], t[(i + 1) % n]
        d += f"Q{p[0]:.1f},{p[1]:.1f} {(p[0] + q[0]) / 2:.1f},{(p[1] + q[1]) / 2:.1f} "
    return f'<path d="{d}Z" fill="{boja}" {extra}/>'


def krug(x, y, r, boja, extra=""):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{boja}" {extra}/>'


def tocke(cx, cy, r, n, rt, boja):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        s += krug(cx + d * math.cos(a), cy + d * math.sin(a), rt, boja)
    return s


def zrna(cx, cy, r, n, boja):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 180)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="3.2" ry="1.4" fill="{boja}" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>'
    return s


def krumpiri(cx, cy, r, n, vel=11):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += blob(x, y, vel, C["krumpir"], 6, 0.25, f'stroke="{C["krumpir2"]}" stroke-width="1.5"')
    return s


def kriske_krumpira(cx, cy, r, n):
    s = ""
    for i in range(n):
        a = 2 * math.pi * i / n + R.uniform(-.2, .2)
        x, y = cx + r * math.cos(a) * R.uniform(.3, 1), cy + r * math.sin(a) * R.uniform(.3, 1)
        k = math.degrees(a) + R.uniform(-30, 30)
        s += (f'<path d="M{x - 18:.1f},{y + 4:.1f} Q{x - 14:.1f},{y - 16:.1f} {x:.1f},{y - 16:.1f} Q{x + 14:.1f},{y - 16:.1f} {x + 18:.1f},{y + 4:.1f} Z" fill="{C["krumpir"]}" '
              f'stroke="{C["zlatno2"]}" stroke-width="3" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>')
    return s


def pire(cx, cy, r):
    return (blob(cx, cy, r, C["pire"], 10, .12) +
            f'<path d="M{cx - r * .5:.1f},{cy:.1f} q{r * .25:.1f},{-r * .35:.1f} {r * .5:.1f},0 t{r * .5:.1f},0" fill="none" stroke="{C["krumpir2"]}" stroke-width="2" opacity=".55"/>'
            + krug(cx + r * .15, cy - r * .2, r * .16, C["zuto"], 'opacity=".8"'))


def riza(cx, cy, r):
    return blob(cx, cy, r, C["riza"], 10, .12, f'stroke="{C["riza2"]}" stroke-width="1.5"') + zrna(cx, cy, r * .85, int(r * 1.3), C["riza2"])


def grasak(cx, cy, r, n):
    return tocke(cx, cy, r, n, 4.2, C["grasak"])


def mrkva_kolutovi(cx, cy, r, n):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += krug(x, y, 7.5, C["mrkva"]) + krug(x, y, 3.3, C["mrkva2"])
    return s


def mrkva_stapici(cx, cy, r, n):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 180)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += f'<rect x="{x - 14:.1f}" y="{y - 4:.1f}" width="28" height="8" rx="4" fill="{C["mrkva"]}" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>'
    return s


def krastavci(cx, cy, r, n):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += krug(x, y, 9, C["zeleno"]) + krug(x, y, 7, "#dcefc4") + tocke(x, y, 3, 3, 1, C["svjetlozeleno"])
    return s


def lisce(cx, cy, r, n, boja=None, vel=10):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 360)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += (f'<path d="M{x:.1f},{y - vel:.1f} Q{x + vel * .8:.1f},{y:.1f} {x:.1f},{y + vel:.1f} Q{x - vel * .8:.1f},{y:.1f} {x:.1f},{y - vel:.1f}Z" '
              f'fill="{boja or C["zeleno"]}" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>')
    return s


def brokula(cx, cy, r, n):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += krug(x, y, 8, C["zeleno2"]) + krug(x - 4, y - 3, 4.5, C["zeleno"]) + krug(x + 4, y - 2, 4.5, C["zeleno"]) + krug(x, y + 4, 4.5, C["zeleno"])
    return s


def trake(cx, cy, r, n, boja, d1=26, d2=7):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 180)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += f'<rect x="{x - d1 / 2:.1f}" y="{y - d2 / 2:.1f}" width="{d1}" height="{d2}" rx="{d2 / 2:.1f}" fill="{boja}" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>'
    return s


def jaje_pola(x, y, k=0):
    return (f'<g transform="rotate({k} {x} {y})"><ellipse cx="{x}" cy="{y}" rx="15" ry="11" fill="{C["bijelo"]}" stroke="{C["rub"]}" stroke-width="1.5"/>'
            f'{krug(x, y, 6.5, C["zumanjak"])}</g>')


def fillet(x, y, w, h, boja, rub, k=0, crumbs=False):
    s = f'<g transform="rotate({k} {x} {y})"><rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="{h / 2.4:.1f}" fill="{boja}" stroke="{rub}" stroke-width="2.5"/>'
    if crumbs:
        s += tocke(x, y, min(w, h) / 2.4, 18, 1.4, rub)
    return s + '</g>'


def losos(x, y, k=0):
    s = f'<g transform="rotate({k} {x} {y})"><rect x="{x - 34}" y="{y - 20}" width="68" height="40" rx="14" fill="{C["losos"]}" stroke="{C["zlatno2"]}" stroke-width="3"/>'
    for i in range(-2, 3):
        s += f'<path d="M{x + i * 12 - 4},{y - 17} q8,17 0,34" fill="none" stroke="{C["losos2"]}" stroke-width="3" opacity=".85"/>'
    return s + '</g>'


def tjestenina(cx, cy, r, n, boja=None):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 180)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += (f'<g transform="rotate({k:.0f} {x:.1f} {y:.1f})"><path d="M{x - 11:.1f},{y - 5:.1f} L{x + 9:.1f},{y - 5:.1f} L{x + 12:.1f},{y + 5:.1f} L{x - 8:.1f},{y + 5:.1f}Z" '
              f'fill="{boja or C["tijesto"]}" stroke="{C["tijesto2"]}" stroke-width="1.4"/>'
              f'<path d="M{x - 6:.1f},{y - 5:.1f} l2,10 M{x:.1f},{y - 5:.1f} l2,10 M{x + 6:.1f},{y - 5:.1f} l2,10" stroke="{C["tijesto2"]}" stroke-width="1" opacity=".6"/></g>')
    return s


def spageti(cx, cy, r):
    s = blob(cx, cy, r, C["tijesto"], 10, .1)
    for i in range(16):
        rr = R.uniform(r * .2, r * .95); a0 = R.uniform(0, 6.28)
        x1, y1 = cx + rr * math.cos(a0), cy + rr * math.sin(a0)
        x2, y2 = cx + rr * math.cos(a0 + 2), cy + rr * math.sin(a0 + 2)
        s += f'<path d="M{x1:.1f},{y1:.1f} A{rr:.1f},{rr:.1f} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{C["tijesto2"]}" stroke-width="1.6" opacity=".7"/>'
    return s


def kuglice(cx, cy, r, n, boja, rub, vel=11):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += krug(x, y, vel, boja, f'stroke="{rub}" stroke-width="2"') + krug(x - vel * .3, y - vel * .35, vel * .3, "#ffffff", 'opacity=".18"')
    return s


def kocke(cx, cy, r, n, boja, rub, vel=12):
    s = ""
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi); d = r * math.sqrt(R.random()); k = R.uniform(0, 90)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s += f'<rect x="{x - vel / 2:.1f}" y="{y - vel / 2:.1f}" width="{vel}" height="{vel}" rx="3" fill="{boja}" stroke="{rub}" stroke-width="1.5" transform="rotate({k:.0f} {x:.1f} {y:.1f})"/>'
    return s


def kozica(x, y, k=0):
    return (f'<g transform="rotate({k} {x} {y})"><path d="M{x - 10},{y - 8} A11,11 0 1 0 {x + 10},{y - 6}" fill="none" stroke="{C["kozica"]}" stroke-width="8" stroke-linecap="round"/>'
            f'<path d="M{x - 10},{y - 8} A11,11 0 1 0 {x + 10},{y - 6}" fill="none" stroke="{C["kozica2"]}" stroke-width="1.5" stroke-dasharray="3 4"/></g>')


def batak(x, y, k=0):
    return (f'<g transform="rotate({k} {x} {y})"><rect x="{x + 22}" y="{y - 5}" width="26" height="10" rx="5" fill="#f3ead8" stroke="#cfc3ad" stroke-width="1.5"/>'
            f'<circle cx="{x + 48}" cy="{y - 5}" r="6" fill="#f3ead8" stroke="#cfc3ad" stroke-width="1.5"/><circle cx="{x + 48}" cy="{y + 5}" r="6" fill="#f3ead8" stroke="#cfc3ad" stroke-width="1.5"/>'
            f'<path d="M{x - 30},{y} Q{x - 28},{y - 24} {x},{y - 22} Q{x + 22},{y - 14} {x + 26},{y} Q{x + 22},{y + 14} {x},{y + 22} Q{x - 28},{y + 24} {x - 30},{y} Z" fill="{C["zlatno"]}" stroke="{C["zlatno2"]}" stroke-width="3"/>'
            f'<ellipse cx="{x - 8}" cy="{y - 7}" rx="12" ry="5" fill="#ffffff" opacity=".22"/></g>')


def zlatni_odrezak(x, y, w, h, k=0):
    return fillet(x, y, w, h, C["zlatno"], C["zlatno2"], k, crumbs=True)


def sarma(x, y, k=0):
    s = f'<g transform="rotate({k} {x} {y})"><rect x="{x - 24}" y="{y - 14}" width="48" height="28" rx="13" fill="{C["kupus2"]}" stroke="#9fb36c" stroke-width="2"/>'
    for i in (-12, 0, 12):
        s += f'<path d="M{x + i},{y - 13} q4,13 0,26" fill="none" stroke="#9fb36c" stroke-width="1.6"/>'
    return s + '</g>'


def paprika_punjena(x, y):
    return (krug(x, y, 25, C["paprika"], f'stroke="{C["umak2"]}" stroke-width="2.5"') +
            krug(x, y, 15, C["smede"]) + tocke(x, y, 10, 8, 2, C["riza"]) +
            f'<rect x="{x - 3}" y="{y - 31}" width="6" height="10" rx="2" fill="{C["zeleno2"]}"/>')


def cevap(x, y, k=0):
    return f'<rect x="{x - 21}" y="{y - 8}" width="42" height="16" rx="8" fill="{C["smede"]}" stroke="{C["smede2"]}" stroke-width="2.5" transform="rotate({k} {x} {y})"/>'


def ploska_mesa(x, y, k=0, boja=None):
    return (f'<g transform="rotate({k} {x} {y})"><ellipse cx="{x}" cy="{y}" rx="28" ry="17" fill="{boja or "#c98d6a"}" stroke="{C["smede2"]}" stroke-width="3"/>'
            f'<ellipse cx="{x + 4}" cy="{y + 2}" rx="12" ry="6" fill="#e3b496" opacity=".7"/></g>')


def kruh(x, y, k=0, boja=None):
    return (f'<g transform="rotate({k} {x} {y})"><rect x="{x - 22}" y="{y - 18}" width="44" height="36" rx="10" fill="{C["kruh2"]}"/>'
            f'<rect x="{x - 18}" y="{y - 14}" width="36" height="28" rx="8" fill="{boja or C["kruh"]}"/>'
            f'{tocke(x, y, 10, 7, 1.4, C["kruh2"])}</g>')


def zdjela_variva(cx, cy, r, boja):
    return blob(cx, cy, r, boja, 12, .05)


# ---------------- jela ----------------
def losos_krumpir_salata():
    return (blob(140, 150, 46, "#f6eccb", 10, .12) + krumpiri(140, 150, 34, 11, 11) + krastavci(145, 145, 36, 6) + tocke(140, 150, 34, 10, 3.2, C["rajcica"]) +
            jaje_pola(95, 168, 20) + jaje_pola(118, 190, -10) + '<g transform="translate(-20,-18) scale(1.2)">' + losos(95, 92, -20) + '</g>' +
            lisce(150, 145, 30, 5, C["svjetlozeleno"], 5) + krug(182, 98, 10, C["limun"], f'stroke="{C["zuto"]}" stroke-width="3"'))


def tjestenina_tuna():
    return (blob(120, 120, 70, C["umak"], 10, .15) + tjestenina(120, 120, 56, 26) + tocke(120, 120, 50, 18, 4.2, C["grasak"]) +
            tocke(120, 120, 45, 12, 5, "#d9c4a8") + tocke(120, 120, 40, 20, 1.4, "#fff6d6"))


def pizza_sir():
    s = krug(120, 120, 72, C["tijesto2"]) + krug(120, 120, 63, C["umak"])
    s += tocke(120, 120, 50, 14, 9, C["sir"]) + tocke(120, 120, 50, 8, 5, C["rajcica"]) + lisce(120, 120, 46, 5, C["zeleno"], 6)
    for i in range(6):
        a = math.pi * i / 3
        s += f'<line x1="120" y1="120" x2="{120 + 72 * math.cos(a):.1f}" y2="{120 + 72 * math.sin(a):.1f}" stroke="{C["tijesto2"]}" stroke-width="2.5" opacity=".7"/>'
    return s


def oslic_blitva():
    return (blob(148, 145, 46, C["zeleno2"], 10, .15) + krumpiri(148, 145, 32, 7, 9) + lisce(148, 145, 34, 11, C["zeleno"], 10) +
            zlatni_odrezak(88, 102, 84, 40, -25) + zlatni_odrezak(112, 70, 64, 32, -15) + krug(180, 88, 10, C["limun"], f'stroke="{C["zuto"]}" stroke-width="3"'))


def rizoto_kozice():
    s = blob(120, 120, 72, "#f3ecd6", 12, .1) + zrna(120, 120, 64, 110, C["riza2"]) + tocke(120, 120, 58, 20, 4.2, C["grasak"])
    s += kocke(120, 120, 55, 8, C["svjetlozeleno"], C["zeleno"], 8)
    for x, y, k in [(95, 95, 10), (140, 90, 80), (150, 140, 160), (100, 145, 230), (122, 118, 300)]:
        s += kozica(x, y, k)
    return s


def fritaja_krumpir_spinat():
    s = f'<path d="M120,120 L190,85 A78,78 0 0 1 175,175 Z" fill="{C["zuto"]}" stroke="{C["zlatno2"]}" stroke-width="3"/>'
    s += f'<path d="M110,118 L40,95 A78,78 0 0 0 70,170 Z" fill="{C["zuto"]}" stroke="{C["zlatno2"]}" stroke-width="3"/>'
    s += lisce(165, 120, 22, 6, C["zeleno2"], 6) + lisce(70, 125, 22, 6, C["zeleno2"], 6) + tocke(165, 120, 22, 5, 4, C["krumpir2"]) + tocke(70, 125, 22, 5, 4, C["krumpir2"])
    s += trake(118, 168, 24, 7, C["paprika"], 30, 9) + trake(118, 70, 22, 6, C["zuto"], 30, 9) + trake(118, 72, 20, 3, C["paprika"], 30, 9)
    return s


def posni_grah():
    return (zdjela_variva(120, 120, 80, "#b8603e") + kuglice(118, 120, 58, 26, C["grah"], "#6d2b20", 6.5) +
            kocke(118, 120, 52, 8, C["krumpir"], C["krumpir2"], 11) + mrkva_kolutovi(118, 120, 52, 7) + lisce(120, 120, 50, 6, C["zeleno"], 5) +
            kruh(175, 175, 20, C["palenta"]))


def lazanje_tikvice():
    s = f'<rect x="55" y="70" width="130" height="100" rx="10" fill="{C["tijesto"]}" stroke="{C["tijesto2"]}" stroke-width="3"/>'
    s += f'<rect x="55" y="70" width="130" height="100" rx="10" fill="{C["umak"]}" opacity=".35"/>'
    s += tocke(120, 120, 50, 12, 10, "#fbf3dc") + tocke(120, 120, 50, 12, 6.5, C["svjetlozeleno"]) + tocke(120, 120, 50, 10, 4, C["sir"])
    s += lisce(120, 120, 45, 4, C["zeleno"], 7)
    return s


def riblji_stapici_pire():
    s = pire(150, 150, 40) + grasak(85, 160, 26, 30)
    for i, (x, y) in enumerate([(85, 85), (95, 105), (105, 125), (125, 75), (140, 95)]):
        s += f'<rect x="{x - 26}" y="{y - 8}" width="52" height="16" rx="5" fill="{C["zlatno"]}" stroke="{C["zlatno2"]}" stroke-width="2.5" transform="rotate(-25 {x} {y})"/>'
    s += krug(185, 105, 9, C["limun"], f'stroke="{C["zuto"]}" stroke-width="3"')
    return s


def spageti_bolonjez():
    return (spageti(120, 120, 74) + blob(120, 112, 38, C["umak"], 10, .2) + tocke(120, 112, 32, 26, 4, C["smede"]) +
            tocke(120, 112, 30, 10, 3, C["mrkva"]) + tocke(120, 112, 30, 14, 1.8, "#fff6d6") + lisce(130, 100, 6, 2, C["zeleno"], 6))


def cufte_pire():
    return (pire(85, 145, 40) + blob(150, 105, 52, C["umak"], 10, .12) + kuglice(150, 105, 34, 6, C["smede"], C["smede2"], 12) +
            tocke(150, 105, 40, 10, 3, C["mrkva"]) + lisce(85, 140, 10, 2, C["zeleno"], 5))


def bataci_krumpir_mrkva():
    return (kriske_krumpira(82, 145, 30, 6) + mrkva_stapici(150, 162, 26, 8) + batak(100, 82, -10) + batak(118, 118, 15) +
            lisce(150, 130, 30, 4, C["zeleno2"], 5))


def pasticada_njoki():
    s = blob(140, 110, 56, "#6e3220", 10, .12)
    s += ploska_mesa(130, 95, -15, "#7d3f27") + ploska_mesa(150, 125, 10, "#7d3f27")
    s += tocke(140, 110, 46, 8, 3, C["mrkva"]) + tocke(140, 110, 42, 5, 4, C["ljubicasto"])
    for _ in range(14):
        a = R.uniform(0, 6.28); d = 34 * math.sqrt(R.random()); x, y = 80 + d * math.cos(a), 160 + d * math.sin(a) * .8
        s += (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="11" ry="8" fill="{C["pire"]}" stroke="{C["krumpir2"]}" stroke-width="1.8"/>'
              f'<path d="M{x - 5:.1f},{y - 6:.1f} v12 M{x:.1f},{y - 7:.1f} v14 M{x + 5:.1f},{y - 6:.1f} v12" stroke="{C["krumpir2"]}" stroke-width="1.2" opacity=".7"/>')
    return s


def sarma_pire():
    return (pire(85, 150, 38) + blob(150, 105, 54, "#c56a3c", 10, .1, 'opacity=".55"') + trake(150, 110, 45, 10, C["kupus"], 30, 5) +
            sarma(140, 85, -20) + sarma(160, 115, 15) + sarma(130, 130, -5) + kocke(180, 145, 6, 1, C["smede"], C["smede2"], 14))


def pohana_piletina_rizi_bizi():
    return (riza(85, 145, 38) + grasak(85, 145, 30, 20) + krastavci(160, 160, 18, 5) + blob(160, 160, 22, "#ffffff", 8, .1, 'opacity=".35"') +
            zlatni_odrezak(130, 85, 76, 40, -15) + krug(180, 105, 8, C["limun"], f'stroke="{C["zuto"]}" stroke-width="3"'))


def punjene_paprike():
    return (blob(130, 105, 60, C["umak"], 10, .1) + paprika_punjena(110, 90) + paprika_punjena(155, 115) +
            blob(85, 165, 17, C["krumpir"], 7, .15, f'stroke="{C["krumpir2"]}" stroke-width="2"') +
            blob(120, 175, 17, C["krumpir"], 7, .15, f'stroke="{C["krumpir2"]}" stroke-width="2"') + lisce(100, 170, 20, 3, C["zeleno"], 5))


def gulas_palenta():
    return (blob(95, 135, 46, C["palenta"], 9, .12, f'stroke="{C["zlatno"]}" stroke-width="2"') + krug(95, 130, 10, C["zuto"], 'opacity=".7"') +
            blob(150, 105, 50, "#9b3d22", 10, .12) + kocke(150, 105, 34, 9, C["smede"], C["smede2"], 14) +
            mrkva_kolutovi(150, 105, 34, 4) + tocke(150, 105, 36, 6, 4, C["paprika"]))


def piletina_wok_riza():
    return (riza(85, 140, 40) + blob(150, 105, 50, "#a8642d", 10, .12, 'opacity=".45"') + trake(150, 105, 38, 8, C["zlatno"], 26, 9) +
            brokula(150, 105, 36, 5) + mrkva_stapici(150, 105, 36, 4) + trake(150, 105, 34, 4, C["paprika"], 22, 6) + tocke(85, 135, 20, 8, 2, C["zeleno"]))


def cevapi_krumpir():
    s = kriske_krumpira(78, 150, 26, 6) + trake(152, 168, 24, 16, C["kupus"], 28, 5)
    s += blob(172, 112, 20, C["umak"], 8, .1) + kocke(120, 152, 12, 9, "#f4eef6", "#d9c8de", 6)
    for (x, y) in [(88, 82), (100, 98), (112, 114), (122, 72), (134, 88), (146, 104), (152, 70)]:
        s += cevap(x, y, 35)
    return s


def svinjska_pecenka():
    return (kriske_krumpira(82, 150, 24, 6) + trake(155, 162, 24, 18, C["kupus2"], 28, 5) +
            '<g transform="translate(-24,-20) scale(1.2)">' + ploska_mesa(110, 90, -10) + ploska_mesa(145, 100, 15) + ploska_mesa(128, 118, -5) + '</g>' +
            tocke(130, 100, 30, 8, 1.6, C["smede2"]))


def musaka_krumpir():
    s = f'<rect x="60" y="70" width="120" height="96" rx="12" fill="{C["zuto"]}" stroke="{C["zlatno2"]}" stroke-width="3"/>'
    s += tocke(120, 118, 46, 10, 9, C["zlatno"]) + tocke(120, 118, 46, 10, 4, "#fff1b8")
    s += f'<rect x="60" y="150" width="120" height="16" rx="6" fill="{C["smede"]}" opacity=".85"/>'
    s += f'<rect x="60" y="138" width="120" height="10" rx="5" fill="{C["krumpir"]}"/>'
    s += lisce(165, 75, 5, 2, C["zeleno"], 6)
    return s


def hamburgeri_domaci():
    s = krug(105, 105, 44, C["kruh2"]) + krug(105, 105, 40, C["kruh"])
    s += tocke(105, 100, 30, 14, 1.8, "#fff4d6")
    s += f'<path d="M64,118 q41,22 82,0" fill="none" stroke="{C["zeleno"]}" stroke-width="7" stroke-linecap="round"/>'
    s += f'<path d="M66,124 q39,18 78,0" fill="none" stroke="{C["rajcica"]}" stroke-width="5" stroke-linecap="round"/>'
    for i in range(9):
        x = 140 + i * 6; y = 150 + (i % 3) * 8
        s += f'<rect x="{x}" y="{y}" width="8" height="34" rx="3" fill="{C["krumpir"]}" stroke="{C["zlatno2"]}" stroke-width="1.4" transform="rotate({-20 + i * 6} {x} {y})"/>'
    s += krastavci(80, 170, 14, 3)
    return s


def pureci_medaljoni_gljive():
    s = riza(80, 135, 36) + trake(165, 155, 22, 12, C["zeleno"], 30, 6)
    s += blob(140, 95, 42, "#e6d3b6", 10, .12)
    s += ploska_mesa(128, 88, 0, "#e2b98c") + ploska_mesa(152, 104, 20, "#e2b98c")
    for _ in range(6):
        a = R.uniform(0, 6.28); d = 34 * math.sqrt(R.random()); x, y = 140 + d * math.cos(a), 95 + d * math.sin(a)
        s += f'<path d="M{x - 7:.1f},{y:.1f} a7,6 0 0 1 14,0 Z" fill="{C["gljiva"]}" stroke="{C["gljiva2"]}" stroke-width="1.5"/><rect x="{x - 2:.1f}" y="{y:.1f}" width="4" height="5" fill="{C["gljiva"]}"/>'
    return s + lisce(140, 95, 30, 3, C["zeleno2"], 4)


def varivo_mahune():
    return (zdjela_variva(115, 115, 76, "#d9b26f") + trake(115, 115, 55, 16, C["zeleno"], 24, 6) + mrkva_kolutovi(115, 115, 50, 7) +
            kocke(115, 115, 50, 6, C["krumpir"], C["krumpir2"], 11) + kocke(115, 115, 48, 5, C["smede"], C["smede2"], 11) + kruh(178, 175, -15))


CRTEZI = {
    "losos-krumpir-salata": losos_krumpir_salata, "tjestenina-tuna": tjestenina_tuna, "pizza-sir": pizza_sir,
    "oslic-blitva": oslic_blitva, "rizoto-kozice": rizoto_kozice, "fritaja-krumpir-spinat": fritaja_krumpir_spinat,
    "posni-grah": posni_grah, "lazanje-tikvice": lazanje_tikvice, "riblji-stapici-pire": riblji_stapici_pire,
    "spageti-bolonjez": spageti_bolonjez, "cufte-pire": cufte_pire, "bataci-krumpir-mrkva": bataci_krumpir_mrkva,
    "pasticada-njoki": pasticada_njoki, "sarma-pire": sarma_pire, "pohana-piletina-rizi-bizi": pohana_piletina_rizi_bizi,
    "punjene-paprike": punjene_paprike, "gulas-palenta": gulas_palenta, "piletina-wok-riza": piletina_wok_riza,
    "cevapi-krumpir": cevapi_krumpir, "svinjska-pecenka": svinjska_pecenka, "musaka-krumpir": musaka_krumpir,
    "hamburgeri-domaci": hamburgeri_domaci, "pureci-medaljoni-gljive": pureci_medaljoni_gljive, "varivo-mahune": varivo_mahune,
}


def svg(sadrzaj, naslov):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240" role="img">'
            f'<title>{naslov}</title>{sadrzaj}</svg>\n')


def main():
    global R
    import json
    recepti = json.loads((KORIJEN / "podaci" / "recepti.json").read_text(encoding="utf-8"))
    (KORIJEN / "slike").mkdir(exist_ok=True)
    for r in recepti:
        R = random.Random(r["id"])
        (KORIJEN / "slike" / f'{r["id"]}.svg').write_text(svg(tanjur() + CRTEZI[r["id"]](), r["kratkiNaziv"]), encoding="utf-8")
    R = random.Random("ikona")
    ikona = (f'<rect width="240" height="240" rx="0" fill="#2f6b4f"/>' + tanjur().replace('cy="124"', 'cy="122"') +
             krug(120, 120, 34, C["palenta"]) + lisce(120, 120, 2, 1, C["zeleno"], 20))
    (KORIJEN / "ikone").mkdir(exist_ok=True)
    (KORIJEN / "ikone" / "ikona.svg").write_text(svg(ikona, "Ručak u dva"), encoding="utf-8")
    print(f"Nacrtano {len(recepti)} slika.")


if __name__ == "__main__":
    main()
