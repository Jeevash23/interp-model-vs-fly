# Saved outputs

The studies' results, packed as deterministic tar archives compressed with xz. Member paths are relative to the release root, so `make unpack` (or `python tools/unpack.py`) puts every file where the study code reads it and checks each SHA-256 against `data/PACKED-FILES.json`. Text records inside the archives had personal strings replaced, as listed in `RELEASE-CHANGES.md`.

| Archive | Files | Packed (MB) | Unpacked (MB) | Contents |
|---|---|---|---|---|
| `reference-study-results.tar.xz` | 103 | 19.2 | 37.1 | the reference study's analysis tables of exact silencing (development and confirmation models), its intact-network records of the 50 models at both stimuli, and the FlyVis connectome the connectivity baseline reads |
| `study-results.tar.xz` | 2433 | 3.3 | 5.5 | the study's saved outputs: development checks and settings, the confirmation scores, per-model values, scored predictions and independent rechecks of stage 1; stage 2's run, replay and integrity records, the pair scores and the supplement's scores, report and rechecks; and the 1,200 pair-silencing records of the 4 development and 46 confirmation models, without their time traces |

Total packed size: 22.5 MB. Rendered figures are not included; `make figures` draws them from these outputs.
