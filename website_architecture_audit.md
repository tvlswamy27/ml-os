# ML-OS Web Architecture Audit & Specification

This audit examines the current ML-OS prototype (Flask/Vanilla-JS Studio) and outlines the design and technology blueprint for migrating to a proper modern web application (React, Vite, TypeScript, FastAPI).

---

## 1. Current Frontend Architecture
The current frontend is a prototype implementation built as a single-page application (SPA):
* **Framework:** Vanilla HTML, Vanilla CSS (`styles.css` ~28KB), and Vanilla JavaScript (`app.js` ~84KB, ~2000 lines).
* **Delivery:** Served directly via Flask's static and template engine (`index.html` ~65KB).
* **Routing:** Hash-based client-side routing parsing `window.location.hash` (`#/dashboard`, `#/analyze`, `#/run`, `#/experiments`).
* **State Management:** Held globally in in-memory JavaScript variables (`activeProject`, `currentRunId`, etc.) and synchronized via DOM manipulation queries.
* **Polling/Execution:** Uses `setInterval` to query status endpoints `/api/project/run/status/<run_id>` every 1s.
* **Visuals:** Uses inline SVGs for drawing connections between pipeline stages, raw CSS transitions, and HTML tables for display.

---

## 2. Current Backend APIs
The Flask backend (`mlos/ui/app.py`) serves the HTML page and provides the following REST APIs:
1. `GET /api/project`: Resolves active project path from `~/.mlos_active_project`, loads `ProjectMemory` configuration, collects telemetry (metrics, experiments, registry model status) and outputs the project context status.
2. `POST /api/project/init`: Creates project directory, saves standard `.mlos/project_config.yaml`, and maps active project home directory pointer.
3. `POST /api/project/analyze`: Ingests dataset path, extracts metadata columns (numerical vs categorical), profiles rows/columns/duplicates, runs the `IntelligenceEngine` analysis, and updates project memory with preprocessing decisions and recommendations.
4. `POST /api/project/run`: Spawns a background thread utilizing `MLProject` SDK to run the lifecycle loop (Analysis $\rightarrow$ Preparation $\rightarrow$ AutoML Battle $\rightarrow$ Assembly $\rightarrow$ Local execution $\rightarrow$ Evaluation $\rightarrow$ Explainability $\rightarrow$ Serialization).
5. `GET /api/project/run/status/<run_id>`: Retrieves active background thread execution metrics, status stages, and execution duration.
6. `POST /api/project/run/cancel/<run_id>`: Signals a cooperative cancellation token via the `GlobalEventBus` to terminate execution at the next pipeline stage.
7. `GET /api/experiments`: Lists all logged runs tracked under the project workspace.
8. `GET /api/experiments/<experiment_id>`: Queries metric data, features, hyperparameters, SHAP values, and artifact maps for a specific execution.
9. `POST /api/experiments/compare`: Side-by-side diff comparison scoring variance, accuracy, and trade-offs.
10. `POST /api/project/validate-dataset`: Verifies path traversal restrictions and confirms dataset formats (CSV or Parquet) inside the workspace root.
11. `GET /api/project/files`: Safely crawls the workspace up to 3 levels deep to list available dataset tables.

---

## 3. Existing Reusable Components
To guarantee functional parity, the following visual components from the prototype must be mapped to modern, reusable React components:
* **Project Onboarding overlay:** Modal workspace initialization forms.
* **Dashboard Summary Grid:** Performance metrics, problem configurations, and directory paths.
* **Project Journey Timeline:** Sequential status nodes mapping progress (Understand $\rightarrow$ Prepare $\rightarrow$ Plan $\rightarrow$ Build).
* **Decisions Table:** Detailed list of engine preprocessing logic with toggleable **"Why?"** explanation boxes.
* **Recommendations Table:** Prioritized lists of risk warnings and mitigations.
* **Pipeline DAG Visualizer:** Node network indicating execution flow states.
* **Active Thinking Assistant Panel:** Explanations of active stage runtime details (**"What we are doing"** and **"Why we are doing it"**).
* **Leaderboard and Metrics Grid:** Candidate model evaluation results.
* **Feature Importance Chart:** Horizontal indicator bars for feature weight bounds with contextual helper boxes.
* **Artifact Cards:** Downloadable assets details (model joblib, preprocessors, reports).
* **Experiment Comparator Table:** Dual column metric analysis showing positive/negative variance.

---

