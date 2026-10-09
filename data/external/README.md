# External data inventory for the Virtual Patient Model

Downloaded and audited on 2026-10-06. The raw archives, extracted datasets, references, and third-party tools in this directory are intentionally ignored by Git. Only this guide, `.gitignore`, and `MANIFEST.csv` should be committed.

## Final recommended list

| Priority | Source and local location | Verified local contents | Recommended role | License / access |
| --- | --- | --- | --- | --- |
| 1 | [ShanghaiT1DM and ShanghaiT2DM v5](https://www.nature.com/articles/s41597-023-01940-7) in `datasets/shanghai-v5/` | 100 people with T2D in 109 recording files and 12 people with T1D in 16 recording files. Each recording has 3-14 days of 15-minute CGM plus timed dietary intake, insulin, non-insulin medication, and clinical/laboratory summaries. | Primary real-world T2D dataset for glucose forecasting and two-hour post-meal response modelling. Split by the base patient ID, not by recording or time window. | [CC BY 4.0, Figshare DOI 10.6084/m9.figshare.20425518.v5](https://doi.org/10.6084/m9.figshare.20425518.v5) |
| 2 | [CGMacros v1.0.0](https://physionet.org/content/cgmacros/1.0.0/) in `datasets/cgmacros-v1.0.0/` | 45 participants: 14 T2D, 16 prediabetes, and 15 healthy. The local tabular extraction contains 687,580 one-minute rows with Libre and Dexcom CGM, Fitbit heart rate/activity, meal time and macros, BMI, HbA1c, blood tests, and microbiome tables. The original ZIP retains meal photos; the photos were not separately extracted. | Multimodal meal/activity model development, feature ablation, and transfer testing. The T2D subgroup is small, so it should supplement rather than replace ShanghaiT2DM. | [CC BY-NC-SA 4.0](https://physionet.org/content/cgmacros/1.0.0/) — non-commercial restriction applies. |
| 3 | [Indian Food Composition Tables 2017](https://www.nin.res.in/ebooks/IFCT2017.pdf) in `references/IFCT2017.pdf` | Official ICMR-NIN reference covering 528 Indian foods and 151 food components. | Map Indian meal descriptions to carbohydrate, fibre, protein, fat, and energy features. This is a food reference, not patient or CGM data. | Official ICMR-NIN publication; review publication/reuse terms before redistributing extracted tables. |
| 4 | [BIG IDEAs v1.1.3](https://physionet.org/content/big-ideas-glycemic-wearable/1.1.3/) selective download in `datasets/big-ideas-cgm-food-v1.1.3/` | Demographics, Dexcom CGM, and food logs for all 16 participants: 36,962 numeric glucose rows and 1,421 food-log rows. Local HbA1c range is 5.3-6.4%. All 33 selected source files match the official SHA-256 list. | Pretraining and testing meal/CGM feature engineering in high-normal or prediabetic participants. Do not use it as a T2D evaluation cohort. | [Open Data Commons Attribution 1.0](https://physionet.org/content/big-ideas-glycemic-wearable/1.1.3/) |
| 5 | [Colas et al. 2019 supplement](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0225817) in `datasets/colas-2019/` | 208 CGM case files, 114,912 readings, sampled every five minutes for at least 24 hours. Participants had hypertension but no diagnosed diabetes at baseline; 17 developed T2D during follow-up. | Secondary work on glucose dynamics and progression risk. It lacks meals and is not a direct T2D postprandial-response cohort. | [CC BY 4.0](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0225817) |
| 6 | [Synthea latest CSV sample](https://synthetichealth.github.io/downloads.html) in `datasets/synthea-sample-csv/` | The downloaded package contains 108 synthetic patient rows, including six patients with a Type 2 diabetes condition record and 34 with a prediabetes record. It contains synthetic EHR tables but no CGM trajectory. | Application demos, database/schema testing, and synthetic patient timelines only. Do not use it to estimate real glucose physiology or clinical performance. | Synthea states the sample is free from cost, privacy, and security restrictions. |
| 7 | [Glucose-ML Project](https://github.com/Augmented-Health-Lab/Glucose-ML-Project) at commit `decf266` in `tools/Glucose-ML-Project-main/` | Harmonisation/download scripts, pre-standardised open CGM resources, metadata, preprocessing tools, and case studies. The project reports 44.9 million CGM samples from more than 4,300 people across 20+ datasets; this local repository snapshot occupies about 298 MB. | Reuse its harmonisation conventions and benchmark preparation. Treat the licences of every underlying dataset separately; the repository's MIT licence does not replace them. | MIT for repository code; underlying dataset licences vary. |

## Recommended modelling sequence

1. Start with ShanghaiT2DM. Convert each recording to a common time-series schema and create train/validation/test partitions by the 100 base patient IDs before generating windows.
2. Define the initial target precisely, for example glucose at +120 minutes, change from meal baseline at +120 minutes, or postprandial incremental area under the curve. Keep this as research output, not a clinical treatment recommendation.
3. Add CGMacros for carbohydrate/macronutrient, heart-rate, and activity features. Evaluate the 14 T2D participants separately from the healthy and prediabetes groups.
4. Use IFCT to normalise Indian meal names and portions. Keep the original food text and the mapped nutrient fields so mappings remain auditable.
5. Use BIG IDEAs and Colas only for representation learning, robustness checks, or progression-oriented analyses. Use Synthea only for software integration and UI demonstrations.

A practical common schema is: `source`, `participant_id`, `episode_id`, `timestamp`, `glucose_mg_dl`, `meal_timestamp`, `carbohydrate_g`, `protein_g`, `fat_g`, `fibre_g`, `activity`, `heart_rate_bpm`, `medication`, and static clinical covariates. Not every source supplies every field, so missingness must remain explicit.

## Data-quality and safety notes

- CGMacros' `DataDictionary_Bio.csv` labels `A1c PDL (Lab)` as mmol/mol, but its published range is 4.6-8.5 and the study uses percentage thresholds. Treat this as a likely metadata unit error and verify HbA1c as percent before modelling.
- CGMacros dates are shifted for privacy. BIG IDEAs timestamps are also de-identified/time-shifted. Relative timing within a participant is useful; calendar-date interpretation is not.
- Do not join people across independent datasets or assume participant identifiers refer to the same person.
- Preserve glucose units explicitly. The downloaded CGM data uses mg/dL, while some clinical fields use SI units.
- Perform imputation, scaling, meal parsing, and window generation after patient-level splitting to avoid leakage.
- These datasets are for research. They do not by themselves validate diagnosis, dosing, or other clinical decisions.
- Keep raw human health data local. Do not commit or push `archives/`, `datasets/`, `references/`, or `tools/`.

## Integrity verification

- Shanghai archive: valid ZIP; all 130 entries readable; the Figshare-supplied MD5 matches.
- CGMacros: valid ZIP with 3,593 entries; the archive plus six documentation files match all seven published SHA-256 values.
- BIG IDEAs selective download: all 33 selected data files match the PhysioNet `SHA256SUMS.txt` values.
- Synthea, Colas, and Glucose-ML: archives passed ZIP structure checks; local SHA-256 values are recorded in `MANIFEST.csv` because their download pages did not publish matching archive hashes.
- IFCT: the local file has a valid PDF signature and a local SHA-256 value in `MANIFEST.csv`.

## Deliberately not downloaded

- [AI-READI v3.0.0](https://docs.aireadi.org/): 2,280 participants, 15 modalities, and about 3.82 TB. It is an excellent future multimodal T2D source, but it requires acceptance of a custom licence, some variables require controlled access, and it does not fit the available local storage.
- Full BIG IDEAs wearable package: about 4.7 GB compressed and 34.1 GB uncompressed. Only demographics, Dexcom CGM, and food logs were selected because they directly support the current model and fit locally.
- GlucoInsight: potentially useful T2D CGM/Fitbit/diet data, but no verified public patient-level download was found.
- ICMR-INDIAB and similar Indian cohort data: access is request-based rather than an immediate open download. No open Indian patient-level dataset combining T2D, linked CGM, meals, wearables, and clinical records was verified in this audit.
- OhioT1DM, PhysioCGM, and similar sources: excluded from the initial list because they are T1D-only or require a data-use agreement and do not match the first T2D objective.

## Local layout

```text
data/external/
  archives/      Original downloaded ZIP files
  datasets/      Extracted or selectively downloaded patient datasets
  references/    Indian food-composition reference
  tools/         Glucose-ML harmonisation toolkit and resources
  MANIFEST.csv   Sizes, hashes, source links, licences, and verification results
  README.md      This selection and usage guide
```
