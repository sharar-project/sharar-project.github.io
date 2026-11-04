"""Export the paper's main-results data (warm decode at 8k/16k/32k, agent replay) to data/results.json.

Reuses the figure builders: main-results.py's Flare merge over bench-figures-rerun-1027/fig_combo.py.

    uv run --no-project --with matplotlib --with numpy python -I tools/export_data.py
"""
import json
import sys
from pathlib import Path

SRC = Path.home() / ".local/share/sharar/paper-figs/han-style/src/main-results.py"
OUT = Path(__file__).resolve().parent.parent / "data" / "results.json"

# run main-results.py with side() replaced by a no-op, keeping its patched module and the agents dict it builds
code = SRC.read_text().replace("combo.side(out", "(lambda *a: None)(out").replace(
    '(out / f"{name}.png").replace', "(lambda *a: None)")
sys.argv = [str(SRC)]
g = {"__file__": str(SRC), "__name__": "mr"}
exec(compile(code, str(SRC), "exec"), g)
combo, agents = g["combo"], g["agents"]
ef, HERE = combo.ef, combo.HERE

warm = {}
for m in combo.MODELS:
    cells = ef.rows(HERE / f"warm_{m.lower()}_{combo.THINKING}.csv")
    for ctx in ("8k", "16k", "32k"):
        for e in ("Sharar", "vLLM", "TensorFold", "llama.cpp", "Flare"):
            pts = ef.warm_best(cells, e, ctx)
            if pts:
                warm.setdefault(m, {}).setdefault(ctx, {})[e] = [
                    dict(n=int(n), user=round(float(r["per_stream_tok_s"]), 2), agg=round(float(r["aggregate_tok_s"]), 1),
                         accept=r.get("accept_length") or None) for n, r in pts]
ag = {}
for (model, engine, n), v in agents.items():
    ag.setdefault(model, {}).setdefault(engine, []).append([n, round(float(v), 1)])
for d in ag.values():
    for v in d.values():
        v.sort()
OUT.write_text(json.dumps({"models": list(combo.MODELS), "warm": warm, "agents": ag}, indent=1))
print(OUT, {m: {c: list(v) for c, v in d.items()} for m, d in warm.items()})
