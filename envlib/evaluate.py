"""One evaluation function for the base model and every checkpoint (vLLM on the host)."""
import json
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from .io import to_chat
from .reward import classify_error, extract_code, score
from .sandbox import run_episode


def make_llm(cfg, enable_lora=False):
    from vllm import LLM
    e = cfg.get("eval", {})
    return LLM(model=cfg["model"], enable_lora=enable_lora, max_lora_rank=32,
               gpu_memory_utilization=e.get("vllm_mem", 0.75),
               max_model_len=e.get("max_model_len", 4096),
               seed=cfg.get("seed", 0), **cfg.get("vllm_extra", {}))


def generate(llm, cfg, tasks, n, lora_path=None):
    from vllm import SamplingParams
    from vllm.lora.request import LoRARequest
    e = cfg.get("eval", {})
    sp = SamplingParams(n=n, temperature=e.get("temperature", 0.7),
                        max_tokens=cfg.get("max_completion_length", 768))
    req = LoRARequest(str(lora_path), abs(hash(str(lora_path))) % 10**6 + 1,
                      str(lora_path)) if lora_path else None
    t0 = time.time()
    outs = llm.chat([to_chat(t["prompt"]) for t in tasks], sp, lora_request=req,
                    chat_template_kwargs=cfg.get("chat_kwargs", {}), use_tqdm=False)
    gen_s = time.time() - t0
    n_tok = sum(len(o.token_ids) for out in outs for o in out.outputs)
    return outs, {"gen_seconds": gen_s, "gen_tokens": n_tok, "gen_tok_per_s": n_tok / gen_s}


def score_outputs(cfg, tasks, outs, workers=16):
    jobs = [(t, o.text) for t, out in zip(tasks, outs) for o in out.outputs]
    backend = cfg.get("sandbox_backend", "docker")
    with ThreadPoolExecutor(max_workers=cfg.get("sandbox_workers", workers)) as ex:
        results = list(ex.map(lambda j: run_episode(extract_code(j[1]), backend=backend), jobs))

    per_task = defaultdict(list)
    for (t, text), (state, err) in zip(jobs, results):
        r, passed = score(state, err, t, cfg.get("reward_weights"))
        per_task[t["id"]].append({
            "reward": r, "full_pass": bool(passed) and all(passed),
            "checks": passed, "error": classify_error(err, passed),
            "err_tail": (err or "")[-400:], "text": text})
    return per_task


def summarize(per_task):
    flat = [s for v in per_task.values() for s in v]
    return {
        "n_tasks": len(per_task), "n_samples": len(flat),
        "pass_at_1": mean(s["full_pass"] for s in flat),
        "pass_at_n": mean(any(s["full_pass"] for s in v) for v in per_task.values()),
        "mean_reward": mean(s["reward"] for s in flat),
        "signal_fraction": mean(len({round(s["reward"], 3) for s in v}) > 1
                                for v in per_task.values()),
        "errors": dict(Counter(s["error"] for s in flat)),
        "per_task_pass": {k: mean(s["full_pass"] for s in v) for k, v in per_task.items()},
    }


def evaluate(llm, cfg, tasks, n=8, lora_path=None, out_prefix=None):
    outs, speed = generate(llm, cfg, tasks, n, lora_path)
    per_task = score_outputs(cfg, tasks, outs)
    res = {**summarize(per_task), **speed}
    if out_prefix is not None:
        out_prefix.with_suffix(".json").write_text(json.dumps(res, indent=1))
        with open(out_prefix.with_suffix(".samples.jsonl"), "w") as f:
            for tid, samples in per_task.items():
                for s in samples:
                    f.write(json.dumps({"task_id": tid, **s}) + "\n")
    return res
