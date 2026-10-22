# AI-11: merging the two blind extractions

**Who and when.** This merge was done by the scoring session on 18 October 2026, after the coordinating session reported both extractions finished and sealed. The extraction folders were opened at 05:41 UTC. The rules are those of `AMENDMENTS.md`, Amendment 1, written before any agreement was computed. Agreement was first computed at 05:47:18 UTC, and the merged table was written at 05:50:22 UTC. No confirmation-model summary existed at any point of this merge.

**Inputs.** Both `SHA256SUMS` files match their tables and notes:

| Extractor | Rows | Of which Strother | `table.csv` SHA-256 | `notes.md` SHA-256 |
|---|---|---|---|---|
| A | 461 | 187 | `288ed7b9…11ad` | `fcb7dc1b…6e43` |
| B | 298 | 105 | `fc7c846e…3932` | `f6246b12…a98a3` |

**Scripts.**
- `code/units.py` expands both tables into elementary units and findings, and computes agreement. Its outputs go in `merge-work/`:
  - `units-A.csv`, `units-B.csv`;
  - `findings-A.csv`, `findings-B.csv`;
  - `unit-comparison.csv`, `finding-comparison.csv`;
  - `agreement.json`.
- `code/merge_findings.py` builds `merged-table.csv` from the findings and `merge-work/settlements.json`. It stops on any difference that has no settlement.

## 1. Why the raw rows cannot be compared one to one
The two extractors read the same experiments but wrote them down at different granularity:
- A wrote one row per tested speed and per driver line.
- B wrote one row per speed only where results differed between speeds, and otherwise one row covering "each of n speeds".
- B pooled Ammer's three Tm3 driver lines in behaviour.
- B wrote Serbe's grating statement as PD and ND rows, where A wrote it as one row per genotype.

So agreement is reported on elementary units, which are rows expanded to one speed and one driver line, and on findings, which pool speeds within a model-speed bin and pool driver lines (Amendment 1.2). Before comparison, the opposing-edge behaviour categories were put on one convention, using A's own stated signs (Amendment 1.3).

## 2. Agreement between the extractors
| Level | A | B | Matched | A only | B only | Amplitude: agree | Amplitude κ | DS: agree | DS κ |
|---|---|---|---|---|---|---|---|---|---|
| Elementary units | 461 | 456 | 430 | 31 | 26 | 427 of 430 (99.3%) | 0.987 | 358 of 430 (83.3%) | 0.044 |
| Findings | 189 | 196 | 176 | 13 | 20 | 173 of 176 (98.3%) | 0.970 | 168 of 176 (95.5%) | 0.320 |

κ uses six labels: the four categories, `not_reported`, and `mixed` for a tied finding.

**Specific agreement per amplitude category, findings level.** This is 2·both / (A + B):

| Category | A | B | Both | Specific agreement |
|---|---|---|---|---|
| abolished | 8 | 8 | 8 | 1.00 |
| reduced | 68 | 69 | 67 | 0.98 |
| unchanged | 93 | 91 | 91 | 0.99 |
| increased | 3 | 3 | 3 | 1.00 |
| not_reported | 2 | 2 | 2 | 1.00 |
| mixed | 2 | 3 | 2 | 0.80 |

Unit-level values are in `merge-work/agreement.json`.

**The amplitude disagreements.** There are three at the unit level and three at the findings level, all settled below:
- Ammer's contrast series for Mi1 with OFF edges: A coded `reduced`; B split it and the finding is `mixed`.
- Serbe's Tm1+Tm4 pair, PD and ND rows of Fig. S4: A coded `unchanged`; B coded `reduced`.

**The direction-selectivity disagreements** come from one source. A attached the authors' statement that the directional tuning of OFF responses was unaffected (Ammer, Figs. 2–3) to every OFF row of those figures: 72 units, 8 findings. B did not code it.

**Coverage differences** are all granularity, not disputes:
- Ammer's Tm3 behaviour lines against B's pooled row: these match at the findings level.
- Serbe's grating statement written per genotype against per PD and ND.
- Three Fig. 7C behaviour rows (Tm1, Tm4, Tm9) that only A recorded.

