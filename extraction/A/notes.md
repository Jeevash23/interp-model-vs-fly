# Extractor A: notes

Extractor A, 18 October 2026. I worked only from `EXTRACTION-RULES.md`, the three source PDFs in `../../sources/` and this folder.

`table.csv` has 461 rows plus a header, with row IDs A001–A461:

| Source | Rows | Row IDs |
|---|---|---|
| Ammer et al. 2015 | 180 | A001–A180 |
| Serbe et al. 2016 | 94 | A181–A274 |
| Strother et al. 2017 | 187 | A275–A461 |

Page numbers below are PDF page numbers of the file named, not printed page numbers.

## 1. What I read

### Ammer et al. 2015 (`ammer-dissertation.pdf`, 236 pages)

- I used the contents pages (pp. 5–8) to find the article. Manuscript II is printed pp. 33–56, which is PDF pp. 43–66; in this part of the file the PDF page is the printed page plus 10.
- I read the whole article: highlights p. 44, main text and Figs. 1–4 pp. 45–51.
- I read the whole supplement, pp. 52–66:
  - Figs. S1–S4;
  - Table S1 (resting potentials);
  - the note that Table S2 is a separate spreadsheet, not reproduced here;
  - the supplemental procedures, including genotypes, stimuli, behaviour protocol, the model and statistics.
- I rendered Figs. 1–4 (pp. 46–49) at 300–2400 dpi to read where the significance asterisks fall.
- I searched the dissertation's introduction (pp. 11–32) and discussion (pp. 203–218) for Mi1 and Tm3. They only summarise the article, so I took nothing from them. They also summarise Strother et al. 2017, which I did not use.

### Serbe et al. 2016 (`serbe-dissertation.pdf`, 177 pages)

- I used the contents pages (pp. 4–6) to find the article. Manuscript Nr. 1 is printed pp. 15–41, which is PDF pp. 24–50; here the PDF page is the printed page plus 9.
- This copy is the 'in press' version, paginated 1–13. The published issue is Neuron 89:829–841.
- I read the whole article (pp. 25–38) and the whole supplement (pp. 39–50).
  - The supplement covers Figs. S1–S7, the Movie S1 legend and the supplemental procedures.
  - Table S1 (genotypes) is a caption only, on p. 48, so the Gal4 lines are not named in this copy.
- I rendered Figs. 5–7 (pp. 31–33), Figs. S4–S6 (pp. 43–45) and the Table S1 page (p. 48).
- I read the dissertation discussion (pp. 146–160).
  - One sentence there (p. 152) restates the article's preferred-direction (PD) and null-direction (ND) result. I cite it only as a supporting locator in the Fig. S4 PD and ND rows.
  - Two extra experiments reported there are left out (section 4).

### Strother et al. 2017 (`strother-2017.pdf`, 26 pages)

- The file appeared in `sources/` while I was working, at about 05:10 UTC. I read it after finishing Ammer and Serbe.
- I read the highlights (p. 1), the article (pp. 2–16, Neuron 94:168–182) and the STAR Methods (pp. 17–26, e1–e10).
- The supplementary Figs. S1–S7 and Tables S1–S2 are not in this PDF.
- I rendered Figs. 3 and 4 (pp. 5, 7) at 300–600 dpi.

## 2. How I coded

### Categories

- Categories come from the authors' own significance marks where they drew them:
  - asterisks in Ammer Figs. 1–4, Serbe Figs. 5–6 and Strother Fig. 3;
  - filled versus open circles in Strother Fig. 4.
- From the figures I read only whether a mark is present and where it sits, never a value.
- Where a legend says that marks show significance, a missing mark is coded `unchanged`.
- Where no test is reported, the category follows the authors' statement, and the row's notes say "no test".
- Where a test and the authors' text disagree, I followed the test, because the rules define `reduced`, `unchanged` and `increased` by the authors' own test. The conflict is written in the row's notes and listed in section 3.

### Speeds

