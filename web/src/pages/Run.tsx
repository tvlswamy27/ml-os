import * as React from "react";
import { Play, Square, Terminal } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useProjectStore } from "../store/projectStore";
import { useProjectDetails, useRun, useToast, useProjectArtifacts } from "../hooks";
import { eventService } from "../services/eventService";
import { Timeline } from "../components/Timeline";
import type { TimelineStep } from "../components/Timeline";
import { Button } from "../components/Button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";
import { ArtifactCard } from "../components/ArtifactCard";
import { ApiRequestError } from "../services/apiClient";

export const Run: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { selectedProjectId } = useProjectStore();
  const { details } = useProjectDetails(selectedProjectId);

  const [runId, setRunId] = React.useState<string | null>(null);
  const [currentStage, setCurrentStage] = React.useState<string | null>(null);
  const [completedStages, setCompletedStages] = React.useState<string[]>([]);
  const [failedStage, setFailedStage] = React.useState<string | null>(null);
  const [runStatus, setRunStatus] = React.useState<'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'cancel_requested'>('idle');

  const { startRunMutation, cancelRunMutation, runStatus: realRunStatus } = useRun(selectedProjectId, runId);
  const { artifacts, isLoading: artifactsLoading, downloadArtifactMutation } = useProjectArtifacts(selectedProjectId);

  // SSE subscription
  React.useEffect(() => {
    if (!runId || !selectedProjectId) return;

    const unsubscribe = eventService.subscribeToRunEvents(
      selectedProjectId,
      runId,
      (event) => {
        if (event.run_id !== runId) return;

        if (event.event_type === "ExecutionStarted") {
          setRunStatus("running");
        } else if (event.event_type === "StageStarted") {
          setCurrentStage(event.stage);
          setRunStatus("running");
        } else if (event.event_type === "StageCompleted") {
          setCompletedStages((prev) => [...new Set([...prev, event.stage])]);
          if (currentStage === event.stage) {
            setCurrentStage(null);
          }
        } else if (event.event_type === "ExecutionCompleted") {
          setRunStatus("completed");
          setCurrentStage(null);
          queryClient.invalidateQueries({ queryKey: ["projectDetails", selectedProjectId] });
          queryClient.invalidateQueries({ queryKey: ["runStatus", selectedProjectId, runId] });
        } else if (event.event_type === "ExecutionFailed") {
          const isCancelled = event.payload?.status === "CANCELLED" || event.payload?.error?.includes("cancelled");
          setRunStatus(isCancelled ? "cancelled" : "failed");
          setCurrentStage(null);
          queryClient.invalidateQueries({ queryKey: ["projectDetails", selectedProjectId] });
          queryClient.invalidateQueries({ queryKey: ["runStatus", selectedProjectId, runId] });
        }
      },
      (errorMsg) => {
        toast(errorMsg, "error");
      }
    );

    return () => {
      unsubscribe();
    };
  }, [runId, selectedProjectId, queryClient, currentStage, toast]);

  // Synchronize state from API query in case of reconnects / polling fallback
  React.useEffect(() => {
    if (realRunStatus) {
      const targetStatus = realRunStatus.status;
      const targetCompleted = realRunStatus.completed_stages || [];
      const targetFailed = realRunStatus.failed_stage || null;
      const timer = setTimeout(() => {
        if (targetStatus) {
          setRunStatus((prev) => (prev !== targetStatus ? (targetStatus as any) : prev));
        }
        setCompletedStages((prev) =>
          JSON.stringify(prev) !== JSON.stringify(targetCompleted) ? targetCompleted : prev
        );
        setFailedStage((prev) => (prev !== targetFailed ? targetFailed : prev));
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [realRunStatus]);

  if (!selectedProjectId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 border border-dashed border-border rounded-lg p-12 text-center bg-card/10 select-none">
        <div className="p-3 bg-primary/10 border border-primary/20 rounded-full text-primary">
          <Terminal className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            No Project Selected
          </h2>
          <p className="text-xs text-muted-foreground max-w-xs">
            Please use the project switcher at the top left of the sidebar to select or create a project workspace first.
          </p>
        </div>
      </div>
    );
  }

  const handleStartRun = async () => {
    if (!details?.dataset?.path) {
      toast("Please configure and analyze a dataset first.", "error");
      return;
    }

    setCompletedStages([]);
    setFailedStage(null);
    setCurrentStage(null);
    setRunStatus("queued");

    try {
      const resp = await startRunMutation.mutateAsync({
        datasetPath: details.dataset.path,
        targetColumn: details.dataset.target || undefined,
      });
      setRunId(resp.run_id);
      toast("AutoML pipeline execution started", "info");
    } catch (err: any) {
      setRunStatus("idle");
      if (err instanceof ApiRequestError) {
        toast(err.message, "error");
      } else {
        toast(err.message || "Failed to start pipeline run", "error");
      }
    }
  };

  const handleCancelRun = async () => {
    if (!runId) return;
    try {
      setRunStatus("cancel_requested");
      await cancelRunMutation.mutateAsync();
      toast("Cancellation request dispatched", "info");
    } catch (err: any) {
      if (err instanceof ApiRequestError) {
        toast(err.message, "error");
      } else {
        toast(err.message || "Failed to cancel run", "error");
      }
    }
  };

  const getStageStatus = (stageId: string): "completed" | "active" | "waiting" | "failed" => {
    if (failedStage === stageId) return "failed";
    if (completedStages.includes(stageId)) return "completed";
    if (currentStage === stageId) return "active";
    return "waiting";
  };

  const steps: TimelineStep[] = [
    { id: "Analysis", title: "Dataset Analysis", status: getStageStatus("Analysis"), description: "Parsing dataset columns, missingness, and types." },
    { id: "Intelligence", title: "Intelligence Diagnostics", status: getStageStatus("Intelligence"), description: "Formulating baseline estimators and profiling risks." },
    { id: "AutoML Search", title: "AutoML HPO Search", status: getStageStatus("AutoML Search"), description: "Evaluating classifier candidates and cross-validation bounds." },
    { id: "Decision", title: "Preprocessing Decisions", status: getStageStatus("Decision"), description: "Structuring target constraints and split ratios." },
    { id: "Generation", title: "Code Block Generation", status: getStageStatus("Generation"), description: "Formulating code templates for preprocessing pipelines." },
    { id: "Assembly", title: "Pipeline Code Assembly", status: getStageStatus("Assembly"), description: "Assembling pipeline.py source module." },
    { id: "Execution", title: "Subprocess Execution", status: getStageStatus("Execution"), description: "Fitting preprocessor pipelines and model parameters." },
    { id: "Evaluation", title: "Model Evaluation", status: getStageStatus("Evaluation"), description: "Running validation test suites on fitted models." },
    { id: "Experiment Tracking", title: "Lineage Archiving", status: getStageStatus("Experiment Tracking"), description: "Archiving run records and model artifacts." }
  ];

  const isRunning = ["queued", "running", "cancel_requested"].includes(runStatus);

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
            Run Pipeline
          </h1>
          <p className="text-xs text-muted-foreground">
            Execute the stage-based pipeline, watch execution progress in real-time, and view output logs.
          </p>
        </div>
        <div>
          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancelRun}
              className="text-xs"
              disabled={runStatus === "cancel_requested"}
            >
              <Square className="h-4 w-4 mr-1.5" />
              {runStatus === "cancel_requested" ? "Cancelling..." : "Cancel Run"}
            </Button>
          ) : (
            <Button variant="primary" size="sm" onClick={handleStartRun} className="text-xs">
              <Play className="h-4 w-4 mr-1.5" />
              Run ML Pipeline
            </Button>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Left: Execution timeline */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-border/10">
              <CardTitle className="text-sm font-semibold tracking-tight text-foreground">
                Pipeline Execution Timeline {runId ? `(${runId.slice(0, 8)})` : ""}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <Timeline steps={steps} />
            </CardContent>
          </Card>

          {/* Generated Artifacts */}
          {runStatus === "completed" && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-sm font-semibold tracking-tight text-foreground">Generated Artifacts</h3>
              {artifactsLoading ? (
                <div className="text-xs text-muted-foreground p-4 border border-border rounded bg-card/45 text-center">Loading artifacts...</div>
              ) : artifacts && artifacts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {artifacts.map((artifact) => (
                    <ArtifactCard
                      key={artifact.relative_path}
                      name={artifact.name}
                      type={artifact.artifact_type}
                      path={artifact.relative_path}
                      size={`${(artifact.size_bytes / 1024).toFixed(1)} KB`}
                      created={new Date(artifact.modified_at).toLocaleString()}
                      onDownload={() => {
                        toast(`Downloading ${artifact.name}...`, "info");
                        downloadArtifactMutation.mutate(
                          { path: artifact.relative_path, name: artifact.name },
                          {
                            onError: (err: any) => toast(err.message || "Download failed", "error")
                          }
                        );
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground p-4 border border-border rounded bg-card/45 text-center">No artifacts have been generated for this run yet.</div>
              )}
            </div>
          )}
        </div>

        {/* Right: Cognitive Panel & Metrics */}
        <div className="space-y-6">
          {/* Active Status Header */}
          <Card className="bg-card/45">
            <CardHeader className="pb-3 border-b border-border/10">
              <CardTitle className="text-xs font-mono font-bold text-muted-foreground uppercase">
                Execution Status
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current State:</span>
                <span className="font-mono font-bold capitalize text-primary">
                  {runStatus === "idle" ? "Ready" : runStatus.replace("_", " ")}
                </span>
              </div>
              {realRunStatus?.execution_time_s && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration:</span>
                  <span className="font-mono font-bold">
                    {realRunStatus.execution_time_s.toFixed(2)}s
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Metrics card (shown when complete) */}
          {runStatus === "completed" && realRunStatus?.metrics && (
            <div className="space-y-3 animate-in fade-in duration-200">
              <h3 className="text-xs font-mono font-bold text-muted-foreground/60 uppercase tracking-wider block">
                Fitted Run Metrics
              </h3>
              <Card className="p-4 space-y-2 text-xs">
                {Object.entries(realRunStatus.metrics).map(([metricName, metricVal]) => (
                  <div key={metricName} className="flex justify-between">
                    <span className="text-muted-foreground capitalize">{metricName.replace("_", " ")}:</span>
                    <span className="font-mono font-bold text-foreground">
                      {typeof metricVal === "number" ? metricVal.toFixed(4) : String(metricVal)}
                    </span>
                  </div>
                ))}
              </Card>
            </div>
          )}

          {/* Errors card (shown when failed) */}
          {runStatus === "failed" && (realRunStatus?.error || startRunMutation.error) && (
            <div className="space-y-3 animate-in fade-in duration-200">
              <h3 className="text-xs font-mono font-bold text-destructive/80 uppercase tracking-wider block">
                Execution Failure Log
              </h3>
              <Card className="p-4 border-destructive/20 bg-destructive/5 text-xs text-destructive leading-relaxed font-mono">
                {realRunStatus?.error || startRunMutation.error?.message}
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Run;
