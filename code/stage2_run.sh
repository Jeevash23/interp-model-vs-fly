#!/usr/bin/env bash
# Run one stage-2 simulation phase on the local GPU under the portfolio GPU lock, with a write audit of AI-06.
#   systemd-run --user --collect -p Nice=10 -p WorkingDirectory=<AI-11>/code --unit=ai11-stage2-<phase> code/stage2_run.sh <phase>
# phase: replay | development | confirmation
set -euo pipefail
phase="$1"
cd "$(dirname "$0")"
study="$(cd .. && pwd)"
ai06="$(cd ../reference/flyvis-first-order && pwd)"  # release: the reference study's files
python="${PYTHON:-$study/.venv/bin/python}"  # release: the release environment
lock="$study/code/gpu_lock.py"  # release: a copy of the companion study's lock helper
touch "$study/${GPU_LOCK:-gpu.lock}"
logs="$study/results/stage2/logs"
mkdir -p "$logs"
free_gib=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
if [ "$free_gib" -lt 5 ]; then echo "less than 5 GiB free; not starting"; exit 1; fi
marker="$logs/audit-$phase.marker"
touch "$marker"
sleep 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
"$python" -B "$lock" "$python" -B stage2_simulate.py "$phase" 2>&1 | tee "$logs/$phase.log"
changed=$(find "$ai06" -path "$ai06/03-Data/flyvis-root" -prune -o -newer "$marker" -print 2>/dev/null | wc -l)  # release: flyvis-root skipped
printf '{"phase": "%s", "finished": "%s", "files_changed_under_AI06": %s}\n' "$phase" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$changed" > "$logs/audit-$phase.json"
echo "write audit: $changed files changed under AI-06"
[ "$changed" -eq 0 ]
