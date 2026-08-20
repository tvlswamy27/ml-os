# Phase 4.1 Experiments Report — Historical Experiments & Model Leaderboard

This report documents the design, implementation, and verification for Phase 4.1 of the Machine Learning Operating System (ML-OS).

---

## 1. Implementation Overview

Phase 4.1 integrates historical experiment persistence with an AutoML model leaderboard, enabling users to view and compare candidate models evaluated during previous AutoML runs.

The complete flow is established as follows:

```
AutoML Search (Orchestrator HPO)
    ↓
Candidate Trial Results (ExperimentTrial objects)
    ↓
ExperimentTracker
    ↓
.mlos/experiments/experiments.json (Local project persistence)
    ↓
GET /api/projects/{project_id}/experiments (FastAPI route with authorization)
    ↓
Historical Experiment / Leaderboard UI (React Page)
```

---

## 2. Trial Schema & Persistence Format

### 2.1 ExperimentTrial Schema
Each individual candidate model evaluation is modeled as an `ExperimentTrial` (defined in [`mlos/experiment/tracker.py`](file:///c:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/experiment/tracker.py)):

| Field Name | Type | Description |
|---|---|---|
| `trial_id` | `str` | Unique trial identifier (e.g. `trial-<model_id>`) |
| `model_name` | `str` | Human-readable name of the candidate model |
| `estimator_class` | `str` | Full python import path of the estimator class |
| `metric` | `str` | The primary evaluation metric name |
| `score` | `float` | Best metric score achieved by the trial |
| `cv_mean` | `float` | Cross-validation score mean |
| `cv_std` | `float` | Cross-validation score standard deviation |
| `cv_scores` | `list[float]` | Individual scores across CV folds |
| `parameters` | `dict[str, Any]` | Best hyperparameter combination searched |
| `rank` | `int` | Rank of this model relative to others in the HPO loop |
| `status` | `str` | Execution status: `SUCCESS` or `FAILED` |
| `selected` | `bool` | Flag designating if this candidate was selected as the winner |
| `duration_seconds`| `float` | Execution duration in seconds |
| `error` | `str \| None` | Error stack/message if the candidate run failed |

### 2.2 Serialization & Persistence
Trials are stored inside `.mlos/experiments/experiments.json` located within the project directory. The file maintains a dictionary of experiments keyed by `experiment_id`.
Inside each experiment dictionary, candidate trials are saved as a serialized list under `candidate_trials`.

Large items (such as pandas DataFrames, fitted estimators, or binary model objects) are **never** serialized inside the JSON file. Instead, they remain stored under `artifacts/` with relative paths referenced in the experiment logs.

---

## 3. AutoML Capture Flow

The capture and persistence flow follows these steps:
1. `AutoMLOrchestrator` runs the HPO search across estimators.
2. The orchestrator returns a list of results containing scores, params, CV splits, errors, and timing.
3. `MLOSEngine` invokes its private method `_track_experiment`, converting results into a list of structured `ExperimentTrial` objects.
4. `ExperimentTracker.log_experiment` writes the records to disk in `.mlos/experiments/experiments.json`.
5. The winning candidate is automatically marked with `selected=True` and assigned `rank=1`. Failed candidates store error information safely.

---

## 4. API Endpoints & Authorization

### 4.1 Endpoint
`GET /api/projects/{project_id}/experiments`
- Returns a list of all logged experiment runs for the project.
- Sanitizes paths (converts absolute filesystem paths of artifacts into relative project paths).
- Standard Response Schema is defined by `ExperimentRecordResponse` in `mlos/ui/api/schemas.py`.

### 4.2 Authorization & Security Isolation
- **Authentication**: FastAPI checks session cookies using the `get_current_user` dependency helper.
- **Workspace isolation**: Rejects requests with `403 Forbidden` if the authenticated user is not a member of the workspace associated with the project.
- **Path Traversal Prevention**: Resolves project paths via `ProjectService.validate_project_path` to prevent path injection or traversal.
- **Sensitive Data**: Excludes internal files, system paths, and secrets.

---

## 5. Backward Compatibility

The system maintains backward compatibility with older `experiments.json` records (pre-Phase 4.1) which do not contain candidate trials.
- `ExperimentTracker._load()` parses the legacy file format without raising errors.
- If `candidate_trials` is missing, the endpoint returns an empty array `[]` for that run's trials, allowing the frontend to render the record gracefully without crashing.

---

## 6. Verification Results

### 6.1 Backend Tests
All 243 backend pytest cases passed successfully:
- Focused tests verify:
  1. Trial serialization.
  2. Backward-compatible loading.
  3. Leaderboard ranking.
  4. Project isolation & workspace checks (unauthenticated → 401, unauthorized → 403).

### 6.2 Real Persistence Verification
A dedicated python verification script (`scratch/verify_persistence.py`) was run. It verified:
1. Candidate evaluation trials are successfully stored in `.mlos/experiments/experiments.json`.
2. Property assertions pass (ranks, CV means, selected indicators, parameters).
3. The process can be shut down/restarted, and a fresh tracker loads the data perfectly without re-running AutoML.

---

## 7. Frontend Leaderboard UI

The React page at `web/src/pages/Experiments.tsx` was implemented to display the leaderboard.
- **Experiment Selector**: Users can switch between historical runs.
- **Resource Cards**: Displays run details like peak memory, training duration, and dataset fingerprint.
- **Interactive Leaderboard Table**: Shows ranks, names, estimator classes, primary scores, CV standard deviation, training durations, execution statuses (with red errors for failures), and hyperparameter tags. The selected winning candidate displays a gold 🏆 badge.
- **Run History Comparison**: Compares the metrics across multiple historical experiments in a clean comparison table.

---

## 8. Explicit Scope Boundaries

This implementation is restricted to **Phase 4.1 — Historical Experiments & Model Leaderboard**.
The following phases remain unimplemented and are left out of this scope:
- **Phase 4.2**: Artifact Download & Code Surface APIs.
- **Phase 4.3**: Workspace Roles & Membership Administration.
- **Phase 4.4**: Frontend pages complete integration (for roles & workspace administration).
