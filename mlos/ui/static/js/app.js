// Global variables to hold project state
let activeProject = null;
let currentRunId = null;
let runPollInterval = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    // Navigation routing setup
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const page = item.getAttribute("data-page");
            if (item.classList.contains("nav-future")) {
                showToast("Coming in a future milestone", false);
                return;
            }
            switchPage(page);
        });
    });

    // Checkbox select all handling
    const selectAllCheckbox = document.getElementById("experiments-select-all");
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", (e) => {
            const rowCheckboxes = document.querySelectorAll(".exp-row-checkbox");
            rowCheckboxes.forEach(cb => {
                cb.checked = e.target.checked;
            });
            updateCompareButtonState();
        });
    }

    // Initialize Project Button
    const btnInitProject = document.getElementById("btn-init-project");
    if (btnInitProject) {
        btnInitProject.addEventListener("click", initProjectWorkspace);
    }

    // Analyze Dataset Button
    const btnRunAnalysis = document.getElementById("btn-run-analysis");
    if (btnRunAnalysis) {
        btnRunAnalysis.addEventListener("click", runDatasetAnalysis);
    }

    // Run ML Pipeline Button
    const btnRunPipeline = document.getElementById("btn-run-pipeline");
    if (btnRunPipeline) {
        btnRunPipeline.addEventListener("click", startMLPipelineRun);
    }

    // Compare Experiments Button
    const btnCompareExp = document.getElementById("btn-compare-experiments");
    if (btnCompareExp) {
        btnCompareExp.addEventListener("click", compareSelectedExperiments);
    }

    // Fetch active project settings
    fetchProjectMetadata();
});

