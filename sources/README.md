# Source documents (not included)

The experimental results were extracted from four documents by other authors. They are not included in this release
(copyright). Each is identified below by its size and SHA-256, which the freeze records also hold (`sources_sha256`
in `PREDICTIONS-RECORD.json` and `FREEZE.json`; `FREEZE-STAGE2-STROTHER.json`). The extraction rules
(`extraction/EXTRACTION-RULES.md`) and the extractors' notes refer to them by these file names.

| File name | Document | Bytes | SHA-256 |
|---|---|---|---|
| `ammer-dissertation.pdf` | G. Ammer, *Functional Dissociation of Neural Circuits for Motion Vision in Drosophila*, doctoral dissertation, Graduate School of Systemic Neurosciences, Ludwig-Maximilians-Universität München (submitted 2017, defended 2018), 236 pages. Its Manuscript II (PDF pp. 43–66) reproduces Ammer et al. 2015. | 33930768 | `eea3b405c6c1065e1d879200b62a5fc9f8d697ae31557929c4c0e998857c829b` |
| `serbe-dissertation.pdf` | É. Serbe, *Analysis of the Neural Circuit Underlying the Detection of Visual Motion in Drosophila melanogaster*, doctoral dissertation, Graduate School of Systemic Neurosciences, Ludwig-Maximilians-Universität München, 2016, 177 pages. Its Manuscript 1 (PDF pp. 24–50) reproduces Serbe et al. 2016. | 57681471 | `5f799bb86ed60be4f574a4ac071d2f6617de9360ecee2ce40b4141eb7e0040b3` |
| `strother-2017.pdf` | J. A. Strother, S.-T. Wu, A. M. Wong, A. Nern, E. M. Rogers, J. Q. Le, G. M. Rubin and M. B. Reiser, "The emergence of directional selectivity in the visual motion pathway of *Drosophila*", *Neuron* 94(1):168–182.e10, 2017, doi:10.1016/j.neuron.2017.03.010: the article and its STAR Methods (26 pages). | 3578879 | `1302dee6c8987aeab9c29193e7bd46cfb66e5abd7984163b215e8b7161b78958` |
| `strother-2017-supplement.pdf` | The Supplemental Information of the same article: Figures S1–S7 and Tables S1–S2 (22 pages). | 4384537 | `6d1da44a868575a90d817cc4c6f6ded5a3dfacc248d3c3638a4afd3a36fcaea8` |

The articles that the two dissertations reproduce:

- G. Ammer, A. Leonhardt, A. Bahl, B. J. Dickson and A. Borst, "Functional specialization of neural input elements to
  the *Drosophila* ON motion detector", *Current Biology* 25(17):2247–2253, 2015, doi:10.1016/j.cub.2015.07.014.
- E. Serbe, M. Meier, A. Leonhardt and A. Borst, "Comprehensive characterization of the major presynaptic elements to
  the *Drosophila* OFF motion detector", *Neuron* 89(4):829–841, 2016, doi:10.1016/j.neuron.2016.01.006.

To rerun a step that reads a source document (the extraction itself, or `code/stage2_s3h_markers.py`, which reads the
markers of Fig. S3H from the supplement's vector paths), obtain the document, check its SHA-256 against this table
and place it in this folder under the file name given. The release's freeze check treats these four files as not
shipped; it does not need them.
