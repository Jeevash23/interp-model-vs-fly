# Silencing in the FlyVis models compared with genetic silencing in flies: code release.
# `make help` lists the targets. PYTHON defaults to the environment that `make setup` creates. The study's own
# Makefile, part of its freeze, is kept as provenance/Makefile-at-freeze.
PYTHON ?= .venv/bin/python
PY := $(if $(findstring /,$(PYTHON)),$(abspath $(PYTHON)),$(PYTHON))
CPU := CUDA_VISIBLE_DEVICES= $(PY)
DEVICE ?= cuda
FLYVIS_ROOT := reference/flyvis-first-order/03-Data/flyvis-root
export PYTHONDONTWRITEBYTECODE := 1
export OMP_NUM_THREADS ?= 2
export OPENBLAS_NUM_THREADS ?= 2
export MKL_NUM_THREADS ?= 2
.NOTPARALLEL:

.PHONY: help setup python-check unpack check-freezes quick-check test numbers flyvis-models stage2-rerun

help:
	@echo "make setup          create .venv with the recorded environment (downloads packages, see ENVIRONMENT.md)"
	@echo "make quick-check    CPU, about a minute, no model and no network: every freeze record, every number and"
	@echo "                    table of the manuscript, and the merge, scoring, prediction and recheck steps of both"
	@echo "                    stages rerun from the saved inputs and compared with the saved outputs"
	@echo "make test           the study's unit tests (toy tables and the development set; NumPy and SciPy)"
	@echo "make numbers        rewrite paper/generated/ from the saved outputs"
	@echo "make flyvis-models  download the released FlyVis models (for the stage-2 simulation; needs network access)"
	@echo "make stage2-rerun   simulate the pair silencing again in a copy and compare it with the saved records:"
	@echo "                    COPY=<new folder> PHASE=development|confirmation [DEVICE=cpu]"

setup:
	uv venv --python 3.12.14 .venv
	grep -v -E '^(torch|torchvision)==' requirements.txt > .venv/requirements-pypi.txt
	uv pip install --python .venv/bin/python -r .venv/requirements-pypi.txt --no-deps
	uv pip install --python .venv/bin/python --no-deps --index-url https://download.pytorch.org/whl/cu124 \
	  'torch==2.5.1+cu124' 'torchvision==0.20.1+cu124'

python-check:
	@$(PY) -c "import numpy, scipy" 2>/dev/null || { echo "No usable Python at $(PYTHON): run make setup, or set PYTHON=..."; exit 1; }

unpack: python-check
	$(PY) tools/unpack.py

check-freezes: unpack
	$(PY) tools/check_freezes.py

quick-check: unpack
	$(CPU) tools/check_freezes.py
	$(CPU) -B paper/make_numbers.py --check && echo "paper/make_numbers.py --check: every macro and table matches"
	$(CPU) tools/replay_analyses.py

test: unpack
	cd code && $(CPU) -B test_ai11.py

numbers: unpack
	$(PY) -B paper/make_numbers.py

# The released checkpoints of the 50 models (the FlyVis authors' archive); flyvis builds its connectome tables and
# stimulus renderings in the same folder on first use. The reference study's code points FLYVIS_ROOT_DIR there.
flyvis-models: python-check
	mkdir -p $(FLYVIS_ROOT)
	FLYVIS_ROOT_DIR=$(CURDIR)/$(FLYVIS_ROOT) $(dir $(PY))flyvis download-pretrained

# The simulator keeps valid records and writes the rest, so it runs in a fresh copy of the release without the phase's
# saved records; the FlyVis models are linked into the copy. With DEVICE=cuda it runs through code/stage2_run.sh
# (GPU lock, write audit); with DEVICE=cpu it runs the simulator directly on the CPU.
stage2-rerun: unpack
	@test -n "$(COPY)" || { echo "usage: make stage2-rerun COPY=<new folder> PHASE=development|confirmation [DEVICE=cpu]"; exit 1; }
	@case "$(PHASE)" in development|confirmation) ;; *) echo "PHASE must be development or confirmation"; exit 1;; esac
	@test ! -e "$(COPY)" || { echo "$(COPY) exists"; exit 1; }
	@test -d $(FLYVIS_ROOT)/results || { echo "the FlyVis models are missing: run make flyvis-models first"; exit 1; }
	mkdir -p "$(COPY)"
	tar --exclude=./data --exclude='./.venv*' --exclude=./$(FLYVIS_ROOT) --exclude=./results/stage2/$(PHASE) \
	  -cf - . | tar -xf - -C "$(COPY)"
	ln -s $(CURDIR)/$(FLYVIS_ROOT) "$(COPY)/$(FLYVIS_ROOT)"
	if [ "$(DEVICE)" = cpu ]; then cd "$(COPY)/code" && $(CPU) -B stage2_simulate.py $(PHASE); \
	else cd "$(COPY)/code" && PYTHON=$(PY) ./stage2_run.sh $(PHASE); fi
	$(PY) tools/compare_stage2_records.py "$(COPY)" $(PHASE)
