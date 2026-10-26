"""Oracle solutions pass every check; broken ones don't. Uses host Blender (trusted code only)."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from envlib.reward import classify_error, extract_code, score  # noqa: E402
from envlib.sandbox import run_episode  # noqa: E402
from envlib.tasks import TEMPLATES, oracle_for  # noqa: E402

backend = sys.argv[1] if len(sys.argv) > 1 else "local"
rng = np.random.default_rng(0)
tasks = [{"id": f"{n}-{i}", "template": n, "params": t.sample_params(rng)}
         for n, t in TEMPLATES.items() for i in range(6)]

def go(t):
    state, err = run_episode(oracle_for(t), backend=backend)
    r, passed = score(state, err, t)
    return t, r, passed, err

with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(go, tasks))
bad = [(t["id"], r, p, (e or "")[-300:]) for t, r, p, e in res if r < 0.999]
print(f"oracle: {len(res) - len(bad)}/{len(res)} full pass")
for b in bad:
    print("FAIL", b)

# Negative controls: off-by-a-bit placement, wrong size, an API error.
t = tasks[0]
wrong = oracle_for(t).replace("location=(", "location=(0.5+", 1)
for label, code in [("shifted", wrong), ("api_err", "import bpy\nbpy.ops.mesh.add_cube()\n"),
                    ("syntax", "import bpy\nfor\n")]:
    state, err = run_episode(code, backend=backend)
    r, passed = score(state, err, t)
    print(label, round(r, 3), classify_error(err, passed))
print(repr(extract_code("Sure!\n```python\nimport bpy\n```\nDone")))
assert not bad
