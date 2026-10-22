# Files of the reference study

The study builds on a reference study of the same 50 FlyVis models (exact and first-order silencing of each cell type,
released separately). Its scorers read that study's saved results, and its stage-2 simulation runs that study's
simulator. The files they read or import are copied here, in the reference study's own layout, and `config.json`
(`ai06_root`) points at this folder. The freeze records list them: `FREEZE.json` and `PREDICTIONS-RECORD.json` under
`ai06_inputs_sha256`, and `FREEZE-BASELINES.json`.

| File | What it is | Read by |
|---|---|---|
| `study/results/analysis/development/effects.csv`, `.../confirmation/effects.csv` | Exact silencing of every cell type in the 4 development and 46 confirmation models: amplitude ratios, changes in direction selectivity, first-order estimates and abolition, per model, stimulus, strength and T4/T5 readout | the scorers and rechecks of both stages |
| `study/results/runs/<model>/{final_slow,dev_fast}/baseline.npz` | The intact network's responses of the 50 models at the two stimuli | the weighted pooling of stage 1, the pair ratios of stage 2 and the simulator's baseline check |
| `03-Data/stage1/stimulus-dev_fast.npz`, `stimulus-final_slow.npz`, `stimulus-manifest.json` | The two moving-edge stimuli (110.2 and 27.55°/s) and their manifest | the same, and the simulator |
| `03-Data/stage1/model-selection.json`, `network-structure.json` | The 50 models with the SHA-256 of every checkpoint, and the network's cell types | the simulator |
| `02-Code/stage1/core.py`, `02-Code/stage1/common.py`, `study/code/revision_common.py`, `study/config.json` | The batched FlyVis simulator, its settings, and the helpers for paths, stimuli and readouts | the stage-2 simulation |
| `03-Data/biology-key.csv` | The reference study's key of experimental results (2 October 2026), from which `code/standin_table.csv` was made | hashed in `PREDICTIONS-RECORD.json` |
| `01-Papers/sources/flyvis/flyvis/connectome/fib25-fib19_v2.2.json`, `01-Papers/sources/flyvis/LICENSE` | The FlyVis connectome (synapse counts and signs between cell types), a data file of the flyvis 1.2.0 package identical to the one the package installs, with the package's MIT licence | the connectivity baseline of both stages |

The analysis tables, the intact-network records and the connectome are packed in
`data/saved-outputs/reference-study-results.tar.xz`, and `make unpack` restores them here. One file differs from the
reference study's copy: `02-Code/stage1/common.py` sets the `TIMEZONE` variable, which flyvis uses only for the time
stamps of its log messages, to UTC (see `RELEASE-CHANGES.md`). Rerunning the reference study's own pipeline needs
more of it (its other code and its response arrays); its own release holds them.
