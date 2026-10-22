"""Run a worker while holding a GPU advisory lock; refuse if the GPU is busy.

    python gpu_lock.py <python> -B stage2_simulate.py <phase>      (code/stage2_run.sh runs it this way)

A copy, for this release, of the lock helper of the companion study (released separately), which stage2_run.sh ran
from that study's folder. The lock file is named by GPU_LOCK (default gpu.lock in the release root; stage2_run.sh
creates it). The simulator uses the GPU only when it runs under this helper, which sets AI09_GPU_LOCK_FD; otherwise it
runs on the CPU.
"""
import fcntl
import os
from pathlib import Path
import subprocess
import sys

LOCK = Path(__file__).resolve().parents[1] / os.environ.get("GPU_LOCK", "gpu.lock")

handle = open(LOCK, "rb")
fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
os.set_inheritable(handle.fileno(), True)
query = subprocess.run(["nvidia-smi", "--query-gpu=memory.free,memory.used,temperature.gpu",
                        "--format=csv,noheader,nounits"], capture_output=True, text=True, check=True)
if int(query.stdout.split(",")[0]) < 4096:
    raise SystemExit("GPU memory is in use by another process; not starting")
print("GPU lock acquired; free/used MiB and temperature:", query.stdout.strip(), flush=True)
os.environ["AI09_GPU_LOCK_FD"] = str(handle.fileno())
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.execv(sys.argv[1], sys.argv[1:])