- **One row per speed** where the authors test each speed: Ammer Figs. 2–4 and Strother Fig. 4.
- **One row for the averaged speed range** where the authors test only a response averaged over speeds: Serbe Figs. 5–6 and 7D. Their statement about single speeds is in the notes.
- **One row for the stated speed range** where the authors make a statement covering all speeds without per-speed results: Serbe Fig. S4 and Fig. 7C.
- Speeds are given as printed, with three exceptions:
  - Serbe gratings: speed derived as temporal frequency × 45°, and marked as derived.
  - Strother Increasing ON Edges: speed derived as temporal frequency × 60°, and marked as derived.
  - Strother Figs. 4A and 4B: the speeds are printed; the temporal frequencies are speed / 30° period.

### Cell types and lines

- Ammer used three driver lines for Tm3: R55D08 ('Tm3a'), R59C10 ('Tm3b') and R13E12 ('Tm3c'). I gave each line its own rows, because the authors test them separately and the results differ at some speeds. `silenced_types` is `Tm3` for all of them, and `method` names the line.
- Pairs are written as, for example, `Tm1+Tm2`. The T4/T5 group is written `T4a-d+T5a-d`.

### Polarity, direction and sign

- **Polarity.** I used `ON+OFF`, which is outside the ON/OFF set in the rules, for stimuli that contain both polarities:
  - balanced opposing edges (Ammer Fig. 4, Serbe Fig. 7);
  - square-wave gratings (Serbe Fig. S5; Strother Figs. 4A and 4B, and the direction-selectivity rows).
- **Direction.** I used `both` in four cases:
  - PD-minus-ND measures (Ammer Fig. 1; Serbe Figs. 5–6);
  - behaviour, where mirror-image or clockwise/counterclockwise versions of the stimulus are subtracted;
  - Strother's population imaging of T4 dendrites, where all four subtypes are recorded together;
  - Serbe gratings, where the authors' statement is not direction-specific.
- **Sign of the behavioural measures.** The sign differs between papers:
  - Ammer: positive means turning with the OFF edges, so `increased` means an ON-pathway deficit.
  - Serbe: positive means turning with the ON edges, so `increased` means an OFF-pathway deficit.
  - Strother: the turning index is positive with the stimulus.

### Numbers

- Only Serbe prints response values. All are mean ± SEM, in % of control:

  | Fig. | Shibire copies | Tm1 | Tm2 | Tm4 | Tm9 |
  |---|---|---|---|---|---|
  | 5 | two | 53.98 ± 8.33 | 39.22 ± 4.50 | 70.59 ± 8.41 | 25.69 ± 6.37 |
  | 6 | one | 76.29 ± 7.88 | 69.13 ± 4.25 | 89.17 ± 7.95 | 51.39 ± 6.02 |

- Ammer prints only the speeds at which the tuning curves peak (12.5 and 25°/s for the two Tm3 lines; 100°/s for control). These are in the notes of the matching rows.
- Strother prints no silencing values.
- No row meets the 10% numeric rule for `abolished`. `abolished` is used only where the authors state that the response was abolished: Strother's T4/T5 behaviour rows.

## 3. Decisions I was not sure of

### Rows and mark reading

1. **Three Tm3 lines as separate rows (Ammer).** Read strictly, the row key in the rules would merge them.
2. **Tm3 marks in Ammer Figs. 2D and 3D.** The asterisks for the two Tm3 lines are unlabelled. I assigned them by position: R55D08 marks sit below its curve, R59C10 marks above its curve.
   - At 75°/s (PD), only R55D08 is significant.
   - At 700°/s (ND), the single asterisk is under the R55D08 curve.
3. **Tm3 marks in Ammer Fig. 4D (behaviour).** The asterisks for the three Tm3 lines are unlabelled.
   - At 40, 80 and 160°/s there are three asterisks, so all three lines are significant.
   - At 20 and 320°/s there are two asterisks. I read them as R13E12 and R55D08 significant, R59C10 not. This is the least certain reading in the table.

### Where the test and the text disagree (coded from the test)

