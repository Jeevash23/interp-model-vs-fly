# AI-11 stage 2: merging the two blind extractions of Strother's supplement

**Who and when.** This merge was done by the scoring session on 18 October 2026, after the coordinating session reported both stage-2 extractions sealed and checked: A at 08:52:52 UTC and B at 08:55:04 UTC. The session opened the tables from about 08:58 UTC.
- **Rules:** `STAGE2-AMENDMENTS.md`, S4, written at 09:14 UTC. They apply stage 1's Amendment 1 to the supplement.
- **Order:** agreement was first computed at 09:16 UTC, and the supplement table was written at 09:20 UTC.
- **Blindness:** no supplement finding was compared with any model value during the merge. The extractors' exposure to stage 1's aggregate result is recorded in S3.

**Inputs.** Both `SHA256SUMS-stage2` files match their tables and notes:

| Extractor | Rows | `table-stage2.csv` SHA-256 | `notes-stage2.md` SHA-256 |
|---|---|---|---|
| A | 275 | `701e6f14…2f44` | `ae7994eb…f9ea` |
| B | 179 | `837595a2…eeb0` | `a1aa62d9…6ac4` |

**Scripts.**
- `code/stage2_units.py` expands both tables into elementary units and findings and computes agreement. It writes `merge-work/` (units, findings, comparisons, `agreement.json`).
- `code/stage2_s3h_markers.py` reads every marker of Fig. S3H from the PDF's vector paths. It writes `merge-work/s3h-markers.csv`.
- `code/stage2_merge.py` builds `supplement-table.csv` and `repeats.csv` from the findings and `settlements.json`. It stops on any difference without a settlement, and on any Fig. S3H unit that differs from the vector-path reading.

## 1. How the two tables differ
Both extractors read the same panels but wrote them down at different granularity.
- **Rows.** A wrote one row per tested point (speed, contrast, driver line, reset duration). B wrote one row per point only where results differed, and otherwise one row covering "each" of a list.
- **Shared conditions.** Some grating conditions belong to two protocols (S3A–B with S3C; S3A–B with S3D–E). A wrote one row naming both panels; B wrote one row per panel. Each row gives a unit in every panel it names (S4 rule 1).
- **Hidden markers.** In Fig. S3H, one line's marker covers the other's in nine places. A read them from the vector paths; B left them out.
- **100% contrast in Figs. S3A–B.** A left these points out as Fig. 4B's condition; B coded them. They are treated as repeats of a stage-1 condition (S4 rule 5).
- **Points both left out.** Fig. S3H's main-line points at 90°/s, which are the data of Fig. 3E. Neither made rows for Figs. S4B–D.

## 2. Agreement between the extractors
| Level | A | B | Matched | A only | B only | Amplitude: agree | Amplitude κ |
|---|---|---|---|---|---|---|---|
| Elementary units | 295 | 296 | 286 | 9 | 10 | 286 of 286 (100%) | 1.00 |
| Findings | 83 | 83 | 83 | 0 | 0 | 82 of 83 (98.8%) | 0.97 |

κ uses six labels, as in stage 1. Neither table reports direction selectivity, so it has no κ.
- **Coverage differences.** The 9 units only A has are the hidden S3H markers. The 10 only B has are the 100% contrast points.
- **The one disagreement.** For S3H, Tm3, OFF edges at 90–270°/s, A has unchanged and B has mixed. B's tie comes from the hidden marker it left out.
- **Mixed in both.** Three findings are ties in both extractions.

**Specific agreement per amplitude category, findings level.** This is 2·both / (A + B):

| Category | A | B | Both | Specific agreement |
|---|---|---|---|---|
| reduced | 23 | 23 | 23 | 1.00 |
| unchanged | 56 | 55 | 55 | 0.99 |
| increased | 1 | 1 | 1 | 1.00 |
| mixed | 3 | 4 | 3 | 0.86 |

## 3. Check against the PDF's vector paths
The supplement stores every marker of Fig. S3H as its own path. The reading covers all 96 line markers: 8 lines, 4 stimuli and 3 speeds.
- **Open or filled.** An open marker is not significant and a filled one is significant (legend, supplement PDF p. 8).
- **Direction.** It comes from the marker's position against the control's marker.

