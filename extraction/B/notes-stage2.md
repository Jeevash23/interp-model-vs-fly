# Extractor B: stage-2 notes (Strother et al. 2017, Supplemental Information)

AI-11 blind extraction, stage 2, 18 October 2026. The rules are unchanged (`../EXTRACTION-RULES.md`).

- **Source.** `../../sources/strother-2017-supplement.pdf`, 22 pages, SHA-256 `6d1da44a868575a90d817cc4c6f6ded5a3dfacc248d3c3638a4afd3a36fcaea8`. This matches the hash the coordinating session gave.
- **Output.** `table-stage2.csv` (179 rows, IDs `B2-STR-001` to `B2-STR-179`), this file, and `SHA256SUMS-stage2`.
- **Stage-1 files.** `table.csv`, `notes.md` and `SHA256SUMS` were only read. Their checksums still verify.
- **Page references.** "supp p." means a PDF page of the supplement; "main p." means a PDF page of `strother-2017.pdf`. The stimulus protocols and statistics are described there.

## 1. What I opened, and a disclosure

Opened: the supplement PDF; my own stage-1 files (read only, to cite row IDs); `../EXTRACTION-RULES.md`; and, for the stimulus methods, the main Strother PDF I had already extracted in stage 1.

Not opened: `extraction/A`; `sources/PROVENANCE.md`; any protocol, prediction or model file; anything in AI-06, AI-09, REVIEW-COPIES, RELEASES, `<abstract-folder>` or <dependent-folder>; any project note. No web search, and nothing downloaded.

**Disclosure.** The application crashed twice during this stage. After the first restart, the project's note index was shown to me again automatically. That index now carries a one-line summary of the AI-11 study's outcome: "COMPLETE: 34/64 agree, κ 0.13; ON pathway ok, OFF inputs missed".
- I did not open that project note. The line gives no cell-type-level model result.
- Every significance reading below was finished before the line appeared: Figures S2B, S3A–H and S4A, including the high-zoom checks.
- After the restart I made three further checks, none open to judgement:
  - pixel sampling of five overlapping markers: three open, as already read; one unreadable; and Mi9-1 OFF at 90 °/s (a stage-1 duplicate, used only for the check in section 6), which appears open;
  - the colours of the S4A asterisks, which are unambiguous;
  - the row-building and checks.
- The stage-1 files were sealed at 05:38 UTC, before the line existed.

## 2. What I read

- **Supp pp. 1–22.** Read in full: the title page, every figure legend (S1–S7), Table S2 and the legends of Movies S1–S2.
- **Table S1 (supp p. 18).** Holds only its caption and "provided as a separate Excel spreadsheet". The table itself is not in the file, so the genotypes and stock numbers are not available; neither is the shibire copy number.
- **Figure pages rendered** with `pdftoppm`:
  - S2: supp p. 4, at 100–300 dpi;
  - S3: supp p. 7, at 100–2400 dpi;
  - S4: supp p. 9, at 100–300 dpi;
  - S1: supp p. 2, labels read from the text layer.
- **Overlapping markers in S3H.** Where one line's marker partly covers the other line's, I sampled the pixel colours down the centre line of the hidden marker at 2400 dpi, to see whether its white interior was visible. The tool is a short decoding script kept in the session scratchpad, run inside a resource-limited systemd scope.

## 3. Which driver line the main figures used (an inference)

- **Two lines per type.** The main text says two split-GAL4 lines were made for each input type, and "the strongest, most complete driver" was used for the experiments (main p. 3).
- **Fig S1A labels the second lines.** The legend calls the lines it shows "the second Split-GAL4 line developed for each cell type". The panels shown are labelled Mi1-2 (SS00809), Tm3-2 (SS00313), Mi4-2 (SS01019) and Mi9-2 (SS02430) (supp pp. 2–3).
- **The main lines are therefore the "-1" lines:** Mi1-1 SS00955, Tm3-1 SS00300, Mi4-1 SS00316 and Mi9-1 SS02432.
- **Consistent evidence from S3H.**
  - The S3H legend lists stocks 14–21 for the eight lines; the main figures use 14, 16, 18 and 20. Reading these as the first of each pair is itself part of the inference.
  - At the Fig 3E condition, only Mi4-1 shows the significant increase that Fig 3E reports; Mi4-2 does not.
- **Status.** This is still an inference, because Table S1 is missing. The stage-2 rows for the main lines say "by inference". It also applies to every stage-1 Strother row (see section 6).

## 4. Coding rules (as in stage 1, plus five)

