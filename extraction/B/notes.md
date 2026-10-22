# Extractor B: notes

AI-11 blind extraction of published silencing results, 18 October 2026. Extractor B worked independently of extractor A, following `../EXTRACTION-RULES.md`. Order of work: Serbe et al. 2016, then Ammer et al. 2015, then Strother et al. 2017.

Output in this folder: `table.csv` (298 rows), this file, and `SHA256SUMS`.

## 1. What I opened

Opened:
- `../EXTRACTION-RULES.md`.
- `../../sources/serbe-dissertation.pdf`, `../../sources/ammer-dissertation.pdf` and `../../sources/strother-2017.pdf`.
- This folder.

Not opened:
- `extraction/A`, and every other file in the project. This includes `sources/PROVENANCE.md`, which appeared with the Strother PDF; it is not one of the three sources the rules list.
- Anything in AI-06, AI-09, REVIEW-COPIES, RELEASES, `<abstract-folder>` or <dependent-folder>, and no project note.
- The shared notes folder for this group. I listed it, but opened none of its files: they concern other projects, or AI-06 and AI-09, which the rules exclude.
- No web search, and nothing downloaded.

Two disclosures:
- The session started with the one-line note index loaded automatically. It includes titles of the AI-06, AI-09 and AI-11 notes. I opened none of those notes, and the index lines give no cell-type results.
- While scanning the Ammer dissertation's own Discussion (PDF pp. 207-208) for more detail on Ammer 2015, I read its short summary of Strother 2017. None of it was used. The Strother rows come from the Strother article alone.

## 2. What I read

All page numbers are PDF page numbers of the file named.

**Serbe dissertation** (177 pp.). Manuscript Nr. 1 is Serbe et al. 2016: PDF pp. 24-50, printed dissertation pp. 15-41.
- Article pages 1-13 are PDF pp. 26-38; the supplement is PDF pp. 39-50.
- Read in full: the main text; Figures 1-8 and their legends; Supplemental Figures S1-S7; the Supplemental Experimental Procedures.
- Table S1 (genotypes, PDF p. 48) has only its caption in the dissertation; the table itself is blank.
- I scanned the dissertation's Discussion (PDF pp. 146-159) and read pp. 147-152 and 154-156.
  - Two statements there restate the article's experiments and are cited in locators: PDF p. 150 (double blocks never abolished OFF responses) and PDF p. 152 (OFF reductions present for PD and ND).
  - Discussion Figures 8 and 9 report new experiments; see section 5.

**Ammer dissertation** (236 pp.). Manuscript II is Ammer et al. 2015: PDF pp. 43-66, printed pp. 33-56.
- Read in full: the main text; Figures 1-4 and their legends; Figures S1-S4; Table S1; the Supplemental Experimental Procedures.
- Table S2 (PDF p. 58) holds only the note that it was "supplied as a separate Excel spreadsheet". There are therefore no exact p-values.
- I scanned the Discussion chapter (PDF pp. 203-213) for sentences on Mi1 and Tm3; nothing was used.

**Strother 2017** (26 pp.).
- Read in full: the main text (PDF pp. 1-16) and the STAR Methods (PDF pp. 17-26).
- The Supplemental Information is not in this PDF: Figures S1-S7, Tables S1-S2 and the movies. Missing with it are the genotype per panel, the behavioural control genotype and the shibire copy number.

**Figure pages rendered** with `pdftoppm` at 110 to 1400 dpi, to read panel labels and significance marks:
- Serbe PDF pp. 31-33, 43-45 and 48.
- Ammer PDF pp. 46-49.
- Strother PDF pp. 5 and 7.

## 3. Coding rules I applied

1. **Numbers.** Numbers come only from text or tables, and no value was read from a figure.
   - The only printed response values are Serbe's percent-of-control values for the single blocks (8 rows, in `numeric_value`).
   - Ammer's text also prints the velocities of the ON tuning maxima: 12.5 °/s (Tm3a) and 25 °/s (Tm3b), against 100 °/s in controls. These are not response amplitudes, so they sit in the notes of the Tm3 PD ON rows.
