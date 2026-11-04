# Sharar site

The Sharar project site: a home page, a blog index, and posts. `src/` holds the pages, `src/partials/` the shared CSS,
nav, footer and post card; `tools/build.py` assembles them.

```bash
uv run --no-project --with matplotlib --with numpy python -I tools/export_data.py   # paper post: main results
python3 tools/build.py                                                             # writes dist/ and site/
```

- `site/` is the GitHub Pages output: `index.html`, `blog/index.html`, `blog/sharar-paper/index.html`.
- `dist/` is the same for the claude.ai artifact preview (its main page has no doctype; the host adds one).

To add a post: write `src/posts/<slug>.html`, add it to `PAGES` in `tools/build.py`, and add a card to
`src/blog.html` (and to the home page's "From the blog").

Data for the paper post comes from the paper figure builders in `~/.local/share/sharar` (bench-figures-rerun-1027,
bench-figures-flare-1102); the hill-climb steps and accuracy table follow the paper on `main`.
