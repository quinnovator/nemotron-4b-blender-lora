#!/bin/bash
# Run a command inside the NeMo RL container (NeMo RL + NeMo Gym) with this repo
# (at the same path as on the host), the Hugging Face cache and the Blender Gym
# resources server mounted.
# Host networking lets Gym's resources server reach the sandbox broker on
# 127.0.0.1; the container never gets the Docker socket.
# The NCCL settings shrink each communicator from ~0.38 GiB to ~0.01 GiB of GPU
# memory. Megatron opens about nine single-rank groups; on one GPU nothing is
# ever sent, and the default buffers alone push the weight refit out of memory.
#
# Usage: nemo/docker_run.sh '<shell command run in /opt/nemo-rl>'
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGE=${NEMO_RL_IMAGE:-nvcr.io/nvidia/nemo-rl:v0.7.0}
GYM=/opt/nemo-rl/3rdparty/Gym-workspace/Gym
OWNER="$(id -u):$(id -g)"

exec docker run --rm --name "${BRL_CONTAINER_NAME:-brl-nemo}" \
    --device nvidia.com/gpu=all --network host --ipc host \
    --ulimit memlock=-1 --ulimit stack=67108864 \
    -v "$ROOT:$ROOT" \
    -v "$ROOT/gym_env/blender_scene:$GYM/resources_servers/blender_scene" \
    -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
    -v "$ROOT/.cache/gym_venvs:/opt/gym_venvs" \
    -e PYTHONUNBUFFERED=1 -e BLENDER_LORA_ROOT="$ROOT" \
    -e NCCL_BUFFSIZE=1048576 -e NCCL_MAX_NCHANNELS=2 -e NCCL_NVLS_ENABLE=0 -e NCCL_CUMEM_ENABLE=0 \
    -w /opt/nemo-rl "$IMAGE" \
    bash -lc "$1; rc=\$?; chown -R $OWNER $ROOT/runs $ROOT/gym_env $ROOT/logs $ROOT/.cache 2>/dev/null; exit \$rc"
