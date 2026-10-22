# Extractor A, stage 2: notes on the Strother et al. 2017 Supplemental Information

Extractor A, 18 October 2026. Source: `../../sources/strother-2017-supplement.pdf` (22 pages; SHA-256 6d1da44a868575a90d817cc4c6f6ded5a3dfacc248d3c3638a4afd3a36fcaea8, which matches the hash the coordinating session gave).

`table-stage2.csv` has **275 rows** plus a header, with row IDs A2-001 to A2-275. The columns and coding conventions are the same as stage 1 (`notes.md`, section 2). The stage-1 files (`table.csv`, `notes.md`, `SHA256SUMS`) are unchanged, and their seal still verifies.

Page numbers below are PDF pages of the supplement unless marked "article", which means `strother-2017.pdf`.

## 1. What I read

| Pages | Content | Used? |
|---|---|---|
| 1 | Title page | — |
| 2–3 | Fig. S1 (anatomy of the driver lines) and legend | Driver-line names only |
| 4–6 | Fig. S2 (calcium imaging) and legend | **S2B used** |
| 7–8 | Fig. S3 (behaviour tuning) and legend | **S3A–H used** |
| 9–11 | Fig. S4 and legend | **S4A used**; S4B–D see section 4 |
| 12–13 | Fig. S5 (RNA-seq, GluClα RNAi) and legend | Section 5 |
| 14–15 | Fig. S6 (photoactivation) and legend | Section 5 |
| 16–17 | Fig. S7 (the paper's model) | Caption read only |
| 18 | Table S1 | Caption only |
| 19–20 | Table S2 (model parameters) | Caption read only |
| 21–22 | Movie S1 and S2 legends | No data |

- **Table S1** says it "is provided as a separate Excel spreadsheet". That spreadsheet is not in the PDF, so the exact genotype for each panel is still unavailable. Section 3 says how far the figures go towards filling that gap.
- **Fig. S7 and Table S2** describe the paper's own computational model. I read their captions and stopped there.
- **How I read the marks.** I rendered Figs. S2, S3 and S4 at 300–1200 dpi to read the authors' significance marks: asterisks in S2B and S4A, filled versus open circles in S3.
  - Fig. S3 is vector graphics. I listed every circle marker from the page's SVG conversion (centre, colour and whether it is filled), using `pdftocairo -svg`.
  - All 195 marker readings in panels A–G agree with my readings from the image.
  - In panel H, the vector paths settled nine markers that the other driver line's marker hides in the image.
  - I read no values from the figures, only the presence, fill and position of the marks.

## 2. Rows added

| Figure | Rows | What it adds | Related stage-1 rows |
|---|---|---|---|
| S2B: T4 calcium, single edges at 30°/s | 10 | The 30°/s edges of the Fig. 3C experiment | A275–A284 (90°/s) |
| S3A–E: walking behaviour, ON+OFF gratings | 85 | Contrast series at 1 and 9 Hz; 9% contrast at 3, 6 and 27 Hz; 40% contrast at spatial periods 15, 22.5 and 60° (1 and 9 Hz) | Fig. 4B rows at the same temporal frequency (A325–A349) |
| S3F–G: repeating ON or OFF edges in 30° windows | 80 | The Fig. 4C–D stimulus with 30° instead of 60° windows | Fig. 4C/4D rows at the same speed |
| S3H: second driver lines and other contrasts | 88 | Both split-GAL4 lines per cell type; ON contrasts 29%, 38% and 44%; OFF 43%; 30, 90 and 270°/s | Fig. 3E rows A285–A292 |
| S4A: repeating ON edges with OFF gaps of 42, 21 and 7 ms | 12 | Mi4 and Mi9 at 90 and 540°/s | Fig. 4C rows at the same speed |

Results, by figure:

- **Fig. S2B.** The same pattern as at 90°/s:
  - Mi1 and Tm3 blocks reduce T4 calcium responses to both ON and OFF edges.
  - Mi4, Mi9 and T4/T5 blocks give no significant change.
- **Figs. S3A–E.**
  - T4/T5 blocks reduce turning at almost every condition.
  - Mi1 and Tm3 blocks reduce it at 9% contrast from 3 to 9 Hz.
  - At 9 Hz, the Mi1 block reduces it only at 9% contrast, while the Tm3 block also reduces it at 20% and 40% contrast and at 30° and 60° periods.
  - Mi4 and Mi9 blocks never reach significance.
- **Fig. S3F (ON, 30° windows).**
  - Mi1 block: reduced at 30, 180, 270 and 540°/s.
  - Tm3 block: reduced at 90–540°/s.
  - Mi4 block: increased at 180–540°/s.
  - Mi9 block: unchanged throughout.
  - T4/T5 block: reduced at every speed except 1080°/s.
- **Fig. S3G (OFF, 30° windows).**
  - Mi4 block: increased at 270°/s.
  - Mi9 block: reduced at 60°/s.
  - T4/T5 block: reduced at every speed except 1080°/s.
  - Everything else unchanged.
- **Fig. S3H.** Both Mi1 lines and both Tm3 lines reduce ON-edge turning at most conditions. The two Mi4 lines differ:
  - Mi4-1 increases ON turning at 270°/s for all three contrasts.
  - Mi4-2 increases it only at 29% contrast.
  - Mi9-2 is never significant; Mi9-1 only at 44%, 270°/s.
- **Fig. S4A.** The asterisks are colour-coded by genotype, so they can be assigned with certainty.
  - Mi4 block: increased turning at 90 and 540°/s for all three gap lengths.
  - Mi9 block: increased at 540°/s only.
  - This supports the authors' statement that the enhanced response persists when the OFF period is varied.

## 3. Decisions I was not sure of

1. **Which driver line was the article's main line.**
   - The Fig. S1 legend calls Mi1-2 (SS00809), Tm3-2 (SS00313), Mi4-2 (SS01019) and Mi9-2 (SS02430) "the second Split-GAL4 line" for each type. So the main lines are most likely Mi1-1 (SS00955), Tm3-1 (SS00300), Mi4-1 (SS00316) and Mi9-1 (SS02432).
   - For Mi4 this is confirmed: only Mi4-1's Fig. S3H marks at 90°/s match the article's Fig. 3E (ON 44% increased, OFF unchanged).
   - For Mi1, Tm3 and Mi9, both lines match Fig. 3E, so the identification rests on the legend.
   - This narrows the `method` fields of the stage-1 Strother rows. If the main Mi9 line is Mi9-1, the stage-1 note that Mi9-2 also labels Mi13 does not apply to those rows. Stage-1 files are not changed.
2. **Duplicates left out.** Some supplementary points are almost certainly the same data as stage-1 rows, so they are not repeated:
   - **Fig. S3H, main lines at 90°/s (ON 44% and OFF 43%):** 8 points. These are the Fig. 3E condition (protocol B1, n = 10). Their marks equal stage-1 rows A285–A292 for all four cell types.
   - **Figs. S3A–B, 100% contrast at 1 Hz and 9 Hz:** 10 points. These match the Fig. 4B conditions. Their marks equal stage-1 rows A325, A328, A330, A333, A335, A338, A340, A343, A345 and A348 for all five genotypes.
   - The authors don't say the data are shared. I relied on the protocol descriptions (the A1 and A2 protocols both include these conditions) and the matching marks. If the data were separate measurements, leaving them out loses no category, because every mark agrees.
3. **Shared conditions merged within stage 2.**
   - 9% contrast at 1 and 9 Hz appears in Figs. S3A–B and in S3C.
   - 40% contrast at a 30° period, 1 and 9 Hz, appears in S3A–B and in S3D–E.
   - In every case the marks agree, so each condition is one row whose locator names both panels.
4. **Hidden markers (Fig. S3H).** These marks were read from the PDF's vector paths:
   - Mi1-1 at 30°/s, ON 44%, and at 270°/s, ON 38%;
   - Tm3-1 at 270°/s, OFF, and at 90°/s, ON 29%;
   - Mi9-1 at 30 and 270°/s, OFF, at 90°/s, ON 29%, and at 90 and 270°/s, ON 38%.
5. **T4/T5 coded `reduced`, not `abolished`,** in Figs. S3A–G. The article states abolition only for the 100% grating (Fig. 4B) and the 60°-window repeating edges (Figs. 4C–D), not for these supplementary stimuli. This matches the stage-1 coding of Fig. 4E.
6. **Significant results the text does not discuss** (coded from the test):
   - Mi9 block: OFF edges reduced at 60°/s (Fig. S3G).
   - Mi1-1 and Tm3-2 blocks: OFF edges increased at 270°/s (Fig. S3H).
   - Mi9-1 block: ON 44% increased at 270°/s (Fig. S3H).
7. **Control genotype.** For Figs. S3A–G and S4A, the control is stock 23 of Table S1, judging from the legend stock lists. It is most likely the empty split-GAL4 control that Fig. S3H names; I couldn't confirm this, because Table S1 is missing. In Fig. S3H, the second control (empty-GAL4) has open circles throughout, and I made no rows for it.
8. **Derived values.**
   - Speeds for the contrast series (protocol A1) and spatial-period series (protocol A3) are temporal frequency × spatial period, and are marked as derived. Protocols A2 and B2 print their speeds.
   - Fig. S3H temporal frequencies (0.44, 1.33 and 4.0 Hz) are the printed speeds divided by the 67.5° window.

## 4. Considered and left out

- **Figs. S2A, S2E–F, S1 and S5:** no silencing of the listed cell types with a valid readout.
- **Figs. S2C–D:** Tm3 calcium with Mi1 silenced. The readout is outside the rules. The authors report no significant effect, and all circles in S2D are open.
- **Fig. S2B, Flash column:** luminance steps, not moving stimuli.
- **Figs. S4B–D:** direction-selectivity histograms with Mi4 or Mi9 silenced.
  - They add detail on stage-1 rows A460–A461: 2 flies per condition, a 1 Hz grating (30°/s), and every histogram significantly different from its shuffled version (one-sample Kolmogorov–Smirnov, p < 0.05).
  - That test shows direction selectivity is present. It is not a comparison with control, so the stage-1 category (`unchanged`, from the authors' statement) stands and I added no row.
- **Fig. S7 and Table S2:** the paper's own model.
- **Movies S1–S2:** no results.

## 5. Activation, photoactivation and other manipulations (not in the table)

- **Fig. S6 (photoactivation details for article Fig. 6).**
  - Chrimson-tdTomato and GCaMP6f were co-expressed in each input type (S6A).
  - Chrimson was expressed in each input type with GCaMP6s in T4/T5 (S6B), and in Mi1 or Tm3 together with each other input type (S6C–D).
  - Every light-intensity tuning curve saturates at the highest intensities.
  - The Mi9-1 driver's expression was somewhat lower than the others'.
  - The fly results are those of article Fig. 6, already listed in stage-1 `notes.md`, section 5.
- **Fig. S5.** GluClα RNAi in T4/T5 reduced GluClα transcripts by about 51-fold. The authors caution that this may be an overestimate. This is a receptor knockdown, not silencing.

## 6. Process, checks and blindness

- **Stage-1 check, no errors found.** The vector method above also confirmed every stage-1 mark I had read from article Figs. 4B–E, including:
  - Mi9's reduction at 60°/s in Fig. 4C;
  - Mi4's increases in Figs. 4C–E.
  Article Fig. 4A builds its markers differently (straight-line polygons, not curves), so it was checked by image only, where the marks are clear.
- **The application crashes were my fault.** A scratch script of mine (`f4_panels.py`, a copy of `s3_panels.py`) found its helper by text replacement on its own file name. In the copy the name did not match, so the script kept launching copies of itself. This crashed the application at about 08:17 UTC, and again at about 08:27 UTC when I re-ran the same command after the first crash.
  - Another session patched it at 08:42 UTC.
  - I checked the patch and applied the same fix to `s3_panels.py`.
  - All later scripts ran inside a memory and task limit (`systemd-run --user --scope -p TasksMax=… -p MemoryMax=…`).
  - Only scratchpad files were involved.
- **Blindness.**
  - I opened only `EXTRACTION-RULES.md`, the source PDFs, my own folder and my scratchpad. I did not open `sources/PROVENANCE.md`, the other extractor's folder, the protocol, the predictions or any project note about AI-06, AI-09 or AI-11.
  - When the application restarted after the crashes, the system showed me the project's note index. One line of it summarises the AI-11 comparison result. I did not open the note it points to.
  - None of my stage-2 categories depends on that line: each comes from the authors' marks as described above.
  - No web search, no download, no GPU.

## 7. Files

- `table-stage2.csv`: 275 rows plus a header, UTF-8, row IDs A2-001 to A2-275.
- `notes-stage2.md`: this file.
- `SHA256SUMS-stage2`: SHA-256 of the two files above, written last. Nothing is edited after it; any correction would go into a new versioned file with the reason given.
