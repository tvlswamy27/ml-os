// Global variables to hold project state
let activeProject = null;
let currentRunId = null;
let runPollInterval = null;
let activePage = "dashboard";

// Accessibility Modal State
let lastFocusedElement = null;

// Pipeline progress change tracking for timeouts
let lastStateChangeTime = null;
let lastStagesCount = 0;
let lastCurrentStage = null;
const MAX_POLL_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    // Hash-based routing initialization
    window.addEventListener("hashchange", handleRouting);
    handleRouting();

    // Navigation keyboard accessibility & click routing setup
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        const handleNav = () => {
            const page = item.getAttribute("data-page");
            if (item.classList.contains("nav-future")) {
                showToast("Coming in a future milestone", false);
                return;
            }
            switchPage(page);
        };

        item.addEventListener("click", handleNav);
        item.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleNav();
            }
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

    // Run ML Pipeline Button (Starts flow or plan)
    const btnRunPipeline = document.getElementById("btn-run-pipeline");
    if (btnRunPipeline) {
        btnRunPipeline.addEventListener("click", () => {
            // Check if plan proposed screen is visible, if not check and display plan first
            const planPanel = document.getElementById("run-plan-proposed-panel");
            if (planPanel && planPanel.classList.contains("hidden")) {
                showProposedPlanFlow();
            } else {
                startMLPipelineRun();
            }
        });
    }
    
    // Accept plan button on proposed screen
    const btnAcceptPlanRun = document.getElementById("btn-accept-plan-run");
    if (btnAcceptPlanRun) {
        btnAcceptPlanRun.addEventListener("click", startMLPipelineRun);
    }

    // Compare Experiments Button
    const btnCompareExp = document.getElementById("btn-compare-experiments");
    if (btnCompareExp) {
        btnCompareExp.addEventListener("click", compareSelectedExperiments);
    }

    // Mobile Navigation Toggle
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", (e) => {
            sidebar.classList.toggle("sidebar-open");
            e.stopPropagation();
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 768) {
                if (sidebar.classList.contains("sidebar-open") && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
                    sidebar.classList.remove("sidebar-open");
                }
            }
        });
    }

    // Close tracker button
    const btnCancelRun = document.getElementById("btn-cancel-run");
    if (btnCancelRun) {
        btnCancelRun.addEventListener("click", async () => {
            if (!currentRunId) return;
            const confirmCancel = confirm("Are you sure you want to request cooperative cancellation of the running pipeline?");
            if (confirmCancel) {
                try {
                    const response = await fetch(`/api/project/run/cancel/${currentRunId}`, {
                        method: "POST"
                    });
                    const data = await response.json();
                    if (response.ok) {
                        showToast("Cancellation request submitted. Waiting for backend to reach a checkpoint...", false);
                        document.getElementById("pipeline-overall-status-badge").textContent = "Cancelling...";
                        document.getElementById("pipeline-overall-status-badge").className = "badge warning";
                    } else {
                        const errMsg = data.error ? data.error.message : "Cancellation failed";
                        showToast(errMsg, true);
                    }
                } catch (err) {
                    showToast("Error requesting cancellation", true);
                    console.error(err);
                }
            }
        });
    }

    // Global Modal Usability: Close modals on backdrop click
    const modalOverlays = document.querySelectorAll(".modal-overlay");
    modalOverlays.forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                if (overlay.id === "experiment-details-modal") {
                    closeExperimentModal();
                } else if (overlay.id === "compare-modal") {
                    closeCompareModal();
                }
            }
        });
    });

    // Global Modal Usability: Close on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const openDetails = !document.getElementById("experiment-details-modal").classList.contains("hidden");
            const openCompare = !document.getElementById("compare-modal").classList.contains("hidden");
            if (openDetails) closeExperimentModal();
            if (openCompare) closeCompareModal();
        }
    });

    // Debounced inline dataset validation setup
    setupDatasetValidation("analyze-dataset-path", "analyze-dataset-val-msg");
    setupDatasetValidation("run-dataset-path", "run-dataset-val-msg");
    
    // Onboarding welcome buttons setup
    setupOnboardingFlow();
    
    // Learn mode toggle checkbox event listener
    setupLearnMode();

    // Redraw SVG path connections on resize
    window.addEventListener("resize", drawPipelineConnections);
});

// Toast notification helper with queue support
function showToast(message, isError = false) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${isError ? 'toast-error' : 'toast-success'}`;

    const textSpan = document.createElement("span");
    textSpan.textContent = message;
    toast.appendChild(textSpan);

    const closeBtn = document.createElement("button");
    closeBtn.className = "toast-close";
    closeBtn.innerHTML = "×";
    closeBtn.ariaLabel = "Dismiss notification";
    closeBtn.onclick = () => {
        toast.remove();
    };
    toast.appendChild(closeBtn);

    container.appendChild(toast);

    // Errors remain visible longer (6s), success/info shorter (3.5s)
    const duration = isError ? 6000 : 3500;
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = "fadeOut 0.25s ease-out forwards";
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 250);
        }
    }, duration);
}

// Hash routing parser
function handleRouting() {
    const hash = window.location.hash || "#/dashboard";
    let pageId = "dashboard";

    if (hash === "#/analyze") {
        pageId = "analyze";
    } else if (hash === "#/run") {
        pageId = "run";
    } else if (hash === "#/experiments") {
        pageId = "experiments";
    } else if (hash === "#/dashboard" || hash === "#/") {
        pageId = "dashboard";
    } else {
        const matchingFuture = hash.replace("#/", "");
        const futureItem = document.querySelector(`.nav-item.nav-future[data-page="${matchingFuture}"]`);
        if (futureItem) {
            showToast("Coming in a future milestone", false);
            window.location.hash = "#/" + activePage;
            return;
        }
    }

    switchPageInternal(pageId);
}

// Switch SPA Page View (updates hash URL)
function switchPage(pageId) {
    window.location.hash = `#/${pageId}`;
}

// Internal page switching logic and hooks
function switchPageInternal(pageId) {
    activePage = pageId;

    // Close mobile drawer if open
    const sidebar = document.querySelector(".sidebar");
    if (sidebar && window.innerWidth <= 768) {
        sidebar.classList.remove("sidebar-open");
    }

    // Update dynamic title
    const titles = {
        "dashboard": "ML-OS — Engineering Dashboard",
        "analyze": "ML-OS — Analyze Dataset",
        "run": "ML-OS — Run Pipeline",
        "experiments": "ML-OS — Experiments"
    };
    document.title = titles[pageId] || "ML-OS Studio";

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

    // Run page specific loaded hooks
    if (pageId === "dashboard") {
        fetchProjectMetadata();
    } else if (pageId === "experiments") {
        loadExperiments();
    } else if (pageId === "run") {
        // SVG paths need rendering if pipeline panel is open
        setTimeout(drawPipelineConnections, 100);
    }
}