// Toast notification helper
function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${isError ? 'toast-error' : 'toast-success'}`;
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4000);
}

// Switch SPA Page View
function switchPage(pageId) {
    // Update sidebar nav state
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        if (item.getAttribute("data-page") === pageId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    // Update main container visible section
    const pages = document.querySelectorAll(".page-view");
    pages.forEach(page => {
        if (page.id === `view-${pageId}`) {
            page.classList.remove("hidden");
        } else {
            page.classList.add("hidden");
        }
    });

    // Run custom page hooks
    if (pageId === "dashboard") {
        fetchProjectMetadata();
    } else if (pageId === "experiments") {
        loadExperiments();
    }
}

// Load metadata about the active project workspace
async function fetchProjectMetadata() {
    try {
        const response = await fetch("/api/project");
        const data = await response.json();

        const overlay = document.getElementById("init-project-overlay");
        const projNameElem = document.getElementById("active-project-name");
        const statusText = document.getElementById("system-status-text");
        const statusDot = document.getElementById("system-status-indicator");

        if (data.status === "no_project") {
            overlay.classList.remove("hidden");
            projNameElem.textContent = "No Project";
            statusText.textContent = "Inactive";
            statusDot.className = "status-dot dot-inactive";

            // Set input path fallback for convenience
            if (data.project_path) {
                document.getElementById("init-path").value = data.project_path;
            }
            return;
        } else {
            overlay.classList.add("hidden");
        }

        activeProject = data;

        // Update top-bar
        projNameElem.textContent = data.project_name;
        statusText.textContent = "Active";
        statusDot.className = "status-dot dot-active";

        // Update dashboard elements
        document.getElementById("dash-project-path").textContent = data.project_path;

        if (data.dataset) {
            document.getElementById("dashboard-empty-state").classList.add("hidden");
            document.getElementById("dashboard-content").classList.remove("hidden");

            document.getElementById("dash-problem-type").textContent = data.profile ? data.profile.problem_type : "Classification";
            document.getElementById("dash-dataset").textContent = data.dataset.path.split(/[\\/]/).pop();
            document.getElementById("dash-target").textContent = data.dataset.target || "None";

            document.getElementById("dash-rows").textContent = data.dataset.rows;
            document.getElementById("dash-columns").textContent = data.dataset.columns;

            document.getElementById("dash-latest-exp").textContent = data.latest_experiment || "None";
            document.getElementById("dash-latest-model").textContent = data.latest_model || "None";

            const badge = document.getElementById("dash-model-stage");
            badge.textContent = data.model_stage || "staging";
            badge.className = `badge ${data.model_stage === 'production' ? 'success' : 'warning'}`;

            // Sync values to configuration forms if empty
            const analyzePath = document.getElementById("analyze-dataset-path");
            if (analyzePath && !analyzePath.value) analyzePath.value = data.dataset.path;
            const analyzeTarget = document.getElementById("analyze-target");
            if (analyzeTarget && !analyzeTarget.value) analyzeTarget.value = data.dataset.target || "";

            const runPath = document.getElementById("run-dataset-path");
            if (runPath && !runPath.value) runPath.value = data.dataset.path;
            const runTarget = document.getElementById("run-target");
            if (runTarget && !runTarget.value) runTarget.value = data.dataset.target || "";

            // Populate dashboard metrics
            populateDashboardMetrics(data.latest_metrics);
            loadRecentExperimentsTable();
        } else {
            document.getElementById("dashboard-empty-state").classList.remove("hidden");
            document.getElementById("dashboard-content").classList.add("hidden");
        }

    } catch (err) {
        showToast("Error loading project information", true);
        console.error(err);
    }
}

// Populate metric cards on dashboard
function populateDashboardMetrics(metrics) {
    const container = document.getElementById("dashboard-metrics-container");
    if (!container) return;

    container.innerHTML = "";

    if (!metrics || Object.keys(metrics).length === 0) {
        container.innerHTML = `<p class="dim-text col-span-2">No evaluation metrics recorded yet.</p>`;
        return;
    }

    Object.entries(metrics).forEach(([metric, val]) => {
        let displayVal = typeof val === 'number' ? val.toFixed(4) : String(val);
        const card = document.createElement("div");
        card.className = "metric-card";
        card.innerHTML = `
            <div class="score">${displayVal}</div>
            <div class="title">${metric}</div>
        `;
        container.appendChild(card);
    });
}

// Initializing project workspace
async function initProjectWorkspace() {
    const name = document.getElementById("init-name").value;
    const goal = document.getElementById("init-goal").value;
    const path = document.getElementById("init-path").value;
    const errorElem = document.getElementById("init-error");

    if (!name) {
        errorElem.textContent = "Project Name is required";
        errorElem.classList.remove("hidden");
        return;
    }

    errorElem.classList.add("hidden");

    try {
        const response = await fetch("/api/project/init", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, goal, path })
        });
        const result = await response.json();

        if (response.ok) {
            showToast(result.message);
            document.getElementById("init-project-overlay").classList.add("hidden");
            fetchProjectMetadata();
        } else {
            errorElem.textContent = result.error || "Initialization failed";
            errorElem.classList.remove("hidden");
        }
    } catch (err) {
        errorElem.textContent = "Server connection error";
        errorElem.classList.remove("hidden");
    }
}

// Execute dataset profiling analysis
async function runDatasetAnalysis() {
    const datasetPath = document.getElementById("analyze-dataset-path").value;
    const targetColumn = document.getElementById("analyze-target").value;
    const btn = document.getElementById("btn-run-analysis");

    if (!datasetPath) {
        showToast("Dataset path is required", true);
        return;
    }

    btn.disabled = true;
    btn.textContent = "Analyzing...";

    try {
        const response = await fetch("/api/project/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dataset_path: datasetPath, target_column: targetColumn })
        });
        const data = await response.json();

        if (response.ok) {
            showToast("Dataset analysis complete");
            document.getElementById("analysis-empty-state").classList.add("hidden");
            document.getElementById("analysis-results").classList.remove("hidden");

            // Update Dataset summary card
            const ds = data.dataset_summary;
            document.getElementById("analysis-problem-type").textContent = ds.problem_type;
            document.getElementById("analysis-rows").textContent = ds.rows;
            document.getElementById("analysis-cols").textContent = ds.columns;
            document.getElementById("analysis-duplicates").textContent = ds.duplicate_rows;

            // Update Feature tag lists
            const numList = document.getElementById("analysis-num-cols");
            const catList = document.getElementById("analysis-cat-cols");
            document.getElementById("analysis-num-count").textContent = data.features.numerical.length;
            document.getElementById("analysis-cat-count").textContent = data.features.categorical.length;

            numList.textContent = data.features.numerical.length > 0 ? data.features.numerical.join(", ") : "None";
            catList.textContent = data.features.categorical.length > 0 ? data.features.categorical.join(", ") : "None";

            // Populate Decisions Table
            const decisionsBody = document.querySelector("#analysis-decisions-table tbody");
            decisionsBody.innerHTML = "";
            const pi = data.problem_intelligence;

            if (pi.decisions.length === 0) {
                decisionsBody.innerHTML = `<tr><td colspan="4" class="center dim-text">No preprocessing decisions formulated.</td></tr>`;
            } else {
                pi.decisions.forEach(dec => {
                    const tr = document.createElement("tr");
                    let displayConfidence = dec.confidence;
                    if (displayConfidence !== null && displayConfidence !== undefined) {
                        displayConfidence = displayConfidence.toString();
                        const num = Number(displayConfidence);
                        if (!isNaN(num)) {
                            displayConfidence = `${(num * 100).toFixed(0)}%`;
                        }
                    } else {
                        displayConfidence = "Unknown";
                    }
                    tr.innerHTML = `
                        <td><strong>${dec.title}</strong></td>
                        <td><span class="badge">${dec.strategy}</span></td>
                        <td>${displayConfidence}</td>
                        <td class="dim-text">${dec.reason}</td>
                    `;
                    decisionsBody.appendChild(tr);
                });
            }

            // Populate Recommendations Table
            const recsBody = document.querySelector("#analysis-recs-table tbody");
            recsBody.innerHTML = "";
            if (pi.recommendations.length === 0) {
                recsBody.innerHTML = `<tr><td colspan="3" class="center dim-text">No recommendations generated.</td></tr>`;
            } else {
                pi.recommendations.forEach(rec => {
                    const tr = document.createElement("tr");
                    const priorityClass = rec.priority.toLowerCase();
                    tr.innerHTML = `
                        <td><span class="badge ${priorityClass === 'high' ? 'danger' : 'warning'}">${rec.priority}</span></td>
                        <td><strong>${rec.title}</strong></td>
                        <td class="dim-text">${rec.description}</td>
                    `;
                    recsBody.appendChild(tr);
                });
            }

            // Refresh top details
            fetchProjectMetadata();

        } else {
            showToast(data.error || "Analysis failed", true);
        }
    } catch (err) {
        showToast("Server connection error during analysis", true);
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = "Analyze Dataset";
    }
}

// Trigger ML pipeline run background thread execution
async function startMLPipelineRun() {
    const datasetPath = document.getElementById("run-dataset-path").value;
    const targetColumn = document.getElementById("run-target").value;
    const btn = document.getElementById("btn-run-pipeline");

    if (!datasetPath) {
        showToast("Dataset path is required", true);
        return;
    }

    btn.disabled = true;
    btn.textContent = "Starting...";

    try {
        const response = await fetch("/api/project/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dataset_path: datasetPath, target_column: targetColumn })
        });
        const data = await response.json();

        if (response.ok) {
            showToast("ML Pipeline background process initiated");
            document.getElementById("run-empty-state").classList.add("hidden");
            document.getElementById("run-progress-panel").classList.remove("hidden");

            document.getElementById("pipeline-overall-status-badge").textContent = "Running";
            document.getElementById("pipeline-overall-status-badge").className = "status-badge running";
            document.getElementById("pipeline-active-run-id").textContent = data.run_id;

            // Reset checklist state
            resetTimelineUI();

            // Success & failed sections hide
            document.getElementById("run-success-stats").classList.add("hidden");
            document.getElementById("run-failed-stats").classList.add("hidden");

            currentRunId = data.run_id;

            // Clear any old poll
            if (runPollInterval) clearInterval(runPollInterval);

            // Poll progress every 1s
            runPollInterval = setInterval(() => pollRunStatus(data.run_id), 1000);

        } else {
            showToast(data.error || "Pipeline startup failed", true);
            btn.disabled = false;
            btn.textContent = "Run ML Pipeline";
        }
    } catch (err) {
        showToast("Connection error starting pipeline", true);
        console.error(err);
        btn.disabled = false;
        btn.textContent = "Run ML Pipeline";
    }
}

// Reset timeline status list UI
function resetTimelineUI() {
    const items = document.querySelectorAll(".timeline-item");
    items.forEach(item => {
        item.className = "timeline-item waiting";
        item.querySelector(".icon").textContent = "○";
    });
}

// Polling background run progress
async function pollRunStatus(runId) {
    try {
        const response = await fetch(`/api/project/run/status/${runId}`);
        if (!response.ok) {
            clearInterval(runPollInterval);
            return;
        }

        const data = await response.json();

        // Map UI timeline element IDs to api names
        const stageElementMap = {
            "Analysis": "stage-Analysis",
            "Feature Intelligence": "stage-Feature-Intelligence",
            "Meta Reasoning": "stage-Meta-Reasoning",
            "Planning": "stage-Planning",
            "Execution Runtime": "stage-Execution-Runtime",
            "Training": "stage-Training",
            "Evaluation": "stage-Evaluation",
            "Explainability": "stage-Explainability",
            "Artifacts Generation": "stage-Artifacts-Generation",
            "Experiment Tracking": "stage-Experiment-Tracking",
            "Knowledge Capture": "stage-Knowledge-Capture"
        };

        // Update stages
        Object.entries(stageElementMap).forEach(([stageName, elemId]) => {
            const elem = document.getElementById(elemId);
            if (!elem) return;

            if (data.completed_stages.includes(stageName)) {
                elem.className = "timeline-item completed";
                elem.querySelector(".icon").textContent = "✓";
            } else if (data.current_stage === stageName) {
                elem.className = "timeline-item running";
                elem.querySelector(".icon").textContent = "⟳";
            } else {
                elem.className = "timeline-item waiting";
                elem.querySelector(".icon").textContent = "○";
            }
        });

        // Check if finished
        if (data.status === "success") {
            clearInterval(runPollInterval);
            document.getElementById("btn-run-pipeline").disabled = false;
            document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";

            document.getElementById("pipeline-overall-status-badge").textContent = "Success";
            document.getElementById("pipeline-overall-status-badge").className = "status-badge success";

            // Mark all finished
            Object.values(stageElementMap).forEach(elemId => {
                const elem = document.getElementById(elemId);
                if (elem) {
                    elem.className = "timeline-item completed";
                    elem.querySelector(".icon").textContent = "✓";
                }
            });

            // Populate success metrics
            document.getElementById("run-success-stats").classList.remove("hidden");
            document.getElementById("res-exp-id").textContent = data.experiment_id;
            document.getElementById("res-problem-type").textContent = data.problem_type;
            document.getElementById("res-artifacts-count").textContent = data.artifacts_count;
            document.getElementById("res-exec-time").textContent = `${data.execution_time_s.toFixed(2)} sec`;

            // Metrics grid
            const metricsGrid = document.getElementById("run-final-metrics");
            metricsGrid.innerHTML = "";

            if (data.metrics && Object.keys(data.metrics).length > 0) {
                Object.entries(data.metrics).forEach(([m, val]) => {
                    let displayVal = typeof val === 'number' ? val.toFixed(4) : String(val);
                    const div = document.createElement("div");
                    div.className = "metric-card";
                    div.innerHTML = `<div class="score">${displayVal}</div><div class="title">${m}</div>`;
                    metricsGrid.appendChild(div);
                });
            } else {
                metricsGrid.innerHTML = `<p class="dim-text">No evaluation metrics returned.</p>`;
            }

            showToast("ML-OS Pipeline run succeeded!");
            fetchProjectMetadata();

        } else if (data.status === "failed") {
            clearInterval(runPollInterval);
            document.getElementById("btn-run-pipeline").disabled = false;
            document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";

            document.getElementById("pipeline-overall-status-badge").textContent = "Failed";
            document.getElementById("pipeline-overall-status-badge").className = "status-badge failed";

            // Find current stage and mark failed
            if (data.current_stage) {
                const elemId = stageElementMap[data.current_stage];
                const elem = document.getElementById(elemId);
                if (elem) {
                    elem.className = "timeline-item failed";
                    elem.querySelector(".icon").textContent = "✗";
                }
            }

            document.getElementById("run-failed-stats").classList.remove("hidden");
            document.getElementById("run-failed-error").textContent = data.error || "Execution terminated with errors.";
            showToast("ML Pipeline execution failed", true);
        }

    } catch (err) {
        console.error("Error polling progress", err);
    }
}

// Fetch all experiments recorded in project
async function loadExperiments() {
    try {
        const response = await fetch("/api/experiments");
        const experiments = await response.json();

        const tableBody = document.querySelector("#experiments-table tbody");
        tableBody.innerHTML = "";

        if (!experiments || experiments.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" class="center dim-text">No experiments logged yet.</td></tr>`;
            return;
        }

        experiments.forEach(exp => {
            const tr = document.createElement("tr");

            // Format metric scores string
            const metricsStr = Object.entries(exp.metrics || {})
                .map(([m, val]) => `${m}=${typeof val === 'number' ? val.toFixed(4) : val}`)
                .join(", ");

            tr.innerHTML = `
                <td><input type="checkbox" class="exp-row-checkbox" value="${exp.experiment_id}" onchange="updateCompareButtonState()"></td>
                <td><strong class="text-accent">${exp.experiment_id}</strong></td>
                <td class="dim-text">${exp.timestamp ? exp.timestamp.substring(0, 19).replace('T', ' ') : '---'}</td>
                <td class="dim-text" style="font-family: var(--font-mono); font-size:11px;">${exp.dataset_fingerprint ? exp.dataset_fingerprint.substring(0, 8) : '---'}</td>
                <td><span class="badge">${exp.problem_type || 'Unknown'}</span></td>
                <td><strong>${exp.selected_model || 'None'}</strong></td>
                <td>${metricsStr || 'No metrics logged'}</td>
                <td>
                    <button class="btn btn-secondary" onclick="viewExperimentDetails('${exp.experiment_id}')">Details</button>
                </td>
            `;
            tableBody.appendChild(tr);
        });

        // Reset compare state
        updateCompareButtonState();

    } catch (err) {
        showToast("Error loading experiments", true);
    }
}

