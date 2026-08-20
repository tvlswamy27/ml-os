import * as React from "react";
import {
  Scale,
  Beaker,
  Clock,
  Cpu,
  Database,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  LayoutGrid,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { useProjectStore } from "../store/projectStore";
import { useProjectExperiments } from "../hooks/useProjects";
import { Badge } from "../components/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../components/Table";
import { Tabs } from "../components/Tabs";

export const Experiments: React.FC = () => {
  const { selectedProjectId } = useProjectStore();
  const { experiments, isLoading, isError, error } = useProjectExperiments(
    selectedProjectId
  );

  const [activeTab, setActiveTab] = React.useState<string>("leaderboard");
  const [selectedExpId, setSelectedExpId] = React.useState<string | null>(null);

  // Automatically select the latest experiment when list loads
  React.useEffect(() => {
    if (experiments && experiments.length > 0 && !selectedExpId) {
      // Sort by timestamp descending to find latest
      const sorted = [...experiments].sort((a, b) => {
        const tA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const tB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return tB - tA;
      });
      setSelectedExpId(sorted[0].experiment_id);
    }
  }, [experiments, selectedExpId]);

  if (!selectedProjectId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 border border-dashed border-border rounded-lg p-12 text-center bg-card/10 select-none">
        <div className="p-3 bg-primary/10 border border-primary/20 rounded-full text-primary animate-pulse">
          <Beaker className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-foreground font-sans">
            No Project Selected
          </h2>
          <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
            Please use the project switcher at the top left of the sidebar to select or create a project workspace first.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-xs text-muted-foreground font-mono">
          Loading historical experiments...
        </p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 border border-destructive/20 rounded-lg p-12 text-center bg-destructive/5">
        <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-full text-destructive">
          <AlertCircle className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-destructive">
            Failed to Load Experiments
          </h2>
          <p className="text-xs text-muted-foreground max-w-xs">
            {error?.message || "An unexpected error occurred while fetching experiment runs."}
          </p>
        </div>
      </div>
    );
  }

  if (!experiments || experiments.length === 0) {
    return (
      <div className="space-y-6 text-left">
        {/* Header */}
        <div className="border-b border-border pb-4 select-none">
          <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
            Experiments Tracker
          </h1>
          <p className="text-xs text-muted-foreground">
            Audit historically serialized logs and compare metric variance.
          </p>
        </div>

        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4 border border-dashed border-border rounded-lg p-12 text-center bg-card/10 select-none">
          <div className="p-3 bg-secondary border border-border/80 rounded-full text-muted-foreground">
            <Scale className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-sm font-semibold tracking-tight text-foreground">
              No experiments found
            </h2>
            <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
              No historical search run exists for this project yet. Go to the **Run Pipeline** tab to execute your first AutoML workflow!
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Find currently selected experiment details
  const activeExp = experiments.find((e) => e.experiment_id === selectedExpId) || experiments[0];

  // Helper to format date nicely
  const formatDate = (isoString?: string) => {
    if (!isoString) return "Unknown Date";
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // Prepare trials list, sorted by rank ascending (rank 1 is best)
  const trials = [...(activeExp.candidate_trials || [])].sort((a, b) => a.rank - b.rank);

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4 select-none">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
            Experiments Tracker
          </h1>
          <p className="text-xs text-muted-foreground">
            Audit historically serialized logs and compare metric variance.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-muted-foreground font-sans font-medium whitespace-nowrap">
            Selected Experiment:
          </span>
          <select
            value={selectedExpId || ""}
            onChange={(e) => setSelectedExpId(e.target.value)}
            className="flex h-9 rounded border border-border bg-card px-3 py-1 pr-8 text-xs shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary font-mono"
          >
            {experiments.map((exp) => (
              <option key={exp.experiment_id} value={exp.experiment_id}>
                {exp.experiment_id} ({formatDate(exp.timestamp)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Experiment Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Core Stats Card */}
        <Card className="md:col-span-3 bg-card/45 backdrop-blur-sm border-border/80">
          <CardHeader className="pb-2 border-b border-border/60">
            <CardTitle className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-1.5">
              <LayoutGrid className="h-4 w-4 text-primary" />
              Experiment Execution Details — {activeExp.experiment_id}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider block">
                Selected Model
              </span>
              <span className="text-xs font-semibold text-foreground block truncate">
                {activeExp.selected_model || "None"}
              </span>
              <Badge variant="success" className="text-[9px] mt-0.5 px-1 py-0 select-none">
                Active Winner
              </Badge>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider block">
                Problem Type
              </span>
              <span className="text-xs font-medium text-foreground block">
                {activeExp.problem_type || "Classification"}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider block">
                Timestamp
              </span>
              <span className="text-xs font-medium text-foreground block font-mono">
                {formatDate(activeExp.timestamp)}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider block">
                Dataset Fingerprint
              </span>
              <span
                className="text-xs font-medium text-foreground block font-mono truncate"
                title={activeExp.dataset_fingerprint}
              >
                {activeExp.dataset_fingerprint || "N/A"}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Runtime Performance Summary */}
        <Card className="bg-card/45 backdrop-blur-sm border-border/80">
          <CardHeader className="pb-2 border-b border-border/60">
            <CardTitle className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-success" />
              Resource Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" /> Training Time
              </span>
              <span className="font-semibold text-foreground font-mono">
                {activeExp.training_time_s ? `${activeExp.training_time_s.toFixed(2)}s` : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1">
                <Cpu className="h-3 w-3" /> Memory Peak
              </span>
              <span className="font-semibold text-foreground font-mono">
                {activeExp.memory_usage_mb ? `${activeExp.memory_usage_mb.toFixed(1)} MB` : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1">
                <Database className="h-3 w-3" /> Total Candidates
              </span>
              <span className="font-semibold text-foreground font-mono">
                {trials.length || activeExp.candidate_models?.length || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs
        activeId={activeTab}
        onChange={setActiveTab}
        items={[
          { id: "leaderboard", label: "Model Leaderboard" },
          { id: "history", label: "Run History Comparison" },
        ]}
      />

      {/* Tab Panels */}
      {activeTab === "leaderboard" && (
        <Card className="bg-card/40 backdrop-blur-sm border-border/80">
          <CardContent className="p-0">
            {trials.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-xs select-none">
                No detailed trial telemetry registered for this experiment. Only summary model information is available.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Rank</TableHead>
                    <TableHead>Model Identity & Class</TableHead>
                    <TableHead>Metric</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>CV Mean & Spread</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Parameters</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trials.map((trial) => {
                    const isWinner = trial.selected;
                    const isFailed = trial.status === "FAILED";

                    return (
                      <TableRow
                        key={trial.trial_id}
                        className={isWinner ? "bg-primary/5 hover:bg-primary/8" : ""}
                      >
                        <TableCell className="font-bold text-foreground">
                          {isWinner ? (
                            <Badge variant="success" className="px-1.5 py-0.5 select-none font-bold">
                              🏆 #{trial.rank}
                            </Badge>
                          ) : (
                            <span className="pl-2 font-mono text-muted-foreground text-xs">
                              #{trial.rank}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col space-y-0.5">
                            <span className="font-semibold text-foreground text-xs flex items-center gap-1">
                              {trial.model_name}
                              {isWinner && (
                                <Badge variant="primary" className="text-[9px] px-1 py-0">
                                  Selected
                                </Badge>
                              )}
                            </span>
                            <span className="text-[10px] text-muted-foreground font-mono block max-w-[280px] truncate" title={trial.estimator_class}>
                              {trial.estimator_class}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-muted-foreground uppercase text-[10px]">
                          {trial.metric}
                        </TableCell>
                        <TableCell className="font-bold text-foreground font-mono text-xs">
                          {trial.score.toFixed(4)}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col space-y-0.5">
                            <span className="font-semibold text-foreground font-mono text-xs">
                              {trial.cv_mean.toFixed(4)}
                            </span>
                            {trial.cv_std !== undefined && (
                              <span className="text-[10px] text-muted-foreground font-mono">
                                ±{trial.cv_std.toFixed(4)}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-muted-foreground text-xs">
                          {trial.duration_seconds ? `${trial.duration_seconds.toFixed(2)}s` : "0.00s"}
                        </TableCell>
                        <TableCell>
                          {isFailed ? (
                            <div className="flex items-center gap-1 text-destructive font-semibold">
                              <XCircle className="h-3.5 w-3.5" />
                              <span className="text-[10px]">FAILED</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1 text-success">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span className="text-[10px]">SUCCESS</span>
                            </div>
                          )}
                        </TableCell>
                        <TableCell>
                          {isFailed ? (
                            <span className="text-destructive font-mono text-[10px] leading-tight block max-w-[200px] break-words">
                              {trial.error || "Unknown candidate evaluation error."}
                            </span>
                          ) : (
                            <div className="flex flex-wrap gap-1 max-w-[300px]">
                              {Object.entries(trial.parameters || {}).map(([key, val]) => (
                                <span
                                  key={key}
                                  className="inline-block px-1 py-0.5 rounded bg-secondary/80 border border-border text-[9px] font-mono text-muted-foreground select-all"
                                  title={`${key}: ${JSON.stringify(val)}`}
                                >
                                  {key}={typeof val === "object" ? JSON.stringify(val) : String(val)}
                                </span>
                              ))}
                              {Object.keys(trial.parameters || {}).length === 0 && (
                                <span className="text-[10px] text-muted-foreground italic">None</span>
                              )}
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "history" && (
        <Card className="bg-card/40 backdrop-blur-sm border-border/80">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Experiment ID</TableHead>
                  <TableHead>Executed At</TableHead>
                  <TableHead>Selected Winner Model</TableHead>
                  <TableHead>Problem Type</TableHead>
                  <TableHead>Metrics Summary</TableHead>
                  <TableHead className="w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...experiments]
                  .sort((a, b) => {
                    const tA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
                    const tB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
                    return tB - tA;
                  })
                  .map((exp) => {
                    const isSelected = exp.experiment_id === selectedExpId;

                    return (
                      <TableRow
                        key={exp.experiment_id}
                        className={
                          isSelected
                            ? "bg-secondary/40 hover:bg-secondary/50"
                            : "cursor-pointer"
                        }
                        onClick={() => setSelectedExpId(exp.experiment_id)}
                      >
                        <TableCell className="font-bold text-foreground font-mono">
                          {exp.experiment_id}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {formatDate(exp.timestamp)}
                        </TableCell>
                        <TableCell className="font-semibold text-foreground">
                          {exp.selected_model || "None"}
                        </TableCell>
                        <TableCell className="text-xs font-medium text-foreground">
                          {exp.problem_type || "Classification"}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(exp.metrics || {}).map(([metricKey, metricValue]) => (
                              <span
                                key={metricKey}
                                className="inline-flex items-center px-1.5 py-0.5 rounded bg-primary/10 border border-primary/20 text-[10px] font-mono text-primary select-all"
                              >
                                {metricKey}:{" "}
                                {typeof metricValue === "number"
                                  ? metricValue.toFixed(4)
                                  : String(metricValue)}
                              </span>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedExpId(exp.experiment_id);
                              setActiveTab("leaderboard");
                            }}
                            className="inline-flex items-center text-xs text-primary hover:text-primary/80 font-sans font-semibold cursor-pointer group"
                          >
                            View Leaderboard
                            <ChevronRight className="h-3 w-3 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                          </button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Experiments;