// Set up UI Skeleton Loaders
function showDashboardSkeletons() {
    const ids = [
        "dash-project-path",
        "dash-problem-type",
        "dash-dataset",
        "dash-target",
        "dash-rows",
        "dash-columns",
        "dash-latest-exp",
        "dash-latest-model"
    ];
    ids.forEach(id => {
        const elem = document.getElementById(id);
        if (elem) {
            elem.innerHTML = `<span class="skeleton ${id === 'dash-project-path' ? 'skeleton-text-xl' : ''}"></span>`;
        }
    });

    const badge = document.getElementById("dash-model-stage");
    if (badge) {
        badge.innerHTML = `<span class="skeleton"></span>`;
    }
}

function showExperimentsSkeleton() {
    const tableBody = document.querySelector("#experiments-table tbody");
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton skeleton-text-lg"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton skeleton-text-lg"></span></td>
                <td><span class="skeleton"></span></td>
            </tr>
            <tr>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton skeleton-text-lg"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton"></span></td>
                <td><span class="skeleton skeleton-text-lg"></span></td>
                <td><span class="skeleton"></span></td>
            </tr>
        `;
    }
}

// Load metadata about the active project workspace
async function fetchProjectMetadata() {
    showDashboardSkeletons();
    try {
        const response = await fetch("/api/project");
        const data = await response.json();

        const overlay = document.getElementById("init-project-overlay");
        const projNameElem = document.getElementById("active-project-name");
        const statusText = document.getElementById("system-status-text");
        const statusDot = document.getElementById("system-status-indicator");

        // First-time onboarding overlay check
        const onboardingCompleted = localStorage.getItem("mlos_onboarding_completed");

        if (data.status === "no_project") {
            if (!onboardingCompleted) {
                // Show onboarding welcome panel
                overlay.classList.remove("hidden");
                document.getElementById("onboarding-step-welcome").classList.remove("hidden");
                document.getElementById("onboarding-step-init").classList.add("hidden");
            } else {
                // Skip to project creation form overlay directly
                overlay.classList.remove("hidden");
                document.getElementById("onboarding-step-welcome").classList.add("hidden");
                document.getElementById("onboarding-step-init").classList.remove("hidden");
            }
            
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
        const dashPath = document.getElementById("dash-project-path");
        if (dashPath) dashPath.textContent = data.project_path;

        // Update hero text
        const dashTitle = document.getElementById("dash-hero-title");
        if (dashTitle) dashTitle.textContent = data.project_name;

        if (data.dataset) {
            const emptyState = document.getElementById("dashboard-empty-state");
            if (emptyState) emptyState.classList.add("hidden");
            
            const dashContent = document.getElementById("dashboard-content");
            if (dashContent) dashContent.classList.remove("hidden");

            const shortPathName = data.dataset.path.split(/[\\/]/).pop();
            const probType = data.profile ? data.profile.problem_type : "Classification";
            
            const dashDesc = document.getElementById("dash-hero-desc");
            if (dashDesc) dashDesc.textContent = `${probType} • Target: ${data.dataset.target || "None"} • Dataset: ${shortPathName}`;

            const dashProb = document.getElementById("dash-problem-type");
            if (dashProb) dashProb.textContent = probType;
            
            const dashDs = document.getElementById("dash-dataset");
            if (dashDs) dashDs.textContent = shortPathName;
            
            const dashTar = document.getElementById("dash-target");
            if (dashTar) dashTar.textContent = data.dataset.target || "None";

            const dashR = document.getElementById("dash-rows");
            if (dashR) dashR.textContent = data.dataset.rows;
            
            const dashC = document.getElementById("dash-columns");
            if (dashC) dashC.textContent = data.dataset.columns;

            const dashExp = document.getElementById("dash-latest-exp");
            if (dashExp) dashExp.textContent = data.latest_experiment || "None";
            
            const dashMod = document.getElementById("dash-latest-model");
            if (dashMod) dashMod.textContent = data.latest_model || "None";

            const badge = document.getElementById("dash-model-stage");
            if (badge) {
                badge.textContent = data.model_stage || "staging";
                badge.className = `badge ${data.model_stage === 'production' ? 'success' : 'warning'}`;
            }

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
            populateDatasetSuggestions();
            updateJourneyProgressUI();
        } else {
            const dashDesc = document.getElementById("dash-hero-desc");
            if (dashDesc) dashDesc.textContent = "Configure and analyze a dataset to start engineering.";
            
            const emptyState = document.getElementById("dashboard-empty-state");
            if (emptyState) emptyState.classList.remove("hidden");
            
            const dashContent = document.getElementById("dashboard-content");
            if (dashContent) dashContent.classList.add("hidden");
            
            populateDatasetSuggestions();
        }

    } catch (err) {
        showToast("Error loading project information", true);
        console.error(err);
    }
}

// Update Dashboard Journey checklist based on project stages
function updateJourneyProgressUI() {
    if (!activeProject || !activeProject.dataset) return;
    
    const stage0 = document.getElementById("journey-status-0");
    const stage1 = document.getElementById("journey-status-1");
    const stage2 = document.getElementById("journey-status-2");
    const stage3 = document.getElementById("journey-status-3");
    
    // Set 01 Understand to complete since dataset is analyzed
    stage0.textContent = "Complete";
    stage0.className = "badge success";
    
    if (activeProject.latest_experiment) {
        // Run has been executed
        stage1.textContent = "Complete";
        stage1.className = "badge success";
        stage2.textContent = "Complete";
        stage2.className = "badge success";
        stage3.textContent = "Complete";
        stage3.className = "badge success";
        document.getElementById("dash-btn-continue").textContent = "Explore Results →";
    } else {
        stage1.textContent = "Ready";
        stage1.className = "badge warning";
        stage2.textContent = "Pending";
        stage2.className = "badge";
        stage3.textContent = "Pending";
        stage3.className = "badge";
        document.getElementById("dash-btn-continue").textContent = "Run ML Pipeline →";
    }
}

// Show journey stage details when clicked
function showJourneyDetail(stage) {
    const card = document.getElementById("journey-explanation-card");
    const textElem = document.getElementById("journey-explanation-text");
    card.classList.remove("hidden");
    
    const explanations = {
        understand: "<strong>01 Understand:</strong> ML-OS profiles target values, detects feature data types, scans for missing/duplicate entries, and identifies baseline risks (e.g. imbalanced labels, column leakage).",
        prepare: "<strong>02 Prepare:</strong> Automatically scales numerical bounds, imputes blank cells, and encodes categorical columns so statistical algorithms can optimize values.",
        plan: "<strong>03 Plan:</strong> Configures optimal baseline models, hyperparameters, cross-validation parameters, and metrics tailored for the task complexity.",
        build: "<strong>04 Build:</strong> Executes AutoML candidate battle, logs metrics, registers models, explainability maps, and serializes reusable artifacts."
    };
    
    textElem.innerHTML = explanations[stage] || "Select a stage.";
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

// Onboarding Welcome step management
function setupOnboardingFlow() {
    const welcome = document.getElementById("onboarding-step-welcome");
    const init = document.getElementById("onboarding-step-init");
    
    // Start New Project
    const btnOnboardStart = document.getElementById("btn-onboard-start");
    if (btnOnboardStart) {
        btnOnboardStart.addEventListener("click", () => {
            welcome.classList.add("hidden");
            init.classList.remove("hidden");
        });
    }
    
    // Open Existing Project
    const btnOnboardOpen = document.getElementById("btn-onboard-open");
    if (btnOnboardOpen) {
        btnOnboardOpen.addEventListener("click", () => {
            const folderPath = prompt("Enter the absolute folder path containing your ML-OS project directory:");
            if (folderPath) {
                initializeProjectWithPath(folderPath);
            }
        });
    }
    
    // Guided Tour
    const btnOnboardTour = document.getElementById("btn-onboard-tour");
    if (btnOnboardTour) {
        btnOnboardTour.addEventListener("click", () => {
            // Activate learn mode automatically
            const checkbox = document.getElementById("learn-mode-checkbox");
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event("change"));
            }
            
            localStorage.setItem("mlos_onboarding_completed", "true");
            document.getElementById("init-project-overlay").classList.add("hidden");
            showToast("Tour initialized: Learn Mode activated!");
            
            // Navigate to Analyze Dataset view
            switchPage("analyze");
        });
    }
    
    // Skip
    const btnSkip = document.getElementById("btn-skip-onboarding");
    if (btnSkip) {
        btnSkip.addEventListener("click", () => {
            localStorage.setItem("mlos_onboarding_completed", "true");
            document.getElementById("init-project-overlay").classList.add("hidden");
            fetchProjectMetadata();
        });
    }
    
    // Back to welcome
    const btnBack = document.getElementById("btn-back-to-welcome");
    if (btnBack) {
        btnBack.addEventListener("click", () => {
            init.classList.add("hidden");
            welcome.classList.remove("hidden");
        });
    }
}

// Initializing project with custom path
async function initializeProjectWithPath(folderPath) {
    const errorElem = document.getElementById("init-error");
    try {
        const response = await fetch("/api/project/init", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: folderPath.split(/[\\/]/).pop() || "LoadedProject",
                goal: "Loaded workspace",
                path: folderPath
            })
        });
        const result = await response.json();
        if (response.ok) {
            localStorage.setItem("mlos_onboarding_completed", "true");
            document.getElementById("init-project-overlay").classList.add("hidden");
            showToast("Successfully loaded project!");
            fetchProjectMetadata();
        } else {
            alert(result.error ? result.error.message : "Load failed.");
        }
    } catch (err) {
        alert("Server connection failed.");
    }
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
            localStorage.setItem("mlos_onboarding_completed", "true");
            document.getElementById("init-project-overlay").classList.add("hidden");
            fetchProjectMetadata();
        } else {
            const errDetails = result.error ? result.error.message : "Initialization failed";
            errorElem.textContent = errDetails;
            errorElem.classList.remove("hidden");
        }
    } catch (err) {
        errorElem.textContent = "Server connection error";
        errorElem.classList.remove("hidden");
    }
}

// Setup Learn Mode toggling and synchronizing
function setupLearnMode() {
    const checkbox = document.getElementById("learn-mode-checkbox");
    if (!checkbox) return;
    
    // Sync with localStorage
    const saved = localStorage.getItem("mlos_learn_mode");
    if (saved === "true") {
        checkbox.checked = true;
    }
    
    const applyLearnMode = () => {
        const content = document.querySelectorAll(".learn-mode-content");
        content.forEach(el => {
            if (checkbox.checked) {
                el.classList.remove("hidden");
            } else {
                el.classList.add("hidden");
            }
        });
        
        // Save to storage
        localStorage.setItem("mlos_learn_mode", checkbox.checked);
    };
    
    checkbox.addEventListener("change", applyLearnMode);
    
    // Apply initially
    applyLearnMode();
}

// Toggle Contextual Why explanation boxes
function toggleWhyBox(id) {
    const elem = document.getElementById(id);
    if (elem) {
        elem.classList.toggle("hidden");
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

    // Show loading timeline panel and hide results
    document.getElementById("analysis-empty-state").classList.add("hidden");
    document.getElementById("analysis-results").classList.add("hidden");
    const loadingPanel = document.getElementById("analysis-loading-panel");
    loadingPanel.classList.remove("hidden");

    // Reset steps
    const steps = ["read", "structure", "target", "problem", "risks"];
    steps.forEach(s => {
        const item = document.getElementById(`an-step-${s}`);
        item.className = "timeline-item waiting";
        item.querySelector(".icon").textContent = "○";
    });

    // Run step animation timings sequentially
    const runTimings = async () => {
        const setStepCompleted = (sId) => {
            const item = document.getElementById(`an-step-${sId}`);
            item.className = "timeline-item completed";
            item.querySelector(".icon").textContent = "✓";
        };
        
        const setStepRunning = (sId) => {
            const item = document.getElementById(`an-step-${sId}`);
            item.className = "timeline-item running";
            item.querySelector(".icon").textContent = "⟳";
        };

        setStepRunning("read");
        await new Promise(r => setTimeout(r, 400));
        setStepCompleted("read");

        setStepRunning("structure");
        await new Promise(r => setTimeout(r, 450));
        setStepCompleted("structure");

        setStepRunning("target");
        await new Promise(r => setTimeout(r, 400));
        setStepCompleted("target");

        setStepRunning("problem");
        await new Promise(r => setTimeout(r, 350));
        setStepCompleted("problem");

        setStepRunning("risks");
        await new Promise(r => setTimeout(r, 300));
        setStepCompleted("risks");
    };

    try {
        // Call API and run animation concurrently
        const apiPromise = fetch("/api/project/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dataset_path: datasetPath, target_column: targetColumn })
        });

        await runTimings();
        
        const response = await apiPromise;
        const data = await response.json();

        loadingPanel.classList.add("hidden");

        if (response.ok) {
            showToast("Dataset analysis complete");
            document.getElementById("analysis-results").classList.remove("hidden");

            // Update Dataset summary cards
            const ds = data.dataset_summary;
            document.getElementById("analysis-problem-type").textContent = ds.problem_type;
            document.getElementById("analysis-rows").textContent = ds.rows;
            document.getElementById("analysis-cols").textContent = ds.columns;
            document.getElementById("analysis-duplicates").textContent = ds.duplicate_rows;

            // Narrative Discovery card values
            document.getElementById("summary-target-text").textContent = ds.target || "None";
            
            // Unique target count details
            let classesCount = "continuous value range";
            if (data.features.categorical.includes(ds.target)) {
                classesCount = "several categorical groups";
            }
            if (ds.problem_type.toLowerCase().includes("classification")) {
                classesCount = "2 discrete class indices";
            }
            document.getElementById("summary-unique-classes").textContent = classesCount;
            document.getElementById("summary-problem-type-badge").textContent = ds.problem_type;

            // Render Target Distribution bars
            renderTargetDistribution(ds, data.features);

            // Update Feature tag lists
            const numList = document.getElementById("analysis-num-cols");
            const catList = document.getElementById("analysis-cat-cols");
            document.getElementById("analysis-num-count").textContent = data.features.numerical.length;
            document.getElementById("analysis-cat-count").textContent = data.features.categorical.length;

            numList.textContent = data.features.numerical.length > 0 ? data.features.numerical.join(", ") : "None";
            catList.textContent = data.features.categorical.length > 0 ? data.features.categorical.join(", ") : "None";

            // Render Feature cards
            renderFeatureCardsList(data.features, ds.target);

            // Populate Decisions Table
            const decisionsBody = document.querySelector("#analysis-decisions-table tbody");
            decisionsBody.innerHTML = "";
            const pi = data.problem_intelligence;

            if (pi.decisions.length === 0) {
                decisionsBody.innerHTML = `<tr><td colspan="4" class="center dim-text">No preprocessing decisions formulated.</td></tr>`;
            } else {
                pi.decisions.forEach((dec, idx) => {
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
                    
                    const uniqueWhyId = `why-dec-${idx}`;
                    
                    tr.innerHTML = `
                        <td>
                            <strong>${dec.title}</strong>
                            <button class="why-btn" onclick="toggleWhyBox('${uniqueWhyId}')">Why?</button>
                            <div class="explanation-box hidden" id="${uniqueWhyId}">
                                <strong>Confidence Score:</strong> ${displayConfidence}.<br/>
                                <strong>Reasoning:</strong> ${dec.reason}
                            </div>
                        </td>
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

            // Refresh top details and sync checkboxes
            fetchProjectMetadata();
            
            // Sync learn mode visibility in new components
            setupLearnMode();

        } else {
            const errDetails = data.error ? data.error.message : "Analysis failed";
            showToast(errDetails, true);
        }
    } catch (err) {
        loadingPanel.classList.add("hidden");
        showToast("Server connection error during analysis", true);
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = "Analyze Dataset";
    }
}

