"""Render before/after scenes for the write-up. Model code only ever runs in the sandbox.

Usage: python tools/render_examples.py runs/<run> <out_dir>
"""
import collections
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from envlib.io import ROOT, read_jsonl                     # noqa: E402
from envlib.reward import extract_code                     # noqa: E402
from envlib.sandbox import IMAGE, JOBS_DIR, run_episode    # noqa: E402
from envlib.tasks import oracle_for                        # noqa: E402

PALETTE = [(0.07, 0.13, 0.26), (0.80, 0.42, 0.10), (0.0, 0.42, 0.45)]
GHOST, GROUND, SKY = (1.0, 0.08, 0.30), (0.62, 0.62, 0.60), (0.75, 0.78, 0.82)


def _docker(job, *cmd, timeout=180, cpus="4"):
    return subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--read-only",
         "--tmpfs", "/tmp:rw,size=256m", "--memory", "2g", "--cpus", cpus, "--pids-limit", "128",
         "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
         "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
         "-v", f"{job}:/job", "-v", f"{ROOT / 'sandbox/render_scene.py'}:/opt/render_scene.py:ro",
         IMAGE, *cmd], capture_output=True, timeout=timeout)


def task_objects(task):
    p = task["params"]
    if task["template"] == "between":
        return [(p["a"], "cube"), (p["c"], "cube"), (p["mid"]["name"], p["mid"]["shape"])]
    if task["template"] == "next_to":
        return [(p["anchor"], "cube"), (p["other"]["name"], p["other"]["shape"])]
    return [(n, "cube") for n in p["names"]]


def render(task, code, target, bounds, out_png):
    """Run untrusted code in the sandbox, then render its scene in a second container."""
    names = task_objects(task)
    cfg = {"colors": {n: PALETTE[i % 3] for i, (n, _) in enumerate(names)},
           "ghosts": [{"name": n, "shape": s, **target["objects"][n]} for n, s in names],
           "bounds": bounds, "ghost_rgb": GHOST, "ground_rgb": GROUND, "sky_rgb": SKY}
    JOBS_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=JOBS_DIR) as d:
        Path(d, "agent.py").write_text(code)
        p = _docker(d, "sh", "-c",
                    "timeout -s KILL 20 blender --background --factory-startup --disable-autoexec "
                    "/opt/base_empty.blend --python /job/agent.py "
                    "--python /opt/save_scene.py -- /tmp/out.blend; "
                    "cp /tmp/out.blend /job/scene.blend 2>/dev/null || "
                    "cp /opt/base_empty.blend /job/scene.blend", timeout=60, cpus="1")
        Path(d, "cfg.json").write_text(json.dumps(cfg))
        Path(d, "agent.py").unlink()
        p = _docker(d, "blender", "--background", "--factory-startup", "--disable-autoexec",
                    "/job/scene.blend", "--python-exit-code", "1", "--python", "/opt/render_scene.py",
                    "--", "/job/cfg.json", "/job/out.png")
        if p.returncode != 0:
            raise RuntimeError(p.stderr.decode()[-800:] + p.stdout.decode()[-800:])
        Path(out_png).write_bytes(Path(d, "out.png").read_bytes())


def bounds_of(states, names):
    xs, ys, zs = [], [], []
    for s in states:
        for n, o in (s or {}).get("objects", {}).items():
            for v in (o["bbox_min"], o["bbox_max"]):
                xs.append(v[0]); ys.append(v[1]); zs.append(v[2])
    return [[min(xs), min(ys), 0], [max(xs), max(ys), max(zs)]]


def main(run, out):
    run, out = Path(run), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    picks = json.load(open(out / "picks.json"))
    tasks = {t["id"]: t for f in ["tasks_eval_id.jsonl", "tasks_eval_transfer.jsonl"]
             for t in read_jsonl(run / f)}
    meta = []
    for pk in picks:
        task = tasks[pk["task_id"]]
        target, err = run_episode(oracle_for(task), backend="local")
        assert target, err
        codes = [extract_code(s) for s in pk["texts"]]
        states = [run_episode(c)[0] for c in codes]
        names = [n for n, _ in task_objects(task)]
        b = bounds_of([target] + states, names)
        for i, (label, code) in enumerate(zip(pk["labels"], codes)):
            png = out / f"{pk['key']}_{i}.png"
            render(task, code, target, b, png)
            print("rendered", png, flush=True)
        meta.append({**pk, "prompt": task["prompt"], "codes": codes, "states": states,
                     "target": target})
    (out / "meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
