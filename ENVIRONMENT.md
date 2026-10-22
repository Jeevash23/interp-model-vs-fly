# Environment

The study ran in the reference study's Python environment: CPython 3.12.14 with flyvis 1.2.0, PyTorch 2.5.1 and
torchvision 0.20.1 (CUDA 12.4 builds), NumPy 1.26.4 and SciPy 1.17.1, 102 packages in all; `requirements.txt` pins
every one of them. Every script ran with `python -B`; the independent rechecks and the marker reader ran in Python's
isolated mode with the standard library only (`python3 -I`).

## A fresh install

```sh
make setup
```

creates `.venv` with uv's managed CPython 3.12.14, installs the pinned packages from PyPI and then PyTorch and
torchvision from PyTorch's CUDA 12.4 index (`https://download.pytorch.org/whl/cu124`), all without dependency
resolution, so the environment is exactly the recorded one. It includes PyTorch's CUDA libraries (several GB).

## A smaller environment

The quick check and the unit tests need only NumPy and SciPy:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv numpy==1.26.4 scipy==1.17.1
```

The scorers' permutation tests draw from NumPy's random generator with a fixed seed, so the byte-for-byte comparison
of the quick check expects NumPy 1.26.4.

## The FlyVis models and the GPU

Only the stage-2 simulation (`make stage2-rerun`) uses them. It runs the reference study's simulator
(`reference/flyvis-first-order/02-Code/stage1/core.py`) on the 50 released FlyVis models (Lappalainen et al., 2024),
which flyvis reads from the folder named by `FLYVIS_ROOT_DIR`; the simulator sets it to
`reference/flyvis-first-order/03-Data/flyvis-root/`. `make flyvis-models` downloads the released archive there with
flyvis's own command (`flyvis download-pretrained`); flyvis builds its connectome tables and stimulus renderings in the
same folder on first use. `reference/flyvis-first-order/03-Data/stage1/model-selection.json` holds the SHA-256 of
every checkpoint, and the simulator refuses a checkpoint whose digest differs.

The simulator uses the GPU when it runs under `code/gpu_lock.py` (as `code/stage2_run.sh` runs it), which takes a lock
file named by `GPU_LOCK` and needs `nvidia-smi` and at least 4 GB of free GPU memory; otherwise it runs on the CPU. The
study ran on one 6 GB NVIDIA GPU with CUDA 12.4.