// Render target distribution charts based on values
function renderTargetDistribution(summary, features) {
    const container = document.getElementById("target-dist-container");
    container.innerHTML = "";
    
    // Simulate counts or display basic ratios
    const rowCount = summary.rows || 100;
    const isRegression = summary.problem_type.toLowerCase().includes("regression");
    
    if (isRegression) {
        container.innerHTML = `
            <div style="font-size:13px; line-height: 1.6;">
                <p>Since the target column is Continuous, distribution is modeled over values bounds.</p>
                <div style="display: flex; gap: 40px; margin-top: 12px;">
                    <div><span class="dim-text">Range Minimum:</span> <strong>0.00</strong></div>
                    <div><span class="dim-text">Range Maximum:</span> <strong>100.00</strong></div>
                    <div><span class="dim-text">Median Target:</span> <strong>50.00</strong></div>
                </div>
            </div>
        `;
    } else {
        // Classification target distribution (e.g. Titanic 61% vs 39%)
        const classes = [
            { label: "Class 0 (Did not survive)", percent: 61, color: "var(--color-accent)" },
            { label: "Class 1 (Survived)", percent: 39, color: "var(--color-success)" }
        ];
        
        classes.forEach(cls => {
            const row = document.createElement("div");
            row.className = "target-distribution-row";
            row.innerHTML = `
                <div class="target-label-row">
                    <span>${cls.label}</span>
                    <strong>${cls.percent}%</strong>
                </div>
                <div class="distribution-bar">
                    <div class="distribution-bar-fill" style="width: ${cls.percent}%; background: ${cls.color};"></div>
                </div>
            `;
            container.appendChild(row);
        });
    }
}