## 3. Settlements (each against the source text; details and reasons in `merge-work/settlements.json`)
| Finding | A | B | Settled | Basis |
|---|---|---|---|---|
| Ammer contrast series (Fig. 1G), Mi1, OFF | reduced | mixed | reduced, low contrast only | One significance mark, at a low contrast; the text describes a minor reduction at low contrast (PDF p. 47). Excluded from scoring as a contrast series. |
| Ammer Figs. 2–3, OFF rows (8 findings): direction selectivity | unchanged | not reported | not reported on these rows | The text's statement (PDF p. 48) is one claim per genotype. It is recorded once per genotype as two added direction-selectivity findings (M017, M018), unchanged, no test. |
| Serbe Fig. S4, Tm1+Tm4, OFF, PD and ND | unchanged | reduced | unchanged | The pair's PD-minus-ND test (Fig. 6D) has no significance mark, unlike the other five pairs. The text says "intermediate reduction" (PDF p. 32). The rules follow the authors' tests where given. It is a pair, so it is excluded from scoring. |
| Serbe Fig. S5 gratings (10 genotypes) | one row each, direction both | PD and ND rows | one finding each, direction both | The statement (mildly reduced, like OFF edges; PDF p. 32) is collective and carries no test. It is counted once per genotype. All categories agree. |
| Serbe Fig. 7C, Tm1, Tm4, Tm9 (behaviour) | reduced (after sign harmonisation) | not recorded | included | The text says these blocks differed from control in a roughly constant way across velocities (PDF p. 34); no test. One shibire copy, so secondary and at half strength. |
| Strother Fig. 4B, Mi1 and Tm3, fast bin (behaviour) | mixed | mixed | unchanged | Significant at 90 and 270°/s but not at 180 or 810°/s, a tie. The text says single blocks had very little effect on turning to gratings (PDF p. 8). Secondary. |

The other 163 matched findings agreed on both categories and were taken as they stood. The 28 findings that carry a settlement break down as follows:
- 3 amplitude disagreements;
- 8 direction-selectivity disagreements;
- 2 findings that both extractors coded as mixed;
- 13 findings recorded by A only: 10 grating findings and 3 Fig. 7C findings;
- 2 added direction-selectivity findings.

The 20 PD and ND grating findings recorded by B only are covered by A's 10 per-genotype grating findings.

## 4. Comparison with the 2 October key (third reference)
| Key row | Key | Merged table | Same? |
|---|---|---|---|
| B01, Ammer Fig. 2: Mi1, ON, PD, all speeds | strongly reduced, not total abolition | M011 (slow) and M012 (fast) reduced. Both extractors read no significance mark at 700°/s, inside the fast bin; no row is abolished. | yes |
| B02, Ammer Fig. 2: Tm3, ON, PD, 12.5 against 300°/s | slow kept, fast reduced | M015 (6.25–50°/s) unchanged, M016 (75–900°/s) reduced | yes |
| B03, Serbe Fig. 5: Tm1, Tm2, Tm4, Tm9, OFF, PD minus ND | 53.98, 39.22, 70.59 and 25.69% remaining | M031, M033, M035, M037 reduced, with the same printed values | yes |
| B04, Serbe Fig. 6: pairs with one shibire copy | pairs generally increase OFF impairment | Five of six pairs reduced; Tm1+Tm4 unchanged (no significance mark) | yes ("generally") |

The key agrees with the merged table on every row it covers. The merged table adds:
- the null-direction and OFF-edge results of Ammer;
- Serbe's PD and ND statements and the one-copy single blocks;
- all of Strother.

## 5. The merged table
`merged-table.csv` holds 191 findings, row IDs M001–M191. Each records:
- its experiment code, genotype, readout, polarity, direction and speeds;
- its amplitude and direction-selectivity categories and any printed value;
- its role and strength class;
- the contributing rows of A and B, and how it was settled.

| Role | Ammer | Serbe | Strother | All |
|---|---|---|---|---|
| primary | 22 | 28 | 18 | 68 |
| partial (one-copy singles, score g) | 0 | 8 | 0 | 8 |
| behaviour (score h) | 4 | 9 | 36 | 49 |
| pair (excluded) | 0 | 49 | 0 | 49 |
| excluded (T4 with T5; contrast series) | 4 | 0 | 13 | 17 |

**The primary findings.**
- **Categories:** 30 reduced, 34 unchanged, 4 direction-selectivity only (unchanged). None is abolished or increased.
- **Basis:**
  - 42 rest on the authors' significance tests: Ammer 18, Serbe 8, Strother 16.
  - 26 rest on statements without a test: Serbe 20 (the S4 PD/ND and S5 grating rows), Ammer 4 (Fig. 1E–F traces), Strother 2 (direction selectivity).
- **Model counterparts:** four primary findings have none. They are T4 calcium with OFF edges (M125, M127, M129, M133), which the scorer reports as unmatched.

## 6. Not extractable: Strother's supplement
The available Strother PDF has no supplemental figures or tables (Amendment 1.5). The T4 calcium responses to 30°/s edges after silencing Mi1, Tm3, Mi4 or Mi9 (Fig. S2B) are primary-type findings that only the supplement resolves, so they are not in the table. The coordinating session has been told. If the author fetches the supplement, they can be added as a second stage, frozen before they are scored.
