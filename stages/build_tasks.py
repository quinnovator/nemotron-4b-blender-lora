import numpy as np

from envlib.io import write_jsonl
from envlib.tasks import TEMPLATES


def build_splits(cfg, run):
    rng = np.random.default_rng(cfg["seed"])
    sizes = cfg.get("split_sizes", {"train": 2000, "eval_id": 200, "eval_transfer": 200})

    def make(split, names, n):
        out = []
        for i in range(n):
            name = names[i % len(names)]
            params = TEMPLATES[name].sample_params(rng)
            out.append({"id": f"{split}-{name}-{i}", "template": name, "params": params,
                        "prompt": TEMPLATES[name].prompt(params)})
        return out

    # Eval params come from the same RNG stream after train, then leakage is asserted away.
    train = make("train", cfg["train_templates"], sizes["train"])
    eval_id = make("eval_id", cfg["train_templates"], sizes["eval_id"])
    eval_tr = make("eval_transfer", cfg["transfer_templates"], sizes["eval_transfer"])
    key = lambda t: (t["template"], repr(sorted(t["params"].items())))  # noqa: E731
    seen = {key(t) for t in train}
    assert not any(key(t) in seen for t in eval_id + eval_tr), "eval task leaked into train"
    assert not set(cfg["transfer_templates"]) & set(cfg["train_templates"])

    write_jsonl(run / "tasks_train.jsonl", train)
    write_jsonl(run / "tasks_eval_id.jsonl", eval_id)
    write_jsonl(run / "tasks_eval_transfer.jsonl", eval_tr)
    return True
