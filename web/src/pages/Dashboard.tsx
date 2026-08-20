import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Terminal, BarChart2 } from "lucide-react";
import { useProjectStore } from "../store/projectStore";
import { useProjectDetails } from "../hooks/useProjects";
import { MetricCard } from "../components/MetricCard";
import { InsightCard } from "../components/InsightCard";
import { Button } from "../components/Button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectedProjectId, learnMode } = useProjectStore();
  const { details, isLoading, isError, error } = useProjectDetails(selectedProjectId);

  if (!selectedProjectId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 border border-dashed border-border rounded-lg p-12 text-center bg-card/10 select-none">
        <div className="p-3 bg-primary/10 border border-primary/20 rounded-full text-primary">
          <Terminal className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            Create your first ML project
          </h2>
          <p className="text-xs text-muted-foreground max-w-xs">
            Please use the project switcher at the top left of the sidebar to select or create a project workspace.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6 text-left animate-pulse">
        <div className="h-10 bg-secondary rounded w-1/3" />
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-secondary rounded" />
          ))}
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 h-64 bg-secondary rounded" />
          <div className="h-64 bg-secondary rounded" />
        </div>
      </div>
    );
  }

  if (isError || !details) {
    return (
      <div className="border border-destructive/20 bg-destructive/5 p-4 rounded text-xs text-left leading-relaxed text-destructive select-none">
        <span className="font-bold font-mono text-[10px] uppercase block mb-1">
          ❌ Server Connection Lost
        </span>
        {error?.message || "Failed to retrieve project details from the FastAPI server."}
      </div>
    );
  }

  const f1Metric = details.metrics?.f1_score !== undefined ? details.metrics.f1_score.toFixed(4) : "Unavailable";
  const accuracyMetric = details.metrics?.accuracy !== undefined ? details.metrics.accuracy.toFixed(4) : "Unavailable";
  const targetCol = details.dataset?.target || "Not Configured";
  const problemType = details.dataset?.problem_type || "Not Configured";
  const totalFeatures = details.dataset?.columns ? `${details.dataset.columns} columns` : "Not Configured";

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
            Engineering Dashboard — {details.project_name}
          </h1>
          <p className="text-xs text-muted-foreground">
            Overview of the current ML-OS active project workspace.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => navigate("/workspace/analyze")}
          >
            <BarChart2 className="h-4 w-4 mr-1.5" />
            Analyze Dataset
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="text-xs"
            onClick={() => navigate("/workspace/run")}
          >
            <Terminal className="h-4 w-4 mr-1.5" />
            Run ML Pipeline
          </Button>
        </div>
      </div>

      {/* Learn Mode Banner */}
      {learnMode && (
        <div className="bg-primary/5 border border-primary/20 p-4 rounded text-xs leading-relaxed text-muted-foreground animate-in fade-in duration-200">
          <span className="font-bold text-primary font-mono text-[10px] uppercase block mb-1">
            💡 Engineering Guide
          </span>
          ML-OS guides your ML project transparently. First, configure your raw files in the <strong>Analyze Dataset</strong> tab to scan feature types, targets, and risks. Next, inspect recommendations in the <strong>Decision Engine</strong>, run the model pipeline under <strong>Run Pipeline</strong>, and compare execution records inside the <strong>Experiments</strong> logs.
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Validation Accuracy"
          value={accuracyMetric}
          description="Last model execution"
        />
        <MetricCard
          title="Validation F1 Score"
          value={f1Metric}
          description="Primary target optimizer metric"
        />
        <MetricCard
          title="Active Target Column"
          value={targetCol}
          description={`Task: ${problemType}`}
        />
        <MetricCard
          title="Total Features"
          value={totalFeatures}
          description={details.dataset?.path ? `Source: ${details.dataset.path.split(/[\\/]/).pop()}` : "No dataset loaded"}
        />
      </div>

      {/* Main Grid Section */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Left Side: Recent Runs & Summary */}
        <div className="md:col-span-2 space-y-6">
          {/* Recent Runs Table */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/10">
              <CardTitle className="text-sm font-semibold tracking-tight text-foreground">Recent Experiments</CardTitle>
            </CardHeader>
            <CardContent className="p-6 text-center text-xs text-muted-foreground select-none">
              <p>Experiment history is not available yet.</p>
              <p className="text-[10px] text-muted-foreground/60 font-mono mt-1">
                Note: Missing "/api/experiments" endpoint on the backend.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Risks & Active Profile */}
        <div className="space-y-6">
          {details.profile?.risks && details.profile.risks.length > 0 ? (
            details.profile.risks.map((risk, index) => (
              <InsightCard
                key={index}
                type="risk"
                severity="high"
                title="System Diagnostic Warning"
                whatHappened={risk}
                whyMatters="This condition could introduce statistical bias or computational instability during model fitting."
                recommendation="Review baseline parameters or apply intermediate dataset imputations."
              />
            ))
          ) : (
            <div className="p-4 border border-border rounded bg-card/20 text-xs text-muted-foreground text-center">
              No active diagnostics or risks reported.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
