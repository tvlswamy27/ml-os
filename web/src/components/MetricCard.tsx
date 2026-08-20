import * as React from "react";
import { Card } from "./Card";

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string | number; // e.g. "+0.04" or "-0.01"
  status?: "neutral" | "positive" | "negative";
  description?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  status = "neutral",
  description,
  className = "",
}) => {
  const statusColors = {
    neutral: "text-muted-foreground",
    positive: "text-success",
    negative: "text-destructive",
  };

  const borderColors = {
    neutral: "border-border",
    positive: "border-success/30 bg-success/5",
    negative: "border-destructive/30 bg-destructive/5",
  };

  return (
    <Card className={`p-4 border-l-2 shadow-sm transition-all duration-150 ${change ? borderColors[status] : "border-border"} ${className}`}>
      <div className="flex flex-col space-y-1">
        <span className="text-[11px] font-mono text-muted-foreground tracking-tight uppercase">
          {title}
        </span>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-bold font-mono tracking-tight text-foreground">
            {value}
          </span>
          {change && (
            <span className={`text-xs font-mono font-medium ${statusColors[status]}`}>
              {change}
            </span>
          )}
        </div>
        {description && (
          <p className="text-[10px] text-muted-foreground leading-normal mt-1">
            {description}
          </p>
        )}
      </div>
    </Card>
  );
};
