"""GPU stage: GRPO with NeMo RL + NeMo Gym in the NeMo RL container.

Writes the run's task splits as Gym data, starts the sandbox broker if it is not
up, and runs NeMo RL's Gym GRPO entrypoint (it resumes from the newest step_N in
the checkpoint dir). Then it exports every Megatron LoRA checkpoint as a PEFT
adapter under ckpts/checkpoint-N, which vLLM loads in eval_ckpts.
"""
import glob
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from safetensors.torch import load_file, save_file

from envlib.io import ROOT, load_cfg, log, run_dir
from gym_env.build_data import main as build_gym_data

BROKER = "http://127.0.0.1:8765"
BASE_MCORE = "/root/.cache/huggingface/nemo_rl/{model}/iter_0000000"
MCORE_PY = "/opt/ray_venvs/nemo_rl.models.policy.workers.megatron_policy_worker.MegatronPolicyWorker/bin/python"


def _broker_up():
    try:
        return json.loads(urllib.request.urlopen(f"{BROKER}/health", timeout=3).read())["ok"]
    except OSError:
        return False


def _container(cmd, name, logfile):
    with open(logfile, "a") as f:
        return subprocess.run([str(ROOT / "nemo" / "docker_run.sh"), cmd], stdout=f, stderr=subprocess.STDOUT,
                              env={**__import__("os").environ, "BRL_CONTAINER_NAME": name}).returncode


def export_adapters(cfg, run, logfile):
    """step_N (Megatron torch_dist) -> ckpts/checkpoint-N (PEFT, transformers-5 key names)."""
    run = Path(run).resolve()   # the container's working directory is /opt/nemo-rl
    todo = [p for p in sorted((run / "nemo_ckpts").glob("step_*"))
            if not (run / "ckpts" / f"checkpoint-{p.name[5:]}" / "adapter_model.safetensors").exists()]
    if not todo:
        return
    base = BASE_MCORE.format(model=cfg["model"])
    cmds = [f"PYTHONPATH=/opt/nemo-rl {MCORE_PY} examples/converters/convert_lora_to_hf.py --adapter-only "
            f"--base-ckpt {base} --adapter-ckpt {p}/policy/weights/iter_0000000 "
            f"--hf-model-name {cfg['model']} --hf-ckpt-path {p}/hf_adapter" for p in todo]
    rc = _container(" && ".join(cmds), "brl-nemo-export", logfile)
    if rc != 0:
        raise RuntimeError(f"adapter export failed (rc={rc}), see {logfile}")
    for p in todo:
        out = run / "ckpts" / f"checkpoint-{p.name[5:]}"
        out.mkdir(parents=True, exist_ok=True)
        # Megatron-Bridge names the trunk `backbone`; transformers 5 and vLLM use `model`.
        w = load_file(p / "hf_adapter" / "adapter_model.safetensors")
        save_file({k.replace(".backbone.", ".model."): v.contiguous() for k, v in w.items()},
                  out / "adapter_model.safetensors")
        (out / "adapter_config.json").write_text((p / "hf_adapter" / "adapter_config.json").read_text())
    log(run, f"exported {len(todo)} adapters: {[p.name for p in todo]}")


def write_history(run):
    """TensorBoard scalars (all launches) -> train_log_history.json, one dict per step."""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    by_step = {}
    gpu = []
    for f in sorted(glob.glob(str(run / "nemo_logs" / "exp_*" / "tensorboard" / "events.out.tfevents.*"))):
        ea = EventAccumulator(f, size_guidance={"scalars": 0})
        ea.Reload()
        tags = ea.Tags()["scalars"]
        for tag, key in [("train/total_reward/mean", "reward"), ("timing/train/total_step_time", "time/step_seconds"),
                         ("train/blender_scene_simple_agent/full_pass/mean", "full_pass"),
                         ("train/grad_norm", "grad_norm"), ("train/mean_gen_tokens_per_sample", "completion_len")]:
            if tag in tags:
                for e in ea.Scalars(tag):
                    by_step.setdefault(e.step, {"step": e.step})[key] = e.value
        if "ray/node.0.gpu.0.mem_gb" in tags:
            gpu += [e.value for e in ea.Scalars("ray/node.0.gpu.0.mem_gb")]
    hist = [by_step[s] for s in sorted(by_step)]
    if hist and gpu:
        hist[0]["mem/device_used_gib"] = max(gpu)   # whole-card peak, desktop included
    (run / "train_log_history.json").write_text(json.dumps(hist))


def main(cfg_path):
    cfg = load_cfg(cfg_path)
    run = run_dir(cfg)
    tc = cfg["train"]
    logfile = ROOT / "logs" / f"{cfg['run_name']}.nemo.log"
    logfile.parent.mkdir(exist_ok=True)
    build_gym_data(run)
    broker = None
    if not _broker_up():
        broker = subprocess.Popen([sys.executable, "-m", "sandbox.broker", "--workers", str(cfg.get("sandbox_workers", 16))],
                                  cwd=ROOT, stdout=open(ROOT / "logs" / "broker.log", "a"), stderr=subprocess.STDOUT)
        for _ in range(30):
            if _broker_up():
                break
            time.sleep(1)
        else:
            raise RuntimeError("sandbox broker did not come up")
        log(run, "started sandbox broker")
    try:
        cmd = (f"uv run --no-sync python examples/nemo_gym/run_grpo_nemo_gym.py --config {ROOT / cfg['nemo_config']} "
               f"grpo.max_num_steps={tc['max_steps']} checkpointing.save_period={tc['save_every']} "
               f"checkpointing.checkpoint_dir={run / 'nemo_ckpts'} logger.log_dir={run / 'nemo_logs'} "
               f"data.train.data_path={ROOT / 'gym_env/blender_scene/data/train.jsonl'}")
        cmd += f" grpo.seed={cfg.get('train_seed', cfg['seed'])}"
        rc = _container(cmd, "brl-nemo-train", logfile)
    finally:
        if broker:
            broker.terminate()
    write_history(run)
    done = sorted(int(p.name[5:]) for p in (run / "nemo_ckpts").glob("step_*"))
    if rc != 0 and (not done or done[-1] < tc["max_steps"]):
        log(run, f"NeMo RL exited rc={rc} at step {done[-1] if done else 0}")
        return 1
    export_adapters(cfg, run, logfile)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
