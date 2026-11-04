"""Build the Sharar site from src/ into two outputs:

  dist/  for the claude.ai artifact: dist/index.html has no <!doctype> (the artifact host wraps the main page),
         the other pages carry their own.
  site/  for GitHub Pages: every page is a complete HTML document.

Pages: index.html (project home), blog/index.html (post list), blog/sharar-paper/index.html (the paper post, with
data/results.json inlined).

    python3 tools/build.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PARTS = {name: (SRC / "partials" / name).read_text() for name in ("site.css", "nav.html", "footer.html", "post-card.html")}
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
PAGES = [  # (source, output path, path back to the site root, current nav item)
    ("home.html", "index.html", "", "home"),
    ("blog.html", "blog/index.html", "../", "blog"),
    ("posts/sharar-paper.html", "blog/sharar-paper/index.html", "../../", "blog"),
]


def render(src, root, current):
    page = (SRC / src).read_text()
    nav = PARTS["nav.html"]
    for item in ("models", "start", "blog"):
        nav = nav.replace(f" {{{{CUR_{item}}}}}", ' aria-current="page"' if item == current else "")
    page = (page.replace("/*__SITE_CSS__*/", PARTS["site.css"])
                .replace("<!--__NAV__-->", nav)
                .replace("<!--__FOOTER__-->", PARTS["footer.html"])
                .replace("<!--__POST_CARD__-->", PARTS["post-card.html"])
                .replace("/*__RESULTS__*/", (ROOT / "data/results.json").read_text().replace("</", "<\\/")))
    return page.replace("{{ROOT}}", root)


for src, out, root, current in PAGES:
    page = render(src, root, current)
    assert "{{" not in page and "__NAV__" not in page, f"unfilled placeholder in {src}"
    full = HEAD + page + "\n</body>\n</html>\n"
    for base, text in (("dist", page if out == "index.html" else full), ("site", full)):
        p = ROOT / base / out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print(p.relative_to(ROOT), len(text))