## 4. Existing ML-OS Capabilities Exposed by UI
The prototype UI exposes the following backend operations:
* Workspace initialization and active pointer configuration.
* Inline dataset format checking and workspace isolation validation.
* Autocomplete schema search for dataset files.
* Subsystem profiling: extracting target boundaries and feature properties.
* Automated preprocessor compilation (imputations, categories encoding).
* Background local execution runtime scheduling and event-based checklist progression tracking.
* Model battle comparisons across algorithm architectures (Random Forest, XGBoost, etc.).
* Interpretative feature impact maps.
* Side-by-side run comparisons with trade-off warnings.
* On-demand explanation overlays (ML Mentor).

---

## 5. Missing APIs
To build the foundation of a true ML-OS product, the following backend endpoints must be introduced:
1. **User and Session Authentication:**
   * `/api/auth/login` (REST - Session / JWT token generation)
   * `/api/auth/signup` (REST - Account initialization)
   * `/api/auth/logout` (REST - Session termination)
   * `/api/auth/me` (REST - Current user profile context)
2. **Multi-Project & Workspace Switching:**
   * `GET /api/workspaces`: List workspaces mapped to the authenticated user.
   * `GET /api/projects`: List projects within the active workspace (decoupling from single `~/.mlos_active_project` file).
   * `POST /api/projects`: Initialize a project under a specific workspace directory.
3. **SSE Event Stream:**
   * `GET /api/project/run/events/<run_id>`: Server-Sent Events (SSE) route to push pipeline execution occurrences from the `GlobalEventBus` to the frontend in real time, eliminating polling.
4. **Code Viewer Endpoint:**
   * `GET /api/project/pipeline/code`: Resolves and serves the generated python pipeline script (`pipeline.py`) or preprocessor configuration to the UI.
5. **Artifact Preview Endpoint:**
   * `GET /api/project/artifacts/preview`: Safely serves short snippets of logs, reports, or data tables to be displayed in UI preview frames.

---

## 6. Authentication Requirements
The new React frontend must have a secure, modular authentication boundary:
* **Service Abstraction:** Build an `AuthService` interface on the frontend.
* **Development Sandbox:** Create a mock implementation that validates inputs, stores user information in local storage, and signs mock JWT tokens or session cookies.
* **Production Adaptability:** Designed to allow the frontend to easily plug into enterprise providers (Auth0, Supabase, Firebase, or Keycloak) without refactoring the application shell.
* **Backend Isolation:** All API routes (except auth paths) must check authorization headers (`Authorization: Bearer <token>`).

---

## 7. Event / Real-Time Requirements
Real-time execution must be responsive and resource-efficient:
* **Protocol:** Server-Sent Events (SSE) will stream background execution events (`ExecutionStarted`, `StageStarted`, `StageCompleted`, `StageFailed`, `ExecutionCompleted`).
* **Connection Lifecycle:** The React frontend will initialize an `EventSource` on pipeline launch.
* **Error Tolerant:** Auto-reconnection with exponential backoff if socket boundaries disconnect.
* **Thread Safety:** The backend thread executing the ML-OS project run will publish messages to a thread-safe queue. FastAPI will pull events asynchronously and stream them to open client connections.

---

## 8. Data Visualization Requirements
Analytical charts should feel like an integrated part of the product. They must be built using `Recharts` and styled using Design System tokens:
* **Target Distribution:**
  * Classification: Sleek categorical horizontal bar chart.
  * Regression: Continuous numerical range histogram or density curve.
* **Feature Cardinality & Density:** Compact numerical distribution charts.
* **Correlation Heatmap:** Symmetric grid visualizing correlation coefficient values.
* **Model Battle Comparison:**
  * Multi-metric radar chart or aligned bar charts.
  * Hyperparameter validation metrics lines.
* **Feature Importance Map:** Aligned horizontal value charts with contextual explainability indicators.
* **Explainability (SHAP):** Visual representations of feature impacts on predictions.

---

## 9. New Frontend Architecture
The new frontend will be built as a modern React application:
* **Framework:** React 18+ (using TypeScript and Vite).
* **Styling:** Tailwind CSS + custom Design System tokens matching a premium, developer-focused aesthetic.
* **Routing:** `React Router v6` (or modern layout-based routing).
* **State Management:**
  * `Zustand`: Global state (current project context, user details, notifications, command palette).
  * `TanStack Query (React Query)`: Server state caching, auto-fetching, and background refetching.
* **Animations:** `Framer Motion` (Motion) for staggered reveals, page transitions, layout morphing, and timeline progress.
* **Icons:** `Lucide React` for clean iconography.

---

