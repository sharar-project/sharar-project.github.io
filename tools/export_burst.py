"""Export the context-burst run (paper burst-endurance figure) to data/burst.json, open context downsampled every STEP requests (the rolling series are already windowed).

    uv run --no-project --with numpy python -I tools/export_burst.py
"""
import json
import sys
from pathlib import Path

TT = Path.home() / ".local/share/sharar/ttft-time"
sys.path.insert(0, str(TT / "tools"))
from fig_ttft_time import rolling, series  # noqa: E402

RUNS = {"sharar-ssd-on_aa-s192": "Sharar", "sharar-ssd-off_aa-s192": "Sharar w/o SSD tier",
        "vllm_aa-s192": "vLLM", "tensorfold_aa-s192": "TensorFold"}
STEP = 24
data = {k: series(TT / "raw" / f"{k}.jsonl") for k in RUNS}
ws = [x["ws"] / 1e6 for x in data["sharar-ssd-on_aa-s192"]]
out = {"kv_mtok": 1.58, "open_ctx": [[i, round(v, 3)] for i, v in enumerate(ws) if i % STEP == 0], "runs": {}}
for k, name in RUNS.items():
    xs, hit, ttft, _, _ = rolling(data[k])
    out["runs"][name] = [[int(x), round(float(h), 1), round(float(t), 3)] for x, h, t in zip(xs, hit, ttft)]
p = Path(__file__).resolve().parent.parent / "data" / "burst.json"
p.write_text(json.dumps(out))
print(p, {k: len(v) for k, v in out["runs"].items()}, len(out["open_ctx"]))
