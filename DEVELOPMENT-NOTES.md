# AI-11 development notes

**Scope.** These notes record development on the four development models (000, 001, 004 and 005), done on 18 October 2026 between 05:20 and 05:30 UTC, after the predictions were hashed (`PREDICTIONS-RECORD.json`, 05:18:18 UTC). The stand-in experimental table is `code/standin_table.csv`, made from rows B01–B04 of AI-06's 2 October key. Nothing was computed for the 46 confirmation models. The scoring code refuses them until `FREEZE.json` exists, and a test checks that.

**Commands.**
- `make development` runs `code/develop.py`, then `code/score.py development`.
- `make test` runs `code/test_ai11.py`.
- `python3 -I code/recheck.py development` runs the recheck.

**Outputs.**
- `results/development/dev-checks.json` has every number below.
- `results/development/settings.json` has the settings frozen for confirmation.
- `results/development/summary.json`, `comparisons.csv`, `per-model.csv` and `recheck.json` hold the development scoring.

## Settings decided by the protocol's rules (Section 6)

| Setting | Rule | Development evidence | Result |
|---|---|---|---|
| δ | stays 0.2 unless more than 25% of (row, model) values lie within ±0.05 of 0.8 or 1.2 | 3.1% of 32 values (mean pooling); 15.6% on the weighted values | **0.2** |
| Pooling over subtypes | weighted if mean and weighted pooling give different categories for more than 10% of (row, model) pairs | 7 of 32 pairs (21.9%) differ | **weighted** |
| Speed mapping | log-nearest stays unless the 27.55/110.2°/s categories differ from the 12.5/300°/s categories in more than a quarter of comparisons | 2 of 16 (12.5%) differ; per subtype, 57 of 62 agree | **log-nearest** |
| Mapping by name | reported only, never changed | see below | by name |

No setting was chosen by its agreement with the stand-in table.

**Pooling.**
- **Why the mean failed.** The mean of ratios is dominated by subtypes that barely respond in the intact model.
  - In model 004, T4a's summed ON response is 0.28 at 27.55°/s, against 3.6–3.9 for T4b–d.
  - Silencing Tm3 multiplies it by 96, so the mean over T4a and T4d is 48.7, whereas the weighted value is 8.1.
  - The Serbe stand-in rows reach mean values of 14 to 386 in model 004 for the same reason.
- **The weighted rule.** It divides the summed peaks after silencing by the summed peaks before, over the mapped subtypes. This is what a cell that sums those inputs would see.
- **Weights.** They come from AI-06's saved intact records (`study/results/runs/<model>/<stimulus>/baseline.npz`, preferred-polarity peaks). These are intact responses, not silencing outcomes.
- **Direction-selectivity rows keep the mean DSI ratio (Section 5.8).** The protocol's pooling rule concerns the amplitude ratio. The DSI ratio cannot exceed 1/0.2 = 5, because subtypes with an intact DSI below 0.2 are already left out.
- **δ on the weighted values.** The δ rule was first applied to the mean-pooled values. Repeated on the weighted values, it gives the same answer: 15.6% < 25%. `develop.py` stops if the two ever disagree.

**Speed.** AI-06's stage-1 records hold Mi1 and Tm3 at 12.5 and 300°/s for the development models. Their peaks reproduce AI-06's revision ratios exactly: a largest difference of 0 over 32 shared cases. So the stage-1 ratios at the biological speeds are computed the same way as the confirmation ratios.

| Model | Tm3, 27.55°/s | Tm3, 12.5°/s | Tm3, 110.2°/s | Tm3, 300°/s |
|---|---|---|---|---|
| 000 | 0.54 | 0.49 | 0.62 | 0.76 |
| 001 | 0.16 | 0.09 | 0.23 | 0.31 |
| 004 | 8.1 | 14.5 | 1.8 | 1.2 |
| 005 | 0.97 | 0.97 | 0.96 | 0.95 |

Values are weighted ratios for the pooled preferred-direction mapping (T4a and T4d, ON edges). Mi1 gives 0 at all four speeds in all four models.
- **The two category differences** are 001 at the slow pair (0.16 reduced against 0.09 abolished) and 004 at the fast pair (1.8 increased against 1.2 unchanged).
- **Development information on Tm3's speed dependence.** In models 000 and 001, Tm3 silencing reduces slow responses more than fast ones, at the true speeds as well as at the proxies. Ammer reports the opposite for the fly.

## Readout tuning (mapping by name)
Preferred directions of the intact readouts were computed as the vector-sum angle of the preferred-polarity peaks over the 12 directions (`dev-checks.json`, `tuning`). Angles are in the stimulus's own convention.

