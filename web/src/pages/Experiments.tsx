import * as React from "react";
import { Scale } from "lucide-react";
import { Button } from "../components/Button";

export const Experiments: React.FC = () => {
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
        <div>
          <Button
            variant="primary"
            size="sm"
            disabled={true}
            className="text-xs"
          >
            <Scale className="h-4 w-4 mr-1.5" />
            Compare Selection (0/2)
          </Button>
        </div>
      </div>

      {/* Honest Empty State / Missing Backend Route Message */}
      <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4 border border-dashed border-border rounded-lg p-12 text-center bg-card/10 select-none animate-in fade-in duration-200">
        <div className="p-3 bg-secondary border border-border/80 rounded-full text-muted-foreground">
          <Scale className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            Experiment history is not available yet
          </h2>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            The FastAPI backend currently lacks a dedicated endpoint to query and retrieve historical runs from the underlying <code>ExperimentTracker</code>.
          </p>
          <span className="text-[10px] text-muted-foreground/50 font-mono block mt-2">
            Missing backend router: GET /api/projects/&#123;project_id&#125;/experiments
          </span>
        </div>
      </div>
    </div>
  );
};

export default Experiments;
