# Silencing in the FlyVis models matches fly experiments for Mi1 and Mi9 but not for the OFF-pathway inputs

Code and results for the preprint *Silencing in the FlyVis models matches fly experiments for Mi1 and Mi9 but not for the OFF-pathway inputs*, by Richard Jeevash (link to be added when it is posted).

This repository holds the code, frozen inputs, study records and saved outputs behind it; the saved outputs and the
frozen protocols are attached to its v1.0 release (see [Release files](#release-files)). Every number and generated
table in the manuscript can be recomputed from the saved outputs on a CPU in about a minute, without a model or
network, and the study's merge, scoring and independent rechecks are rerun from the saved inputs and compared with
the saved outputs byte for byte.

## Release files

The saved outputs and the frozen protocols are not in this repository's files; they are attached to its v1.0 release:

| File | Size | Contents |
|---|---|---|
| `per-run-outputs.tar.gz` | 22.5 MB | The saved outputs: the 2 compressed archives in `data/saved-outputs/`, which `make unpack` places in the study folders and checks file by file |
| `frozen-protocols.tar.gz` | 142 kB | The studies' protocols, predictions, amendments, approvals and freeze records (17 files), at their places in the folder, where the checks read them |
| `SHA256SUMS` | | Checksums of the two archives |

Download the three files into an empty folder, check them there, and unpack them into this one:

```sh
sha256sum -c SHA256SUMS
tar -xzf per-run-outputs.tar.gz -C /path/to/interp-model-vs-fly
tar -xzf frozen-protocols.tar.gz -C /path/to/interp-model-vs-fly
```

After unpacking, `sha256sum -c SHA256SUMS` in this folder checks every file that its `SHA256SUMS` lists, the
unpacked attachments included, and the checks below run as described.

## What the paper asks

Connectome-constrained models of the fly visual system can predict what happens when a cell type is silenced. This
study asks whether exact silencing in the 50 released FlyVis models reproduces what genetic silencing did in flies,
in three studies that silenced inputs of the motion detectors T4 and T5 and recorded motion responses: Ammer et al.
2015 (Mi1 and Tm3), Serbe et al. 2016 (Tm1, Tm2, Tm4 and Tm9) and Strother et al. 2017 (Mi1, Tm3, Mi4 and Mi9). Each
published finding's category (abolished, reduced, unchanged or increased) is compared with the category of exact
silencing in the models, read through the lobula plate layers that drive the recorded cells. Secondary scores test
Serbe's order of the four OFF inputs, Tm3's speed dependence, a first-order estimate and a connectivity baseline.

## The study

Stage 1 (`PROTOCOL.md`):

- **Plan.** The draft protocol, as approved (`PROTOCOL-DRAFT.md`, `AUTHOR-APPROVAL.txt`), and the working protocol.
- **Predictions.** `PREDICTIONS.md` was hashed with the protocol in `PREDICTIONS-RECORD.json` (05:18:18 UTC on 18
  October 2026), before any quantity was computed on any model. Development on the four development models
  (`DEVELOPMENT-NOTES.md`) fixed the settings and led to a development-informed addendum (`PREDICTIONS-ADDENDUM.md`
  and its record).
- **Extraction.** Two extractors worked blind to the models, the protocol and the predictions, from the source
  documents alone (`extraction/EXTRACTION-RULES.md`, `extraction/A`, `extraction/B`). Their tables were merged into
  findings under the rules of `AMENDMENTS.md` (Amendment 1), and every disagreement was settled against the source text
  (`extraction/MERGE-DECISIONS.md`, `extraction/merge-work/`, `extraction/merged-table.csv`).
- **Freeze and scoring.** The merged table, code, settings and inputs were hashed in `FREEZE.json` (05:55:15 UTC) and
  `FREEZE-BASELINES.json`, and only then were the 46 confirmation models scored and rechecked by an independent script
  that uses Python's standard library only.

Stage 2 (`STAGE2-PROTOCOL.md`, planned and hashed in `STAGE2-RECORD.json` after stage 1 was complete):

- **Pairs.** Serbe's six pairs of Tm cells were silenced together in the 46 confirmation models, at half and full
  strength, with the reference study's simulator (1,104 records).
- **The supplement.** The same two extractors extracted Strother et al.'s supplementary figures, and their tables were
  merged by the same rules (`extraction/stage2/`).
- **Freezes.** Both were frozen before scoring (`FREEZE-STAGE2.json`, `FREEZE-STAGE2-STROTHER.json`), and the stage-2
  predictions (`STAGE2-PREDICTIONS.md`) were scored after. `STAGE2-AMENDMENTS.md` records the changes made during
  stage 2, including a deviation from blinding in the supplement extraction (S3).

The freezes are local hash records written by the study code, not public preregistrations. Times in the records are
UTC.

## What is in this folder

| Path | Contents |
|---|---|
| `PROTOCOL*.md`, `PREDICTIONS*`, `AUTHOR-APPROVAL.txt`, `DEVELOPMENT-NOTES.md`, `AMENDMENTS.md`, `STAGE2-*`, `FREEZE*.json`, `config.json` | The study records (above) and the configuration |
| `code/` | Matching and scoring (`common.py`, `score.py`), development (`develop.py`), the merge (`units.py`, `merge_findings.py`), freeze records (`freeze.py`), prediction scoring, unit tests, the independent recheck (`recheck.py`), and stage 2: the simulator and its run script, scoring, the supplement's merge and scoring, the integrity check, the freezes and the recheck |
| `extraction/` | The extraction rules, both extractions with their seals, the merge work and the merged tables of both stages |
| `results/` | After `make unpack`: development, confirmation and stage-2 outputs, including the 1,200 pair-silencing records (without their time traces) |
| `reference/flyvis-first-order/` | The files of the reference study that the study reads or imports (see its README) |
| `paper/make_numbers.py`, `paper/generated/` | Every macro and generated table of the manuscript, from the saved outputs, and what the manuscript was built with |
| `sources/README.md` | Citations, sizes and SHA-256 of the four source documents, which are not included |
| `provenance/Makefile-at-freeze` | The study's own Makefile, which the freeze lists (this release's Makefile replaces it) |
| `data/saved-outputs/` | Saved outputs as compressed archives (see its README) (attached to the release: `per-run-outputs.tar.gz`) |
| `tools/` | Unpacking, freeze checking, the replay of the study's steps and the comparison of re-simulated records |
| `requirements.txt`, `ENVIRONMENT.md` | The exact environment, and how to obtain the FlyVis models |
| `RELEASE-CHANGES.md`, `release-changes.json` | Every file that differs from the original project, with the original's SHA-256, and every frozen file not shipped |

## Install

```sh
make setup        # .venv with CPython 3.12.14 and the 102 pinned packages (see ENVIRONMENT.md)
```

This downloads the packages in `requirements.txt`, including PyTorch's CUDA 12.4 build and its CUDA libraries (several
GB). The quick check and the unit tests need only NumPy and SciPy; `ENVIRONMENT.md` gives a small route. Pass
`PYTHON=/path/to/python` to any `make` target to use another environment.

