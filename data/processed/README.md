# Generated data

This directory contains tables created by the repository's preparation scripts.
The generated patient-level files are intentionally ignored by Git: they can be
large, and GitHub is not the right place for working copies of health data.

To recreate the ShanghaiT2DM outputs, follow
[`docs/SHANGHAI_T2DM_PIPELINE.md`](../../docs/SHANGHAI_T2DM_PIPELINE.md).
The preparation program never changes the downloaded Excel workbooks.

Feature engineering and baseline-model outputs are generated under
`shanghai-t2dm/modeling/`. Their method and field meanings are documented in
[`docs/SHANGHAI_BASELINE_MODEL.md`](../../docs/SHANGHAI_BASELINE_MODEL.md) and
[`docs/FEATURE_DICTIONARY.md`](../../docs/FEATURE_DICTIONARY.md).
