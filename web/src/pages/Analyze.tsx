import * as React from "react";
import { Terminal } from "lucide-react";
import { useProjectStore } from "../store/projectStore";
import { useProjectDetails } from "../hooks/useProjects";
import { useAnalyzeProject } from "../hooks/useProjectAnalysis";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { DecisionCard } from "../components/DecisionCard";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";
import { useToast } from "../hooks";
import { ApiRequestError } from "../services/apiClient";
import type { Decision, Recommendation } from "../types";

export const Analyze: React.FC = () => {
  const { selectedProjectId } = useProjectStore();
  const { toast } = useToast();
  const { details, isLoading: detailsLoading } = useProjectDetails(selectedProjectId);
  const { analyzeMutation, analysisReport } = useAnalyzeProject(selectedProjectId);

  const [datasetPath, setDatasetPath] = React.useState("");
  const [targetColumn, setTargetColumn] = React.useState("");

  // Prepopulate inputs with existing dataset config if details are loaded
  React.useEffect(() => {
    if (details?.dataset) {
      const targetPath = details.dataset.path || "";
      const targetCol = details.dataset.target || "";
      const timer = setTimeout(() => {
        setDatasetPath((prev) => (prev !== targetPath ? targetPath : prev));
        setTargetColumn((prev) => (prev !== targetCol ? targetCol : prev));
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [details]);

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

  const handleAnalyze = async () => {
    if (!datasetPath) {
      toast("Please enter a valid dataset path", "error");
      return;
    }
    try {
      await analyzeMutation.mutateAsync({
        datasetPath,
        targetColumn: targetColumn || undefined,
      });
      toast("Dataset analysis and profiling completed", "success");
    } catch (err: any) {
      if (err instanceof ApiRequestError) {
        toast(err.message, "error");
      } else {
        toast(err.message || "Failed to analyze dataset", "error");
      }
    }
  };

  // Decisions and recommendations can come either from the fresh analysis response or the cached details
  const decisions = analysisReport?.decisions || details?.decisions || ([] as Decision[]);
  const recommendations = analysisReport?.recommendations || details?.recommendations || ([] as Recommendation[]);
  const datasetSummary = analysisReport?.dataset_summary || details?.dataset || null;

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="border-b border-border pb-4">
        <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
          Analyze Dataset
        </h1>
        <p className="text-xs text-muted-foreground">
          Profile your raw tables and formulate mathematical preprocessing strategies.
        </p>
      </div>

      {/* Input panel */}
      <Card className="bg-card/45">
        <CardContent className="p-5 flex flex-col md:flex-row items-end gap-4">
          <div className="flex-1 space-y-1.5">
            <label className="text-xs font-mono font-medium text-muted-foreground">Dataset File Path</label>
            <Input
              value={datasetPath}
              onChange={(e) => setDatasetPath(e.target.value)}
              placeholder="e.g. data/titanic.csv (relative to project path)"
              className="text-xs h-9 bg-background"
            />
          </div>
          <div className="w-full md:w-64 space-y-1.5">
            <label className="text-xs font-mono font-medium text-muted-foreground">Target Prediction Column</label>
            <Input
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              placeholder="e.g. Survived (Optional)"
              className="text-xs h-9 bg-background"
            />
          </div>
          <Button
            onClick={handleAnalyze}
            disabled={analyzeMutation.isPending || detailsLoading}
            className="w-full md:w-auto text-xs h-9 px-6 shrink-0"
          >
            {analyzeMutation.isPending ? "Analyzing..." : "Analyze Dataset"}
          </Button>
        </CardContent>
      </Card>

      {analyzeMutation.isPending && (
        <div className="flex flex-col items-center justify-center p-12 space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="text-xs font-mono text-muted-foreground">
            Parsing table structure and performing statistical profile scans...
          </span>
        </div>
      )}

      {!analyzeMutation.isPending && datasetSummary && (
        <div className="grid md:grid-cols-3 gap-6 animate-in fade-in duration-200">
          {/* Profiles and Distributions */}
          <div className="md:col-span-2 space-y-6">
            {/* Dataset Overview */}
            <Card>
              <CardHeader className="pb-3 border-b border-border/10">
                <CardTitle className="text-sm font-semibold tracking-tight text-foreground">Dataset Properties</CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-3 text-xs">
                <div className="flex justify-between border-b border-border/20 pb-1.5">
                  <span className="text-muted-foreground">Dataset File Path</span>
                  <span className="font-mono font-bold text-foreground truncate max-w-[200px]">
                    {datasetSummary.path}
                  </span>
                </div>
                <div className="flex justify-between border-b border-border/20 pb-1.5">
                  <span className="text-muted-foreground">Rows Count</span>
                  <span className="font-mono font-bold text-foreground">
                    {datasetSummary.rows}
                  </span>
                </div>
                <div className="flex justify-between border-b border-border/20 pb-1.5">
                  <span className="text-muted-foreground">Columns Count</span>
                  <span className="font-mono font-bold text-foreground">
                    {datasetSummary.columns}
                  </span>
                </div>
                {targetColumn && (
                  <div className="flex justify-between pb-1.5">
                    <span className="text-muted-foreground">Target Prediction Column</span>
                    <span className="font-mono font-bold text-primary">
                      {targetColumn}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Decisions List */}
            <div className="space-y-3">
              <h3 className="text-xs font-mono font-bold text-muted-foreground/60 uppercase tracking-wider block">
                Preprocessing Decisions formulated
              </h3>
              {decisions.length > 0 ? (
                <div className="grid sm:grid-cols-2 gap-4">
                  {decisions.map((dec, idx) => (
                    <DecisionCard key={idx} {...dec} />
                  ))}
                </div>
              ) : (
                <div className="p-4 border border-border rounded bg-card/25 text-xs text-muted-foreground text-center">
                  No automatic decisions formulated for the current dataset structure.
                </div>
              )}
            </div>
          </div>

          {/* Feature variables / Recommendations list card */}
          <div className="space-y-6">
            <Card className="bg-card/45 h-fit">
              <CardHeader className="pb-3 border-b border-border/10">
                <CardTitle className="text-sm font-semibold tracking-tight text-foreground">Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                {recommendations.length > 0 ? (
                  <div className="space-y-3">
                    {recommendations.map((rec, index) => (
                      <div key={index} className="p-3 border border-border rounded bg-background/50 text-left space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-foreground text-xs">{rec.title}</span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-primary/10 text-primary uppercase">
                            Priority: {rec.priority}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {rec.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground text-center py-4">
                    No intelligence recommendations reported.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
export default Analyze;
