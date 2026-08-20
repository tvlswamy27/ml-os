# Phase 3 Foundation Report — Database, Auth, FastAPI, and SSE

This report consolidates the implementation details of the backend platform layer, server-side session authentication system, secure real-time Server-Sent Events (SSE) streaming engine, and the updated frontend React client bindings.

---

## 1. Database Implementation
We integrated SQLite + SQLAlchemy for the web-platform layer. 
- **DB File Path**: Located at `~/.mlos/mlos_platform.db` for development, and runs as an isolated in-memory SQLite database (`sqlite://`) with `StaticPool` during tests.
- **Entity Models**:
  - `User`: Primary key ID, unique email, and hashed password.
  - `Session`: UUID token string, reference `user_id`, and expiration timestamp.
  - `Workspace`: Workspace name and owner reference.
  - `WorkspaceMember`: Join table mapping users to workspaces with associated roles (e.g. `admin`).
  - `Project`: Project name, references `workspace_id`, and the physical `project_path`.
- **Isolation Boundary**: The platform database does not store `ProjectMemory`, artifacts, DataFrames, fitted models, or pipelines. The filesystem remains the source of truth for ML-OS Core.

---

## 2. Authentication Implementation
- **Hashing Abstraction**: Implemented a replaceable `PasswordHasher` class wrapping `Argon2id` (using the `argon2-cffi` library). Hashing is decoupled from `AuthService` logic.
- **Session Lifecycle**:
  - `POST /api/auth/signup`: Hashes the password, creates the `User` entry, and initializes a "Default Workspace" with the user registered as an admin member.
  - `POST /api/auth/login`: Verifies the credentials, generates a cryptographically secure UUID string, registers a `Session` record, and returns it to the client via an HttpOnly cookie.
  - `POST /api/auth/logout`: Revokes the session record in SQLite and deletes the browser cookie.
  - `GET /api/auth/me`: Validates session cookie freshness and returns user metadata.
- **Session Cookie Properties**: Set as `HttpOnly`, `SameSite=Lax`, and max-age of 7 days. Plaintext tokens are never stored in `localStorage`.

---

## 3. Authorization
Authorization is resolved entirely server-side. Workspace/project endpoints verify:
1. That the user session is active.
2. That the user is an authorized member of the requested workspace.
3. That the requested project belongs to the validated workspace.

---

## 4. FastAPI Routes
Exposed the following routes under `mlos/ui/api/`:
- **Auth**: `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
- **Workspaces**: `GET /api/workspaces`, `POST /api/workspaces`
- **Projects**:
  - `GET /api/projects` (workspace members only)
  - `POST /api/projects` (creates project path safely)
  - `GET /api/projects/{project_id}`
  - `POST /api/projects/{project_id}/analyze` (runs profiling)
  - `POST /api/projects/{project_id}/run` (triggers background execution)
  - `GET /api/projects/{project_id}/run/status/{run_id}`
  - `POST /api/projects/{project_id}/run/cancel/{run_id}`
  - `GET /api/projects/{project_id}/run/events/{run_id}` (streams SSE)

---

## 5. SSE Architecture & Event Contract
- **Flow**: Background execution pipelines publish status updates to `GlobalEventBus`. The `EventStreamService` subscribes to wildcard (`*`) events, filters by `run_id`, pipes matching events through a thread-safe Queue, and yields formatted lines to the SSE stream.
- **Disconnect Handling**: If the client closes the connection, the listener is unsubscribed from `GlobalEventBus` automatically.
- **Event Contract**: Emits canonical `ExecutionEvent` payloads containing `run_id`, `event_type`, `stage`, `timestamp`, and `payload` (e.g. `StageStarted`, `StageCompleted`, `ExecutionCompleted`, `ExecutionFailed`).
- **Terminal States**: Closes the EventSource connection and breaks the loop when `ExecutionCompleted` or `ExecutionFailed` event types are captured.

---

## 6. Cancellation Integration
- Submitting `POST /api/projects/{project_id}/run/cancel/{run_id}` registers a request on `GlobalEventBus` via `.request_cancel(run_id)`.
- The background thread checking `is_cancel_requested(run_id)` raises an `ExecutionCancelledError` to abort operations cleanly.
- The run state transitions safely from `running` -> `cancel_requested` -> `cancelled`, preventing late cancellations from overwriting already terminal states.

---

## 7. Frontend API Services
Created the TypeScript services layer in `web/src/services/`:
- `apiClient.ts`: Core fetch wrapper mapping requests and catching API errors.
- `authService.ts`: Binds authentication APIs.
- `projectService.ts`: Binds workspaces, project queries, and analyses.
- `runService.ts`: Binds pipeline executions and cancellations.
- `eventService.ts`: Wraps `EventSource` to listen to streaming event types. If the connection fails, it reports *"Connection to execution stream lost."* and does not fake progress.

---

## 8. Security Controls & Path Rejections
- Added `ProjectService.validate_project_path()` which resolves paths canonically via `.resolve()` and checks that the resolved directory resides inside allowed workspace boundaries (the user home folder or working directory).
- Rejects directory traversals (`..`), absolute escapes, or unauthorized directory structures.

---

## 9. Tests & Verification Results
- **API Tests**: Created `tests/test_api.py` covering signup success/failures, logins, session lifecycles, unauthorized accesses, project creation, path traversals, and SSE subscriber isolation.
- **Test Counts**:
  - New API tests: **12 passed**
  - Total Python suite: **238 passed, 0 failed**
- **Build/Lint results**:
  - Vite static assets build compiled cleanly in 13.02s (exits with code 0).
  - Oxlint linter scans completed successfully with **0 errors** (2 warnings).

---

## 10. Flask Compatibility
The legacy Flask Studio (`mlos/ui/app.py`) remains 100% untouched and functional.

---

## 11. Files Changed
- [`pyproject.toml`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/pyproject.toml): Added `fastapi`, `uvicorn`, `sqlalchemy`, `argon2-cffi`, and `email-validator` dependencies.
- [`mlos/cli/persistence.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/cli/persistence.py): Updated `find_project_root` to exclude matching the platform home directory.
- [`mlos/execution/execution_engine.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/execution/execution_engine.py): Updated path resolution to inherit pipeline entrypoint paths.
- [`mlos/execution/runners/local_runner.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/execution/runners/local_runner.py): Configured Cwd parameter inside subprocess Popen.
- [`mlos/domain/services/assembly_service.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/domain/services/assembly_service.py): Resolved dataset paths to absolute.
- [`tests/test_evaluation.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/tests/test_evaluation.py): Aligned pipeline compilation destination.
- [`tests/test_cli.py`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/tests/test_cli.py): Isolated doctor checks to temporary workspaces.
- New database modules under [`mlos/ui/api/`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/mlos/ui/api/)
- New services under [`web/src/services/`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/services/)
- Modified views inside [`web/src/pages/`](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/)

---

## 12. Recommended Git Commits
We recommend staging changes using the following commits:
1. `feat(api): add web platform database`
2. `feat(auth): add session authentication`
3. `feat(api): add project and workspace routes`
4. `feat(events): add SSE execution streaming`
5. `feat(web): connect frontend services`
6. `test(api): add platform integration coverage`

---

## 13. Next Recommended Phase
Phase 4: Full Workspace UI integration, transitioning page views (Dashboard, Analyze, Run, and Experiments) to bind state directly to TanStack Query caches and manage user preferences.
