# Sharar project page

One self-contained page. `src/index.html` is the source; `tools/build.py` inlines `data/*.json` into `dist/index.html`.

```bash
uv run --no-project --with matplotlib --with numpy python -I tools/export_data.py   # main results (warm decode, agents)
uv run --no-project --with matplotlib --with numpy python -I tools/export_burst.py  # SSD-tier burst run
python3 tools/build.py
```

Data comes from the paper figure builders in `~/.local/share/sharar` (bench-figures-rerun-1027, bench-figures-flare-1102,
ttft-time). The hill-climb steps, draft-head bins and expert-sharing example are copied from the paper figure scripts
(paper-figs/han-style/src). For GitHub Pages, publish `dist/index.html`.
