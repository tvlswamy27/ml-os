# Phase 4.2 — Artifact Download & Code Surface APIs Report

## Architecture
This phase implements secure artifact discovery and downloading functionality for ML-OS projects. The backend uses FastAPI to securely serve files from the authorized project directory, while the React frontend leverages TanStack Query and standard `fetch` APIs to trigger browser-native downloads.

## API Endpoints

### 1. `GET /api/projects/{project_id}/artifacts`
- **Purpose**: Lists all available artifacts for a given project.
- **Security**: Validates that the requesting user has access to the project.
- **Discovery**: Scans the `<project_root>/artifacts` directory recursively, and specifically allows `pipeline.py`, `model.joblib`, and `metrics.json` from the project root.
- **Response Schema (`ArtifactResponse`)**:
  - `name`: File name
  - `relative_path`: Path relative to project root
  - `size_bytes`: File size
  - `modified_at`: Last modification timestamp
  - `artifact_type`: Deduced type (`code`, `model`, `metrics`, etc.)
  - `downloadable`: Always true for returned items
  - `mime_type`: Deduced MIME type

### 2. `GET /api/projects/{project_id}/artifacts/download?path={path}`
- **Purpose**: securely downloads an artifact.
- **Security Validation**:
  - Authenticates user and checks project access.
  - Rejects traversal attempts (`..`, absolute paths, drive letters).
  - Validates the resolved path resides within the project root.
  - Verifies the requested path strictly matches an allowed location (`artifacts/` directory or explicitly allowed root files).
  - Confirms the target is a regular file (not a directory).

## Security Model
- Arbitrary filesystem access is **strictly prevented**. The APIs will only serve files from approved directories and specific root files.
- `pathlib` resolution is used to eliminate symlink escapes or tricky relative traversals.
- All errors related to file access (missing, forbidden) avoid leaking underlying internal absolute paths.

## Frontend Integration
- **`types/project.ts`**: Introduced the `Artifact` interface.
- **`apiClient.ts`**: Added `download()` using `fetch` (with `credentials: "include"`) and `window.URL.createObjectURL()` to securely trigger browser downloads without exposing auth tokens in the URL.
- **`useProjectArtifacts` hook**: Centralizes state management for discovering and downloading artifacts.
- **`Run.tsx`**: Updated to show real downloaded artifacts rather than mock views or empty states.

## Verification

### Automated Tests
- `tests/test_v4_2_artifacts.py` implements comprehensive security checks (unauthenticated access, unauthorized projects, path traversals).
- Full regression suite completed successfully (`255 passed`).

### Limitations & Warnings
- Frontend `npm run lint` and `npm run build` were **blocked** due to `npm` not being available in the environment.
- The `Run.tsx` page will only display artifacts once the run status transitions to "completed" and there are actual files in the corresponding directory.