// Populate the Dashboard's mini experiments list
async function loadRecentExperimentsTable() {
    try {
        const response = await fetch("/api/experiments");
        const experiments = await response.json();

        const tableBody = document.querySelector("#dash-experiments-table tbody");
        tableBody.innerHTML = "";

        if (!experiments || experiments.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="center dim-text">No experiments logged yet.</td></tr>`;
            return;
        }

        // Display up to 5 recent
        const recent = experiments.slice(0, 5);
        recent.forEach(exp => {
            const tr = document.createElement("tr");
            const metricsStr = Object.entries(exp.metrics || {})
                .map(([m, val]) => `${m}=${typeof val === 'number' ? val.toFixed(3) : val}`)
                .join(", ");

            tr.innerHTML = `
                <td><strong class="text-accent">${exp.experiment_id}</strong></td>
                <td class="dim-text">${exp.timestamp ? exp.timestamp.substring(0, 19).replace('T', ' ') : '---'}</td>
                <td><strong>${exp.selected_model || 'None'}</strong></td>
                <td><span class="badge">${exp.problem_type || 'Unknown'}</span></td>
                <td>${metricsStr || '---'}</td>
            `;
            tableBody.appendChild(tr);
        });

    } catch (err) {
        console.error(err);
    }
}

// Show experiment details modal
async function viewExperimentDetails(experimentId) {
    try {
        const response = await fetch(`/api/experiments/${experimentId}`);
        if (!response.ok) {
            showToast("Failed to load experiment details", true);
            return;
        }

        const exp = await response.json();

        document.getElementById("modal-exp-id").textContent = exp.experiment_id;
        document.getElementById("modal-timestamp").textContent = exp.timestamp ? exp.timestamp.replace('T', ' ') : '---';
        document.getElementById("modal-problem-type").textContent = exp.problem_type || 'Unknown';
        document.getElementById("modal-model").textContent = exp.selected_model || 'None';
        document.getElementById("modal-pipeline").textContent = exp.pipeline_id || 'None';

        const statusSpan = document.getElementById("modal-status");
        statusSpan.textContent = exp.status || 'SUCCESS';
        statusSpan.className = `badge ${exp.status === 'SUCCESS' ? 'success' : 'danger'}`;

        document.getElementById("modal-train-time").textContent = `${exp.training_time_s ? exp.training_time_s.toFixed(2) : 0} sec`;
        document.getElementById("modal-pred-time").textContent = `${exp.prediction_time_s ? exp.prediction_time_s.toFixed(4) : 0} sec`;
        document.getElementById("modal-memory").textContent = `${exp.memory_usage_mb ? exp.memory_usage_mb.toFixed(2) : 0} MB`;
        document.getElementById("modal-hash").textContent = exp.dataset_fingerprint || '---';

        // Render metrics grid
        const mGrid = document.getElementById("modal-metrics");
        mGrid.innerHTML = "";
        if (exp.metrics && Object.keys(exp.metrics).length > 0) {
            Object.entries(exp.metrics).forEach(([m, val]) => {
                let displayVal = typeof val === 'number' ? val.toFixed(4) : String(val);
                const div = document.createElement("div");
                div.className = "metric-card";
                div.innerHTML = `<div class="score">${displayVal}</div><div class="title">${m}</div>`;
                mGrid.appendChild(div);
            });
        } else {
            mGrid.innerHTML = `<p class="dim-text">No metrics logged for this run.</p>`;
        }

        // Render artifacts list
        const aList = document.getElementById("modal-artifacts");
        aList.innerHTML = "";
        if (exp.artifacts && Object.keys(exp.artifacts).length > 0) {
            Object.entries(exp.artifacts).forEach(([name, path]) => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span>${name}</span>
                    <span class="dim-text" style="font-size: 11px;">${path}</span>
                `;
                aList.appendChild(li);
            });
        } else {
            aList.innerHTML = `<li class="dim-text">No saved output artifacts.</li>`;
        }

        // Hyperparameters pre block
        const paramsPre = document.getElementById("modal-hyperparameters");
        if (exp.hyperparameters && Object.keys(exp.hyperparameters).length > 0) {
            paramsPre.textContent = JSON.stringify(exp.hyperparameters, null, 2);
        } else {
            paramsPre.textContent = "None registered.";
        }

        // Show modal overlay
        document.getElementById("experiment-details-modal").classList.remove("hidden");

    } catch (err) {
        showToast("Error fetching experiment detail metrics", true);
        console.error(err);
    }
}

