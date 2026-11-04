# Model- and hardware-specific inference site

An umbrella site for model- and hardware-specific inference projects, with Sharar as the first project. `src/` holds
the pages, `src/partials/` the shared CSS, navs, footer and post card; `tools/build.py` assembles them. The umbrella's
working name is the `SITE` constant in `tools/build.py`.

| Page | Source | Output |
|---|---|---|
| Umbrella home | `src/index.html` | `index.html` |
| Sharar overview | `src/sharar.html` | `projects/sharar/index.html` |
| Sharar models | `src/models.html` | `projects/sharar/models/index.html` |
| Blog index | `src/blog.html` | `blog/index.html` |
| Sharar paper post | `src/posts/sharar-paper.html` | `blog/sharar-paper/index.html` |

```bash
uv run --no-project --with matplotlib --with numpy python -I tools/export_data.py   # paper post: main results
python3 tools/build.py                                                             # writes dist/ and site/
```

- `site/` is the GitHub Pages output (the table above).
- `dist/` is the same for the claude.ai artifact preview (its main page has no doctype; the host adds one).

To add a post: write `src/posts/<slug>.html`, add it to `PAGES` in `tools/build.py`, and add a card to
`src/blog.html` (and to the home page's "Latest posts"). A new project gets `src/<name>.html`, a card on the home page, and its own sub-nav partial.

Data for the paper post comes from the paper figure builders in `~/.local/share/sharar` (bench-figures-rerun-1027,
bench-figures-flare-1102); the hill-climb steps and accuracy table follow the paper on `main`.
