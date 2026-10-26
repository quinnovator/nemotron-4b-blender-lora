# SPDX-License-Identifier: Apache-2.0
"""NeMo Gym resources server: Blender scenes from plain-English descriptions.

The model writes a bpy script for a scene described in plain English. verify()
pulls the script out of the reply, runs it in the hardened Blender sandbox via
the host-side broker (sandbox/broker.py), and scores the resulting scene with
the task's geometric checks. Scoring is the same code the host-side evaluation
uses (envlib.reward.score), so training reward and eval scores agree.
"""
import json
import os
import sys
from asyncio import Semaphore
from typing import Any, Dict, List, Optional

from nemo_gym.base_resources_server import (
    BaseResourcesServerConfig,
    BaseRunRequest,
    BaseVerifyRequest,
    BaseVerifyResponse,
    SimpleResourcesServer,
)
from nemo_gym.server_utils import request


class BlenderSceneResourcesServerConfig(BaseResourcesServerConfig):
    repo_root: Optional[str] = None           # holds envlib/; default $BLENDER_LORA_ROOT
    broker_url: str = "http://127.0.0.1:8765"
    episode_timeout_s: int = 40
    max_concurrent_episodes: int = 16
    reward_weights: Optional[Dict[str, float]] = None


class BlenderSceneRunRequest(BaseRunRequest):
    verifier_metadata: Dict[str, Any]          # {"task": {"id", "template", "params", ...}}


class BlenderSceneVerifyRequest(BlenderSceneRunRequest, BaseVerifyRequest):
    pass


class BlenderSceneVerifyResponse(BaseVerifyResponse):
    task_id: str
    template: str
    full_pass: float
    ran: float
    check_fraction: float
    checks: List[bool]
    error_bucket: str
    error_tail: Optional[str] = None
    extracted_code: str


class BlenderSceneResourcesServer(SimpleResourcesServer):
    config: BlenderSceneResourcesServerConfig

    def model_post_init(self, context: Any) -> None:
        sys.path.insert(0, self.config.repo_root or os.environ["BLENDER_LORA_ROOT"])
        from envlib.reward import classify_error, extract_code, score

        self._extract_code, self._score, self._classify = extract_code, score, classify_error
        self._slots = Semaphore(self.config.max_concurrent_episodes)

    async def _run_episode(self, code: str) -> tuple[Optional[dict], Optional[str]]:
        """Returns (state, error). Broker or transport failures surface as errors, never as a scene."""
        async with self._slots:
            try:
                resp = await request(
                    "POST",
                    f"{self.config.broker_url}/run",
                    json={"code": code, "timeout": self.config.episode_timeout_s},
                )
                body = json.loads(await resp.read())
            except Exception as e:  # task boundary: a dead broker must not crash the rollout
                return None, f"broker error: {type(e).__name__}: {e}"
        if resp.status != 200:
            return None, f"broker error: HTTP {resp.status}: {body}"
        return body.get("state"), body.get("error")

    async def verify(self, body: BlenderSceneVerifyRequest) -> BlenderSceneVerifyResponse:
        task = body.verifier_metadata["task"]
        code = self._extract_code(body.response.output_text or "")
        state, err = await self._run_episode(code)
        reward, passed = self._score(state, err, task, self.config.reward_weights)
        return BlenderSceneVerifyResponse(
            **body.model_dump(),
            reward=reward,
            task_id=task["id"],
            template=task["template"],
            full_pass=float(bool(passed) and all(passed)),
            ran=float(err is None and state is not None),
            check_fraction=sum(passed) / len(passed) if passed else 0.0,
            checks=passed,
            error_bucket=self._classify(err, passed),
            error_tail=(err or "")[-400:] or None,
            extracted_code=code,
        )


if __name__ == "__main__":
    BlenderSceneResourcesServer.run_webserver()
