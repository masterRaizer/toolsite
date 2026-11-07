#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка статического сайта «Пенная полка» в ./out
   Картинки: если в ./images лежит <ключ>.jpg|.jpeg|.webp|.png — берётся он, иначе генерируется SVG.
   Ключи: слаги статей, hero, history, forum, chat, library, about."""
import argparse, hashlib, html, json, os, random, re, shutil, sys, zipfile, datetime as dt

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content_articles import ARTICLES, RUBRICS          # noqa: E402
from content_community import USERS, THREADS, CHAT_SCRIPT, CHAT_REPLIES, TIMELINE  # noqa: E402

OUT = os.path.join(HERE, "out")
IMGDIR = os.path.join(HERE, "images")
# Варианты оформления: (название, подпись под логотипом, фирменный цвет)
VARIANTS = [
    ("Пенная полка", "журнал о пиве", "#c8961e"),
    ("Хмельной вестник", "журнал о пиве и пивоварении", "#b8742a"),
    ("Солод и хмель", "журнал о пиве", "#9a8a2e"),
    ("Янтарная кружка", "журнал о пиве", "#c47a1e"),
    ("Пивной альманах", "журнал о пиве и людях", "#a8632a"),
    ("Пенный листок", "журнал о пиве", "#bf8f2a"),
    ("Хмель и шишка", "журнал о пиве", "#7d8f2e"),
]
SITE, SUB, ACCENT = VARIANTS[0]
TAG = "журнал о пиве: история, стили, пивоварни и люди"
TODAY = dt.date.today()
YEAR = TODAY.year
SLUG = "pennaya-polka"
RND = random.Random(0)
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
E = html.escape

BEER = {"gold": "#f2b632", "amber": "#c9731d", "dark": "#3a2216", "hazy": "#f5c862"}


def rus_date(s):
    d = dt.date.fromisoformat(s)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def write(path, data, mode="w"):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f:
        f.write(data)


def plain(body):
    return re.sub(r"^(## |- |> )", "", body, flags=re.M)


# ------------------------------------------------------------------ иллюстрации (SVG)
GLASS = {
    "pint": ("M-105,-235 L105,-235 L88,235 L-88,235 Z", -235, 235),
    "pilsner": ("M-78,-265 L78,-265 L44,215 L-44,215 Z M-60,215 L60,215 L60,240 L-60,240 Z", -265, 215),
    "tulip": ("M-70,-250 C-110,-170 -120,-60 -85,20 C-60,75 -20,95 -16,120 L-16,205 L-80,225 L80,225 L16,205 L16,120 C20,95 60,75 85,20 C120,-60 110,-170 70,-250 Z", -250, 120),
    "weizen": ("M-62,-270 C-95,-200 -95,-110 -60,-30 C-40,20 -40,80 -55,150 L-60,235 L60,235 L55,150 C40,80 40,20 60,-30 C95,-110 95,-200 62,-270 Z", -270, 235),
    "snifter": ("M-60,-150 C-170,-120 -170,90 -40,110 L-14,118 L-14,200 L-90,222 L90,222 L14,200 L14,118 L40,110 C170,90 170,-120 60,-150 Z", -150, 112),
    "mug": ("M-115,-215 L115,-215 L115,235 L-115,235 Z", -215, 235),
}


def illo(key, glass="pint", color="gold", accent="#c8961e", w=1200, h=675):
    rnd = random.Random(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
    path, top, bottom = GLASS.get(glass, GLASS["pint"])
    beer = BEER.get(color, BEER["gold"])
    foam_y = top + 38
    cx, cy = rnd.randint(int(w * .56), int(w * .70)), h // 2 + 20
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="">')
    s.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{accent}" stop-opacity=".95"/>'
             f'<stop offset="1" stop-color="#1d140e"/></linearGradient>'
             f'<linearGradient id="beer" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{beer}"/>'
             f'<stop offset="1" stop-color="{beer}" stop-opacity=".78"/></linearGradient>'
             f'<clipPath id="g"><path d="{path}"/></clipPath></defs>')
    s.append(f'<rect width="{w}" height="{h}" fill="url(#bg)"/>')
    for _ in range(7):
        r = rnd.randint(60, 260)
        s.append(f'<circle cx="{rnd.randint(0, w)}" cy="{rnd.randint(0, h)}" r="{r}" fill="#fff" opacity="{rnd.uniform(.03, .08):.3f}"/>')
    # колосья ячменя
    for _ in range(3):
        x0, y0 = rnd.randint(40, int(w * .4)), h + 10
        x1, y1 = x0 + rnd.randint(-60, 60), rnd.randint(int(h * .2), int(h * .5))
        s.append(f'<path d="M{x0},{y0} Q{(x0 + x1) // 2 + 30},{(y0 + y1) // 2} {x1},{y1}" stroke="#f3d38a" stroke-width="4" fill="none" opacity=".35"/>')
        for k in range(7):
            t = k / 7
            gx, gy = x1 + (x0 - x1) * t * .35, y1 + (y0 - y1) * t * .35
            s.append(f'<ellipse cx="{gx - 12:.0f}" cy="{gy:.0f}" rx="7" ry="15" transform="rotate(-30 {gx - 12:.0f} {gy:.0f})" fill="#f3d38a" opacity=".35"/>')
            s.append(f'<ellipse cx="{gx + 12:.0f}" cy="{gy:.0f}" rx="7" ry="15" transform="rotate(30 {gx + 12:.0f} {gy:.0f})" fill="#f3d38a" opacity=".35"/>')
    # шишки хмеля
    for _ in range(rnd.randint(2, 4)):
        hx, hy, sc = rnd.randint(int(w * .05), int(w * .45)), rnd.randint(int(h * .1), int(h * .8)), rnd.uniform(.7, 1.3)
        s.append(f'<g transform="translate({hx} {hy}) scale({sc:.2f}) rotate({rnd.randint(-30, 30)})" opacity=".9">')
        for row in range(5):
            n = 3 if row in (1, 2, 3) else 2
            for j in range(n):
                px, py = (j - (n - 1) / 2) * 22, row * 18 - 40
                s.append(f'<ellipse cx="{px:.0f}" cy="{py}" rx="16" ry="14" fill="#7fae4b" stroke="#4f7a2b" stroke-width="3"/>')
        s.append('<path d="M0,-58 q8,-18 22,-24" stroke="#4f7a2b" stroke-width="4" fill="none"/><path d="M8,-66 q26,-20 50,-6 q-26,14 -50,6z" fill="#5f8a3a"/></g>')
    # бокал
    s.append(f'<g transform="translate({cx} {cy})">')
    s.append(f'<ellipse cx="0" cy="{bottom + 30}" rx="150" ry="18" fill="#000" opacity=".25"/>')
    s.append(f'<g clip-path="url(#g)"><rect x="-200" y="{foam_y}" width="400" height="{bottom - foam_y + 40}" fill="url(#beer)"/>')
    for _ in range(26):
        s.append(f'<circle cx="{rnd.randint(-90, 90)}" cy="{rnd.randint(foam_y + 20, bottom)}" r="{rnd.uniform(2, 5):.1f}" fill="#fff" opacity="{rnd.uniform(.25, .6):.2f}"/>')
    s.append(f'<rect x="-200" y="{top - 30}" width="400" height="{foam_y - top + 34}" fill="#fff6e6"/>'
             f'<rect x="-60" y="{top}" width="22" height="{bottom - top}" fill="#fff" opacity=".18"/></g>')
    s.append(f'<path d="{path}" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="5"/>')
    fw = 120 if glass in ("pint", "mug") else 95
    for i in range(6):
        s.append(f'<circle cx="{-fw + i * fw * 2 / 5:.0f}" cy="{top - 6 + (i % 2) * 6}" r="{rnd.randint(26, 36)}" fill="#fff8ec"/>')
    if glass == "mug":
        s.append('<path d="M115,-130 C215,-130 215,120 115,120" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="22"/>')
    s.append('</g></svg>')
    return "".join(s)


def image_for(key, glass, color, accent):
    """Путь к картинке (растровой, если есть, иначе SVG)."""
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        p = os.path.join(IMGDIR, key + ext)
        if os.path.exists(p):
            dst = os.path.join(OUT, "img", key + ext)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(p, dst)
            return f"/img/{key}{ext}"
    write(f"img/{key}.svg", illo(key, glass, color, accent))
    return f"/img/{key}.svg"


LOGO = ('<svg viewBox="0 0 40 40" width="34" height="34" aria-hidden="true"><rect width="40" height="40" rx="10" fill="@ACCENT@"/>'
        '<path d="M11 13h15v19a2 2 0 0 1-2 2H13a2 2 0 0 1-2-2z" fill="#fff6e6"/><path d="M12 18h13v13a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 12 31z" fill="#f2b632"/>'
        '<path d="M26 17h3a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3h-3" fill="none" stroke="#fff6e6" stroke-width="2.4"/>'
        '<circle cx="14" cy="12" r="3.4" fill="#fff6e6"/><circle cx="19" cy="10.5" r="4" fill="#fff6e6"/><circle cx="24" cy="12" r="3.4" fill="#fff6e6"/></svg>')


# ------------------------------------------------------------------ разметка
def body_html(body):
    out, lst, toc = [], [], []

    def flush():
        if lst:
            out.append("<ul>" + "".join(f"<li>{E(x)}</li>" for x in lst) + "</ul>")
            lst.clear()
    for line in body.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            lst.append(line[2:]); continue
        flush()
        if line.startswith("## "):
            t = line[3:]; aid = "s" + str(len(toc) + 1); toc.append((aid, t))
            out.append(f'<h2 id="{aid}">{E(t)}</h2>')
        elif line.startswith("> "):
            out.append(f"<blockquote>{E(line[2:])}</blockquote>")
        else:
            out.append(f"<p>{E(line)}</p>")
    flush()
    return "\n".join(out), toc


NAV = [("/", "Главная"), ("/stati/", "Статьи"), ("/istoriya/", "История"), ("/obsuzhdeniya/", "Обсуждения"),
       ("/chat/", "Чат"), ("/biblioteka/", "Библиотека")]


def page(title, content, active="/", desc=None, extra_head=""):
    desc = desc or f"{SITE} — {TAG}"
    nav = "".join(f'<a href="{u}"{" class=on" if u == active else ""}>{n}</a>' for u, n in NAV)
    full_title = SITE if title == SITE else f"{title} — {SITE}"
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website">
<meta name="theme-color" content="#1d140e">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css?v={VER}">{extra_head}
</head><body>
<div class="age" id="age">18+ Материалы сайта предназначены для совершеннолетних. Чрезмерное употребление алкоголя вредит вашему здоровью. <button type="button" data-close-age>Понятно</button></div>
<header class="top"><div class="wrap top-in">
<a class="brand" href="/">{LOGO}<span><b>{SITE}</b><small>{SUB}</small></span></a>
<nav class="nav" id="nav">{nav}</nav>
<form class="search" action="/poisk/" role="search"><input name="q" type="search" placeholder="Поиск по журналу" aria-label="Поиск"></form>
<button class="icon theme" type="button" data-theme-toggle aria-label="Сменить тему">◐</button>
<button class="icon burger" type="button" data-burger aria-label="Меню">☰</button>
</div></header>
<main class="wrap">{content}</main>
<footer class="foot"><div class="wrap foot-in">
<div><div class="brand small">{LOGO}<b>{SITE}</b></div><p>Независимый журнал для любителей пива: история, стили, гастрономия и пивоварение. Пишем с {YEAR - 1} года.</p></div>
<div><b>Разделы</b>{"".join(f'<a href="/rubrika/{k}/">{v[0]}</a>' for k, v in RUBRICS.items())}</div>
<div><b>Журнал</b><a href="/o-proekte/">О проекте</a><a href="/biblioteka/">Скачать статьи</a><a href="/obsuzhdeniya/">Форум</a><a href="/chat/">Чат</a></div>
<div class="legal">© {YEAR - 1}–{YEAR} {SITE}. Использование материалов — со ссылкой на журнал.<br>18+ Чрезмерное употребление алкоголя вредит вашему здоровью.</div>
</div></footer>
<script src="/assets/app.js?v={VER}" defer></script>
</body></html>"""


