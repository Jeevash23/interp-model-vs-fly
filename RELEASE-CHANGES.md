# Changes from the original project

This release was exported from the project folder in which the study ran. Files are copied byte for byte except
those listed below. There are five kinds of change:

- **adapted:** `config.json` now names `reference/flyvis-first-order` as the folder of the reference study, whose files
  the code reads (they are shipped there), and so do the two scripts that named that folder themselves. The freeze
  checks (`code/freeze.py`, `code/stage2_freeze.py`, `code/stage2_strother.py`) and the record check of
  `code/stage2_score.py` accept the changes listed here, through `tools/release_paths.py`. The stage-2 simulator's gate
  accepts the recorded replay check when the code differs from the recorded code only by the changes listed here (paths
  and a time zone setting), and its run script takes the Python from `PYTHON` and the GPU lock helper from
  `code/gpu_lock.py`, and leaves the FlyVis model folder out of its write audit.
- **replaced:** the project's `Makefile`, which the freeze lists, is replaced by this release's; the original is kept
  (redacted) as `provenance/Makefile-at-freeze`.
- **reduced:** the 1,200 stage-2 pair-silencing records of the 4 development and 46 confirmation models keep every
  array except their time trace (`trace`). The original records' digests are in each record's metadata file and, for
  the confirmation records, in `FREEZE-STAGE2.json`; `release-changes.json` lists the original and reduced digest of
  every record.
