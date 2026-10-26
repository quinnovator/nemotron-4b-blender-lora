# SPDX-License-Identifier: Apache-2.0
"""verify() against scene states captured from the real sandbox; the broker call is stubbed."""
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

from nemo_gym.server_utils import ServerClient

from resources_servers.blender_scene.app import (
    BlenderSceneResourcesServer,
    BlenderSceneResourcesServerConfig,
    BlenderSceneVerifyRequest,
)

HERE = Path(__file__).parent
FIX = json.loads((HERE / "fixtures.json").read_text())
ROOT = os.environ["BLENDER_LORA_ROOT"]       # set by nemo/docker_run.sh


def _server(state, error):
    cfg = BlenderSceneResourcesServerConfig(
        host="127.0.0.1", port=8080, entrypoint="", name="blender_scene", repo_root=ROOT)
    server = BlenderSceneResourcesServer(config=cfg, server_client=MagicMock(spec=ServerClient))
    seen = {}

    async def fake_run(code):
        seen["code"] = code
        return state, error

    server._run_episode = fake_run
    return server, seen


def _request(text):
    response = {"id": "r", "created_at": 0, "model": "m", "object": "response",
                "output": [{"id": "o", "type": "message", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": text, "annotations": []}]}],
                "parallel_tool_calls": False, "tool_choice": "auto", "tools": []}
    return BlenderSceneVerifyRequest.model_validate({**FIX["row"], "response": response})


def test_correct_scene_gets_full_reward():
    server, seen = _server(FIX["good_state"], None)
    out = asyncio.run(server.verify(_request(f"```python\n{FIX['oracle_code']}```")))
    assert out.reward == 1.0 and out.full_pass == 1.0 and out.error_bucket == "pass"
    assert seen["code"].strip() == FIX["oracle_code"].strip()


def test_floating_object_gets_partial_reward():
    server, _ = _server(FIX["floating_state"], None)
    out = asyncio.run(server.verify(_request("```python\nimport bpy\n```")))
    assert 0.1 < out.reward < 1.0 and out.full_pass == 0.0 and out.error_bucket == "ran_but_failed"


def test_crash_gets_zero():
    server, _ = _server(None, "AttributeError: 'BlendData' object has no attribute 'mesh'")
    out = asyncio.run(server.verify(_request("```python\nbpy.data.mesh\n```")))
    assert out.reward == 0.0 and out.ran == 0.0 and out.error_bucket == "bpy_attribute"


def test_broker_down_is_reported_not_rewarded():
    server, _ = _server(None, "broker error: ClientConnectorError: refused")
    out = asyncio.run(server.verify(_request("```python\nimport bpy\n```")))
    assert out.reward == 0.0 and "broker error" in out.error_tail
