import * as React from "react";
import { AlertCircle, CheckCircle, Info, ShieldAlert } from "lucide-react";
import { Card } from "./Card";
import { Badge } from "./Badge";

export interface InsightCardProps {
  type: "risk" | "suggestion" | "success" | "info";
  title: string;
  whatHappened: string;
  whyMatters: string;
  recommendation: string;
  severity?: "low" | "medium" | "high";
  className?: string;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  type,
  title,
  whatHappened,
  whyMatters,
  recommendation,
  severity = "low",
  className = "",
}) => {
  const configs = {
    risk: {
      border: "border-l-destructive border-destructive/20",
      bg: "bg-destructive/5",
      icon: <ShieldAlert className="h-4 w-4 text-destructive" />,
      tag: "Risk Detected",
      tagVariant: "destructive" as const,
    },
    suggestion: {
      border: "border-l-warning border-warning/20",
      bg: "bg-warning/5",
      icon: <AlertCircle className="h-4 w-4 text-warning" />,
      tag: "Recommendation",
      tagVariant: "warning" as const,
    },
    success: {
      border: "border-l-success border-success/20",
      bg: "bg-success/5",
      icon: <CheckCircle className="h-4 w-4 text-success" />,
      tag: "Verified",
      tagVariant: "success" as const,
    },
    info: {
      border: "border-l-primary border-primary/20",
      bg: "bg-primary/5",
      icon: <Info className="h-4 w-4 text-primary" />,
      tag: "Telemetry",
      tagVariant: "primary" as const,
    },
  };

  const config = configs[type];

  return (
    <Card className={`p-5 border-l-4 shadow-sm bg-card/65 ${config.border} ${config.bg} ${className}`}>
      <div className="flex items-start justify-between border-b border-border/20 pb-3 mb-3">
        <div className="flex items-center space-x-2">
          {config.icon}
          <h4 className="text-sm font-semibold tracking-tight text-foreground">{title}</h4>
        </div>
        <div className="flex items-center space-x-1.5">
          {type === "risk" && (
            <Badge variant="destructive" className="capitalize text-[10px]">
              {severity} severity
            </Badge>
          )}
          <Badge variant={config.tagVariant} className="text-[10px]">
            {config.tag}
          </Badge>
        </div>
      </div>

      <div className="space-y-3 text-xs leading-relaxed text-left text-muted-foreground">
        <div>
          <span className="font-semibold text-foreground">Discovery: </span>
          {whatHappened}
        </div>
        <div>
          <span className="font-semibold text-foreground">Why It Matters: </span>
          {whyMatters}
        </div>
        <div className="bg-secondary/40 p-2.5 rounded border border-border/10 text-foreground">
          <span className="font-bold text-primary font-mono text-[10px] uppercase block mb-1">
            Recommendation
          </span>
          {recommendation}
        </div>
      </div>
    </Card>
  );
};
