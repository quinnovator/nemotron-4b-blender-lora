"""The run report: four questions, each with its pass bar, plus the architecture panel."""
import json
import re

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from envlib.io import read_jsonl  # noqa: E402

BUCKETS = ["pass", "ran_but_failed", "bpy_attribute", "bpy_type_or_arg", "bpy_runtime",
           "key_or_lookup", "name_or_import", "syntax", "timeout", "other_error"]


def _boot_ci(per_task_pass, iters=2000, seed=0):
    v = np.array(list(per_task_pass.values()))
    rng = np.random.default_rng(seed)
    means = [rng.choice(v, len(v)).mean() for _ in range(iters)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _diff_ci(a, b, iters=2000, seed=0):
    """Bootstrap CI over tasks of (b - a) in per-task pass rate."""
    keys = sorted(a)
    d = np.array([b[k] - a[k] for k in keys])
    rng = np.random.default_rng(seed)
    means = [rng.choice(d, len(d)).mean() for _ in range(iters)]
    return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _load(p):
    return json.loads(p.read_text()) if p.exists() else None


def report(cfg, run):
    out = []
    base = {s: _load(run / f"baseline_{s}.json") for s in ["eval_id", "eval_transfer"]}
    evals = {}
    for p in sorted((run / "evals").glob("step*_eval_*.json")) if (run / "evals").exists() else []:
        if p.name.endswith(".samples.jsonl"):
            continue
        m = re.match(r"step(\d+)_(eval_\w+)\.json", p.name)
        evals.setdefault(m.group(2), {})[int(m.group(1))] = json.loads(p.read_text())
    out.append(f"# Run report: {cfg['run_name']}\n\nModel: `{cfg['model']}`\n")
    if (run / "gate.md").exists():
        out.append("## Gate\n\n```\n" + (run / "gate.md").read_text() + "```\n")

    # Q1: learning curves with bootstrap CIs.
    fig, ax = plt.subplots(figsize=(7, 4))
    out.append("## 1. Did held-out pass@1 go up?\n")
    out.append("| split | base pass@1 | best step | best pass@1 | gain (95% CI over tasks) | verdict |")
    out.append("|---|---|---|---|---|---|")
    best_step = {}
    for split, color in [("eval_id", "#2563eb"), ("eval_transfer", "#d97706")]:
        b, e = base[split], evals.get(split, {})
        if b is None:
            continue
        steps = [0] + sorted(e)
        ys = [b["pass_at_1"]] + [e[s]["pass_at_1"] for s in sorted(e)]
        cis = [_boot_ci(b["per_task_pass"])] + [_boot_ci(e[s]["per_task_pass"]) for s in sorted(e)]
        ax.plot(steps, ys, "-o", color=color, label=split)
        ax.fill_between(steps, [c[0] for c in cis], [c[1] for c in cis], color=color, alpha=0.15)
        if e:
            s_best = max(e, key=lambda s: e[s]["pass_at_1"])
            best_step[split] = s_best
            d, lo, hi = _diff_ci(b["per_task_pass"], e[s_best]["per_task_pass"])
            verdict = "PASS" if lo > 0 else "not significant"
            out.append(f"| {split} | {b['pass_at_1']:.3f} | {s_best} | {e[s_best]['pass_at_1']:.3f} "
                       f"| {d:+.3f} [{lo:+.3f}, {hi:+.3f}] | {verdict} |")
        else:
            out.append(f"| {split} | {b['pass_at_1']:.3f} | – | – | – | no checkpoints |")
    ax.set_xlabel("training step")
    ax.set_ylabel("pass@1 (held-out)")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(run / "curves.png", dpi=130)
    out.append("\n![curves](curves.png)\n\nThe best step is picked per split on that split's own "
               "curve, so treat the gain as slightly optimistic; the final checkpoint is in the curve.\n")

    # Q2: error mix.
    out.append("## 2. Did the error mix change?\n")
    s_id = best_step.get("eval_id")
    rows = [("base", base["eval_id"])] + ([(f"step {s_id}", evals["eval_id"][s_id])] if s_id else [])
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for i, (label, r) in enumerate(rows):
        if r is None:
            continue
        tot = sum(r["errors"].values())
        left = 0.0
        for k, bkt in enumerate(BUCKETS):
            w = r["errors"].get(bkt, 0) / tot
            ax.barh(i, w, left=left, color=plt.cm.tab10(k), label=bkt if i == 0 else None)
            left += w
        mix = ", ".join(f"{k} {v / tot:.0%}" for k, v in sorted(r["errors"].items(), key=lambda x: -x[1]))
        out.append(f"- **{label}** (eval_id): {mix}")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.legend(fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.tight_layout()
    fig.savefig(run / "errors.png", dpi=130)
    out.append("\n![errors](errors.png)\n")

    # Q3: trained pass@1 vs base pass@n.
    out.append("## 3. Does trained pass@1 beat base pass@8?\n")
    out.append("| split | base pass@1 | base pass@8 | trained pass@1 (best) | trained pass@1 (final) | beats base pass@8? |")
    out.append("|---|---|---|---|---|---|")
    for split in ["eval_id", "eval_transfer"]:
        b, e = base[split], evals.get(split, {})
        if b is None or not e:
            continue
        tb, tf = e[best_step[split]]["pass_at_1"], e[max(e)]["pass_at_1"]
        out.append(f"| {split} | {b['pass_at_1']:.3f} | {b['pass_at_n']:.3f} | {tb:.3f} | {tf:.3f} "
                   f"| {'yes' if tf > b['pass_at_n'] else 'no'} (final) |")

    # Q4: reward-hack review material.
    out.append("\n## 4. Do top-reward samples look like real solutions?\n")
    hack_pat = re.compile(r"state\.json|extract_scene|os\._exit|sys\.exit|except\s*:\s*pass|"
                          r"scale\s*=\s*\(?0[,)]|subprocess|socket|open\(")
    if s_id is not None:
        samples = read_jsonl(run / "evals" / f"step{s_id:05d}_eval_id.samples.jsonl")
        top = sorted(samples, key=lambda s: -s["reward"])[:20]
        flagged = [s for s in top if hack_pat.search(s["text"])]
        out.append(f"Top 20 eval_id samples at step {s_id}: {len(flagged)} match the hack "
                   f"watchlist regex (manual read still required). Full texts in "
                   f"`report_top20.md`.\n")
        with open(run / "report_top20.md", "w") as f:
            for s in top:
                f.write(f"### {s['task_id']} reward={s['reward']:.2f} "
                        f"{'FLAGGED' if s in flagged else ''}\n\n{s['text']}\n\n")
    # Architecture panel.
    hist = _load(run / "train_log_history.json") or []
    used = max((h.get("mem/device_used_gib", 0) for h in hist), default=0)
    st = [h["time/step_seconds"] for h in hist if "time/step_seconds" in h]
    out.append("## 5. Architecture panel\n")
    # NeMo RL logs whole-card usage: vLLM's reserved pool and the desktop included.
    out.append(f"- Peak device memory used during training (whole card): {used:.1f} GiB")
    if st:
        out.append(f"- Median step time: {np.median(st):.1f} s over {len(st)} steps")
    if base["eval_id"]:
        out.append(f"- Rollout throughput at baseline (vLLM, n=8): "
                   f"{base['eval_id']['gen_tok_per_s']:.0f} tokens/s")
    rew = [(h["step"], h["reward"]) for h in hist if "reward" in h and "step" in h]
    if rew:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(*zip(*rew), lw=0.8)
        ax.set_xlabel("step")
        ax.set_ylabel("train reward")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(run / "train_reward.png", dpi=130)
        out.append("\n![train reward](train_reward.png)\n")
    (run / "report.md").write_text("\n".join(out) + "\n")
    return True