## 10. Migration Strategy from Flask Studio
We will migrate incrementally without breaking existing features:
1. **Co-existence Phase:** Leave the prototype Flask application intact.
2. **FastAPI Implementation:** Create the new API layer using FastAPI (e.g. `mlos/ui/api_fastapi.py`). It will call the exact same `MLOSEngine` and `MLProject` SDK functions.
3. **Separate Runs:** Run the React app using Vite's development server (port `5173`) proxying API calls to the FastAPI app (port `8000`).
4. **Parity Validation:** Validate React pages against Flask screens.
5. **Vite Packaging:** Compile the React app into static files (`dist`).
6. **FastAPI Static Serving:** Configure FastAPI to serve the static build from the `dist` directory.
7. **CLI Command Update:** Update the `mlos ui` command in `mlos/cli/commands/ui.py` to start the FastAPI server via Uvicorn instead of Flask, completing the migration.

---

## 11. Risks & Mitigation
* **Thread Safety in Python Lifecycle:** 
  * *Risk:* Running heavy scikit-learn AutoML jobs in the same process as FastAPI might block the event loop.
  * *Mitigation:* Spawn the pipeline execution in a standard Python background thread or sub-process, communicating status events to FastAPI asynchronously through a thread-safe Queue.
* **Path Traversal / Local Vulnerabilities:**
  * *Risk:* Allowing the user to supply arbitrary workspace path configurations could lead to reading or writing outside the workspace directory.
  * *Mitigation:* Strictly enforce relative path resolution checks (`Path(target).resolve().relative_to(root)`) and sanitize user path arguments on the server.
* **API Resource Contention:**
  * *Risk:* Concurrent requests to read/write `project_config.yaml` during an active training run could lead to file corruption.
  * *Mitigation:* Implement write locks on project memory operations.

---

## 12. Recommended Technology Stack
* **Frontend:**
  * React + Vite (TypeScript)
  * Tailwind CSS (Styling)
  * Framer Motion (Transitions and progress animations)
  * TanStack Query (Query handling & API sync)
  * Zustand (Core global UI state)
  * Recharts (Analytic charts)
  * Lucide React (Icons)
* **Backend:**
  * FastAPI (API Gateway)
  * Uvicorn (ASGI web server)
  * Pydantic v2 (Data verification schemas)
  * sse-starlette (SSE streaming provider)

---

## 13. Recommended Folder Structure
```
ml-os/
├── mlos/                  # Python backend package
│   ├── ui/                # UI package
│   │   ├── api/           # FastAPI application & endpoints
│   │   │   ├── router/    # Sub-routes (auth, project, run, experiments)
│   │   │   ├── schemas/   # Pydantic schemas (Request/Response contracts)
│   │   │   └── main.py    # FastAPI main startup application entrypoint
│   │   └── app.py         # [Legacy] Flask server
│   └── ...                # Core engines
├── web/                   # New React frontend application (Vite root)
│   ├── public/            # Static assets (logos, favicon)
│   ├── src/
│   │   ├── assets/        # Global stylesheets and media
│   │   ├── components/    # Reusable UI controls (Button, Card, Modals)
│   │   ├── context/       # Auth or global configuration contexts
│   │   ├── hooks/         # Custom React hooks (useAuth, useProject, useSSE)
│   │   ├── layouts/       # Main app wrappers (AppShell, MarketingShell)
│   │   ├── pages/         # Page components (Dashboard, Analyze, etc.)
│   │   ├── services/      # Fetch services (apiClient, authService)
│   │   ├── store/         # Zustand global stores (projectStore, authStore)
│   │   ├── styles/        # CSS index and design tokens configurations
│   │   ├── types/         # TypeScript interfaces matching backend models
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
└── pyproject.toml         # Python packaging config
```

---

## 14. Proposed Page Map
* **Public Website:**
  * `/` : Product Homepage highlighting ML-OS core vision, lifecycle loop, and CTA.
  * `/features` : Deep-dive into automated code generation and explained decisions.
  * `/how-it-works` : Educational breakdown of the pipeline phases.
  * `/docs` : API & CLI development document guide.
  * `/pricing` : Visual pricing grids.
  * `/about` : Vision, team, and contribution values.
  * `/login` : Authentication page.
  * `/signup` : Project workspace sign up form.
  * `/forgot-password` : Recovery page.
* **Application Shell (Authenticated):**
  * `/workspace` : Workspace switcher and project overview list.
  * `/workspace/:project_id/dashboard` : Central hub displaying active dataset metadata, latest metric card scores, and journey checklist progress.
  * `/workspace/:project_id/analyze` : Ingest dataset paths and view target/features distributions.
  * `/workspace/:project_id/intelligence` : Risk profile overview.
  * `/workspace/:project_id/plan` : Interactive stage dependency visualizer.
  * `/workspace/:project_id/run` : Live pipeline execution dashboard.
  * `/workspace/:project_id/experiments` : Historical run metrics log and comparator.
  * `/workspace/:project_id/artifacts` : Registry tracking compiled pipeline code files and configurations.
  * `/workspace/:project_id/learn` : Explanations grounded in active runs.
  * `/workspace/:project_id/settings` : Workspace path configurations.