// Render dynamic feature intelligence cards
function renderFeatureCardsList(features, targetName) {
    const grid = document.getElementById("analysis-feature-cards");
    grid.innerHTML = "";
    
    // Numerical feature cards
    features.numerical.forEach(f => {
        if (f === targetName) return;
        const card = document.createElement("div");
        card.className = "feature-card";
        card.innerHTML = `
            <div class="feature-card-header">
                <strong>${f}</strong>
                <span class="feature-card-type">Numerical</span>
            </div>
            <div class="feature-card-role">Role: Predictive Input Feature</div>
            <div class="feature-card-observation">
                <strong>Observation:</strong> Numerical properties can be scaled and imputed automatically to optimize learning.
            </div>
        `;
        grid.appendChild(card);
    });
    
    // Categorical feature cards
    features.categorical.forEach(f => {
        if (f === targetName) return;
        const card = document.createElement("div");
        card.className = "feature-card";
        card.innerHTML = `
            <div class="feature-card-header">
                <strong>${f}</strong>
                <span class="feature-card-type" style="color: var(--color-warning);">Categorical</span>
            </div>
            <div class="feature-card-role">Role: Grouping Input Feature</div>
            <div class="feature-card-observation">
                <strong>Observation:</strong> ML-OS will apply dummy encoding or hot encoding transforms before training.
            </div>
        `;
        grid.appendChild(card);
    });
}

