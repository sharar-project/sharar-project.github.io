"""Build the site from src/ into two outputs:

  dist/  for the claude.ai artifact: dist/index.html has no <!doctype> (the artifact host wraps the main page),
         the other pages carry their own.
  site/  for GitHub Pages: every page is a complete HTML document.

Pages: the umbrella home, the Sharar project (overview and models), the blog index, and posts. The paper post reads
data/results.json (the paper's main results); the quantized-LLM repair post reads data/wsp-repair.json.

    python3 tools/build.py
"""
import base64
import json
import re
from pathlib import Path

SITE = "Sharar"  # the umbrella site's name; one place to change it
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PARTS = {p.name: p.read_text() for p in (SRC / "partials").iterdir()}
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
PAGES = [  # (source, output, path back to the site root, current nav item, unused)
    ("index.html", "index.html", "", "", ""),
    ("sharar.html", "projects/sharar/index.html", "../../", "overview", ""),
    ("blog.html", "blog/index.html", "../", "blog", ""),
    ("posts/sharar-paper.html", "blog/sharar-paper/index.html", "../../", "blog", ""),
    ("posts/repairing-quantized-llm.html", "blog/repairing-quantized-llm/index.html", "../../", "blog", ""),
]
LOGO = ('<svg class="logo" width="24" height="24" viewBox="0 0 100 100" aria-hidden="true"><defs>'
        '<linearGradient id="{id}" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#a31f34" stop-opacity="0.1"/>'
        '<stop offset="0.7" stop-color="#a31f34" stop-opacity="0.9"/></linearGradient></defs>'
        '<path d="M56 24 L6 94 L78 46 Z" fill="url(#{id})"/>'
        '<path d="M70.5 10.4 L73.9 28.4 L91.7 32.4 L75.7 41.2 L77.4 59.4 L64.1 46.8 L47.3 54.1 L55.1 37.5 L43.0 23.8 '
        'L61.2 26.1 Z" fill="#a31f34" stroke="#a31f34" stroke-width="7" stroke-linejoin="round"/></svg>')
# favicon: the board's 16 px form, a plain star (the trail does not survive at that size)
FAVICON = ('<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 10 L60 36.2 L88 37.6 L66.2 55.3 "
           "L73.5 82.4 L50 67 L26.5 82.4 L33.8 55.3 L12 37.6 L40 36.2 Z' fill='%23a31f34' stroke='%23a31f34' "
           "stroke-width='10' stroke-linejoin='round'/%3E%3C/svg%3E\">")
SIDE_CUR = {"index.html": "home", "sharar.html": "overview", "blog.html": "blog",
            "posts/sharar-paper.html": "paper", "posts/repairing-quantized-llm.html": "repair"}
FAVICON_FILES = ('<link rel="icon" type="image/png" sizes="32x32" href="{root}favicon-32.png?v=2">\n'
                 '<link rel="icon" href="{root}favicon.ico?v=2" sizes="any">\n'
                 '<link rel="icon" type="image/svg+xml" href="{root}favicon.svg?v=2">\n'
                 '<link rel="apple-touch-icon" sizes="180x180" href="{root}apple-touch-icon.png?v=2">')  # bump v to refresh caches
MIME = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}  # {{IMG:...}} data URIs
RESULTS = json.loads((ROOT / "data/results.json").read_text())


def slug(t):
    t = re.sub(r"<[^>]+>|\\\(|\\\)|\\[a-zA-Z]+", "", t)
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def post_toc(page):
    """A post's "On this page" list: each <section id> with its <h2>, and the <h3>s inside it, which get ids here."""
    items, out, last = [], [], 0
    for m in re.finditer(r'<section id="([\w-]+)">', page):
        sid, end = m.group(1), page.find("</section>", m.end())
        body = page[m.end():end]
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
        if not h2:
            continue
        items.append(f'    <a class="toc-link" href="#{sid}">{h2.group(1).strip()}</a>')
        def add_id(h):
            t = h.group(2).strip()
            hid = f"{sid}-{slug(t)}"
            items.append(f'    <a class="toc-link toc-sub" href="#{hid}">{t}</a>')
            return f'<h3{h.group(1)} id="{hid}">{h.group(2)}</h3>'
        body = re.sub(r"<h3((?:(?! id=)[^>])*)>(.*?)</h3>", add_id, body, flags=re.S)
        out.append(page[last:m.end()] + body); last = end
    out.append(page[last:])
    return "".join(out), "\n".join(items)


