"""Build the site from src/ into two outputs:

  dist/  for the claude.ai artifact: dist/index.html has no <!doctype> (the artifact host wraps the main page),
         the other pages carry their own.
  site/  for GitHub Pages: every page is a complete HTML document.

Pages: the umbrella home, the Sharar project (overview and models), the blog index, and posts. The paper post and the
models page read data/results.json (the paper's main results).

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
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
PAGES = [  # (source, output, path back to the site root, current site-nav item, current Sharar sub-nav item)
    ("index.html", "index.html", "", "", ""),
    ("sharar.html", "projects/sharar/index.html", "../../", "projects", "overview"),
    ("models.html", "projects/sharar/models/index.html", "../../../", "projects", "models"),
    ("blog.html", "blog/index.html", "../", "blog", ""),
    ("posts/sharar-paper.html", "blog/sharar-paper/index.html", "../../", "blog", ""),
]
RESULTS = json.loads((ROOT / "data/results.json").read_text())


def model_numbers():
    """Placeholders for the models page: Sharar's one-user and peak speed, tasks/h at 16 agents, and comparison rows."""
    fill, rows = {}, []
    for m in RESULTS["models"]:
        warm = RESULTS["warm"][m]
        one = {e: next((p["user"] for p in pts if p["n"] == 1), None) for e, pts in warm.items()}
        peak = {e: max(pts, key=lambda p: p["agg"]) for e, pts in warm.items()}
        fill[f"ONE_{m}"] = f"{one['Sharar']:.0f}"
        fill[f"PEAK_{m}"] = f"{peak['Sharar']['agg']:.0f}"
        fill[f"PEAKN_{m}"] = str(peak["Sharar"]["n"])
        fill[f"AG_{m}"] = f"{dict(RESULTS['agents'][m.lower()]['sharar'])[16]:.0f}"
        base = [e for e in ("vLLM", "TensorFold", "llama.cpp") if e in warm]  # the paper's headline baselines
        b1 = max((e for e in base if one[e]), key=lambda e: one[e])
        bp = max(base, key=lambda e: peak[e]["agg"])
        flare = f'{peak["Flare"]["agg"]:.0f}' if "Flare" in peak else "–"
        rows.append(f'<tr><td>{m.replace("Nemotron-3.5-", "Nemotron 3.5 ")}</td>'
                    f'<td class="num">{one["Sharar"]:.0f}</td><td class="num">{one[b1]:.0f} <span class="muted">{b1}</span></td>'
                    f'<td class="num">{peak["Sharar"]["agg"]:.0f}</td><td class="num">{peak[bp]["agg"]:.0f} <span class="muted">{bp}</span></td>'
                    f'<td class="num"><b>{peak["Sharar"]["agg"] / peak[bp]["agg"]:.1f}×</b></td><td class="num">{flare}</td></tr>')
    return fill, "\n          ".join(rows)


FILL, CMP_ROWS = model_numbers()


def render(src, root, current, sub):
    page = (SRC / src).read_text()
    nav, subnav = PARTS["nav.html"], PARTS["sharar-nav.html"]
    for item in ("projects", "blog"):
        nav = nav.replace(f" {{{{CUR_{item}}}}}", ' aria-current="page"' if item == current else "")
    for item in ("overview", "models"):
        subnav = subnav.replace(f" {{{{SUB_{item}}}}}", ' aria-current="page"' if item == sub else "")
    page = (page.replace("/*__SITE_CSS__*/", PARTS["site.css"])
                .replace("<!--__NAV__-->", nav)
                .replace("<!--__SHARAR_NAV__-->", subnav)
                .replace("<!--__FOOTER__-->", PARTS["footer.html"])
                .replace("<!--__POST_CARD__-->", PARTS["post-card.html"])
                .replace("<!--__CMP_ROWS__-->", CMP_ROWS)
                .replace("/*__RESULTS__*/", (ROOT / "data/results.json").read_text().replace("</", "<\\/")))
    for k, v in FILL.items():
        page = page.replace("{{" + k + "}}", v)
    # images are inlined as data URIs: the artifact viewer loads nothing from other hosts
    page = re.sub(r"\{\{IMG:([\w.-]+)\}\}", lambda m: "data:image/jpeg;base64,"
                  + base64.b64encode((SRC / "assets" / m.group(1)).read_bytes()).decode(), page)
    return page.replace("{{ROOT}}", root).replace("{{SITE}}", SITE)


for src, out, root, current, sub in PAGES:
    page = render(src, root, current, sub)
    assert "{{" not in page and "<!--__" not in page, f"unfilled placeholder in {src}"
    full = HEAD + page + "\n</body>\n</html>\n"
    for base, text in (("dist", page if out == "index.html" else full), ("site", full)):
        p = ROOT / base / out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print(p.relative_to(ROOT), len(text))