2. **Significance marks.** Asterisks, and filled versus open circles, are the authors' tests. I read them from the figures, zooming in where needed, to set the categories.
3. **Test versus text.** Where a mark and the text summary disagree, the category follows the mark and the row's notes say UNCERTAIN.
4. **Direction of a change.** Where a mark shows a significant difference but the text does not say which way, I judged the direction (reduced or increased) from the relative position of the plotted means. No number was read, and these rows say so.
5. **Speed granularity.** I made per-speed rows only where the authors' marks or statements differ between speeds. Where a series gives the same result at every speed, it has one row whose speed field reads "each of n speeds". Averaged measures keep their averaging range ("mean of 9 velocities").
6. **PD and ND.** PD and ND have separate rows wherever a source reports them separately (Serbe Figs S4-S5, Ammer Figs 2-3). Direction is coded `both` for three kinds of measure:
   - PD-minus-ND measures;
   - population recordings of T4 dendrites with mixed preferred directions (Strother);
   - clockwise-minus-anticlockwise turning.
7. **Grating polarity.** Gratings drive the ON and OFF pathways together, so their polarity is coded `ON+OFF`. This value is outside the rules' ON/OFF list.
8. **Opposing-edge behaviour** (Serbe and Ammer). Control flies barely turn. A block makes flies turn with the edges of the intact polarity. I coded the impaired polarity (OFF for Serbe, ON for Ammer) as `reduced`, following the authors' conclusions. The raw measure is a shift of turning towards the other polarity.
9. **Abolished.** `abolished` is used only where the authors state the response is abolished: the T4+T5 behaviour rows in Strother. No source prints a residual of 10% or less.
10. **"No test".** "no test" is written in the notes wherever the category rests on a statement without a test (81 rows).
11. **Driver lines.** Ammer's two Tm3 lines in the electrophysiology (R55D08 'Tm3a', R59C10 'Tm3b') are kept as separate rows. Ammer's three Tm3 lines in behaviour are pooled, because the asterisks cannot be attributed to individual lines. Strother's driver per panel is in Table S1, which is not available; the notes list both lines for each type.
12. **Speeds.** Speeds are as printed, except where marked "derived":
    - Serbe gratings: temporal frequency x 45° wavelength;
    - Strother Fig 4E: temporal frequency x 60° window.
13. **How the table was built.** The rows were typed into a short Python script, which is kept in the session scratchpad and is not part of this output. The script writes `table.csv` with the csv module and checks four things: allowed readout, category and direction values; paraphrases of at most 25 words; duplicate row keys; and stray whitespace.

## 4. Decisions I was not sure of

Serbe 2016:
1. **Tm1+Tm4, one shibire copy, OFF (B-SER-019).** The text calls this an "intermediate reduction", but Fig 6D has no significance mark, while every other double block has one. Coded `unchanged`. The two matching PD and ND rows from Fig S4 (B-SER-049, B-SER-051) follow the text and are coded `reduced`. Both decisions are flagged.
2. **PD/ND rows from Fig S4 (40 rows) and grating rows from Fig S5 (20 rows)** rest on general statements, with no test and nothing genotype-specific. The statements are: effects were consistent across velocities for PD and ND; grating responses were only mildly reduced, in a pattern like that for OFF edges. Grating polarity is coded `ON+OFF`.
3. **Fig 6 measure.** The legend does not say PD minus ND. The text compares the Fig 6 percentages directly with the PD-minus-ND percentages of Fig 5, so Fig 6 is coded `both`.
4. **Tm2, one copy.** The text describes a "reduction to 69.13%" with p = 0.07; coded `unchanged`. Tm1 (p = 0.18) is treated the same way.
5. **Behaviour (13 rows)** has no statistics. The categories follow the authors' conclusions (see rule 8).
6. **Tm2 behaviour (B-SER-101)** depends on velocity: little effect at low velocities, a pronounced effect at high ones. The authors do not define low and high, so the row is not split.

