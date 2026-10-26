import json
import os
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# FlashInfer's sampler JIT-compiles with nvcc; vLLM's native sampler needs nothing extra.
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
if Path("/opt/cuda/bin/nvcc").exists():
    os.environ.setdefault("CUDA_HOME", "/opt/cuda")

SYSTEM_PROMPT = (
    "You write Python scripts for Blender 5.2 (the bpy API). The script runs in "
    "background mode on a scene that starts with no objects. Units are metres and "
    "Z is up; the ground plane is z = 0. Build exactly what the task asks, with the "
    "exact object names given. Reply with one ```python code block and nothing else."
)


def load_cfg(path):
    cfg = yaml.safe_load(open(path))
    cfg["_path"] = str(Path(path).resolve())
    return cfg


def run_dir(cfg):
    run = ROOT / "runs" / cfg["run_name"]
    run.mkdir(parents=True, exist_ok=True)
    return run


def read_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def to_chat(prompt):
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}]


def log(run, msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(Path(run) / "orchestrate.log", "a") as f:
        f.write(line + "\n")