---

## 15. Proposed Component Hierarchy
```
App
└── Routing
    ├── MarketingLayout
    │   └── [Marketing Pages: Home, Features, How it works, Docs, Pricing, About]
    ├── AuthLayout
    │   └── [Auth Pages: Login, Signup, ForgotPassword]
    └── AppShell (Sidebar, Header, CommandPalette, UserProfileMenu)
        └── WorkspaceLayout
            ├── ProjectBreadcrumbs & StatusIndicators
            ├── [Workspace Views]
            │   ├── DashboardView (MetricGrid, JourneyChecklist, RecentRunsTable)
            │   ├── AnalyzeView (DatasetUploader, TargetDistributionChart, FeatureCardsGrid)
            │   ├── IntelligenceView (RiskCardsGrid)
            │   ├── PlanView (SVGWorkflowDiagram, StageDetailsCard)
            │   ├── ModelBattleView (LeaderboardList, CompareMetricChart)
            │   ├── PipelineView (CodeViewerWithContext, AssemblyDetails)
            │   ├── ExecutionView (TimelineStagesList, SSELogsConsole, CancelButton)
            │   ├── EvaluationView (MetricsRadarChart, ConfusionMatrixGrid)
            │   ├── ExplainabilityView (SHAPImportanceChart, MetricDescriptionCard)
            │   └── ExperimentsView (RunsHistoryTable, SideBySideCompareModal)
            └── MLMentorDrawer (InteractiveExplainPanel)
```

---

## 16. API Contract Requirements
To coordinate data transfers safely, the following Pydantic schemas are defined for FastAPI endpoints:

### Project Schemas:
* `ProjectInitRequest`: `{ name: str, goal: str, path: Optional[str] }`
* `ProjectInitResponse`: `{ message: str, project_path: str }`
* `ProjectDetailsResponse`:
  ```json
  {
    "status": "active" | "no_project",
    "project_name": "Titanic Survival",
    "project_goal": "Maximize F1",
    "project_path": "/workspace/titanic",
    "current_stage": "Analysis",
    "dataset": {
      "path": "data/train.csv",
      "rows": 891,
      "columns": 12,
      "target": "Survived",
      "problem_type": "Classification",
      "duplicate_rows": 0,
      "missing_values_count": 177
    },
    "profile": {
      "problem_type": "Classification",
      "complexity": "low",
      "baseline_models": ["Logistic Regression", "Random Forest"],
      "risks": ["Class imbalance", "Missing values"]
    },
    "latest_experiment": "exp-1234",
    "latest_model": "Random Forest Classifier",
    "model_stage": "staging",
    "latest_metrics": { "accuracy": 0.824, "f1_score": 0.811 }
  }
  ```

### Analysis Schemas:
* `AnalysisRequest`: `{ dataset_path: str, target_column: Optional[str] }`
* `AnalysisResponse`:
  ```json
  {
    "dataset_summary": {
      "path": "data/train.csv",
      "rows": 891,
      "columns": 12,
      "target": "Survived",
      "problem_type": "Classification",
      "duplicate_rows": 0,
      "missing_values": { "Age": 177, "Cabin": 687 }
    },
    "features": {
      "numerical": ["Age", "Fare", "SibSp"],
      "categorical": ["Pclass", "Sex", "Embarked"]
    },
    "problem_intelligence": {
      "problem_type": "Classification",
      "complexity": "low",
      "baseline_models": ["Logistic Regression", "Random Forest"],
      "risks": ["Class Imbalance"],
      "decisions": [
        { "title": "Standard Scaler", "strategy": "Scale", "confidence": 0.95, "reason": "Numerical scales differ." }
      ],
      "recommendations": [
        { "priority": "High", "title": "Handle Imbalance", "description": "Prioritize F1 score evaluation metrics." }
      ]
    }
  }
  ```

### Real-Time Event Schema:
* `SSEEvent`: `{ run_id: str, event_type: str, stage: str, timestamp: str, payload: dict }`

---

## 17. Definition of Done
Phase 1 (Product Architecture & Audit Review) is considered **Done** when:
1. `website_architecture_audit.md` is compiled and successfully approved by the user.
2. The core developer guidelines and directory setup plans are formally agreed upon.
3. The new technology choices (React, Vite, Tailwind CSS, FastAPI) are verified against the existing project dependencies.
4. The system is ready to proceed to Phase 2 (Design System Implementation) and Phase 3 (Public Website).