**Result.**
- All 167 Fig. S3H units of both extractions (A 88, B 79) match this reading.
- Eleven markers have their centre covered by the other line's marker:
  - the nine that B left out;
  - Mi4-1 with OFF edges at 30°/s, which both extractors read;
  - Mi9-1 with ON edges (44%) at 90°/s, a repeat of Fig. 3E that B could not read.

## 4. Settlements (each against the source; the reasons in full are in `settlements.json`)
| Finding | A | B | Settled | Basis |
|---|---|---|---|---|
| S3H, Tm3, OFF edges, 90–270°/s | unchanged | mixed | unchanged | The vector paths show line Tm3-1's covered marker at 270°/s as open, as A read it. With it, two units are unchanged and one increased. |
| S4A, Mi9, ON edges, 90–540°/s | mixed | mixed | increased | Unchanged at 90°/s and increased at 540°/s, for every reset duration. The experiment was run to test Mi9's enhanced turning (methods, protocol B3). The text says the enhanced response "was still observed" when the OFF period was varied (article PDF p. 8). Stage 1 settled the tie in Fig. 4B the same way, from the text's account of the experiment. |
| S3E, Tm3, gratings, 135–540°/s | mixed | mixed | left out (mixed) | Unchanged at the 15° and 22.5° periods, reduced at 30° and 60°. The text's statement covers Figs. S3A–E and all four input types together, so it does not decide this finding. |
| S3H, Tm3, ON edges, 30°/s | mixed | mixed | left out (mixed) | Line Tm3-1 reduced at all three contrasts and line Tm3-2 unchanged at all three. The text says only that the phenotypes were "generally reproducible with additional driver lines". |

The other 79 findings agreed in both extractions and were taken as they stood. The two findings left out stay in the table as mixed, so the scorer skips them, as the rule for undecided ties requires.

## 5. Points that repeat stage-1 conditions (for prediction R2)
| Condition | Points | Same as stage 1 | Notes |
|---|---|---|---|
| Fig. S3H, main lines, 90°/s, 44% ON and 43% OFF (= Fig. 3E) | 8 | 8 | Read from the vector paths, including Mi9-1's covered ON marker. |
| Figs. S3A–B, 100% contrast at 1 and 9 Hz (= Fig. 4B's condition) | 10 | 10 | Two by direction only: T4 and T5 silenced together, reduced in the marks, abolished in stage 1, from the text's statement for this stimulus. |
| Figs. S4B–D, direction selectivity with Mi4 or Mi9 silenced | 2 | not compared | The histograms are tested against shuffled data, not against control, so the supplement gives no category. Selectivity remains, which is consistent with stage 1's "unchanged" (M190, M191). |

`repeats.csv` lists each point with its basis.

## 6. The supplement table
`supplement-table.csv` holds 83 findings, row IDs SM001–SM083. The columns are those of stage 1's merged table, plus the driver lines and stimulus conditions pooled in each finding.

| Role | Findings | Of which |
|---|---|---|
| primary | 8 | Fig. S2B, T4 calcium at 30°/s: 4 with bright edges (model counterpart: T4 at 27.55°/s) and 4 with dark edges (no counterpart; reported as unmatched) |
| behaviour (score h) | 54 | Figs. S3C–H and S4A; 2 left out as mixed, so 52 scored |
| excluded | 21 | 10 contrast-series findings (Figs. S3A–B) and 11 with T4 and T5 silenced together |

**The primary findings.** Mi1 and Tm3 blocks reduced T4 responses to both edge polarities, and Mi4 and Mi9 blocks left them unchanged. The same pattern holds at 90°/s in stage 1 (Fig. 3C).

## 7. Table S1
The merge did not need Table S1 (a separate spreadsheet that is not on disk). Driver lines are pooled within findings. The identity of the main lines matters only for which Fig. S3H points repeat Fig. 3E. That identity is the "-1" lines, by three pieces of evidence:
- the Fig. S1 legend, which calls the "-2" lines the second lines;
- the stock numbers in the legends;
- the marks for Mi4.

Both extractors drew the same inference.
