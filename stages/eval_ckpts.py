"""GPU stage: run evaluate() on each kept LoRA checkpoint against both eval splits."""
import re
import sys
from pathlib import Path

from envlib.evaluate import evaluate, make_llm
from envlib.io import load_cfg, log, read_jsonl, run_dir


def checkpoints(run, every):
    ck = sorted(((int(re.search(r"(\d+)$", p.name).group(1)), p)
                 for p in (run / "ckpts").glob("checkpoint-*")
                 if (p / "adapter_model.safetensors").exists()), key=lambda x: x[0])
    if not ck:
        return []
    keep = [c for c in ck if c[0] % every == 0]
    if ck[-1] not in keep:
        keep.append(ck[-1])
    return keep


def main(cfg_path):
    cfg = load_cfg(cfg_path)
    run = run_dir(cfg)
    e = cfg.get("eval", {})
    ck = checkpoints(run, e.get("every", cfg["train"]["save_every"]))
    if not ck:
        log(run, "eval_ckpts: no checkpoints found")
        return 1
    out = run / "evals"
    out.mkdir(exist_ok=True)
    llm = make_llm(cfg, enable_lora=True)
    splits = {s: read_jsonl(run / f"tasks_{s}.jsonl") for s in ["eval_id", "eval_transfer"]}
    for step, path in ck:
        for split, tasks in splits.items():
            prefix = out / f"step{step:05d}_{split}"
            if prefix.with_suffix(".json").exists():
                continue
            r = evaluate(llm, cfg, tasks, n=e.get("n", 8), lora_path=Path(path), out_prefix=prefix)
            log(run, f"ckpt {step} {split}: pass@1={r['pass_at_1']:.3f} "
                     f"pass@n={r['pass_at_n']:.3f} reward={r['mean_reward']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
