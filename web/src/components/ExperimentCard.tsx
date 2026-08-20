import * as React from "react";
import { Award, Calendar, Layers } from "lucide-react";
import { Card } from "./Card";
import { Badge } from "./Badge";
import { Button } from "./Button";
import type { Experiment } from "../types";

export interface ExperimentCardProps {
  experiment: Experiment;
  isSelected?: boolean;
  onSelect?: () => void;
  onViewDetails?: () => void;
  className?: string;
}

export const ExperimentCard: React.FC<ExperimentCardProps> = ({
  experiment,
  isSelected = false,
  onSelect,
  onViewDetails,
  className = "",
}) => {
  const metricsList = Object.entries(experiment.metrics || {}).slice(0, 3);
  
  return (
    <Card className={`p-5 border bg-card/45 hover:bg-card/90 transition-all ${isSelected ? "border-primary bg-primary/5 ring-1 ring-primary/30" : "border-border"} ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between border-b border-border/20 pb-3 mb-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs font-bold text-foreground">
              {experiment.experiment_id}
            </span>
            <Badge variant="secondary" className="text-[10px]">
              {experiment.problem_type || "ML Project"}
            </Badge>
          </div>
          <div className="flex items-center space-x-3 text-[10px] text-muted-foreground font-mono">
            <span className="flex items-center">
              <Calendar className="h-3 w-3 mr-1" />
              {experiment.timestamp ? experiment.timestamp.substring(0, 10) : "N/A"}
            </span>
            <span className="flex items-center">
              <Layers className="h-3 w-3 mr-1" />
              Dataset: {experiment.dataset_fingerprint ? experiment.dataset_fingerprint.substring(0, 8) : "N/A"}
            </span>
          </div>
        </div>

        {onSelect && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            className="h-4 w-4 rounded border-border bg-secondary text-primary focus:ring-primary focus:ring-offset-background"
            aria-label={`Select experiment ${experiment.experiment_id} for comparison`}
          />
        )}
      </div>

      {/* Model Selected */}
      <div className="flex items-center space-x-2 mb-4 bg-secondary/35 p-2 rounded border border-border/10">
        <Award className="h-4 w-4 text-primary" />
        <span className="text-xs font-semibold text-foreground truncate">
          Winner: {experiment.selected_model || "N/A"}
        </span>
      </div>

      {/* Metrics List */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {metricsList.map(([metric, value]) => (
          <div key={metric} className="p-2 rounded bg-secondary/25 border border-border/15 text-center">
            <span className="text-[9px] font-mono text-muted-foreground uppercase block truncate">
              {metric.replace("_", " ")}
            </span>
            <span className="text-xs font-bold font-mono text-foreground">
              {typeof value === "number" ? value.toFixed(4) : value}
            </span>
          </div>
        ))}
        {metricsList.length === 0 && (
          <span className="text-[10px] text-muted-foreground col-span-3">
            No metrics logged for this run.
          </span>
        )}
      </div>

      {/* Actions */}
      {onViewDetails && (
        <div className="flex justify-end pt-2 border-t border-border/10">
          <Button variant="outline" size="sm" className="text-[11px] h-8 w-full" onClick={onViewDetails}>
            View Run Telemetry
          </Button>
        </div>
      )}
    </Card>
  );
};
