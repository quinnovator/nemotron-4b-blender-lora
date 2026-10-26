"""Run model-written bpy code in a throwaway, network-less container."""
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from .io import ROOT

JOBS_DIR = ROOT / ".jobs"
IMAGE = "blender-sandbox"
SANDBOX = ROOT / "sandbox"


def _docker_cmd(job_dir, name, inner_timeout):
    return ["docker", "run", "--rm", "--name", name,
            "--network", "none",
            "--read-only", "--tmpfs", "/tmp:rw,size=256m",
            "--memory", "2g", "--memory-swap", "2g", "--cpus", "1", "--pids-limit", "128",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
            "-v", f"{job_dir}:/job",
            IMAGE, "/opt/run_job.sh", str(inner_timeout)]


def _local_cmd(job_dir, inner_timeout):
    """Same two phases on host Blender. Dev only: trusted code (oracles, tests)."""
    tmp = Path(job_dir) / "out.blend"
    state = Path(job_dir) / "state.json"
    b = ["blender", "--background", "--factory-startup", "--disable-autoexec"]
    script = (
        f"set -e; rm -f {state}; "
        f"timeout -s KILL {inner_timeout} {' '.join(b)} {SANDBOX}/base_empty.blend "
        f"--python-exit-code 1 --python {job_dir}/agent.py "
        f"--python {SANDBOX}/save_scene.py -- {tmp}; "
        f"rm -f {state}; "
        f"timeout -s KILL 15 {' '.join(b)} {tmp} --python-exit-code 1 "
        f"--python {SANDBOX}/extract_scene.py -- {state}")
    return ["sh", "-c", script]


def run_episode(agent_code: str, timeout: int = 40, backend: str = "docker"):
    """Returns (state, None) on success or (None, error_text)."""
    JOBS_DIR.mkdir(exist_ok=True)
    name = f"brl-{uuid.uuid4().hex[:12]}"
    with tempfile.TemporaryDirectory(dir=JOBS_DIR) as d:
        Path(d, "agent.py").write_text(agent_code)
        inner = max(timeout - 20, 5)
        cmd = _docker_cmd(d, name, inner) if backend == "docker" else _local_cmd(d, inner)
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            if backend == "docker":
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return None, "timeout"
        out = Path(d, "state.json")
        if p.returncode in (124, 137):   # timeout -s KILL, or the memory cap
            return None, "timeout"
        if p.returncode != 0 or not out.exists():
            err = (p.stdout.decode(errors="replace")[-1500:] + "\n"
                   + p.stderr.decode(errors="replace")[-1500:])
            return None, err.strip() or f"exit {p.returncode}"
        try:
            return json.loads(out.read_text()), None
        except json.JSONDecodeError as e:
            return None, f"bad state json: {e}"
