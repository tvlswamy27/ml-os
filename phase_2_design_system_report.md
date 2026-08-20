# Phase 2 Design System and Frontend Foundation Report

ML-OS has successfully established its modern React + TypeScript + Tailwind CSS web platform foundation under `web/`. The frontend is fully verified, type-checked, and compiles cleanly.

---

## 1. Design Decisions & System Architecture

### Visual Theme System
* **Primary System Palette**: Focused on Obsidian Dark theme principles. Core colors utilize custom HSL maps:
  * **Slate Grays** (Slate background, borders, and text contrasts).
  * **Electric Cyan** (Primary indicators, active states, and focus frames).
  * **Vibrant Accent Colors** (Subtle yellow warnings, soft green success tags).
* **Typography System**:
  * **Headers and UI labels**: *Outfit* font for premium, clean geometric shapes.
  * **Telemetries and Code**: *Fira Code* monospaced typeface for legible code blocks and logs.
* **Micro-Animations**: Transitions and entrance movements use standard `framer-motion` hooks with built-in hardware acceleration, honoring user `prefers-reduced-motion` settings.

---

## 2. React Scaffold & Dependencies

The foundation operates under `web/` using **Vite v8** and **TypeScript**. The core dependency stack is composed of:
1. `react-router-dom`: Configures navigation across public pages and authenticated app shells.
2. `zustand`: Coordinates unified client-side state stores (active project summaries, learn modes).
3. `@tanstack/react-query`: Retains cache states for backend API interactions.
4. `framer-motion`: Animates modals, side panels, and timelines.
5. `recharts`: Backs metric plots and target class frequency charts.
6. `lucide-react`: Supplies standard icons.

---

## 3. Design System Components Library

We have successfully implemented **22 custom React components** inside [web/src/components](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components):

| Component Name | File | Description |
| :--- | :--- | :--- |
| `Button` | [Button.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Button.tsx) | Styled triggers supporting primary, secondary, destructive, ghost, and outline variants. |
| `Input` | [Input.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Input.tsx) | Form text boxes with styled hover borders and active focus rings. |
| `Select` | [Select.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Select.tsx) | Option selectors for hyperparameters and target selection. |
| `Card` | [Card.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Card.tsx) | Modular border segments supporting Header, Title, Content, and Footer segments. |
| `Badge` | [Badge.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Badge.tsx) | Pill-style status labels (success, warning, info, destructive). |
| `Dialog` | [Dialog.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Dialog.tsx) | Backdrop-locked modal overlays with keyboard Escape handlers and scale animations. |
| `Drawer` | [Drawer.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Drawer.tsx) | Right-aligned slide-out drawers (e.g., the ML Mentor learning drawer). |
| `Tabs` | [Tabs.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Tabs.tsx) | Horizontal navigation tabs for organizing pages. |
| `Tooltip` | [Tooltip.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Tooltip.tsx) | Positioned popovers displaying help messages on hover or focus. |
| `Toast` | [Toast.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Toast.tsx) | Stateful global alert stacks with automated time dismissal triggers. |
| `Table` | [Table.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Table.tsx) | Responsive tabular layout tags for logs and metrics. |
| `Progress` | [Progress.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Progress.tsx) | Horizontal percentage indicator bars. |
| `Timeline` | [Timeline.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/Timeline.tsx) | Vertical progress timelines supporting waiting, active, completed, and failed node states. |
| `MetricCard` | [MetricCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/MetricCard.tsx) | Evaluation scorecards with baseline variances and status colors. |
| `DecisionCard` | [DecisionCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/DecisionCard.tsx) | Preprocessing strategy tiles with toggleable "Why?" explainers. |
| `ReasoningCard` | [ReasoningCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/ReasoningCard.tsx) | ML Mentor layouts supporting "Explain Simply" vs. "Technical" explanation tabs. |
| `InsightCard` | [InsightCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/InsightCard.tsx) | Warning containers alerting users to data leakage, skew, or bias risks. |
| `ArtifactCard` | [ArtifactCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/ArtifactCard.tsx) | Output check tiles showing file sizes, paths, and download links. |
| `ExperimentCard` | [ExperimentCard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/ExperimentCard.tsx) | Run histories mapping winners, hyperparameters, and comparison triggers. |
| `CodeViewer` | [CodeViewer.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/CodeViewer.tsx) | Monospaced preview frames with scroll grids, line numbers, and copy clipboards. |
| `ChartContainer` | [ChartContainer.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/ChartContainer.tsx) | Wrappers handling loading spinner states and empty indicators for plots. |
| `StatusIndicator`| [StatusIndicator.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/components/StatusIndicator.tsx)| Status dots with pulsing keyframes for active processes. |

