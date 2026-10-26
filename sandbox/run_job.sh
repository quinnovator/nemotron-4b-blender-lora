#!/bin/sh
# Two-phase episode. Phase 1 runs the agent's code and saves the scene to tmpfs.
# Phase 2 is a fresh Blender that runs only trusted code, so nothing the agent
# does in phase 1 (exiting early, pre-writing state.json, patching bpy) can
# reach the extractor's output.
set -e
T="${1:-20}"
rm -f /job/state.json
timeout -s KILL "$T" blender --background --factory-startup --disable-autoexec \
    /opt/base_empty.blend --python-exit-code 1 \
    --python /job/agent.py --python /opt/save_scene.py -- /tmp/out.blend
rm -f /job/state.json
timeout -s KILL 15 blender --background --factory-startup --disable-autoexec \
    /tmp/out.blend --python-exit-code 1 \
    --python /opt/extract_scene.py -- /job/state.json