def card(a, img, big=False):
    rn, rc = RUBRICS[a["rubric"]]
    return f"""<article class="card{' big' if big else ''}"><a href="/stati/{a['slug']}/" class="ph"><img src="{img}" alt="" loading="lazy"></a>
<div class="cb"><a class="rub" style="--c:{rc}" href="/rubrika/{a['rubric']}/">{rn}</a>
<h3><a href="/stati/{a['slug']}/">{E(a['title'])}</a></h3><p>{E(a['lead'])}</p>
<div class="meta">{rus_date(a['date'])} · {a['read']} мин чтения</div></div></article>"""


def avatar(uid):
    name = USERS[uid][0]
    hue = int(hashlib.md5(uid.encode()).hexdigest()[:2], 16) * 360 // 256
    return f'<span class="ava" style="--h:{hue}">{E(name[0])}</span>'


# ------------------------------------------------------------------ EPUB / FB2
def epub(path, title, chapters):
    """chapters: [(title, html_body)]"""
    uid = "urn:uuid:" + hashlib.md5(title.encode()).hexdigest()
    css = "body{font-family:serif;line-height:1.5}h1{font-size:1.5em}h2{font-size:1.2em;margin-top:1.4em}blockquote{font-style:italic;border-left:3px solid #c8961e;padding-left:.8em}"
    items, spine, navli, ncx = [], [], [], []
    files = {}
    for i, (t, b) in enumerate(chapters, 1):
        fn = f"c{i}.xhtml"
        files["OEBPS/" + fn] = (f'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ru"><head><title>{E(t)}</title>'
                                f'<link rel="stylesheet" href="s.css"/></head><body><h1>{E(t)}</h1>{b}<p><small>{SITE} — {TAG}</small></p></body></html>')
        items.append(f'<item id="c{i}" href="{fn}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="c{i}"/>')
        navli.append(f'<li><a href="{fn}">{E(t)}</a></li>')
        ncx.append(f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{E(t)}</text></navLabel><content src="{fn}"/></navPoint>')
    files["OEBPS/s.css"] = css
    files["OEBPS/nav.xhtml"] = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ru">'
                                f'<head><title>Оглавление</title></head><body><nav epub:type="toc"><h1>Оглавление</h1><ol>{"".join(navli)}</ol></nav></body></html>')
    files["OEBPS/toc.ncx"] = (f'<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{uid}"/></head>'
                              f'<docTitle><text>{E(title)}</text></docTitle><navMap>{"".join(ncx)}</navMap></ncx>')
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files["OEBPS/content.opf"] = (f'<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
                                  f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">{uid}</dc:identifier><dc:title>{E(title)}</dc:title>'
                                  f'<dc:language>ru</dc:language><dc:creator>Редакция «{SITE}»</dc:creator><meta property="dcterms:modified">{now}</meta></metadata>'
                                  f'<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
                                  f'<item id="css" href="s.css" media-type="text/css"/>{"".join(items)}</manifest><spine toc="ncx">{"".join(spine)}</spine></package>')
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with zipfile.ZipFile(full, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', compress_type=zipfile.ZIP_DEFLATED)
        for n, d in files.items():
            z.writestr(n, d, compress_type=zipfile.ZIP_DEFLATED)


def fb2(path, title, chapters_plain):
    secs = []
    for t, body in chapters_plain:
        ps = []
        for line in body.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("## "):
                ps.append(f"<subtitle>{E(line[3:])}</subtitle>")
            elif line.startswith("- "):
                ps.append(f"<p>• {E(line[2:])}</p>")
            elif line.startswith("> "):
                ps.append(f"<cite><p>{E(line[2:])}</p></cite>")
            else:
                ps.append(f"<p>{E(line)}</p>")
        secs.append(f"<section><title><p>{E(t)}</p></title>{''.join(ps)}</section>")
    doc = (f'<?xml version="1.0" encoding="utf-8"?>\n<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">'
           f'<description><title-info><genre>home_cooking</genre><author><first-name>Редакция</first-name><last-name>{SITE}</last-name></author>'
           f'<book-title>{E(title)}</book-title><lang>ru</lang></title-info><document-info><author><nickname>{SITE}</nickname></author>'
           f'<date>{YEAR}</date><id>{hashlib.md5(title.encode()).hexdigest()}</id><version>1.0</version></document-info></description>'
           f'<body><title><p>{E(title)}</p></title>{"".join(secs)}</body></FictionBook>')
    write(path, doc)


# ------------------------------------------------------------------ сборка
VER = ""


TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","h","ts","ch","sh","sch","","y","","e","yu","ya"]))


def translit(s):
    return re.sub(r"[^a-z0-9]+", "-", "".join(TRANSLIT.get(c, c) for c in s.lower())).strip("-")


def setup(seed, name=None, out=None):
    """Вариант сайта по seed: название, цвет, набор статей/тем, даты от сегодняшнего дня."""
    global SITE, SUB, ACCENT, SLUG, RND, OUT, LOGO, ARTICLES, THREADS
    RND = random.Random(seed)
    SITE, SUB, ACCENT = VARIANTS[RND.randrange(len(VARIANTS))] if seed else VARIANTS[0]
    if name:
        SITE = name
    SLUG = translit(SITE) or "zhurnal"
    if out:
        OUT = os.path.abspath(out)
    LOGO = LOGO.replace("@ACCENT@", ACCENT)
    arts = list(ARTICLES)
    if seed:
        keep_hist = [a for a in arts if a["rubric"] == "history"][:1]
        others = [a for a in arts if a not in keep_hist]
        RND.shuffle(others)
        arts = keep_hist + others[:len(others) - RND.randint(0, 3)]
    # даты: самая свежая — 1–4 дня назад, дальше шаг 2–4 дня
    order = arts[:] if not seed else RND.sample(arts, len(arts))
    d = TODAY - dt.timedelta(days=RND.randint(1, 4))
    for a in order:
        a["date"] = d.isoformat()
        d -= dt.timedelta(days=RND.randint(2, 4))
    ARTICLES = arts
    th = list(THREADS)
    if seed:
        RND.shuffle(th)
        th = th[:RND.randint(6, len(th))]
    THREADS = th


def build():
    global VER
    ARCH, PODS = f"{SLUG}-arhiv-{YEAR}.zip", f"{SLUG}-podshivka-{YEAR}"
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    VER = hashlib.md5((open(os.path.join(HERE, "static", "style.css"), encoding="utf-8").read()
                       + open(os.path.join(HERE, "static", "app.js"), encoding="utf-8").read()).encode()).hexdigest()[:8]
    shutil.copytree(os.path.join(HERE, "static"), os.path.join(OUT, "assets"))
    css = os.path.join(OUT, "assets", "style.css")
    open(css, "w", encoding="utf-8").write(open(css, encoding="utf-8").read().replace("--accent:#c8961e", "--accent:" + ACCENT))
    write("favicon.svg", LOGO.replace('width="34" height="34" ', ''))

    arts = sorted(ARTICLES, key=lambda a: a["date"], reverse=True)
    img = {a["slug"]: image_for(a["slug"], a["glass"], a["color"], RUBRICS[a["rubric"]][1]) for a in arts}
    for key, glass, color, acc in (("hero", "tulip", "gold", "#c8961e"), ("history", "mug", "amber", "#b5651d"),
                                   ("forum", "pint", "dark", "#3d6e8f"), ("chat", "weizen", "hazy", "#5f8a3a"),
                                   ("library", "snifter", "amber", "#6b5b95"), ("about", "pilsner", "gold", "#a8432e")):
        img[key] = image_for(key, glass, color, acc)

    # --- статьи
    for a in arts:
        rn, rc = RUBRICS[a["rubric"]]
        bh, toc = body_html(a["body"])
        same = [x for x in arts if x["rubric"] == a["rubric"] and x is not a][:2]
        other = [x for x in arts if x is not a and x not in same][:4 - len(same)]
        rel = "".join(card(x, img[x["slug"]]) for x in same + other)
        toc_html = "".join(f'<a href="#{i}">{E(t)}</a>' for i, t in toc)
        c = f"""<div class="crumbs"><a href="/">Главная</a> › <a href="/rubrika/{a['rubric']}/">{rn}</a></div>
<article class="post"><header class="post-h"><a class="rub" style="--c:{rc}" href="/rubrika/{a['rubric']}/">{rn}</a>
<h1>{E(a['title'])}</h1><p class="lead">{E(a['lead'])}</p>
<div class="meta">Редакция «{SITE}» · {rus_date(a['date'])} · {a['read']} мин чтения · <span data-views="{a['slug']}"></span></div></header>
<figure class="hero-img"><img src="{img[a['slug']]}" alt=""></figure>
<div class="post-grid"><aside class="toc"><b>Содержание</b>{toc_html}
<div class="dl"><b>Скачать статью</b><a href="/files/{a['slug']}.epub" download>EPUB</a><a href="/files/{a['slug']}.fb2" download>FB2</a></div></aside>
<div class="prose">{bh}
<div class="share"><span>Понравилось?</span><button type="button" data-like="{a['slug']}">♥ <i>Нравится</i></button><a href="/obsuzhdeniya/">Обсудить на форуме</a></div></div></div>
</article><section class="rel"><h2>Читайте также</h2><div class="grid">{rel}</div></section>"""
        write(f"stati/{a['slug']}/index.html", page(a["title"], c, "/stati/", a["lead"]))
        epub(f"files/{a['slug']}.epub", a["title"], [(a["title"], f'<p><i>{E(a["lead"])}</i></p>' + bh)])
        fb2(f"files/{a['slug']}.fb2", a["title"], [(a["title"], a["lead"] + "\n" + a["body"])])

    # --- главная
    top, rest = arts[0], arts[1:]
    rubs = "".join(f'<a class="chip" style="--c:{c}" href="/rubrika/{k}/">{n}</a>' for k, (n, c) in RUBRICS.items())
    popular = "".join(f'<li><a href="/stati/{a["slug"]}/">{E(a["title"])}</a><span>{a["read"]} мин</span></li>'
                      for a in sorted(arts, key=lambda a: hashlib.md5(a["slug"].encode()).hexdigest())[:5])
    forum = "".join(f'<li><a href="/obsuzhdeniya/{t["slug"]}/">{E(t["title"])}</a><span>{len(t["posts"])} ответов</span></li>' for t in THREADS[:5])
    c = f"""<section class="hero"><div class="hero-txt"><span class="kicker">Свежий номер</span>
<h1><a href="/stati/{top['slug']}/">{E(top['title'])}</a></h1><p>{E(top['lead'])}</p>
<div class="hero-cta"><a class="btn" href="/stati/{top['slug']}/">Читать</a><a class="btn ghost" href="/biblioteka/">Скачать подшивку</a></div></div>
<a class="hero-pic" href="/stati/{top['slug']}/"><img src="{img[top['slug']]}" alt=""></a></section>
<div class="chips">{rubs}</div>
<div class="layout"><section><h2 class="sec">Новое в журнале</h2><div class="grid">{''.join(card(a, img[a['slug']]) for a in rest[:8])}</div>
<p class="more"><a class="btn ghost" href="/stati/">Все статьи</a></p></section>
<aside class="side"><div class="box"><h3>Популярное</h3><ol class="list">{popular}</ol></div>
<div class="box"><h3>Сейчас в чате <span class="dot"></span> <small data-online></small></h3><div class="mini-chat" data-chat="mini"></div><a class="btn small" href="/chat/">Открыть чат</a></div>
<div class="box"><h3>Обсуждают</h3><ul class="list">{forum}</ul></div>
<div class="box lib"><h3>Библиотека</h3><p>Все материалы журнала в EPUB и FB2 — читайте в дороге без интернета.</p><a class="btn small" href="/biblioteka/">Скачать</a></div></aside></div>"""
    write("index.html", page(SITE, c, "/", f"{SITE} — {TAG}"))

    # --- все статьи и рубрики
    allcards = "".join(f'<div data-rub="{a["rubric"]}">{card(a, img[a["slug"]])}</div>' for a in arts)
    c = f'<h1 class="pt">Все статьи</h1><div class="chips filter"><button class="chip on" data-filter="*">Все</button>' + \
        "".join(f'<button class="chip" style="--c:{c}" data-filter="{k}">{n}</button>' for k, (n, c) in RUBRICS.items()) + \
        f'</div><div class="grid" data-filter-grid>{allcards}</div>'
    write("stati/index.html", page("Все статьи", c, "/stati/"))
    for k, (n, col) in RUBRICS.items():
        lst = [a for a in arts if a["rubric"] == k]
        c = f'<div class="crumbs"><a href="/">Главная</a> › Рубрика</div><h1 class="pt" style="--c:{col}">{n}</h1><div class="grid">{"".join(card(a, img[a["slug"]]) for a in lst)}</div>'
        write(f"rubrika/{k}/index.html", page(n, c, "/stati/"))

    # --- хронология
    tl = "".join(f'<li><span class="yr">{E(y)}</span><div><h3>{E(t)}</h3><p>{E(d)}</p></div></li>' for y, t, d in TIMELINE)
    hist = [a for a in arts if a["rubric"] == "history"]
    c = f"""<section class="banner"><img src="{img['history']}" alt=""><div><h1>История пива</h1><p>Десять тысяч лет за десять минут: ключевые события, которые сделали пиво таким, каким мы его знаем.</p></div></section>
<ol class="timeline">{tl}</ol><section class="rel"><h2>Подробнее об истории</h2><div class="grid">{''.join(card(a, img[a['slug']]) for a in hist)}</div></section>"""
    write("istoriya/index.html", page("История пива", c, "/istoriya/", "Хронология истории пива от Шумера до крафтовой революции"))

    # --- форум
    base = dt.datetime.combine(TODAY - dt.timedelta(days=3 * len(THREADS) + 6), dt.time(18, 0))
    rows = []
    for i, t in enumerate(THREADS):
        t0 = base + dt.timedelta(days=i * 3, hours=i * 2)
        posts = []
        for j, (uid, text) in enumerate(t["posts"]):
            ts = t0 + dt.timedelta(minutes=37 * j + j * j * 11)
            name, city = USERS[uid]
            mod = " mod" if uid == "brewbot" else ""
            posts.append(f'<div class="fpost{mod}">{avatar(uid)}<div><div class="fhead"><b>{E(name)}</b><span>{E(city)}</span>'
                         f'<time>{ts.day} {MONTHS[ts.month - 1]}, {ts:%H:%M}</time></div><p>{E(text)}</p>'
                         f'<div class="factions"><button type="button" data-like="f-{t["slug"]}-{j}">♥ <i></i></button><span>#{j + 1}</span></div></div></div>')
        last = t0 + dt.timedelta(minutes=37 * (len(t["posts"]) - 1))
        c = (f'<div class="crumbs"><a href="/">Главная</a> › <a href="/obsuzhdeniya/">Обсуждения</a> › {E(t["cat"])}</div>'
             f'<h1 class="pt">{E(t["title"])}</h1><div class="thread">{"".join(posts)}</div>'
             f'<div class="reply"><textarea placeholder="Чтобы ответить, войдите на форум" disabled></textarea>'
             f'<button class="btn" type="button" data-login>Войти и ответить</button></div>')
        write(f"obsuzhdeniya/{t['slug']}/index.html", page(t["title"], c, "/obsuzhdeniya/"))
        rows.append(f'<a class="trow" href="/obsuzhdeniya/{t["slug"]}/">{avatar(t["posts"][0][0])}<div><b>{E(t["title"])}</b>'
                    f'<span>{E(t["cat"])} · начал {E(USERS[t["posts"][0][0]][0])}</span></div><em>{len(t["posts"])}<small>ответов</small></em>'
                    f'<time>{last.day} {MONTHS[last.month - 1]}</time></a>')
    c = f"""<section class="banner"><img src="{img['forum']}" alt=""><div><h1>Обсуждения</h1><p>Форум читателей: советы новичкам, споры о стилях, отчёты с фестивалей и домашние рецепты.</p></div></section>
<div class="forum-stats"><div><b>{len(THREADS)}</b><span>тем</span></div><div><b>{sum(len(t['posts']) for t in THREADS)}</b><span>сообщений</span></div><div><b>{len(USERS) - 1}</b><span>активных участников</span></div><div><b data-online></b><span>сейчас онлайн</span></div></div>
<div class="tlist">{''.join(rows)}</div>"""
    write("obsuzhdeniya/index.html", page("Обсуждения", c, "/obsuzhdeniya/"))

    # --- чат
    c = f"""<section class="chat-page"><div class="chat-head"><div><h1>Пивной чат</h1><p>Общаемся о пиве в реальном времени. Будьте вежливы — модератор не спит.</p></div><div class="online"><span class="dot"></span> онлайн: <b data-online></b></div></div>
<div class="chat" data-chat="full"></div><form class="chat-form" data-chat-form><input name="m" maxlength="300" autocomplete="off" placeholder="Напишите сообщение…"><button class="btn">Отправить</button></form>
<p class="hint">Вы пишете как гость. Сообщения гостей видны в течение текущей сессии.</p></section>"""
    write("chat/index.html", page("Чат", c, "/chat/"))

    # --- библиотека + подшивка
    combo_html = []
    for a in sorted(ARTICLES, key=lambda a: a["date"]):
        bh, _ = body_html(a["body"])
        combo_html.append((a["title"], f'<p><i>{E(a["lead"])}</i></p>' + bh))
    epub(f"files/{PODS}.epub", f"{SITE}. Подшивка {YEAR}", combo_html)
    fb2(f"files/{PODS}.fb2", f"{SITE}. Подшивка {YEAR}", [(a["title"], a["lead"] + "\n" + a["body"]) for a in sorted(ARTICLES, key=lambda a: a["date"])])
    zpath = os.path.join(OUT, "files", ARCH)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(os.path.join(OUT, "files"))):
            if fn.endswith((".epub", ".fb2")):
                z.write(os.path.join(OUT, "files", fn), fn)
        for fn in sorted(os.listdir(os.path.join(OUT, "img"))):
            z.write(os.path.join(OUT, "img", fn), "illustracii/" + fn)
        z.writestr("ПРОЧТИ.txt", f"{SITE} — {TAG}\nАрхив статей журнала в форматах EPUB и FB2, иллюстрации.\n18+ Чрезмерное употребление алкоголя вредит вашему здоровью.\n")

    def size(fn):
        b = os.path.getsize(os.path.join(OUT, "files", fn))
        return f"{b / 1048576:.1f} МБ" if b > 1048576 else f"{max(1, b // 1024)} КБ"
    rows = "".join(f'<tr><td><a href="/stati/{a["slug"]}/">{E(a["title"])}</a><small>{RUBRICS[a["rubric"]][0]}</small></td>'
                   f'<td><a class="fbtn" href="/files/{a["slug"]}.epub" download>EPUB <i>{size(a["slug"] + ".epub")}</i></a></td>'
                   f'<td><a class="fbtn" href="/files/{a["slug"]}.fb2" download>FB2 <i>{size(a["slug"] + ".fb2")}</i></a></td></tr>' for a in arts)
    c = f"""<section class="banner"><img src="{img['library']}" alt=""><div><h1>Библиотека</h1><p>Все статьи журнала для чтения офлайн: в электронной книге, на телефоне или планшете.</p></div></section>
<div class="packs"><a class="pack" href="/files/{ARCH}" download><b>Полный архив {YEAR}</b><span>ZIP · все статьи в EPUB и FB2 + иллюстрации · {size(ARCH)}</span></a>
<a class="pack" href="/files/{PODS}.epub" download><b>Подшивка одной книгой</b><span>EPUB · {size(PODS + '.epub')}</span></a>
<a class="pack" href="/files/{PODS}.fb2" download><b>Подшивка для читалок</b><span>FB2 · {size(PODS + '.fb2')}</span></a></div>
<table class="files"><thead><tr><th>Статья</th><th colspan="2">Скачать</th></tr></thead><tbody>{rows}</tbody></table>
<p class="hint">EPUB открывается в Apple Books, Google Play Книгах и большинстве читалок; FB2 — в ReadEra, FBReader, «Литрес: Читай».</p>"""
    write("biblioteka/index.html", page("Библиотека", c, "/biblioteka/", "Скачать статьи журнала о пиве в EPUB и FB2"))

    # --- о проекте, поиск, 404
    c = f"""<section class="banner"><img src="{img['about']}" alt=""><div><h1>О проекте</h1><p>«{SITE}» — независимый журнал о пиве, который делают любители для любителей.</p></div></section>
<div class="prose narrow"><p>Мы пишем об истории пива, разбираем стили, рассказываем о пивоварении и гастрономических сочетаниях. Наша цель — культура вкуса, а не количество выпитого.</p>
<h2>Редакционные принципы</h2><ul><li>Проверяем исторические факты и указываем, где кончается история и начинается легенда.</li><li>Не публикуем рекламу под видом статей.</li><li>Пишем для взрослых и призываем к умеренности.</li></ul>
<h2>Сообщество</h2><p>У журнала есть <a href="/obsuzhdeniya/">форум</a> и <a href="/chat/">чат</a>, где читатели делятся опытом домашнего пивоварения и впечатлениями.</p>
<h2>Связаться с редакцией</h2><p>Предложения тем и исправления присылайте через форум в разделе «Отзывы о журнале».</p></div>"""
    write("o-proekte/index.html", page("О проекте", c))
    write("poisk/index.html", page("Поиск", '<h1 class="pt">Поиск</h1><form class="search big" action="/poisk/"><input name="q" type="search" placeholder="Например: стаут, хмель, история" autofocus></form><div class="results" data-results></div>'))
    write("404.html", page("Страница не найдена", '<div class="e404"><h1>404</h1><p>Кажется, эту кружку уже допили. Страница не найдена.</p><a class="btn" href="/">На главную</a></div>'))

    # --- данные для JS
    idx = [{"t": a["title"], "u": f"/stati/{a['slug']}/", "r": RUBRICS[a["rubric"]][0], "e": a["lead"], "i": img[a["slug"]],
            "x": (a["title"] + " " + a["lead"] + " " + plain(a["body"])).lower()} for a in arts]
    idx += [{"t": t["title"], "u": f"/obsuzhdeniya/{t['slug']}/", "r": "Форум", "e": t["posts"][0][1], "i": "",
             "x": (t["title"] + " " + " ".join(p[1] for p in t["posts"])).lower()} for t in THREADS]
    write("assets/search.json", json.dumps(idx, ensure_ascii=False))
    users = {k: [v[0], v[1], int(hashlib.md5(k.encode()).hexdigest()[:2], 16) * 360 // 256] for k, v in USERS.items()}
    write("assets/chat.json", json.dumps({"users": users, "script": CHAT_SCRIPT, "replies": CHAT_REPLIES[0], "fallback": CHAT_REPLIES[1]}, ensure_ascii=False))
    write("robots.txt", "User-agent: *\nAllow: /\n")
    total = sum(len(fs) for _, _, fs in os.walk(OUT))
    size_mb = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs) / 1048576
    print(f"OK: {OUT} — файлов {total}, {size_mb:.1f} МБ, статей {len(arts)}, тем {len(THREADS)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Сборка сайта-журнала")
    ap.add_argument("--out", help="куда собрать (по умолчанию ./out)")
    ap.add_argument("--seed", default="", help="вариант сайта (например, домен); пусто — базовый вариант")
    ap.add_argument("--name", help="своё название журнала")
    a = ap.parse_args()
    setup(a.seed, a.name, a.out)
    build()
