# ShanghaiT2DM Model Feature Dictionary

## How to read this document

One row in `model_features.csv` represents one recorded meal that passed the
initial eligibility rules. A **feature** is information the model may use as an
input. The **target** is the answer the model tries to predict.

The program uses 43 numeric features. Identifiers and original meal text remain
in the table for tracing and review, but the model does not use them.

## Fields kept for identification and audit only

| Field | Meaning | Why it is not a model input |
| --- | --- | --- |
| `source_dataset` | Name of the source dataset | It identifies provenance, not physiology |
| `cohort` | Type 2 diabetes cohort label | It has the same value for every row |
| `patient_id` | Base patient identifier | Using it could teach the model to recognise people |
| `recording_id` | Visit/recording identifier | It could memorise a recording instead of learning a general pattern |
| `split` | Train, validation, or test assignment | This controls evaluation and must not influence a prediction |
| `meal_id` | Unique meal identifier | It is for tracing one prediction back to one event |
| `timestamp` | Recorded meal date and time | The model receives derived time features instead |
| `dietary_intake_raw` | Original meal description | Version 1 uses transparent flags and reported weights rather than raw text |
| `source_file`, `source_sheet`, `source_row` | Original workbook location | These fields provide an audit trail only |

## Glucose-history features

All glucose values use **mg/dL**, meaning milligrams of glucose per decilitre.
Only readings at or before the meal are used.

| Feature | Simple meaning | Calculation and missing-value meaning |
| --- | --- | --- |
| `baseline_glucose_mg_dl` | Glucose at the recorded meal time | Direct meal-time CGM value |
| `glucose_lag_15_min_mg_dl` | Glucose 15 minutes before the meal | Missing when there is no reading at that exact time |
| `glucose_lag_30_min_mg_dl` | Glucose 30 minutes before the meal | Missing when there is no exact reading |
| `glucose_lag_60_min_mg_dl` | Glucose 60 minutes before the meal | Missing when there is no exact reading |
| `glucose_lag_120_min_mg_dl` | Glucose two hours before the meal | Missing when there is no exact reading |
| `glucose_change_prev_15_min_mg_dl` | Rise or fall during the previous 15 minutes | Baseline minus the 15-minute lag; positive means glucose rose |
| `glucose_change_prev_30_min_mg_dl` | Rise or fall during the previous 30 minutes | Baseline minus the 30-minute lag |
| `glucose_change_prev_60_min_mg_dl` | Rise or fall during the previous hour | Baseline minus the 60-minute lag |
| `glucose_change_prev_120_min_mg_dl` | Rise or fall during the previous two hours | Baseline minus the 120-minute lag |
| `glucose_mean_prev_120_min_mg_dl` | Average recent glucose | Mean of available readings from two hours before the meal through the meal time |
| `glucose_std_prev_120_min_mg_dl` | How spread out recent glucose values are | **Standard deviation**; a larger number means more variability |
| `glucose_min_prev_120_min_mg_dl` | Lowest recent glucose | Minimum during the previous two hours |
| `glucose_max_prev_120_min_mg_dl` | Highest recent glucose | Maximum during the previous two hours |
| `glucose_range_prev_120_min_mg_dl` | Distance between recent high and low values | Maximum minus minimum |
| `glucose_observations_prev_120_min` | Number of recent readings available | Usually nine for complete 15-minute data, including the meal-time reading |

## Meal and time features