Ammer 2015:
7. **All categories come from asterisks read off the figures**, because Table S2 is missing.
8. **"All velocities" without an asterisk.** In three places the text says "all velocities", but one speed has no asterisk. All three are coded `unchanged` and flagged:
   - Mi1, PD ON, 700 °/s (B-AMM-024);
   - Mi1, ND ON, 700 °/s (B-AMM-060);
   - Mi1 behaviour, 640 °/s (B-AMM-086).
9. **Tm3, ND ON, 700 °/s (B-AMM-072).** Fig 3D has one asterisk at this speed. By its placement below the lower curve, I assigned it to Tm3a, and coded `reduced`. The text says Tm3 block had no effect on ND responses. If the asterisk belongs to Tm3b instead, the Tm3b ND ON row (B-AMM-080) changes at 700 °/s.
10. **Fig 2D: Tm3a or Tm3b.** I attributed asterisks above the upper curve to Tm3b and those below the lower curve to Tm3a. On this reading Tm3a is significant from 75 °/s and Tm3b from 100 °/s, neither at 700 °/s.
11. **Tm3 behaviour (three lines pooled).** Two of three lines are marked at 20 and 320 °/s; both speeds are coded `reduced` (B-AMM-087, B-AMM-091).
12. **Mi1 OFF, contrast series (Fig 1G).** Split into one low-contrast point, which is significant (`reduced`), and the remaining contrasts (`unchanged`). The intermediate contrast values are not printed.
13. **Fig 1E/F (50 °/s, full contrast).** These panels show traces without asterisks, so the categories come from the text ("no test").

Strother 2017:
14. **Categories from filled versus open circles and asterisks.** No p-values are printed, and the supplement is absent.
15. **Fig 4B, Mi1 and Tm3, 3 and 9 Hz.** These points are significant although the text says individual blocks had very little effect on grating turning. Coded `reduced`, with the direction judged from the plot (B-STR-032, -034, -037, -039).
16. **Fig 4A, Tm3, 27 Hz.** The point is open although the text says reduced "across all frequencies". Coded `unchanged` (B-STR-016).
17. **Fig 4C, Mi9, 1 Hz (60 °/s).** The point is significant and its mean lies below control; the text does not mention it. Coded `reduced` (B-STR-069). The increases at 9 and 13.5 Hz match the text.
18. **T4+T5 behaviour.** Coded `abolished` where the text says so: Figs 3E, 4B, 4C and 4D. Fig 4E has no statement, so it is coded `reduced`, although every point is significant.
19. **Only 90 °/s edges were extracted from Fig 3C.** Edges at 30 °/s were also tested (methods, PDF p. 20) but are probably in Fig S2B, which is not in the PDF. The text's summary cites Figs 3C and S2B together.
20. **Direction-selectivity rows for Mi4 and Mi9 (B-STR-104, -105).** These rest on the text alone ("little effect on the directional selectivity"), because Figs S4C-D are absent.
21. **T4+T5 silencing with T4 calcium as readout** is included. Shibire blocks transmitter release from the silenced cells but not their own calcium signals; the authors use this to test T4-T4 connections.

## 5. Rows considered and left out

Serbe 2016:
- Calcium imaging of Tm1, Tm2, Tm4 and Tm9 (Figs 2-4): no silencing.
- Reichardt-detector simulations (Fig 8): a model, not an experiment.
- Example traces at 50 °/s (Figs 5E-H and the Fig 6 traces), and the per-velocity curves of Fig 5I-L:
  - none has a per-velocity test;
  - the text says the effects were the same at every velocity;
  - so they are summarised in the averaged rows' notes.
- Scatter of behaviour against LPTC effects (Fig 7E): derived, not a silencing result.
- Fig S6 behaviour traces: they repeat Figs 7C-D.
- The dissertation Discussion's Figure 8: a Tm2+Tm9 block with two shibire copies (4 cells in 2 flies). Not in the published article.
- The dissertation Discussion's Figure 9: Tm2+Tm9 behaviour to separate ON and OFF edges. Not in the published article.
- The Discussion's mention of a T5 block with shibire ("data not shown"): another study, and no data.
- Other manuscripts in the dissertation (Meier et al. 2014; Maisak et al. 2013, among others): not among the three sources.

