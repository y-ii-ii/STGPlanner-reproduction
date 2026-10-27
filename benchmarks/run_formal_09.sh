#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
python3 "$root/codex/work/prepare_formal_09.py"
exec python3 "$root/codex/work/run_formal_trial.py" --name repair_formal_gbp2_09