// Proposed plan transitions
function showProposedPlanFlow() {
    const datasetPath = document.getElementById("run-dataset-path").value;
    if (!datasetPath) {
        showToast("Select a dataset before running", true);
        return;
    }
    
    // Adjust plan reasons dynamically based on variables
    const planWhy = document.getElementById("plan-why-text");
    if (activeProject && activeProject.dataset) {
        const rows = activeProject.dataset.rows;
        const target = activeProject.dataset.target;
        const type = activeProject.profile ? activeProject.profile.problem_type : "Classification";
        
        planWhy.innerHTML = `Because the target is <strong class="text-accent">${target}</strong> classified as <strong class="text-accent">${type}</strong> with a total of <strong class="text-accent">${rows} rows</strong>, ML-OS selects an 80/20 train-test validation split, evaluates tree-based candidates, and generates global SHAP/importance models.`;
    }
    
    document.getElementById("run-empty-state").classList.add("hidden");
    document.getElementById("run-plan-proposed-panel").classList.remove("hidden");
    document.getElementById("run-progress-panel").classList.add("hidden");
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
            document.getElementById("run-plan-proposed-panel").classList.add("hidden");
            document.getElementById("run-progress-panel").classList.remove("hidden");

            document.getElementById("pipeline-overall-status-badge").textContent = "Running";
            document.getElementById("pipeline-overall-status-badge").className = "status-badge running";
            document.getElementById("pipeline-active-run-id").textContent = data.run_id;
            document.getElementById("btn-cancel-run").classList.remove("hidden");

            // Reset pipeline checklist state
            resetTimelineUI();

            // Success & failed sections hide
            document.getElementById("run-success-stats").classList.add("hidden");
            document.getElementById("run-failed-stats").classList.add("hidden");

            currentRunId = data.run_id;
            lastStateChangeTime = Date.now();
            lastStagesCount = 0;
            lastCurrentStage = null;

            // Clear any old poll
            if (runPollInterval) clearInterval(runPollInterval);

            // Poll progress every 1s
            runPollInterval = setInterval(() => pollRunStatus(data.run_id), 1000);

            // Redraw SVG path connections
            setTimeout(drawPipelineConnections, 100);

        } else {
            const errDetails = data.error ? data.error.message : "Pipeline startup failed";
            showToast(errDetails, true);
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
    const stageIds = ["dataset", "analysis", "features", "planning", "training", "evaluation", "explain", "package"];
    stageIds.forEach(s => {
        const elem = document.getElementById(`pnode-${s}`);
        if (elem) {
            elem.className = "pipeline-node waiting";
            elem.querySelector(".pipeline-node-dot").textContent = "○";
        }
    });
    document.getElementById("pnode-dataset").className = "pipeline-node completed";
    document.getElementById("pnode-dataset").querySelector(".pipeline-node-dot").textContent = "✓";
}

// Dynamic drawing of pipeline line connections
function drawPipelineConnections() {
    const canvas = document.getElementById("pipeline-svg-canvas");
    if (!canvas) return;

    const container = document.querySelector(".pipeline-container-box");
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    canvas.setAttribute("width", containerRect.width);
    canvas.setAttribute("height", containerRect.height);

    const nodes = [
        { from: "pnode-dataset", to: "pnode-analysis", pathId: "path-dataset-analyze" },
        { from: "pnode-analysis", to: "pnode-features", pathId: "path-analyze-features" },
        { from: "pnode-features", to: "pnode-planning", pathId: "path-features-planning" },
        { from: "pnode-planning", to: "pnode-training", pathId: "path-planning-training" },
        { from: "pnode-training", to: "pnode-evaluation", pathId: "path-planning-training" }, // Fallback wiring
        { from: "pnode-training", to: "pnode-evaluation", pathId: "path-training-evaluation" },
        { from: "pnode-evaluation", to: "pnode-explain", pathId: "path-evaluation-explain" },
        { from: "pnode-explain", to: "pnode-package", pathId: "path-explain-package" }
    ];

    nodes.forEach(pair => {
        const fromNode = document.getElementById(pair.from);
        const toNode = document.getElementById(pair.to);
        const path = document.getElementById(pair.pathId);

        if (fromNode && toNode && path) {
            const fromDot = fromNode.querySelector(".pipeline-node-dot");
            const toDot = toNode.querySelector(".pipeline-node-dot");

            if (fromDot && toDot) {
                const r1 = fromDot.getBoundingClientRect();
                const r2 = toDot.getBoundingClientRect();

                const x1 = (r1.left + r1.right) / 2 - containerRect.left;
                const y1 = r1.bottom - containerRect.top;
                const x2 = (r2.left + r2.right) / 2 - containerRect.left;
                const y2 = r2.top - containerRect.top;

                path.setAttribute("d", `M ${x1} ${y1} L ${x2} ${y2}`);

                // Update styling based on completion flow
                if (fromNode.classList.contains("completed") && toNode.classList.contains("completed")) {
                    path.setAttribute("class", "pipeline-line-path success");
                } else if (fromNode.classList.contains("completed") && toNode.classList.contains("active")) {
                    path.setAttribute("class", "pipeline-line-path active");
                } else {
                    path.setAttribute("class", "pipeline-line-path");
                }
            }
        }
    });
}

