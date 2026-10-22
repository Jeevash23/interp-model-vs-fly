# Extraction rules: published silencing results in fly motion vision (blind extraction)

You are one of two independent extractors. Build a table of what three published studies found when they silenced identified cell types in the *Drosophila* visual system and measured motion responses. Work **only from the source PDFs**.

## Sources (in `../sources/`)
1. `ammer-dissertation.pdf`: a dissertation that reproduces Ammer et al. 2015, *Current Biology* 25:2247–2253, "Functional specialization of neural input elements to the *Drosophila* ON motion detector". Find the article inside it and extract from the article. Use the dissertation's other chapters only if they report the same experiments in more detail, and say so in the locator.
2. `serbe-dissertation.pdf`: a dissertation that reproduces Serbe et al. 2016, *Neuron* 89:829–841, "Comprehensive characterization of the major presynaptic elements to the *Drosophila* OFF motion detector". Same rule.
3. `strother-2017.pdf`: Strother et al. 2017, *Neuron* 94:168–182, "The emergence of directional selectivity in the visual motion pathway of *Drosophila*". **It may not be there yet.** If it is missing when you have finished the other two, write "Strother pending" in your notes and stop. The coordinating session will tell you when it arrives.

## What not to open (this keeps the extraction blind)
- No file in this project except this one, the sources and your own output folder. In particular, not `PROTOCOL-DRAFT.md`, `PROTOCOL.md`, `PREDICTIONS*` or `README.md`.
- No other extractor's folder (`extraction/A` or `extraction/B`, whichever isn't yours).
- Nothing in `<reference-project>`, `<companion-project>`, `REVIEW-COPIES`, `RELEASES`, `<abstract-folder>` or `<dependent-folder>`, and no project note about AI-06, AI-09 or AI-11. The two source PDFs are linked from AI-06's folder; open those two files only.
- No web search for model simulations of these cell types (for example the FlyVis model's silencing results). The table must describe the experiments only.

## What to include
- **Silencing:** any genetic, thermogenetic or optogenetic block of one identified cell type (or a defined pair or group) from this list. These are the cell types of the model this table will be compared with: Am, C2, C3, CT1, L1–L5, Lawf1, Lawf2, Mi1–Mi4, Mi9–Mi15, R1–R8, T1, T2, T2a, T3, T4a–d, T5a–d, Tm1, Tm2, Tm3, Tm4, Tm5a/b/c, Tm5Y, Tm9, Tm16, Tm20, Tm28, Tm30, TmY3, TmY4, TmY5a, TmY9, TmY10, TmY13, TmY14, TmY15, TmY18.
- **Readouts:** calcium or voltage of T4 or T5 cells; voltage of lobula plate tangential cells (HS, VS); optomotor (turning) behaviour.
- **Stimuli:** moving edges or gratings, with a matched control genotype or condition.
- Activation, photoactivation and pharmacology go only in a separate list at the end of `notes.md`, not in the table.

## One row per
(source, silenced type or types, readout, polarity, stimulus, speed). If the paper reports preferred and null direction separately, give each its own row.

## Columns of `table.csv` (in this order)
`row_id, source, locator, silenced_types, method, duration, readout, polarity, stimulus, speed_deg_s, direction, measure, amplitude_category, ds_category, numeric_value, numeric_unit, control, statistics, paraphrase, notes`

- **locator:** figure and panel, plus the PDF page number of the file you read.
- **method:** for example Kir2.1, shibire-ts with its copy number, TNT, or an optogenetic silencer.
- **duration:** chronic (constitutive), or acute with its temperature or light regime.
- **readout:** one of `T4_calcium`, `T5_calcium`, `T4_voltage`, `T5_voltage`, `HS_voltage`, `VS_voltage`, `LPTC_voltage_pooled`, `behaviour`.
- **polarity:** ON or OFF. **direction:** PD, ND, or both (combined).
- **measure:** what was measured, such as peak response, mean response, direction-selectivity index or turning response.
- **amplitude_category:** the effect of silencing on the response, as one of:
  - `abolished`: the authors state there is no response, or the residual printed in text or a table is at most 10% of control;
  - `reduced`: a decrease the authors' own test calls significant;
  - `unchanged`: the authors report no significant difference;
  - `increased`: an increase the authors' own test calls significant;
  - `not_reported`.

  If the authors give no test, use their stated conclusion and write "no test" in notes.
- **ds_category:** the same categories for direction selectivity, if reported; otherwise `not_reported`.
- **numeric_value:** only a number printed in the text or a table, such as "remaining response 54% of control". **Do not read values off figures.** Categories come from the authors' statements and tests.
- **statistics:** the test and p-value as printed.
- **paraphrase:** at most 25 words, in your own words, with no long quotation.

## Output (in your own folder, `extraction/<your letter>/`)
- `table.csv`
- `notes.md`: what you read (sections and pages), each decision you weren't sure of, rows you considered and left out (and why), and the list of activation and pharmacology results.
- `SHA256SUMS`: the SHA-256 of `table.csv` and `notes.md`, written when you finish.

Then report to the coordinating session that started you, with your row count. Don't edit anything once the SHA-256 is written. If you must correct something, write `table-v2.csv` and explain why in the notes.
