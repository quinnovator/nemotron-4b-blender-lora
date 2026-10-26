"""Prove the sandbox holds before any GPU time is spent."""
import shutil
import subprocess
from pathlib import Path

from envlib.io import ROOT, log
from envlib.reward import score
from envlib.sandbox import IMAGE, run_episode
from envlib.tasks import TEMPLATES, oracle_for

PROBES = {
    "infinite_loop": "while True:\n    pass\n",
    "network": ("import socket\ns = socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
                "print('NETWORK OPEN')\n"),
    "write_outside_job": "open('/opt/pwned.txt', 'w').write('x')\n",
    "write_host_home": f"open({str(Path.home() / 'pwned.txt')!r}, 'w').write('x')\n",
    "fake_state": ("import json, os\n"
                   "json.dump({'objects': {}}, open('/job/state.json', 'w'))\n"
                   "os._exit(0)\n"),
    "fork_bomb": ("import os\nfor _ in range(400):\n"
                  "    try:\n        os.fork()\n    except OSError:\n        break\n"
                  "raise SystemExit(1)\n"),
}


def _sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def preflight(cfg, run):
    report, ok = [], True

    def check(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        report.append(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")

    check("nvidia-smi responds", _sh(["nvidia-smi", "-L"]).returncode == 0)
    check("docker image present", _sh(["docker", "image", "inspect", IMAGE]).returncode == 0)
    free_gb = shutil.disk_usage(ROOT).free / 2**30
    check("free disk >= 40 GiB", free_gb >= 40, f"{free_gb:.0f} GiB")
    if not ok:
        (run / "preflight.md").write_text("\n".join(report) + "\n")
        return False

    task = {"template": "stack", "params": TEMPLATES["stack"].sample_params(
        __import__("numpy").random.default_rng(0))}
    state, err = run_episode(oracle_for(task))
    r, _ = score(state, err, task)
    check("known-good scene passes", r > 0.999, f"reward={r:.2f} err={(err or '')[-200:]!r}")

    state, err = run_episode(PROBES["infinite_loop"], timeout=40)
    left = _sh(["docker", "ps", "-aq", "--filter", "name=brl-"]).stdout.strip()
    check("infinite loop times out", err == "timeout", repr(err)[:80])
    check("no container left behind", left == "", left)

    state, err = run_episode(PROBES["network"])
    check("network connection fails", state is None and err and "NETWORK OPEN" not in err,
          (err or "")[-120:].replace("\n", " "))
    for p in ["write_outside_job", "write_host_home"]:
        state, err = run_episode(PROBES[p])
        check(f"{p} fails", state is None, (err or "")[-120:].replace("\n", " "))
    check("host home untouched", not (ROOT.home() / "pwned.txt").exists())
    state, err = run_episode(PROBES["fake_state"])
    r, _ = score(state, err, task)
    check("pre-written state.json + early exit earns nothing", r == 0.0, f"reward={r}")
    state, err = run_episode(PROBES["fork_bomb"])
    check("fork bomb contained", state is None)

    (run / "preflight.md").write_text("\n".join(report) + "\n")
    for line in report:
        log(run, "preflight " + line)
    return ok