## Quick check (CPU, about a minute, no model, no network)

First unpack the two release attachments into this folder (see [Release files](#release-files)): the checks read
the saved outputs and the freeze records they contain.

```sh
make quick-check
```

It unpacks the saved outputs (checking every SHA-256), then:

1. checks every freeze record against this folder (`tools/check_freezes.py`): each frozen file is unchanged, changed
   for the release in a documented way (`RELEASE-CHANGES.md`), or documented as not shipped;
2. recomputes every macro and generated table of the manuscript from the saved outputs and compares them with
   `paper/generated/` (`paper/make_numbers.py --check`);
3. reruns, in a temporary copy, the merge of both stages, the scoring of stage 1 (development and confirmation) and of
   stage 2 (pairs and supplement), the confirmation predictions of both stages and every independent recheck, and
   compares each output with the saved file byte for byte (`tools/replay_analyses.py`).

Expected output (abridged):

```
2536 unpacked
PREDICTIONS-RECORD.json: 6 files: 5 changed for the release (documented), 1 unchanged
PREDICTIONS-RECORD.json: 3 files: 3 not shipped (documented)
PREDICTIONS-RECORD.json: 4 files: 1 not shipped (documented), 3 unchanged
FREEZE.json: 39 files: 12 changed for the release (documented), 27 unchanged
FREEZE.json: 3 files: 3 unchanged
FREEZE.json: 3 files: 3 not shipped (documented)
FREEZE-BASELINES.json: 104 files: 104 unchanged
STAGE2-RECORD.json: 5 files: 1 changed for the release (documented), 1 not shipped (documented), 3 unchanged
FREEZE-STAGE2.json: 26 files: 12 changed for the release (documented), 4 not shipped (documented), 10 unchanged
FREEZE-STAGE2.json: 2208 files: 1104 changed for the release (documented), 1104 unchanged
FREEZE-STAGE2-STROTHER.json: 29 files: 7 changed for the release (documented), 1 not shipped (documented), 21 unchanged
total: 1141 changed for the release (documented), 13 not shipped (documented), 1276 unchanged
paper/make_numbers.py --check: every macro and table matches
identical  extraction/merge-work/units-A.csv  (units.py)
identical  extraction/merge-work/units-B.csv  (units.py)
identical  extraction/merge-work/findings-A.csv  (units.py)
...
identical  results/stage2/strother/results/confirmation/recheck.json  (stage2_strother.py recheck <table>)
identical  results/stage2/strother/results/confirmation/recheck-report.json  (stage2_recheck.py strother)
18 steps rerun from the saved inputs: every output identical to the shipped file
```

## Other targets

```sh
make test         # the study's unit tests (toy tables and the development set; seconds)
make numbers      # rewrite paper/generated/
```

`make test` reruns the development scoring as part of its tests, which rewrites `results/development/comparisons.csv`,
`per-model.csv` and `summary.json` with identical contents.

## What needs more than this folder

- **The source documents.** The extraction itself was done by reading them, and `code/stage2_s3h_markers.py` reads the
  markers of Fig. S3H from the supplement's vector paths (with poppler's `pdftocairo`). They are not included
  (`sources/README.md` cites them); the extractions and `extraction/stage2/merge-work/s3h-markers.csv` are.
- **The reference study's earlier response arrays.** The development checks (`make development` in the study's own
  Makefile, `code/develop.py`) and the replay phase of the stage-2 simulation compare with the reference study's
  stage-1 response arrays at other speeds, which neither release includes. Their results are saved and frozen
  (`results/development/dev-checks.json`, `settings.json`; `results/stage2/replay-check.json`).