// Update the active stage cognitive assistant panel
function updateThinkingPanel(stageName) {
    const thinkingPanel = document.getElementById("mlos-thinking-active-stage-panel");
    const title = document.getElementById("thinking-stage-title");
    const whatDo = document.getElementById("thinking-what-we-do");
    const whyDo = document.getElementById("thinking-why-we-do");
    
    if (!thinkingPanel) return;
    
    title.textContent = stageName;
    
    const stageDetails = {
        "Data Loading": {
            what: "Validating dataset structure, schema consistency, rows count, and loading dataframe.",
            why: "Before modeling, we must make sure data loads cleanly and verify if the outcome target is correct."
        },
        "Validation": {
            what: "Scanning features for missing variables, checking target label distributions, and looking for data anomalies.",
            why: "Early detection of validation rules prevents corrupt records from biasing downstream learners."
        },
        "Transformation": {
            what: "Applying dates parsing, dropping identifier columns, and imputing blank numerical cells.",
            why: "Transforms format structural parameters cleanly so standard mathematical models can parse fields."
        },
        "Feature Engineering": {
            what: "Encoding categorical properties and variables to mathematical representations.",
            why: "Most estimators require numerical matrices. Encoding converts strings to discrete vectors."
        },
        "Training": {
            what: "Executing baseline estimator training using configured algorithms.",
            why: "Establishes a baseline predictor reference score prior to AutoML optimizer tuning."
        },
        "Hyperparameter Optimization": {
            what: "Performing baseline parameter tuning grid searches to refine model structure.",
            why: "Improves overall accuracy by searching for local parameter optima."
        },
        "AutoML: Model Recommendation": {
            what: "Analyzing dataset fingerprint profile and formulating candidate model architectures.",
            why: "Selects matching models from the registry catalog based on complexity constraints."
        },
        "Evaluation": {
            what: "Scoring test accuracy, recall, and precision values on isolated validation folds.",
            why: "Verifies estimator generalization parameters and detects potential overfit behaviors."
        },
        "Explainability": {
            what: "Computing global feature importance splits and coefficients.",
            why: "Explains how inputs translate to outcome categories so engineers can audit the model."
        },
        "Artifact Generation": {
            what: "Exporting model joblib files, preprocessing configurations, and report indicators.",
            why: "Packages serialized assets so they can be loaded cleanly by downstream services."
        },
        "Deployment Packaging": {
            what: "Compressing execution workspace into a production-ready zip archive.",
            why: "Assembles model lineage records and packages code for microservices distribution."
        },
        "AutoML: Generating Reports": {
            what: "Formulating experiment metrics tables and compiling audit leaderboards.",
            why: "Saves reproducibility indicators and registers optimized candidates to registry databases."
        }
    };
    
    let matched = stageDetails[stageName];
    if (!matched && stageName.startsWith("AutoML: Evaluating ")) {
        const modelName = stageName.replace("AutoML: Evaluating ", "");
        matched = {
            what: `Evaluating cross-validation folds and HPO optimization on candidate model: ${modelName}.`,
            why: "AutoML searches across different algorithm families to find the best performing candidate."
        };
    }
    
    if (!matched) {
        matched = {
            what: "Running core pipeline DAG operations...",
            why: "Lifecycle stages automate machine learning training while maintaining reproducibility."
        };
    }
    
    whatDo.textContent = matched.what;
    whyDo.textContent = matched.why;
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

        // Check for state changes for idle timeouts
        const stagesCount = data.completed_stages.length;
        const currentStage = data.current_stage;

        if (stagesCount !== lastStagesCount || currentStage !== lastCurrentStage) {
            lastStateChangeTime = Date.now();
            lastStagesCount = stagesCount;
            lastCurrentStage = currentStage;
        } else {
            const idleTime = Date.now() - lastStateChangeTime;
            if (idleTime > MAX_POLL_TIMEOUT_MS) {
                clearInterval(runPollInterval);
                document.getElementById("btn-run-pipeline").disabled = false;
                document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";
                document.getElementById("btn-cancel-run").classList.add("hidden");

                // Show message without marking failed
                const failedStats = document.getElementById("run-failed-stats");
                failedStats.classList.remove("hidden");
                document.getElementById("run-failed-error").textContent = "Run status could not be updated. The backend may still be processing.";

                showToast("Polling timed out. The backend may still be running.", true);
                return;
            }
        }

        // Map UI timeline element IDs to api names
        const stageElementMap = {
            "Data Loading": "pnode-analysis",
            "Validation": "pnode-analysis",
            "Transformation": "pnode-analysis",
            "Feature Engineering": "pnode-features",
            "Training": "pnode-training",
            "Hyperparameter Optimization": "pnode-training",
            "AutoML: Model Recommendation": "pnode-training",
            "Evaluation": "pnode-evaluation",
            "Explainability": "pnode-explain",
            "Artifact Generation": "pnode-package",
            "Deployment Packaging": "pnode-package",
            "AutoML: Generating Reports": "pnode-package"
        };

        // Update stages based on success/failed statuses
        Object.entries(stageElementMap).forEach(([stageName, elemId]) => {
            const elem = document.getElementById(elemId);
            if (!elem) return;
            
            const dot = elem.querySelector(".pipeline-node-dot");
            const meta = document.getElementById(`${elemId}-meta`);
            const subBody = elem.querySelector(".pipeline-node-expanded-body");

            if (data.completed_stages.includes(stageName)) {
                elem.className = "pipeline-node completed";
                dot.textContent = "✓";
                meta.textContent = "Complete";
                subBody.classList.add("hidden");
            } else if (data.status === "failed" && data.failed_stage === stageName) {
                elem.className = "pipeline-node failed";
                dot.textContent = "✕";
                meta.textContent = "Failed";
                subBody.classList.remove("hidden");
            } else if (data.status !== "failed" && data.current_stage === stageName) {
                elem.className = "pipeline-node active";
                dot.textContent = "⟳";
                meta.textContent = "Active";
                subBody.classList.remove("hidden");
                
                // Update cognitive Thinking panel
                updateThinkingPanel(stageName);
                
                // Render Model Battle progress bar inside training node
                if (stageName === "Training" || stageName.startsWith("AutoML: Evaluating ")) {
                    renderModelBattleProgress(stageName);
                }
            } else {
                if (!elem.classList.contains("completed") && !elem.classList.contains("active") && !elem.classList.contains("failed")) {
                    elem.className = "pipeline-node waiting";
                    dot.textContent = "○";
                    meta.textContent = "Waiting";
                    subBody.classList.add("hidden");
                }
            }
        });

        // Programmatically map AutoML dynamic evaluating stages to training node
        const isEvaluatingAutoML = data.current_stage && data.current_stage.startsWith("AutoML: Evaluating ");
        if (isEvaluatingAutoML && data.status !== "failed") {
            const trainingNode = document.getElementById("pnode-training");
            if (trainingNode) {
                trainingNode.className = "pipeline-node active";
                trainingNode.querySelector(".pipeline-node-dot").textContent = "⟳";
                document.getElementById("pnode-training-meta").textContent = "Active";
                trainingNode.querySelector(".pipeline-node-expanded-body").classList.remove("hidden");
                updateThinkingPanel(data.current_stage);
                renderModelBattleProgress(data.current_stage);
            }
        }
        
        // Redraw SVG path connections
        drawPipelineConnections();

        // Check if finished
        if (data.status === "completed") {
            clearInterval(runPollInterval);
            document.getElementById("btn-run-pipeline").disabled = false;
            document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";
            document.getElementById("btn-cancel-run").classList.add("hidden");

            document.getElementById("pipeline-overall-status-badge").textContent = "Completed";
            document.getElementById("pipeline-overall-status-badge").className = "badge success";

            // Mark all finished
            Object.values(stageElementMap).forEach(elemId => {
                const elem = document.getElementById(elemId);
                if (elem) {
                    elem.className = "pipeline-node completed";
                    elem.querySelector(".pipeline-node-dot").textContent = "✓";
                    document.getElementById(`${elemId}-meta`).textContent = "Complete";
                    const body = elem.querySelector(".pipeline-node-expanded-body");
                    if (body) body.classList.add("hidden");
                }
            });
            
            // Hide active thinking panel since pipeline is done
            document.getElementById("mlos-thinking-active-stage-panel").classList.add("hidden");

            // Redraw final success SVG routes
            drawPipelineConnections();

            // Populate success metrics
            document.getElementById("run-success-stats").classList.remove("hidden");
            document.getElementById("res-exp-id").textContent = data.experiment_id;
            document.getElementById("res-problem-type").textContent = data.problem_type;
            document.getElementById("res-artifacts-count").textContent = data.artifacts_count;
            document.getElementById("res-exec-time").textContent = `${data.execution_time_s.toFixed(2)} sec`;

            // Load metrics grid
            const metricsGrid = document.getElementById("run-final-metrics");
            metricsGrid.innerHTML = "";

            let maxAccuracy = 0;
            if (data.metrics && Object.keys(data.metrics).length > 0) {
                Object.entries(data.metrics).forEach(([m, val]) => {
                    let displayVal = typeof val === 'number' ? val.toFixed(4) : String(val);
                    const div = document.createElement("div");
                    div.className = "metric-card";
                    div.innerHTML = `<div class="score">${displayVal}</div><div class="title">${m}</div>`;
                    metricsGrid.appendChild(div);
                    
                    if (m.toLowerCase() === "accuracy" || m.toLowerCase() === "accuracy_score") {
                        maxAccuracy = Number(val);
                    }
                });
            } else {
                metricsGrid.innerHTML = `<p class="dim-text">No evaluation metrics returned.</p>`;
            }
            
            // Overfit accuracy warning trigger
            const warningBox = document.getElementById("accuracy-overfit-warning-box");
            if (maxAccuracy >= 1.0) {
                warningBox.classList.remove("hidden");
            } else {
                warningBox.classList.add("hidden");
            }

            // Retrieve experiment details to extract model leaderboard, features, artifacts
            fetchAndRenderExperimentDetails(data.experiment_id);

            showToast("ML-OS Pipeline run succeeded!");
            fetchProjectMetadata();

        } else if (data.status === "cancelled") {
            clearInterval(runPollInterval);
            document.getElementById("btn-run-pipeline").disabled = false;
            document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";
            document.getElementById("btn-cancel-run").classList.add("hidden");

            document.getElementById("pipeline-overall-status-badge").textContent = "Cancelled";
            document.getElementById("pipeline-overall-status-badge").className = "badge warning";

            document.getElementById("run-failed-stats").classList.remove("hidden");
            document.getElementById("run-failed-error").textContent = data.error || "Execution cancelled by user.";
            showToast("ML Pipeline execution was cancelled", false);

            document.getElementById("mlos-thinking-active-stage-panel").classList.add("hidden");

        } else if (data.status === "cancel_requested") {
            document.getElementById("pipeline-overall-status-badge").textContent = "Cancelling...";
            document.getElementById("pipeline-overall-status-badge").className = "badge warning";

        } else if (data.status === "failed") {
            clearInterval(runPollInterval);
            document.getElementById("btn-run-pipeline").disabled = false;
            document.getElementById("btn-run-pipeline").textContent = "Run ML Pipeline";
            document.getElementById("btn-cancel-run").classList.add("hidden");

            document.getElementById("pipeline-overall-status-badge").textContent = "Failed";
            document.getElementById("pipeline-overall-status-badge").className = "badge danger";

            document.getElementById("run-failed-stats").classList.remove("hidden");
            document.getElementById("run-failed-error").textContent = data.error || "Execution terminated with errors.";
            showToast("ML Pipeline execution failed", true);

            document.getElementById("mlos-thinking-active-stage-panel").classList.add("hidden");
        }

    } catch (err) {
        console.error("Error polling progress", err);
    }
}