4. These rows follow the test rather than the authors' wording:

   | Source and row | Mark | Authors' text |
   |---|---|---|
   | Ammer, Mi1, ON edges, PD and ND, 700°/s | no asterisk | "all velocities" |
   | Ammer, Mi1 behaviour, 640°/s | no asterisk | "whole range" |
   | Ammer, Tm3 (R55D08), ND ON response, 700°/s | asterisk | no effect on ND |
   | Serbe, one-copy Tm1+Tm4, OFF | no asterisk | "intermediate reduction" |
   | Strother, Tm3, T4 calcium, 27 Hz | open circle | decrease at all frequencies |
   | Strother, Mi9, Repeating ON Edges, 60°/s | filled circle below control | not mentioned |

### Category wording

5. **Signed values versus the authors' wording.** I used the authors' word "reduction" or "decrease" in these rows, but a signed comparison would sometimes read as an increase:
   - Ammer Mi1 ND rows: at high speeds the block response is more depolarised than control.
   - Strother Mi1 and Tm3 at 27 and 81 Hz (Fig. 4A): the control response is near or below zero.
6. **Ammer Fig. 1G, Mi1, OFF contrast series.** Coded `reduced`, though only one low contrast is significant; the authors call it a minor reduction at low contrast. Contrast levels other than 6% and 100% are not printed, so I did not split the rows by contrast.
7. **Ammer Figs. 1E–F.** No test is drawn on the trace panels, so the categories come from the authors' statements.
8. **Ammer Figs. 2–3, OFF rows.** These carry `ds_category = unchanged` from the authors' statement that directional tuning of OFF responses was unaffected. There is no separate test of direction selectivity.

### Serbe

9. **Fig. S4 PD and ND rows.** The authors give no PD- or ND-specific test. I carried each genotype's category over from its PD-minus-ND test, using the authors' statement that effects were consistent for PD and ND. For Tm1+Tm4 this gives `unchanged`, although the text speaks of an intermediate reduction.
10. **Fig. S5 gratings.** Coded `reduced` for every genotype from the authors' collective statement that grating responses were only mildly reduced. There is no test; I gave one row per genotype with direction `both`.
11. **Behaviour.** The paper reports no statistics for behaviour, so every behaviour category comes from a statement.
    - Tm1+Tm2 is coded `increased`. The authors compare it only with the Tm2 block: it did not give a stronger turning response than Tm2 alone.
12. **Fig. 7C, Tm2.** The effect depends on speed. I gave one row (`increased`) and described the dependence in the notes, because which speeds count as low or high is not stated.
13. **Fig. 6, one-copy Tm2.** The cell count differs between sources: the text gives n = 11, the legend 13 cells in 9 flies. Both are recorded.

### Strother

14. **T4/T5 behaviour.** Coded `abolished` in Figs. 3E, 4B, 4C and 4D, where the authors say so explicitly. Coded `reduced` in Fig. 4E, because there is no explicit statement for that stimulus.
15. **Fig. 4B, Mi1 and Tm3.** Significant only at 3 and 9 Hz. I coded `reduced` there, although the authors say single blocks had very little effect on this grating.
16. **T4/T5 silencing with T4 calcium as the readout.** The imaged T4 cells are themselves silenced: shibire-ts1 blocks their output, not their calcium. I kept these rows, as the authors treat them as a test of T4–T4 connections.
17. **Driver lines.** The authors made two split-GAL4 lines per cell type and used the stronger one for imaging. Which line was used for each panel is in Table S1, which is not in this PDF. If the Mi9-2 line was used, some Mi13 cells were silenced as well.
18. **Direction selectivity with Mi4 or Mi9 silenced (Figs. S4C–D).** These figures are not in this PDF, so the two rows come from the text only: `ds_category = unchanged`, `amplitude_category = not_reported`.

## 4. Rows considered and left out

### Ammer