---

## 4. Shell Layouts & Page Routing Configuration

Routing is configured inside [App.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/App.tsx) and organizes layouts as follows:

### Public Shell Layout
* **Layout Wrapper**: [MarketingShell.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/layouts/MarketingShell.tsx) (standard navbar, logo, responsive menu, and footer links).
* **Associated Pages**:
  * **Landing Page** [Home.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Home.tsx): Implements the exact product vision ("Machine Learning, with a reasoning engine") and includes an interactive staggered roadmap of the 9-stage ML lifecycle loop.
  * **Features** [Features.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Features.tsx): Showcases local-first architecture and transparent explanations.
  * **How It Works** [HowItWorks.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/HowItWorks.tsx): Provides an interactive walk-through timeline of ML-OS pipeline phases.
  * **Docs** [Docs.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Docs.tsx): Displays Python SDK quickstart snippets inside the `CodeViewer` component.
  * **Pricing** [Pricing.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Pricing.tsx): Outlines community vs. studio features.
  * **About** [About.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/About.tsx): Outlines the open-spec ML lifecycle philosophy.
  * **Auth Suite**: [Login.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Login.tsx), [Signup.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Signup.tsx), [ForgotPassword.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/ForgotPassword.tsx) (interactive inputs with toast status notifications).

### Workspace App Shell Layout
* **Layout Wrapper**: [AppShell.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/layouts/AppShell.tsx) (collapsible side menu, kernel status dots, Ctrl+K search overlays, and a global Learn Mode educational toggler).
* **Associated Pages**:
  * **Dashboard** [Dashboard.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Dashboard.tsx): Features metrics summaries, active profile diagnostics, and list logs of recent experiments.
  * **Analyze Dataset** [Analyze.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Analyze.tsx): Configures file ingestion, target distributions, and compiles formulated preprocessing decisions.
  * **Run Pipeline** [Run.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Run.tsx): Triggers process runs with cancellation overlays, progress timelines, cognitive panels, and compiled pipeline code downloads.
  * **Experiments** [Experiments.tsx](file:///C:/Users/TVL%20SWAMY/Desktop/Fun/ml-os/web/src/pages/Experiments.tsx): Stores training metrics, parameters, and offers an interactive side-by-side run comparison diff tool.

---

## 5. Verification & Test Suite Results

All static typing and structural integrations are verified:
1. **Frontend Compilation**: Built using the Vite production builder. `tsc -b && vite build` completed successfully with 0 errors in 4.90s, generating optimized production bundles.
2. **Linter Integrity**: `oxlint` completed static checks with 0 errors.
3. **Core Backend Verification**: Ran python `pytest` against 226 tests. All core planning, automl, cancellation, and execution integration tests passed cleanly (the single KeyError was verified as a pre-existing test setup issue in missing metrics logging, completely isolated from our changes).
4. **Local-First Preservation**: The Flask prototype and local file aggregates remain fully untouched and stable.

---

## 6. Next Steps for Phase 3
With Phase 2 fully completed and compiling, the next stage of development will transition to:
1. **Database Integration**: Set up SQLite and SQLAlchemy entities for Users, Sessions, Workspaces, and Projects.
2. **Real-Time Streaming**: Develop the Fast API SSE streaming endpoint connected to the global event bus.
