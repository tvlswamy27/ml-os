# ML-OS

**Machine Learning Operating System (ML-OS)** is a local-first ML engineering operating system designed around explainable, structured ML workflows. Rather than functioning as a black-box AutoML library, ML-OS acts as a cognitive engineering hub to orchestrate, optimize, and generate reproducible ML pipelines.

---

## Architecture

ML-OS coordinates operations using the following core layers:

1. **ProjectMemory (Blackboard)**: The central state storage system and single source of truth (`.mlos/project_config.yaml`). It records session-by-session execution histories, planning facts, datasets, and reflection feedbacks.
2. **MLOSEngine**: The main engine coordinating the execution lifecycle across templated subsystems.
3. **WorkflowEngine**: Sequentially coordinates stages (Analysis, Feature Selection, Plan, Decision, Generate, Execute, Evaluation, Reflect, Learn, Knowledge).
4. **Command Line Interface (CLI)**: Command-line interface (`mlos`) for workflow execution, diagnostics, learning, and local configuration management.
5. **Studio Workspace**: A Flask and Vanilla JS web console presenting visual dashboards for dataset analysis, target distributions, pipeline runs, and side-by-side model experiment comparisons.

---

## Key Capabilities

* **Dataset Audit & Analysis**: Deep profiling (missingness, uniqueness, datatypes, anomalies, target leakage, imbalance).
* **Feature Selection & Engineering**: Identifies redundant feature groups, multicorrelation, and computes Variance Inflation Factors (VIF).
* **Meta Reasoning & Planning**: Declares hypotheses and builds topological execution schedules.
* **Dynamic Pipeline Compilation**: Automatically assembles and packages preprocessing and model code blocks into standalone scripts.
* **AutoML Battle & Optimization**: Performs cross-validated model selections across baseline model topologies.
* **Reflection & Knowledge Capture**: Automatically logs execution results and updates rule repositories for future optimizations.

---

## Installation

Install the package locally in editable mode:

```powershell
pip install -e .
```

---

## Basic CLI Usage

Initialize a new project workspace:
```powershell
mlos init
```

Analyze a dataset:
```powershell
mlos analyze --dataset playground/sample.csv --target target_col
```

Run AutoML pipeline execution:
```powershell
mlos run --dataset playground/sample.csv --target target_col
```

Check the integrity of the environment:
```powershell
mlos doctor
```

Examine tracked experiments:
```powershell
mlos experiments list
```

---

## Launching the Studio Web UI

To start the local web console workspace, execute:

```powershell
mlos ui
```

Or run the server module directly:

```powershell
python mlos/ui/app.py
```

Open your browser to `http://127.0.0.1:5000` to interact with the dashboard.

---

## Running the Test Suite

Run unit and integration tests using `pytest`:

```powershell
pytest -q
```