- Fig. 1D: the paper's own model simulation, not an experiment.
- Figs. S2–S4: single-cell or single-fly example traces of data already in the main figures.
- Table S1: resting membrane potentials. This is not a motion response, and there was no significant difference.
- Figs. 2A/2C and 3A/3C (12.5 and 300°/s) and Figs. 4A/4C (20 and 320°/s): averaged traces of the same data as the tuning curves.

### Serbe

- Figs. 1–4: calcium imaging of the Tm cells themselves; no silencing.
- Fig. 8: Reichardt-detector simulations, not experiments.
- Per-speed rows for Figs. 5I–L and 6 and the Fig. S4 curves: there is no per-speed test or printed value. The authors' statement that effects held at all speeds is in the notes.
- Example traces at 50°/s (Figs. 5E–H, the Fig. 6 traces, Figs. S4A/F/J/M) and at 1.11 Hz (Figs. S5A/F/J/M).
- Fig. 7E: relates behavioural to tangential-cell effects; not a comparison with control.
- Fig. S6: per-speed behaviour traces with no test and no speed-specific statement. Figs. 7B and 7C are included.
- Dissertation discussion Fig. 8 (p. 149): Tm2+Tm9 block with two shibire copies (4 cells in 2 flies). It is not in the article.
- Dissertation discussion Fig. 9 (p. 156): Tm2+Tm9 behaviour to single-polarity edges, where the authors describe only a mild reduction for OFF edges. It is not in the article.

### Strother

- Fig. 2: T4 calcium in unmanipulated flies.
- Fig. 3B: calcium responses of the input neurons; no silencing.
- Fig. 3C, Flash column: luminance steps, not moving edges or gratings.
- Supplementary results that are not in this PDF, and whose main-text statements are too general to code by genotype and speed:
  - Fig. S2B: 30°/s edges.
  - Figs. S2C–D: Tm3 calcium with Mi1 silenced; the readout is outside the rules, and the authors report no significant effect.
  - Figs. S3A–H: contrast, spatial wavelength and additional driver lines.
  - Fig. S4A: Repeating ON Edges with different OFF reset durations.
- Fig. 5: GluClα RNAi in T4/T5. This knocks down a receptor; it does not silence a cell type (see section 5).
- Figs. 7 and S7: the paper's own computational model.

## 5. Activation, photoactivation and pharmacology (not in the table)

- **Ammer 2015:** none.
- **Serbe 2016:** none.
- **Strother 2017, Fig. 6 (pp. 10–11).** Chrimson photoactivation at 590 nm in excised brains, with GCaMP imaged in T4 dendrites in medulla layer M10.
  - **One input type at a time (Mi1, Tm3, Mi4 or Mi9):** only small T4 calcium responses. Only Mi1 gave a statistically significant response, and it was below 0.5 ΔF/F.
  - **Mi1 and Tm3 together:** large, robust T4 responses. Mi1 × Tm3 interaction terms were significant in a stepwise generalised linear model (F-test, p < 0.05) for every driver combination. The authors read this as a synergistic, nonlinear interaction.
  - **Mi4 or Mi9, alone or with Mi1 or Tm3:** no contribution to T4 activity was observed.
- **Strother 2017, Fig. 5 (another genetic manipulation, not silencing).** GluClα RNAi in T4/T5 (t-tests with Bonferroni correction):
  - enhanced turning to the faster Repeating ON Edges, but not to Increasing ON Edges;
  - also enhanced turning to Repeating OFF Edges.

## 6. Blindness

- I opened only `EXTRACTION-RULES.md`, the three source PDFs (two reached through their links into the AI-06 folder) and this folder.
- I did not open `sources/PROVENANCE.md`, because it is not one of the source PDFs.
- I listed the shared notes folder but opened no file in it. Two of its files concern AI-06 and AI-09, and none concerns this extraction.
- No web search, no download and no GPU use.

## 7. Files

- `table.csv`: 461 rows plus a header, UTF-8, row IDs A001–A461.
- `notes.md`: this file.
- `SHA256SUMS`: SHA-256 of `table.csv` and `notes.md`, written last. Nothing here is edited after that; any correction goes to `table-v2.csv`, with the reason given in this file.
