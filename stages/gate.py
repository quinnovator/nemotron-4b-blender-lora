import json


def gate(cfg, run):
    b = json.loads((run / "baseline_eval_id.json").read_text())
    g = cfg["gate"]
    ok = (g["min_reward"] <= b["mean_reward"] <= g["max_reward"]
          and b["signal_fraction"] >= g["min_signal"])
    (run / "gate.md").write_text(
        f"mean_reward={b['mean_reward']:.3f}  signal_fraction={b['signal_fraction']:.2f}  "
        f"pass@1={b['pass_at_1']:.3f}  pass@n={b['pass_at_n']:.3f}\n"
        f"band: {g['min_reward']} <= mean_reward <= {g['max_reward']}, "
        f"signal_fraction >= {g['min_signal']}\n"
        f"decision={'PROCEED' if ok else 'STOP'}\n"
        "If too low: make tasks easier or add a short SFT warm start. "
        "If too high: add harder templates.\n")
    return ok
