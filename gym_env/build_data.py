"""Write a run's task splits as NeMo Gym JSONL rows.

Each row carries the chat input in Responses API form, the task for the verifier,
and the agent that should run it. stages/train.py calls this before training, so
NeMo RL trains on exactly the tasks the run's build_tasks stage sampled.

Usage: python -m gym_env.build_data runs/nemotron4b
"""
import json
import sys
from pathlib import Path

from envlib.io import ROOT, read_jsonl, to_chat

OUT = ROOT / "gym_env" / "blender_scene" / "data"
AGENT = {"type": "responses_api_agents", "name": "blender_scene_simple_agent"}


def to_row(task):
    return {"responses_create_params": {"input": to_chat(task["prompt"])},
            "verifier_metadata": {"task": task},
            "agent_ref": AGENT}


def main(run):
    OUT.mkdir(parents=True, exist_ok=True)
    for split in ["train", "eval_id", "eval_transfer"]:
        tasks = read_jsonl(Path(run) / f"tasks_{split}.jsonl")
        with open(OUT / f"{split}.jsonl", "w") as f:
            for t in tasks:
                f.write(json.dumps(to_row(t)) + "\n")
        print(f"{split}: {len(tasks)} rows")
    example = [json.loads(l) for l in open(OUT / "eval_id.jsonl")][:5]
    (OUT / "example.jsonl").write_text("".join(json.dumps(r) + "\n" for r in example))


if __name__ == "__main__":
    main(sys.argv[1])
