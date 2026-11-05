# sharar-project.github.io

The Sharar website, served at https://sharar-project.github.io. Every push to `main` builds the pages with
`tools/build.py` and deploys them through GitHub Actions (`.github/workflows/pages.yml`).

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

- `site/` is the GitHub Pages output (the table above); CI builds it, so it is not committed.
- `dist/` is the same for a claude.ai artifact preview (its main page has no doctype; the host adds one).
- Preview locally: `python3 tools/build.py && python3 -m http.server -d site 8000`.

To add a post: write `src/posts/<slug>.html`, add it to `PAGES` in `tools/build.py`, and add a card to
`src/blog.html` (and to the home page's "Latest posts"). A new project gets `src/<name>.html`, a card on the home page, and its own sub-nav partial.

Data for the paper post comes from the paper figure builders in `~/.local/share/sharar` (bench-figures-rerun-1027,
bench-figures-flare-1102); the hill-climb steps and accuracy table follow the paper on `main`.

## Photo credits

`src/assets/` holds cropped photos from Wikimedia Commons, inlined into the home page at build time:

| File | Source | Author | License |
|---|---|---|---|
| `dgx-spark.jpg` | [Nvidia DGX Spark oblique view dllu.jpg](https://commons.wikimedia.org/wiki/File:Nvidia_DGX_Spark_oblique_view_dllu.jpg) | Daniel Lu | CC BY-SA 4.0 |
| `mac-studio.jpg` | [Mac Studio (2022) front.jpg](https://commons.wikimedia.org/wiki/File:Mac_Studio_(2022)_front.jpg) | Yasu | CC BY-SA 3.0 |
| `strix-halo-hp-z2-mini.jpg` | frame 00:03:56 of 超级核显来袭！AMD新品现场体验 on Commons | 极客湾 Geekerwan | CC BY 3.0 |

The crops of the CC BY-SA photos are shared under the same licenses.
