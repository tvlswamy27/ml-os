# ML-OS AutoML Engine & Experimentation Architecture (Milestone 3 & 3.5)

## Overview
This document details the architecture of the **ML-OS AutoML Engine & Experimentation Platform**. ML-OS automatically profiles raw datasets, queries a plugin-based Model Catalog, formulates tailored preprocessing pipelines, trains and evaluates candidate models via cross-validation and hyperparameter optimization (HPO), generates multi-objective leaderboards and explainability reports (SHAP, Permutation, MDI), tracks experiments, persists reusable pipelines, registers model versions, and records end-to-end lineage.

---

## 1. System Architecture

```
                                  Dataset
                                     ↓
                          Dataset Intelligence
                                     ↓
                            Model Catalog Plugins
                                     ↓
                         Model Recommendation Engine
                                     ↓
                          Preprocessing Planner
                                     ↓
                        AutoML Training & HPO Engine
                                     ↓
       ┌─────────────────────────────┼─────────────────────────────┐
       ↓                             ↓                             ↓
Leaderboard & Audit        Explainability Reports       Production Recommendation
 (csv/json/md)               (SHAP/Permutation)              (automl_summary)
       │                             │                             │
       └─────────────────────────────┼─────────────────────────────┘
                                     ↓
                   Experiment Tracker & Lineage Logger
                     (.mlos/experiments, lineage.json/md)
```

---

## 2. Plugin-Based Model Catalog

The `ModelCatalog` manages models declaratively via capability-based metadata (`ModelMetadata`):

- **Supported Tasks**: Classification, Regression, Clustering, Forecasting, Anomaly Detection.
- **Capabilities Tracked**:
  - `handles_missing_values`, `handles_categorical`, `supports_sparse`, `supports_multiclass`, `supports_multilabel`, `supports_gpu`, `supports_probability`, `supports_feature_importance`, `supports_shap`, `supports_hpo`, `supports_partial_fit`, `supports_online_learning`.
- **Resource Estimates**: Estimated memory (MB), training speed (1-10), inference speed (1-10), interpretability score (1-10).

---

## 3. Dataset Intelligence

The extended `DatasetAnalyzer` automatically detects:
- **10 Problem Types**: Regression, Binary Classification, Multiclass Classification, Multilabel, Time Series, Forecasting, Anomaly Detection, Clustering, Recommendation, NLP, Computer Vision metadata.
- **Column Attributes**: Ordinal columns, Text features, Datetime features, ID columns, Target leakage columns, High-cardinality features, Skewed features, Constant columns, Near-zero variance features, Class imbalance ratios, Outlier counts.

---

## 4. Model Recommendation & Preprocessing Planner

1. **ModelRecommender**: Ranks candidates based on dataset size, feature count, missing values, class imbalance, interpretability preference, and resource limits.
2. **PreprocessingPlanner**: Generates model-family specific transformations:
   - **Tree Models**: Median imputation + Ordinal/OneHot encoding; no feature scaling.
   - **Linear Models**: Median imputation + OneHot encoding + StandardScaler / RobustScaler.
   - **Categorical / Boosting**: Direct categorical passing or OrdinalEncoder.

---

## 5. Training, HPO & Explainability

- **CV Training**: 5-Fold StratifiedKFold (classification) or KFold (regression) with identical seeds and splits across all models.
- **Pluggable HPO**: `GridSearchBackend`, `RandomSearchBackend`, `OptunaBackend` (optional), and `BayesianBackend`.
- **Explainability Engine (`AutoMLExplainer`)**: Automatically selects Tree MDI, Linear Normalized Coefficients, Permutation Importance, or SHAP.

---

## 6. Experiment Tracking, Registries & Lineage (Milestone 3.5)

- **ExperimentTracker**: Logs SHA-256 dataset fingerprints, problem types, metrics, CV scores, timing, memory, parameters, artifacts, and environment.
- **PipelineRegistry**: Supports `save_pipeline()`, `load_pipeline()`, `export_pipeline()`, `clone_pipeline()`, `list_pipelines()`, `delete_pipeline()`.
- **ModelRegistry**: Manages model versioning across `staging`, `production`, `archived`, and `rollback` stages.
- **LineageTracker**: Generates `lineage.json` and Mermaid DAG `lineage.md` mapping Dataset → Features → Pipeline → Model → Experiment → Artifacts → Deployment.

---

## 7. CLI Subcommands

- `mlos run`: Executes full end-to-end workflow + AutoML Engine.
- `mlos experiments`: List, inspect (`--show`), and compare (`--compare`) experiment runs.
- `mlos pipeline`: List (`--list`) and export (`--export`) versioned pipelines.
- `mlos registry`: Manage model version deployment stages (`--transition`).
- `mlos lineage`: View end-to-end dataset-to-model lineage records.