def render(src, root, current, sub):
    page = (SRC / src).read_text()
    nav = PARTS["nav.html"]
    side = PARTS["sidebar.html"]
    if src.startswith("posts/"):  # a post's side menu lists its own chapters; the site menu's drawer script is reused
        page, toc = post_toc(page)
        side = PARTS["post-toc.html"].replace("<!--__TOC__-->", toc) + side[side.index("</aside>") + len("</aside>"):]
    for item in ("home", "overview", "paper", "blog", "repair"):
        side = side.replace(f" {{{{SIDE_{item}}}}}", ' aria-current="page"' if item == SIDE_CUR.get(src) else "")
    page = (page.replace("/*__SITE_CSS__*/", PARTS["site.css"])
                .replace("/*__SIDE_CSS__*/", PARTS["side.css"])
                .replace("<!--__NAV__-->", nav)
                .replace("<!--__SIDEBAR__-->", side)
                .replace("<!--__FOOTER__-->", PARTS["footer.html"])
                .replace("<!--__POST_CARD__-->", PARTS["post-card.html"])
                .replace("/*__RESULTS__*/", (ROOT / "data/results.json").read_text().replace("</", "<\\/")))
    # any other data file: /*__DATA:name.json__*/ inlines data/name.json
    page = re.sub(r"/\*__DATA:([\w.-]+)__\*/", lambda m: (ROOT / "data" / m.group(1)).read_text().strip().replace("</", "<\\/"), page)
    # the logo (canvas board "14 · Shooting star"); each use gets its own gradient id
    page = re.sub(r"\{\{LOGO:(\w+)\}\}", lambda m: LOGO.format(id="lg-" + m.group(1)), page)
    page = page.replace("<title>", "<!--FAVICON-->\n<title>", 1)
    # images are inlined as data URIs: the artifact viewer loads nothing from other hosts
    page = re.sub(r"\{\{IMG:([\w.-]+)\}\}", lambda m: f"data:image/{MIME[Path(m.group(1)).suffix]};base64,"
                  + base64.b64encode((SRC / "assets" / m.group(1)).read_bytes()).decode(), page)
    return page.replace("{{ROOT}}", root).replace("{{SITE}}", SITE)


for src, out, root, current, sub in PAGES:
    page = render(src, root, current, sub)
    assert "{{" not in page and "<!--__" not in page, f"unfilled placeholder in {src}"
    # the page's own head part (icons, <title>, meta, fonts, its first <style>) goes in <head>: Safari only finds the
    # tab icon there
    cut = page.index("</style>") + len("</style>")
    full = HEAD + page[:cut] + "\n</head>\n<body>\n" + page[cut:] + "\n</body>\n</html>\n"
    files = full.replace("<!--FAVICON-->", FAVICON_FILES.format(root=root))  # GitHub Pages serves the icon files
    inline = lambda t: t.replace("<!--FAVICON-->", FAVICON)  # the artifact preview cannot, so it inlines one
    for base, text in (("dist", inline(page if out == "index.html" else full)), ("site", files)):
        p = ROOT / base / out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print(p.relative_to(ROOT), len(text))

# site-wide files served from the root (favicons; tools/make_favicons.py renders them from favicon.svg)
for f in (SRC / "static").iterdir():
    (ROOT / "site" / f.name).write_bytes(f.read_bytes())