Ammer 2015:
- Model simulation of input removal (Fig 1D).
- Resting membrane potentials (Table S1): not a motion response. No significant differences were found.
- Single-cell example traces (Figs S2-S4), and the example traces in Figs 2A, 2C, 3A, 3C, 4A and 4C: covered by the tuning curves.
- Other manuscripts in the dissertation: not among the three sources.

Strother 2017:
- T4 responses to luminance steps without motion (the "Flash" column of Fig 3C): not a moving stimulus.
  - Mi1 block reduced them for ON and OFF.
  - Tm3 block reduced them for OFF only.
- Tm3 calcium after Mi1 silencing (Figs S2C-D): a Tm3 readout, not in the readout list. The text reports no significant effect.
- GluClα RNAi in T4/T5 (Fig 5): a receptor knockdown, not silencing of a cell type. It enhanced turning to faster repeating ON edges and to repeating OFF edges, but not to increasing ON edges.
- The authors' computational model with simulated silencing (Fig 7).
- Lower-contrast and other grating stimuli (Figs S3A-E), additional driver lines (Fig S3H) and repeating ON edges with varied OFF duration (Fig S4A): not in the PDF.

## 6. Problems noticed in the sources (flagged, not fixed)

- **Serbe, Tm2 with one copy.** The text gives n = 11 (PDF p. 31); the Fig 6 legend lists 13 cells (PDF p. 32).
- **Serbe, Table S1** is blank in the dissertation (PDF p. 48).
- **Ammer, Table S2** is missing from the dissertation (PDF p. 58).
- **Ammer, text versus figures.** The text's "all velocities" or "whole range" claims do not match the asterisks at one speed each (decisions 8 and 9).
- **Strother, supplement absent.** The PDF has no Supplemental Information, so Table S1 genotypes are unavailable.
- **Strother, page range.** The PDF metadata gives Neuron 94:168-192; the article runs pp. 168-182, plus STAR Methods e1-e10.

## 7. Activation, photoactivation and pharmacology (not in the table)

- **Serbe et al. 2016:** none in the article.
- **Ammer et al. 2015:** none.
- **Strother et al. 2017, Fig 6** (PDF pp. 10-11; methods PDF p. 22). Chrimson photoactivation in excised brains, read out as T4 calcium in medulla layer M10.
  - Activating each input type alone produced only small T4 responses. The response to Mi1 alone was statistically significant but under 0.5 dF/F (PDF p. 11).
  - Activating Mi1 and Tm3 together produced large, robust T4 responses.
  - In a stepwise generalised linear model (F-test, p < 0.05), only the Mi1 x Tm3 interaction terms were significant. They were significant for every driver combination.
  - No T4 contribution was seen from Mi4 or Mi9, either alone or paired with Mi1 or Tm3.
  - n = 5 flies per type for single activation; 4-6 for pairs.

## 8. Row counts

| Source | Rows | What they cover |
|---|---|---|
| Serbe 2016 | 101 | 28 tested PD-minus-ND rows (Figs 5-6, 8 with printed values); 40 PD/ND rows (Fig S4) and 20 grating rows (Fig S5), statement only; 13 behaviour rows, no statistics |
| Ammer 2015 | 92 | 13 rows from Fig 1 (50 °/s and contrast series); 39 PD and 28 ND velocity-tuning rows (Figs 2-3); 12 behaviour rows (Fig 4) |
| Strother 2017 | 105 | 22 T4-calcium rows (Fig 3C: 10; Fig 4A: 10; direction selectivity: 2); 83 behaviour rows (Fig 3E: 10; Fig 4B: 13; 4C: 33; 4D: 12; 4E: 15) |
| **Total** | **298** | 15 rows flagged UNCERTAIN in their notes |

Strother status: the Strother PDF was not in `sources/` when this extraction started (folder listing at 05:04 UTC). The file carries a 05:10 UTC timestamp, and it was there when I checked after finishing Ammer. It was therefore extracted, and "Strother pending" does not apply.