The stage-1 rules all apply (see `notes.md` section 3):
- categories from the authors' marks, read from the figures;
- where the text is silent, the direction of a significant change judged from the plotted means, with no number read;
- per-point rows only where the marks differ between points;
- `ON+OFF` polarity for gratings;
- direction `both` for turning (clockwise minus anticlockwise) and for population calcium recordings.

Added in stage 2:
1. **Only new results.** A point already in the stage-1 table is left out. The supplement repeats exactly one kind of point: in Fig S3H, the main lines at 90 °/s with 44% ON and 43% OFF contrast are the Fig 3E data.
2. **Each row names its stage-1 relatives.** Where a supplementary figure extends a stage-1 result (another speed, contrast, window size or driver line), the row's notes name the related stage-1 rows. Rows on stimuli with no stage-1 counterpart say "No stage-1 row".
3. **Protocol labels.** Fig S3 comes from three grating protocols (A1 contrast test, A2 speed test, A3 spatial-period test; main pp. 21–22). Some conditions occur in two of them. Each row's stimulus therefore names its protocol (see section 5, decision 9).
4. **One row per driver line in S3H.** Fig S3H shows each input type silenced with each of its two lines; each line has its own rows.
5. **Hidden markers are left out.** Where a marker's centre is covered by the other line's marker, open and filled can't be told apart. Those points are left out and listed in section 7.

## 5. Decisions I was not sure of

1. **Main driver lines are an inference** (section 3). This affects the `silenced_types` field of every row for S2B, S3A–G and S4A.
2. **Directions from the plot.** Every category comes from figure marks: asterisks in S2B and S4A, filled or open circles in S3. Apart from S4A, the supplement prints no statement of which way a significant change goes, so for the S3 rows I judged the direction from the plotted means.
3. **Text versus marks at full contrast.** The main text says turning was reduced "only for lower contrast stimuli" (citing Figs S3A–E, main p. 8). Yet in S3B (9 Hz) the Mi1 and Tm3 points at 100% contrast are marked significant (B2-STR-024, B2-STR-029). I followed the marks and flagged both rows; the Tm3 points at 20% and 40% are also significant.
4. **Significant points the text never mentions:**
   - Mi9 silencing reduced turning to repeating dark edges at 60 °/s (2 Hz, 30° windows; B2-STR-110).
   - Mi1-1 and Tm3-2 silencing increased turning to dark edges at 270 °/s in S3H (B2-STR-126, B2-STR-143). The corresponding points for Mi1-2 are not significant, and for Tm3-1 the marker is hidden.
5. **Mi4 at 90 °/s in S4A** (B2-STR-176). It is significantly increased at all three reset durations, whereas Fig 4C (stage-1 row B-STR-062) shows no significant change at 90 °/s. The protocols differ: 2 s presentations with varied resets in S4A, 1 s in Fig 4C. Both rows stand.
6. **T4+T5 silencing in S3** is coded `reduced`, not `abolished`. The text states abolition only for the main-figure stimuli.
7. **Speeds derived for S3D-E** (spatial-period series): temporal frequency x period. Elsewhere the speeds are printed in the main methods (main pp. 21–22).
8. **S4B-D (direction selectivity)** add detail to stage-1 rows B-STR-104 and B-STR-105 but no new result. Following the instruction, they appear in section 6 and not as rows.
9. **Same condition in two protocols.** The 9% contrast grating at 1 and 9 Hz appears in both A1 (S3A-B) and A2 (S3C). The 40% contrast, 30° period grating at 1 and 9 Hz appears in both A1 and A3 (S3D-E). Each panel is plotted and marked separately, so each keeps its rows, labelled by protocol. For every silenced type the two panels give the same category, so the overlap causes no disagreement.

## 6. Supplementary detail on stage-1 rows (no new rows)

- **Every stage-1 Strother row (B-STR-001 to B-STR-105).** By the inference in section 3, the driver lines were Mi1-1 SS00955, Tm3-1 SS00300, Mi4-1 SS00316 and Mi9-1 SS02432; T4/T5 is SS00324 as stated. The figure legends list stock numbers per panel, but the genotypes behind them are in Table S1, which is missing. Copy number and control genotypes therefore remain unknown.
- **B-STR-104 (Mi4) and B-STR-105 (Mi9), Figs S4C and S4D** (supp pp. 9–10).
  - Direction selectivity was examined per fly, with n = 2 flies per condition.
  - Every histogram, including those from Mi4- and Mi9-silenced flies, differed significantly from its shuffled control (one-sample Kolmogorov-Smirnov, p < 0.05). So direction selectivity remained present after silencing.
  - The legend makes no statistical comparison with the control animals. The stage-1 coding stands: ds_category `unchanged`, from the text, with "no test" against control.