| Feature | Simple meaning | Calculation and limits |
| --- | --- | --- |
| `meal_hour_sin`, `meal_hour_cos` | Time of day represented as a circle | Sine and cosine keep 23:59 close to 00:00; neither value is meaningful alone |
| `meal_is_weekend` | Whether the recorded date is Saturday or Sunday | `1` for weekend and `0` otherwise |
| `minutes_since_previous_meal` | Time since the previous recorded meal | Missing for the first recorded meal in a recording; unrecorded meals remain a limitation |
| `reported_food_weight_g` | Sum of food weights explicitly written in grams | For “Rice 100 g, Vegetable 150 g,” the value is 250; it is not carbohydrate grams |
| `food_items_with_reported_weight` | Count of explicit gram quantities | The example above has two quantities |
| `meal_text_length_characters` | Length of the meal description | A simple measurement of description detail, not nutritional quality |
| `meal_contains_rice` | Meal text mentions rice | Transparent keyword flag: `1` yes, `0` no |
| `meal_contains_noodle` | Meal text mentions noodles or vermicelli | Keyword flag |
| `meal_contains_bread` | Meal text mentions bread, buns, or toast | Keyword flag |
| `meal_contains_fruit` | Meal text mentions one of the listed common fruits | Keyword flag; it cannot recognise every fruit name |
| `meal_contains_vegetable` | Meal text mentions “vegetable” or a listed vegetable | Keyword flag; it is not a measured vegetable quantity |
| `meal_contains_animal_protein` | Meal text mentions meat, fish, egg, or shrimp terms | Keyword flag; it is not measured protein grams |
| `meal_contains_dairy` | Meal text mentions milk or yogurt | Keyword flag |
| `meal_contains_root_or_corn` | Meal text mentions potato, yam, corn, or lotus root | Keyword flag |

These keyword fields are intentionally simple. They make the baseline explainable,
but they do not replace food-composition mapping or nutrient measurements.

## Medication-at-meal features

`CSII` means continuous subcutaneous insulin infusion, commonly called an insulin
pump. Blank event cells mean no event was recorded at that exact meal timestamp.

| Feature | Simple meaning | Representation |
| --- | --- | --- |
| `csii_bolus_insulin_iu_at_meal` | Pump bolus recorded at the meal | Insulin units; `0` when no numeric bolus was recorded at that timestamp |
| `csii_basal_insulin_iu_per_hour_at_meal` | Pump basal setting recorded at the meal | Insulin units per hour; `0` when no numeric setting was recorded there |
| `has_recorded_csii_bolus_at_meal` | Whether a numeric pump bolus was recorded | `1` yes, `0` no |
| `has_recorded_csii_basal_setting_at_meal` | Whether any pump basal entry was recorded | `1` yes, `0` no; includes numeric and text events |
| `has_recorded_subcutaneous_insulin_at_meal` | Whether an injected-insulin event was recorded | `1` yes, `0` no |
| `has_recorded_non_insulin_medication_at_meal` | Whether a non-insulin diabetes medicine was recorded | `1` yes, `0` no |
| `has_recorded_intravenous_insulin_at_meal` | Whether intravenous insulin was recorded | `1` yes, `0` no |

These fields describe recorded events, not confirmed medication adherence.

## Clinical features

| Feature | Simple meaning | Unit or coding |
| --- | --- | --- |
| `sex_female` | Sex code supplied in the source summary | `1` when source code is female, `0` when source code is male |
| `age_years` | Age at the associated recording/visit | Years |
| `bmi_kg_m2` | Body mass index | kg/m²; weight divided by height squared |
| `diabetes_duration_years` | Time since diabetes diagnosis | Years |
| `hba1c_percent` | Approximate average glucose exposure over recent months | Percent; some source values are unavailable/non-numeric |
| `fasting_plasma_glucose_mg_dl` | Laboratory glucose measured after fasting | mg/dL; distinct from the meal-time CGM value |

## Target column

| Field | Meaning |
| --- | --- |
| `spike_within_120_min` | `1` when glucose reaches at least 180 mg/dL or rises by at least 40 mg/dL during the next 120 minutes; otherwise `0` |

The target contains future information and is never an input feature.

## What happens when an input is missing

Logistic Regression requires a number in every input position. During training,
the pipeline learns the **median** of each feature from training patients only and
uses it to fill missing values. The median is the middle observed value after
sorting. The pipeline also creates a missingness indicator so it can distinguish an
observed median from a value that was filled.

The validation and test patients never contribute to those median or scaling
values. This prevents information from the evaluation groups leaking into training.
