"""GPU stage: evaluate the base model on both eval splits (n samples per task)."""
import sys

from envlib.evaluate import evaluate, make_llm
from envlib.io import load_cfg, log, read_jsonl, run_dir


def main(cfg_path):
    cfg = load_cfg(cfg_path)
    run = run_dir(cfg)
    llm = make_llm(cfg)
    n = cfg.get("eval", {}).get("n", 8)
    for split in ["eval_id", "eval_transfer"]:
        tasks = read_jsonl(run / f"tasks_{split}.jsonl")
        r = evaluate(llm, cfg, tasks, n=n, out_prefix=run / f"baseline_{split}")
        log(run, f"baseline {split}: pass@1={r['pass_at_1']:.3f} pass@{n}={r['pass_at_n']:.3f} "
                 f"reward={r['mean_reward']:.3f} signal={r['signal_fraction']:.2f} "
                 f"tok/s={r['gen_tok_per_s']:.0f} errors={r['errors']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