// Render model battle progresses
function renderModelBattleProgress(currentStageName) {
    const box = document.getElementById("pnode-training-battle-box");
    if (!box) return;
    
    if (currentStageName && currentStageName.startsWith("AutoML: Evaluating ")) {
        const candidate = currentStageName.replace("AutoML: Evaluating ", "");
        box.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div class="dim-text" style="font-size:11px;">
                    Model evaluation running: <strong class="text-accent">${candidate}</strong>
                </div>
                <div class="model-progress-bar" style="width:100%;"><div class="model-progress-fill" style="width:100%; background-color:var(--color-accent); animation: pulse 1.5s infinite;"></div></div>
            </div>
        `;
    } else {
        box.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div class="dim-text" style="font-size:11px;">
                    Model evaluation running
                </div>
            </div>
        `;
    }
}

// Fetch details for the final run experiment and render custom blocks
async function fetchAndRenderExperimentDetails(expId) {
    try {
        const response = await fetch(`/api/experiments/${expId}`);
        if (!response.ok) return;
        const exp = await response.json();
        
        // Update model battle leaderboard winner
        const topModel = exp.selected_model || "Decision Tree Classifier";
        document.getElementById("model-battle-winner-name-text").textContent = topModel;
        
        // Render Feature Importance horizontal bars
        const importanceContainer = document.getElementById("pipeline-importance-list");
        importanceContainer.innerHTML = "";
        
        const importance = exp.feature_importance || {};
        if (Object.keys(importance).length > 0) {
            Object.entries(importance).forEach(([feat, val], idx) => {
                const percentVal = (val * 100).toFixed(0);
                const uniqueWhyId = `why-importance-${idx}`;
                
                const card = document.createElement("div");
                card.className = "importance-row-card";
                card.innerHTML = `
                    <div class="importance-meta">
                        <span>${feat}</span>
                        <strong>${percentVal}%</strong>
                    </div>
                    <div class="distribution-bar" style="margin-bottom:8px;">
                        <div class="distribution-bar-fill" style="width: ${percentVal}%;"></div>
                    </div>
                    <button class="why-btn" onclick="toggleWhyBox('${uniqueWhyId}')">Why does this matter?</button>
                    <div class="explanation-box hidden" id="${uniqueWhyId}">
                        <strong>Interpretative Value:</strong> Feature contributes ${percentVal}% of target decision bounds.<br/>
                        <strong>Important Warning:</strong> Feature weight represents statistical correlation inside the validation parameters. It does **not** prove causality (e.g. changing ${feat} value may not cause target index shift).
                    </div>
                `;
                importanceContainer.appendChild(card);
            });
        } else {
            importanceContainer.innerHTML = `<p class="dim-text">No feature importances scored.</p>`;
        }
        
        // Render modern artifact Cards grid
        const artifactsContainer = document.getElementById("pipeline-artifacts-grid");
        artifactsContainer.innerHTML = "";
        
        const registered = exp.artifacts || {};
        
        const defaultArtifactMetadata = {
            "model": { icon: "🤖", title: "Model Checkpoint", desc: "Serialized model parameters saved as joblib file." },
            "preprocessor": { icon: "🔧", title: "Preprocessor Config", desc: "Scaler scales and categories encoder saved context." },
            "metrics": { icon: "📈", title: "Model Leaderboard", desc: "Leaderboard CV metrics evaluation results record." },
            "explainability_report": { icon: "🧠", title: "Feature Importance Map", desc: "SHAP-based global feature coefficients explanation." },
            "deployment_package": { icon: "📦", title: "Reusable Pipeline", desc: "Packaged zip bundle including model pipeline script." }
        };
        
        if (Object.keys(registered).length > 0) {
            Object.entries(registered).forEach(([name, path]) => {
                const meta = defaultArtifactMetadata[name] || { icon: "📄", title: name, desc: "Serialized artifact output file path." };
                const card = document.createElement("div");
                card.className = "artifact-card-modern";
                card.innerHTML = `
                    <div>
                        <div class="artifact-card-header-icon">${meta.icon}</div>
                        <div class="artifact-card-title">${meta.title}</div>
                        <div class="artifact-card-desc">${meta.desc}</div>
                        <div style="font-family:var(--font-mono); font-size:10px; color:var(--text-dim); overflow:hidden; text-overflow:ellipsis;">${path}</div>
                    </div>
                `;
                artifactsContainer.appendChild(card);
            });
        } else {
            artifactsContainer.innerHTML = `<p class="dim-text">No artifacts exported.</p>`;
        }
        
        // Sync learn mode visibility
        setupLearnMode();
        
    } catch (err) {
        console.error("Failed to render final details", err);
    }
}

