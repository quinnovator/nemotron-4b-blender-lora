"""Runs the seven stages in order, skipping any with a .done_* marker.

GPU stages run in their own process so GPU memory is fully freed between them.
Usage: python orchestrate.py configs/<run>.yaml [--until STAGE]   (or ./run.sh, which retries crashes)
"""
import subprocess
import sys

from envlib.io import load_cfg, log, run_dir
from stages.build_tasks import build_splits
from stages.gate import gate
from stages.preflight import preflight
from stages.report import report

STAGES = ["preflight", "build_tasks", "baseline", "gate",
          "train", "eval_ckpts", "report"]
GPU_STAGES = {"baseline", "train", "eval_ckpts"}
STAGE_FNS = {"preflight": preflight, "build_tasks": build_splits, "gate": gate, "report": report}


def write_stop_report(run, name):
    (run / "STOPPED.md").write_text(
        f"Run stopped at stage `{name}`. See orchestrate.log and the stage's own output "
        f"(preflight.md, gate.md, logs/<run>.nemo.log). Remove `.done_*` markers to redo stages.\n")


def main(cfg_path, until=None):
    cfg = load_cfg(cfg_path)
    run = run_dir(cfg)
    (run / "config.yaml").write_text(open(cfg_path).read())
    for name in STAGES:
        if (run / f".done_{name}").exists():
            continue
        log(run, f"=== {name} ===")
        if name in GPU_STAGES:
            ok = subprocess.run([sys.executable, "-m", f"stages.{name}", cfg_path]).returncode == 0
        else:
            ok = STAGE_FNS[name](cfg, run)
        if not ok:
            log(run, f"stopped at {name}")
            write_stop_report(run, name)
            return 3    # a deliberate stop; run.sh only retries crashes
        (run / f".done_{name}").touch()
        if name == until:
            log(run, f"stopping after {name} (--until)")
            return 0
    log(run, "all stages done")
    return 0


if __name__ == "__main__":
    until = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else None
    sys.exit(main(sys.argv[1], until))