- **Models 000 and 001 (AI-06's "upward T4c" group):**
  - T4a about 175°;
  - T4b about 350°;
  - T4c 56–84°;
  - T4d 250–274°.
- **Models 004 and 005 ("downward T4c" group):** all four T4 subtypes are turned by about 180° against 000 and 001:
  - T4a 0–3° (345° once);
  - T4b about 178°;
  - T4c 258–274°;
  - T4d 93–97°.
- **T5 subtypes:**
  - 000 matches its T4.
  - In 001, T5a and T5b are not opposite (66° apart at the slow speed).
  - 004's T5a does not respond to OFF edges, and its T5d does not respond at the fast speed.
  - 005's T5d does not respond at the fast speed.
- **Opposite pairs:** the a/b angle difference has a median of 174° (range 66–180°, 14 pairs). The c/d difference has a median of 159° (128–180°).

As the protocol says, the mapping stays by name. The amplitude ratio sums all 12 directions, so a subtype's learned tuning does not enter it. But in the turned models, the subtype mapped to a tangential cell's preferred direction prefers the opposite direction, so the PD and ND labels of tangential-cell rows are anatomical, not functional. The model metadata (`03-Data/stage1/model-selection.json`) puts 29 of the 46 confirmation models in the "upward" group, 12 in the non-selective group and 5 in the "downward" group.

## Development scoring (information only)
The stand-in table has 8 primary comparisons, all amplitude. The pair row B04 is excluded. Agreement is 1 of 8 (0.125; κ −0.22).

| Row | Key | Model (share of the 4 models) |
|---|---|---|
| Mi1, slower grid | reduced | abolished (4/4) |
| Mi1, faster grid | reduced | abolished (4/4) |
| Tm3, 12.5°/s | unchanged | reduced (2/4; 1 unchanged, 1 increased) |
| Tm3, 300°/s | reduced | reduced (2/4) |
| Tm1, OFF, PD − ND, all speeds | reduced | unchanged (4/4; median 0.92) |
| Tm2 | reduced | unchanged (3/4; median 0.82) |
| Tm4 | reduced | unchanged (4/4; median 1.02) |
| Tm9 | reduced | unchanged (tie 2/2; the median 0.83 decides) |

**Secondary scores on development.**
- **Connectivity:** 7 of 8 (it says "reduced" for every row).
- **Three-category direction agreement:** 3 of 8.
- **Serbe's order:** ρ = 0.8 (p = 4/24); all four models have ρ > 0.
- **Tm3:** the fast value is lower in 2 of 4 models.
- **Half strength:** 3 of 8.
- **δ sensitivity:** 0.1 gives 3 of 8, and 0.3 gives 1 of 8.

## Tests and checks
- **Unit tests:** `make test` passes 10 of 10. They cover the categories and their boundaries, speed matching, the readout mapping and its no-counterpart cases, per-model values (mean, abolished, DSI floor), the ensemble tie rule, κ, the Clopper–Pearson interval, exact Spearman, McNemar, the sign test, signed connectivity, development scoring, and the confirmation lock.
- **Independent recheck** (`code/recheck.py`, standard library only, sharing no code with the scorer): it reproduces every development score, 22 blocks.
- **Synthetic table.** The recheck was also run on a synthetic table in the session scratchpad: 18 rows covering T4 and T5 calcium with layers, null-direction, OFF-polarity T4, HS, VS and pooled rows, behaviour with both polarities, a partial block, a pair, CT1 and direction-selectivity rows with the first-order estimate. The scorer and the recheck agreed on all 21 blocks.
- **Planted errors.** Four errors were planted in the development outputs: a category, a count, Serbe's ρ and one model's rate. The recheck caught all four, and the outputs were then regenerated.

## Technical details fixed in code (not spelled out in the protocol)
- **Ensemble ties.** A tie between categories goes to the median value's category. If that category is not among the tied ones, the tie goes to the tied category nearest to it in the order abolished < reduced < unchanged < increased.
- **Averaging.** Within a speed, values are pooled within each polarity, then averaged over polarities. The row's value is the mean over its speeds.
- **No counterpart.** A T4 or T5 recording with edges of the other polarity has no counterpart; nor does direction selectivity measured in behaviour.
- **First-order eligibility.** The first-order estimate's DSI ratio uses the same subtypes as exact silencing, including subtypes whose response exact silencing abolished.
- **Permutation test.** It counts agreements. Permuting one rater keeps both marginals, so κ is at least the observed exactly when the agreement count is.
- **Sign test.** Models whose fast and slow values are equal are left out.

## Process note
At about 05:11 UTC, while listing `sources/`, this session also listed the empty folder `extraction/A` by mistake. It held no files. Nothing else under `extraction/A` or `extraction/B` has been opened.