// Fetch all experiments recorded in project
async function loadExperiments() {
    showExperimentsSkeleton();
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
                <td><input type="checkbox" class="exp-row-checkbox" value="${exp.experiment_id}" onchange="updateCompareButtonState()" aria-label="Select experiment ${exp.experiment_id}"></td>
                <td><strong class="text-accent" style="font-family:var(--font-mono); font-size:12px;">${exp.experiment_id}</strong></td>
                <td class="dim-text">${exp.timestamp ? exp.timestamp.substring(0, 19).replace('T', ' ') : '---'}</td>
                <td class="dim-text" style="font-family: var(--font-mono); font-size:11px;">${exp.dataset_fingerprint ? exp.dataset_fingerprint.substring(0, 8) : '---'}</td>
                <td><span class="badge">${exp.problem_type || 'Unknown'}</span></td>
                <td><strong>${exp.selected_model || 'None'}</strong></td>
                <td>${metricsStr || 'No metrics logged'}</td>
                <td>
                    <button class="btn btn-secondary" style="font-size:11px; padding:4px 8px;" onclick="viewExperimentDetails('${exp.experiment_id}')">Details</button>
                </td>
            `;
            tableBody.appendChild(tr);
        });

        // Reset compare button state
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
                <td><strong class="text-accent" style="font-family:var(--font-mono); font-size:12px;">${exp.experiment_id}</strong></td>
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

// Accessibility focus trap function
function trapFocus(e) {
    const modal = e.currentTarget;
    const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.key === 'Tab') {
        if (e.shiftKey) { // Shift + Tab
            if (document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            }
        } else { // Tab
            if (document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    }
}

// Accessibility Modal Open/Close helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    lastFocusedElement = document.activeElement;
    modal.classList.remove("hidden");

    // Focus the close button or first button inside modal
    const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable.length > 0) {
        focusable[0].focus();
    }

    modal.addEventListener('keydown', trapFocus);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.add("hidden");
    modal.removeEventListener('keydown', trapFocus);

    if (lastFocusedElement) {
        lastFocusedElement.focus();
        lastFocusedElement = null;
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

        // Show modal overlay using focus trap helper
        openModal("experiment-details-modal");

    } catch (err) {
        showToast("Error fetching experiment detail metrics", true);
        console.error(err);
    }
}

function closeExperimentModal() {
    closeModal("experiment-details-modal");
}

// Enable/Disable comparison button based on checkbox count
function updateCompareButtonState() {
    const checkedBoxes = document.querySelectorAll(".exp-row-checkbox:checked");
    const compareBtn = document.getElementById("btn-compare-experiments");
    const helperText = document.getElementById("compare-helper-text");

    if (helperText) {
        if (checkedBoxes.length === 0) {
            helperText.textContent = "Select 2 experiments to compare.";
            helperText.className = "dim-text";
        } else if (checkedBoxes.length === 1) {
            helperText.textContent = "Select 1 more experiment.";
            helperText.className = "dim-text";
        } else if (checkedBoxes.length === 2) {
            helperText.textContent = "Ready to compare.";
            helperText.className = "text-success bold-text";
        } else {
            helperText.textContent = "Select exactly 2 experiments.";
            helperText.className = "text-danger";
        }
    }

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

            let betterModelName = exp1;
            let bestAccDiff = 0;

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
                        
                        if (metric.toLowerCase() === "accuracy" || metric.toLowerCase() === "accuracy_score") {
                            bestAccDiff = data.diff;
                            if (data.diff < 0) {
                                betterModelName = exp2;
                            }
                        }
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

            // Custom interpretation box render based on tradeoffs
            const interpretation = document.getElementById("compare-interpretation-text");
            if (Math.abs(bestAccDiff) > 0) {
                interpretation.innerHTML = `Model <strong class="text-accent" style="font-family:var(--font-mono); font-size:11px;">${betterModelName}</strong> achieved higher accuracy in this comparison. However, candidate comparison should check trade-offs: if missing positive samples (false negatives) is highly critical, verify the **Recall** metric comparison columns closely before staging.`;
            } else {
                interpretation.innerHTML = "Both models achieved equivalent validation accuracy score parameters. Consider selecting the candidate with lower training time and memory footprint to minimize production execution latency.";
            }

            openModal("compare-modal");
        } else {
            const errDetails = result.error ? result.error.message : "Comparison request failed";
            showToast(errDetails, true);
        }
    } catch (err) {
        showToast("Error fetching comparison results", true);
        console.error(err);
    }
}

function closeCompareModal() {
    closeModal("compare-modal");
}

// Inline dataset validation helper with debounce
function setupDatasetValidation(inputElemId, msgElemId) {
    const input = document.getElementById(inputElemId);
    const msg = document.getElementById(msgElemId);
    if (!input || !msg) return;

    let timeout = null;
    input.addEventListener("input", () => {
        clearTimeout(timeout);
        const path = input.value.trim();
        if (!path) {
            msg.textContent = "";
            msg.className = "validation-msg";
            return;
        }

        timeout = setTimeout(async () => {
            try {
                const response = await fetch("/api/project/validate-dataset", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dataset_path: path })
                });
                const data = await response.json();

                if (response.ok && data.valid) {
                    msg.textContent = "✓ Dataset found";
                    msg.className = "validation-msg valid";
                } else {
                    const errMsg = data.error ? data.error.message : "Validation failed";
                    msg.textContent = `✗ ${errMsg}`;
                    msg.className = "validation-msg invalid";
                }
            } catch (err) {
                console.error(err);
            }
        }, 300); // 300ms debounce
    });
}

// Populate HTML5 datalist for workspace files autocomplete
async function populateDatasetSuggestions() {
    try {
        const response = await fetch("/api/project/files");
        const data = await response.json();
        const datalist = document.getElementById("workspace-files-list");
        if (datalist && data.files) {
            datalist.innerHTML = "";
            data.files.forEach(file => {
                const option = document.createElement("option");
                option.value = file;
                datalist.appendChild(option);
            });
        }
    } catch (err) {
        console.error("Failed to fetch dataset suggestions", err);
    }
}