- **redacted:** records in which personal or machine-specific strings were replaced:
  - absolute paths, the external drive and other projects' folder names by placeholders (`<project>`,
    `<reference-project>`, `<companion-project>`, `<sibling-project>`, `<portfolio>`, `<review-notes>` and similar),
    and the operating system's name by `[distro]`;
  - clock times: the records gave local clock times and their offset from UTC; this copy gives the same instants in
    UTC, so the order and spacing of events are unchanged and can be checked against the UTC stamps of the freeze
    records. The reference study's simulator sets flyvis's `TIMEZONE` (used only for the time stamps of its log
    messages) to UTC;
  - a conference abstract related to the study: its name is replaced by "conference" (in brackets inside the author's
    quoted words), its folder's name by `<abstract-folder>`, and the dates of its decision and poster by `[date]` and
    `[conference]`;
  - the work was done in sessions of a language-model assistant, as the manuscript states. The name of the assistant's
    application is replaced by "the application" (the assistants used are named in README.md, under "Use of AI assistants"), and its terms for the index of project notes that a session is shown
    when it starts by "note index", "project note" and "index line". Everything the records say about what each session
    saw and did is kept, including the deviation from blinding in the supplement extraction (`STAGE2-AMENDMENTS.md`,
    S3, and the extractors' disclosures in their stage-2 notes).

  Nothing else in these files changed; the counts show how many strings of each kind were replaced.
- **not shipped:** files named in a freeze record but left out (listed at the end with their SHA-256): the four source
  documents (copyright; `sources/README.md` cites them), log records and the stage-1 version of the written report.

Files added for the release: `code/gpu_lock.py` (a copy of the companion study's GPU lock helper, which
`code/stage2_run.sh` ran from that study's folder), `tools/`, the READMEs, `sources/README.md`, `requirements.txt`,
`ENVIRONMENT.md`, `LICENSE` and this file.

The two extractors sealed their files with `SHA256SUMS` files in `extraction/A` and `extraction/B`. Where an
extractor's notes were redacted, the seal gives the original's digest, which is also listed below. The files of the
reference study under `reference/flyvis-first-order/` are copies of that study's files (also part of its own release).
Saved outputs are archives under `data/saved-outputs/`; `tools/unpack.py` restores them byte for byte and checks each
SHA-256 against `data/PACKED-FILES.json`. Compression is not a change and is not listed below.

To check every freeze record against this release: `make check-freezes`.

## Files that differ from the project originals

| File | Change | Original SHA-256 | Release SHA-256 | Frozen in |
|---|---|---|---|---|
| `AMENDMENTS.md` | redacted (approval wording x1, local clock time x14, time zone x1) | `ac469a8f3a9160f70019968ea1c5427905a237cecee23a43ed304bf2ed4fa325` | `c131d9218e1f1d63f6d6c13b5cd5514ffa52335f30ac4cb9658f1e9ee75f8927` | `FREEZE.json` |
| `AUTHOR-APPROVAL.txt` | redacted (approval wording x5, conference abstract x2, related write-up x1, time zone x1) | `e2192b098b5ce90b6d81983a697a1288b15eb7fadf96e5aafacbc596a57e3446` | `d7d68d0a8c67a9c739d34d50a5565f4fd6bae3f09dc7086d5d1f77666decdb2e` | `PREDICTIONS-RECORD.json`, `FREEZE.json` |
| `DEVELOPMENT-NOTES.md` | redacted (local clock time x2, time zone x1) | `824b6bb7cb0bf24cdeb90b6d01c4cee4e85501c86f0dbf0ff938e17f5f52c342` | `957b2e9d6fe7b889ebc5ed4ad14400ed3e557f681bb27d77c08f61be7fa06093` | `FREEZE.json` |
| `Makefile` | replaced: this release's Makefile replaces the project's; the original is kept, redacted, as provenance/Makefile-at-freeze | `6e7b434b86fc9f889487aaef8db0f453ede41af37aa67a1fe7c25475e7756953` | `3db79fc6e97b84b45d53314951a3f792732e46011be585e1fb04ebf80bd82d00` | `FREEZE.json` |
| `PREDICTIONS-ADDENDUM-RECORD.json` | redacted (local clock time x5, time zone x1) | `d9041966806a85fcaab656797f3618d6dff3bc22cd12864984d9620be4607ec3` | `3e18c3c42fefa6c6003f80ee85b6adaeb85e159617b79f94bbabc7e17abb8c12` | `FREEZE.json` |
| `PREDICTIONS-RECORD.json` | redacted (approval wording x1) | `c41db78447760184041ca6e0bfcb8de5d3adfbe95185958fbdd447dddb2a43b6` | `94517d183963895fe301ee41906abf52aa77a044ee91f8147861ff1e587b2e6b` | `FREEZE.json` |
| `PROTOCOL-DRAFT.md` | redacted (approval wording x6, conference abstract x2, external drive x1, machine details x2, related write-up x1) | `c926938516900c08fca818c995d5be11c354b98e751c842e16f4fd0dd762de6c` | `723607252163ec5834f40d7057e1bfe4bc46b5b0241b675f70d70c216e768a7b` | `PREDICTIONS-RECORD.json` |
| `PROTOCOL.md` | redacted (approval wording x4, conference abstract x1, local clock time x1, reference project x1, review notes folder x1) | `51e2991d80ef93e317a4ec654dda37de3457c7b69db5a773a02b67fdf53910c6` | `f269e5b48fe1429bbcb4164859b2b3c1baafef7da1bf514725fecbbaa9f98308` | `PREDICTIONS-RECORD.json`, `FREEZE.json` |
| `STAGE2-AMENDMENTS.md` | redacted (assistant application x4, assistant wording x3, local clock time x16, machine details x1, time zone x1) | `3ed95f29dd62390ed6be83246bc9ed583782d69bdb9a46ab951e3fcef075068b` | `46858e379d662f7419fa95c3375ac7537d76d506712e9cfdb79fa867787c8ff4` | `FREEZE-STAGE2.json`, `FREEZE-STAGE2-STROTHER.json` |
| `STAGE2-PROTOCOL.md` | redacted (approval wording x2, assistant wording x1, conference abstract x3, machine details x1) | `6471c1120f04399cf1b36bf8c64da37b4b58aba099bef787e5f8bd1675c45b84` | `3e5cfc9ceb318975940a484768c8ad4b9644d40da13f331e7bb18e2ccfa75aa6` | `STAGE2-RECORD.json`, `FREEZE-STAGE2.json` |
| `STAGE2-RECORD.json` | redacted (approval wording x3, assistant wording x1, conference abstract x3, machine details x1) | `207a1fa507cd2fc87c5588d7ea30e31f9ac80e196dd063ecfcccb0e180b82be4` | `2647c16ea5630318dfb8f764e7c142ab277e293e667c850a685a3424d35d8523` | `FREEZE-STAGE2.json` |
| `code/freeze.py` | adapted and redacted: the freeze checks accept the changes this release documents (tools/release_paths.py); the reference study's files that the code reads or imports are shipped in reference/flyvis-first-order (approval wording x1) | `f869b68c8056c41fbdc80df3353fa221e930446d2148b1b3ea442d23654cd9f7` | `02813062d7621198009622c0a2f6adf014f19f1439b988ecddd16fddddf259a9` | `FREEZE.json` |
| `code/stage2_freeze.py` | adapted: the freeze checks accept the changes this release documents (tools/release_paths.py) | `ce4be71f8f87bca99e296ae680a97b7b612f7c679b6ab7bd0375aaf9d47af0a4` | `117a91d40cf04d47419ac23532307eb1add073b5d7450789a89e32ee4d0761d3` | `FREEZE-STAGE2.json`, `FREEZE-STAGE2-STROTHER.json` |
| `code/stage2_run.sh` | adapted and redacted: the GPU lock helper is a copy shipped in code/gpu_lock.py; its lock file is named by GPU_LOCK; the Python comes from PYTHON (default .venv in the release root); the reference study's files that the code reads or imports are shipped in reference/flyvis-first-order; the write audit skips the FlyVis model folder, where flyvis builds its tables on first use (machine details x1) | `e283178673ba1dc7739d837e41ec566b3ca2771082a7fe8fadc2f7f292d451f1` | `6c45e2faa30636ff8b4a4291497a8c0a1a6427e381fc816a142bf9ceb805692d` | `FREEZE-STAGE2.json` |
| `code/stage2_score.py` | adapted: the record check accepts the reduced stage-2 records, which this release documents | `8cdf8518929c7a36e8581c7c06a0d4fd30795927b6bfaad71511d36bceb56e4c` | `9a0a9054dc621c6cf8e1d39e94a0137a77a6f2a9ebca398685bf2bb856ea3b89` | `FREEZE-STAGE2.json` |
| `code/stage2_simulate.py` | adapted: the confirmation run's gate also accepts the recorded replay check when the code differs from the recorded code only by this release's documented changes (paths and the time zone setting); the reference study's files that the code reads or imports are shipped in reference/flyvis-first-order | `4943402c49a99f078ea810e0e87fd6cc59015970ec78b3a46c34bc4d44469fe8` | `137a415ad7e7b48edfefd5e65f88853d5e655ef295f0db1a308450215c31a237` | `FREEZE-STAGE2.json` |
| `code/stage2_strother.py` | adapted: the freeze checks accept the changes this release documents (tools/release_paths.py) | `4be7edebe5590144b652f1077027309a4f5160d9868468c90014475ad599af1b` | `04f69fe90745662d075cbaa230b28ff04e21a101f55acb7d3d2af42b4039179b` | `FREEZE-STAGE2.json`, `FREEZE-STAGE2-STROTHER.json` |
| `config.json` | adapted: the reference study's files that the code reads or imports are shipped in reference/flyvis-first-order | `fbfd5c991f4fa08433ecfffb0e65ca40ea2135334eb957a7698a74bd1c6e33ea` | `5ca701a571cce5b0524b62ac02ade4096a17fd23827e115caac3a09dcc94c59f` | `PREDICTIONS-RECORD.json`, `FREEZE.json` |
| `extraction/A/notes-stage2.md` | redacted (assistant application x3, assistant wording x2, local clock time x3) | `ae7994ebafa805fa58c3626048a4841e4778beb86c11cf0936eb05368b23f9ea` | `409fb1902e6c990d6f90118093cb5196b893ea94637124696b393ee467db2f1b` | `FREEZE-STAGE2-STROTHER.json` |
| `extraction/A/notes.md` | redacted (assistant wording x1, local clock time x1) | `fcb7dc1b4fff779802d24d4298a60ea44d325bd029266a5bae0e58f2999d6e43` | `4fda9e67b32db2bb7cb0b9a83d5fc9caf65b85bfba94ed814d03e890f2290288` | `FREEZE.json` |
| `extraction/B/notes-stage2.md` | redacted (assistant application x1, assistant wording x4, conference abstract x1, local clock time x1, related write-up x1) | `a1aa62d97dc4f109519e162cadeae40ab49271f99aa7e02f205cd7a2a42a6ac4` | `c0924d7cbdd4a6390c415c1d7b4fb07632ca78b29ac3b9fe9500db227e14c072` | `FREEZE-STAGE2-STROTHER.json` |
| `extraction/B/notes.md` | redacted (assistant wording x3, conference abstract x1, local clock time x2, related write-up x1) | `f6246b12051c36ceb080ba98899f5fdc9c050ce0b891a9c158168b94695a98a3` | `dc543eebf64c252f293cd6a36510777685ba112594b76d2dc454113966725b71` | `FREEZE.json` |
| `extraction/EXTRACTION-RULES.md` | redacted (assistant wording x1, companion project x1, conference abstract x1, reference project x1, related write-up x1) | `f832cf39fa907dabd5d3f93306cac0213e563cbbca3a2df901450fb08626eb17` | `ecf38d6857f311eb6ba0c0d37b9f5f976f89c21b189ec5c09953750464ba56d8` | `PREDICTIONS-RECORD.json`, `FREEZE.json` |
| `extraction/MERGE-DECISIONS.md` | redacted (approval wording x1, local clock time x3) | `0e4485b8eb760aa59841ce5d0d76bbcef160ac89a56f6e77bcd6e1a515534db1` | `9242f77018a65f790bbc0fca946cae9d138fabf5ac465bc3aa0898b67d0e0b85` | `FREEZE.json` |
| `extraction/stage2/MERGE-DECISIONS.md` | redacted (local clock time x6) | `2ecb5fd7131a491251dd56e0cf80779716323227c9a7019aeb8fe6f16a8adb9f` | `e28123bae4603765b1465fdd160fdc7db9e8b3c7d2836d147fe163e68b6ad2da` | `FREEZE-STAGE2-STROTHER.json` |
| `extraction/stage2/settlements.json` | redacted (local clock time x2) | `85f5c43925d36dadad01eadf146d26c6c0e63ea5aa5c76a57e82680cfd1a6933` | `46bcefa3e483c1b787edbc4b17166576cd5cb855904b95bf0f1c6dc9987ad9e8` | `FREEZE-STAGE2-STROTHER.json` |
| `provenance/Makefile-at-freeze` | redacted (environment path x1) | `6e7b434b86fc9f889487aaef8db0f453ede41af37aa67a1fe7c25475e7756953` | `ebd6862682ac80db3b864d85ff03930a7f4d2f545f109317501aa7310aa23977` | `FREEZE.json` |
| `reference/flyvis-first-order/02-Code/stage1/common.py` | redacted (time zone x1) | `e465cb2e1e16b52433e9a642365f2ca6c910ef8d60dbe1bbe91146de648fff50` | `9834aeb2355a31a04faf0cc7611047f02983b6f0b72e118196f94f4884980f41` | - |
| `results/stage2/confirmation-run.json` | redacted (machine details x1, platform string x1); shipped inside `data/saved-outputs/study-results.tar.xz` | `578c90294180abccdb4c94405c53995823c56d70a568a410067ee4eb68fade50` | `b79ef04ba3038d13c15eed0c0bb573556061b0f0303d4fc2406451f4bcb3a15e` | `FREEZE-STAGE2.json` |
| `results/stage2/development-run.json` | redacted (machine details x1, platform string x1); shipped inside `data/saved-outputs/study-results.tar.xz` | `1a084a33b1fc932d2e22ba2f015806bb3e245007afe5b0300757310258e63f89` | `101917fa1939bfd4a70b0f2219d0a73fc089f39cd17b613caa776efec2c6db2c` | `FREEZE-STAGE2.json` |
| `results/stage2/integrity-confirmation.json` | redacted (machine details x1, platform string x1); shipped inside `data/saved-outputs/study-results.tar.xz` | `3cb8454397b9a746406faf83a0a2825f2960156a3fd4a2f99e5212e4aaa561b4` | `289e6df1af1040ce8ce90930c0410f27be3693b214d3e6ac73db2addd3199331` | `FREEZE-STAGE2.json` |
| `results/stage2/replay-check.json` | redacted (machine details x1, platform string x1); shipped inside `data/saved-outputs/study-results.tar.xz` | `a535f5fcc921b66de6b52f2fad0f8317fc716c211c34f8ff0185d8859dbd9bdb` | `dea30369c3afed882c81cff23be2b177ddb72a92e0fcb855c4dd3a20906c036d` | `FREEZE-STAGE2.json` |
| `results/stage2/strother/results/confirmation/recheck.json` | redacted (absolute path x1); shipped inside `data/saved-outputs/study-results.tar.xz` | `2268ae0af316859207c9ef6aa6eb127d8787961518c2e2ceca43f94a68716ddb` | `98de84cc405f68dee82c20fa188a6cb09fc8ab321fe0a06a0db1d80d405758be` | - |
| `results/stage2/{confirmation,development}/*/*/s*.npz` | reduced (1200 files): every array of the record except its time trace (`trace`); the scoring and the rechecks read peaks, direction selectivity and denominators only, and the originals (173 MB for the confirmation records) are not shipped (size); shipped inside `data/saved-outputs/study-results.tar.xz` | each in `release-changes.json` | each in `release-changes.json` | `FREEZE-STAGE2.json` |

## Files named in freeze records that are not shipped

| Original path | Reason | Original SHA-256 |
|---|---|---|
| `RESULTS.md` | the study's written report of results, here in its stage-1 version; not shipped, because the manuscript and the saved outputs give the results | `b3bbf4d0f29f2ec84cdacf813f4a3bb3912bd7ec6b9cef351f97cccd82091a50` |
| `reference/flyvis-first-order/05-Notes/BIOLOGY-ANSWER-KEY.md` | the reference study's notes on its biology key; not part of either release (the key itself is shipped) | `218943717a8a90d91ab4af8efb8ac8e8616f7dc8e96754d19eab4eb1c8b20da6` |
| `results/stage2/logs/audit-confirmation.json` | log record of the simulation run (write audit or end-of-run watcher); logs are not part of the release. results/stage2/integrity-confirmation.json, which is shipped, reports both | `1ae1edaa18ca496f5a670700c500b914f7e2e46f3f2f4fa37133ce7153f168a0` |
| `results/stage2/logs/audit-development.json` | log record of the simulation run (write audit or end-of-run watcher); logs are not part of the release. results/stage2/integrity-confirmation.json, which is shipped, reports both | `5dc579949cb82178dd7c62dae76c9c347c1859ab8926f4b273f03125aec7e0f1` |
| `results/stage2/logs/audit-replay.json` | log record of the simulation run (write audit or end-of-run watcher); logs are not part of the release. results/stage2/integrity-confirmation.json, which is shipped, reports both | `bc702705f5c7f80cee1b738cf260af6d157c677ffe1a782c4b030984d0587453` |
| `results/stage2/logs/confirmation-ended.json` | log record of the simulation run (write audit or end-of-run watcher); logs are not part of the release. results/stage2/integrity-confirmation.json, which is shipped, reports both | `d7498852e5f555b472f8dd6841ecb081e7da3ecfdb48a05edd3c71274d77dcf0` |
| `sources/ammer-dissertation.pdf` | source document by other authors (copyright); not shipped. sources/README.md gives its citation, size and SHA-256 | `eea3b405c6c1065e1d879200b62a5fc9f8d697ae31557929c4c0e998857c829b` |
| `sources/serbe-dissertation.pdf` | source document by other authors (copyright); not shipped. sources/README.md gives its citation, size and SHA-256 | `5f799bb86ed60be4f574a4ac071d2f6617de9360ecee2ce40b4141eb7e0040b3` |
| `sources/strother-2017-supplement.pdf` | source document by other authors (copyright); not shipped. sources/README.md gives its citation, size and SHA-256 | `6d1da44a868575a90d817cc4c6f6ded5a3dfacc248d3c3638a4afd3a36fcaea8` |
| `sources/strother-2017.pdf` | source document by other authors (copyright); not shipped. sources/README.md gives its citation, size and SHA-256 | `1302dee6c8987aeab9c29193e7bd46cfb66e5abd7984163b215e8b7161b78958` |
