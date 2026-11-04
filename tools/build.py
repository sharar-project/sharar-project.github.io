"""Inline data/*.json into src/index.html and write dist/index.html (one self-contained page).

    python3 tools/build.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
page = (ROOT / "src/index.html").read_text()
for key, name in (("RESULTS", "results.json"),):
    page = page.replace(f"/*__{key}__*/", (ROOT / "data" / name).read_text().replace("</", "<\\/"))
(ROOT / "dist").mkdir(exist_ok=True)
(ROOT / "dist/index.html").write_text(page)
print(ROOT / "dist/index.html", len(page))