- **The FlyVis models.** The stage-2 simulation runs the reference study's simulator on the released models:

  ```sh
  make flyvis-models                                         # the 50 released models, from the FlyVis authors
  make stage2-rerun COPY=../rerun-dev PHASE=development      # 4 models; then PHASE=confirmation for the 46
  ```

  `make stage2-rerun` copies this folder (without the phase's saved records), simulates the phase again and compares
  every new record with the saved one (`tools/compare_stage2_records.py`): the peak responses must agree within the
  study's tolerance of 1e-4 of the largest peak. The study ran it on one 6 GB NVIDIA GPU (CUDA 12.4)
  through the GPU lock helper, at about 37 s per model: about 2.5 minutes for the development models and 29 minutes
  for the 46 confirmation models. `DEVICE=cpu` runs it on the CPU instead (much slower; not timed). The confirmation
  phase is gated by the recorded replay check, which this release's simulator accepts (`RELEASE-CHANGES.md`).
  Re-simulated records are not bit-identical to the saved ones on other hardware; the scores are computed from the
  saved records.

## Tables

| Manuscript | Source |
|---|---|
| All numbers in the text | macros in `paper/generated/numbers.tex`, written by `paper/make_numbers.py` |
| Table 1 (agreement by source and by measure) | `paper/generated/table-sources.tex` |
| Table 2 (comparisons by silenced type and pathway) | `paper/generated/table-types.tex` |
| Table 3 (second stage: pair silencing) | `paper/generated/table-stage2-pairs.tex` |
| Table 4 (appendix: all primary comparisons) | `paper/generated/table-comparisons.tex` |
| Tables 5 and 6 (appendix: predictions of the first and second stage, with verdicts) | `paper/generated/table-predictions.tex`, `table-stage2-predictions.tex` |

The manuscript has no figures.

## What is not included

- The source documents (copyright; `sources/README.md` gives their citations and SHA-256).
- The time traces of the stage-2 pair-silencing records (173 MB for the confirmation models) and the replay check's
  records; every other array of each record is included, and the scores, the rechecks and the integrity check's
  report are saved.
- The FlyVis models and the files the flyvis package builds (`make flyvis-models`), and the reference study's other
  files (its own release holds them).
- The study's written report of results (the manuscript reports them), the manuscript and its source, the run logs,
  review notes and the original project's other provenance records. Frozen files not shipped are listed with their
  digests in `RELEASE-CHANGES.md`.

## Licence

MIT (`LICENSE`), covering the code and the studies' records and saved outputs. The FlyVis connectome file under `reference/` is part of the flyvis
package and keeps its MIT licence (included next to it); the FlyVis models and package are distributed under their own
licences.

## Study codes

The records and code name the studies by the codes they had while the work was done. Each code that occurs here,
and where that study is released:

| Code | Released in |
|---|---|
| AI-06 | `interp-flyvis-first-order` |
| AI-09 | `interp-flyvis-first-order` |
| AI-11 | this repository |

## Use of AI assistants

As the preprint states:

> Language-model assistants (Claude, Anthropic; Codex, OpenAI) were used throughout this work, under the author's
> direction, to help design the studies, to write and run the code for the experiments and analyses, to draft and
> revise the text and to check the references against their online records. All reported results come from the
> saved study outputs, and the numbers in the text were generated from those outputs or checked against them.

In the working records shipped here, the names of software tools were replaced by placeholders such as
`[redacted]`; the assistants used are the ones named above.

## Citation

Please cite the preprint (the link will be added here when it is posted) and, for the code and results, this
repository; [CITATION.cff](CITATION.cff) has the details.

```bibtex
@software{interp_model_vs_fly_2026,
  author  = {Jeevash, Richard},
  title   = {{Silencing in the FlyVis models matches fly experiments for Mi1 and Mi9 but not for the OFF-pathway inputs: code and results}},
  year    = {2026},
  version = {1.0.0},
  url     = {https://github.com/Jeevash23/interp-model-vs-fly}
}
```