- **B-STR-021 to B-STR-028 (Fig 3E).** S3H re-plots the main lines' points at 90 °/s, 44% ON and 43% OFF.
  - Their marks agree with the stage-1 categories for Mi1-1 (reduced ON, unchanged OFF), Tm3-1 (reduced ON, unchanged OFF) and Mi4-1 (increased ON, unchanged OFF).
  - Mi9-1's ON marker at this point is hidden behind Mi9-2's, so B-STR-027 cannot be checked. Its OFF marker shows a white interior below the covering marker (pixel sampling), so it appears open, matching B-STR-028 (unchanged).
- **B-STR-001 to B-STR-010 (Fig 3C, 90 °/s).**
  - S2B adds the 30 °/s edges (new rows B2-STR-001 to 010), with the same categories as at 90 °/s.
  - S2A compares unsilenced T4 responses at 20 and 30 °C; there is no silencing in it.
- **Stage-1 notes items 19 and 20.** These said Figs S2B and S4C-D were unavailable. S2B is now extracted (stage-2 rows); S4C-D are covered by the second bullet above.

## 7. Considered and left out

- **Fig S2B, luminance-step columns:** no motion.
  - At 30 °/s, Mi1 silencing is marked significant for both ON and OFF steps.
  - No other silenced type is marked.
- **Figs S2C-D:** Tm3 calcium after Mi1 silencing. Tm3 calcium is not in the readout list, and I did not read these panels point by point. The main text reports no significant effect (main p. 6).
- **Figs S2A, S2E-F:** no silencing (temperature comparison; flicker responses of the input neurons).
- **Fig S3H, main-line points that duplicate Fig 3E** (8 points). For each of Mi1-1, Tm3-1, Mi4-1 and Mi9-1: 90 °/s with 44% ON contrast, and 90 °/s with 43% OFF contrast.
- **Fig S3H, markers hidden by the other line's marker** (9 points, unreadable):
  - Mi1-1: 38% ON at 270 °/s; 44% ON at 30 °/s.
  - Tm3-1: 43% OFF at 270 °/s; 29% ON at 90 °/s.
  - Mi9-1: 43% OFF at 30 and 270 °/s; 29% ON at 90 °/s; 38% ON at 90 and 270 °/s.
- **Fig S3H empty-GAL4 control:** a second control, not a silencing. Its circles are open: no significant difference from the empty split-GAL4 control.
- **Fig S5:** GluClα RNAi in T4/T5, a receptor knockdown and not silencing of a cell type. The legend reports GluClα transcripts reduced about 51-fold, with a caution that this may be an overestimate.
- **Fig S7 and Table S2:** the authors' computational model, its intermediate signals and its parameters. Not an experiment.
- **Movies S1-S2:** stimulus and response examples only.

## 8. Activation, photoactivation and pharmacology (not in the table)

**Strother 2017, Fig S6** (supp pp. 14–15), which extends main Fig 6:
- Expression images and photoactivation tuning curves for Chrimson in each T4 input type.
- The input types' own GCaMP6f responses (A), and T4 responses to single (B) and paired activation (C with Mi1, D with Tm3).
- The response measure is the mean dF/F 1–5 s after photoactivation onset, plotted against 590 nm light intensity.
- The legend says expression was somewhat lower for the Mi9-1 driver, and that all tuning curves saturate at the highest intensities.
- No statistics or numbers beyond the main text.

No pharmacology.

## 9. Row counts

| Figure | Rows | Content |
|---|---|---|
| S2B | 10 | T4 dendrite calcium, edges at 30 °/s |
| S3A | 9 | gratings, 1 Hz, contrast 3–100% |
| S3B | 13 | gratings, 9 Hz, contrast 3–100% |
| S3C | 17 | gratings, 9% contrast, 1–27 Hz |
| S3D | 8 | gratings, 1 Hz, period 15–60° |
| S3E | 8 | gratings, 9 Hz, period 15–60° |
| S3F | 33 | repeating ON edges, 30° windows, 1–36 Hz |
| S3G | 26 | repeating OFF edges, 30° windows, 1–36 Hz |
| S3H | 51 | both driver lines, repeating edges in 67.5° windows |
| S4A | 4 | repeating ON edges with varied dark resets |
| **Total** | **179** | |

- **By category:** 95 unchanged, 70 reduced, 14 increased.
- **Flags:** 6 rows are marked UNCERTAIN in their notes (B2-STR-024, 029, 110, 126, 143, 176).