function closeExperimentModal() {
    document.getElementById("experiment-details-modal").classList.add("hidden");
}

// Enable/Disable comparison button based on checkbox count
function updateCompareButtonState() {
    const checkedBoxes = document.querySelectorAll(".exp-row-checkbox:checked");
    const compareBtn = document.getElementById("btn-compare-experiments");
    if (compareBtn) {
        compareBtn.disabled = (checkedBoxes.length !== 2);
    }
}

// Compare two selected runs side by side
async function compareSelectedExperiments() {
    const checkedBoxes = document.querySelectorAll(".exp-row-checkbox:checked");
    if (checkedBoxes.length !== 2) return;

    const exp1 = checkedBoxes[0].value;
    const exp2 = checkedBoxes[1].value;

    try {
        const response = await fetch("/api/experiments/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exp1, exp2 })
        });
        const result = await response.json();

        if (response.ok) {
            document.getElementById("comp-id-a").textContent = exp1;
            document.getElementById("comp-id-b").textContent = exp2;
            document.getElementById("comp-name-a").textContent = exp1;
            document.getElementById("comp-name-b").textContent = exp2;

            const tbody = document.getElementById("compare-metrics-body");
            tbody.innerHTML = "";

            const comparisons = result.metric_comparison || {};

            if (Object.keys(comparisons).length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="center dim-text">No comparable metric properties found.</td></tr>`;
            } else {
                Object.entries(comparisons).forEach(([metric, data]) => {
                    const tr = document.createElement("tr");

                    let exp1Val = typeof data.exp1 === 'number' ? data.exp1.toFixed(4) : String(data.exp1);
                    let exp2Val = typeof data.exp2 === 'number' ? data.exp2.toFixed(4) : String(data.exp2);
                    let diffVal = typeof data.diff === 'number' ? (data.diff > 0 ? '+' : '') + data.diff.toFixed(4) : String(data.diff);

                    let varianceClass = '';
                    if (typeof data.diff === 'number') {
                        varianceClass = data.diff > 0 ? 'text-success' : (data.diff < 0 ? 'text-danger' : '');
                    }

                    tr.innerHTML = `
                        <td><strong>${metric}</strong></td>
                        <td>${exp1Val}</td>
                        <td>${exp2Val}</td>
                        <td class="${varianceClass}">${diffVal}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            document.getElementById("compare-modal").classList.remove("hidden");
        } else {
            showToast(result.error || "Comparison request failed", true);
        }
    } catch (err) {
        showToast("Error fetching comparison results", true);
        console.error(err);
    }
}

function closeCompareModal() {
    document.getElementById("compare-modal").classList.add("hidden");
}
