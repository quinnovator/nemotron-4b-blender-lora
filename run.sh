#!/usr/bin/env bash
# Launch a run inside tmux with crash retries:  ./run.sh configs/nemotron4b.yaml
set -u
cfg="${1:?config path}"; shift
name="brl-$(basename "$cfg" .yaml)"
cd "$(dirname "$0")"
if [ -z "${TMUX:-}" ] && [ "${BRL_NO_TMUX:-0}" != 1 ]; then
  exec tmux new-session -d -s "$name" "BRL_NO_TMUX=1 $0 $cfg $*; exec bash"
fi
for i in 1 2 3; do
  .venv/bin/python orchestrate.py "$cfg" "$@"; rc=$?
  [ $rc -eq 0 ] || [ $rc -eq 3 ] && exit $rc
  echo "orchestrate crashed (rc=$rc), retry $i in 120 s"; sleep 120
done
