import * as React from "react";
import { Check, Loader2, AlertCircle, Circle } from "lucide-react";

export interface TimelineStep {
  id: string;
  title: string;
  status: "waiting" | "active" | "completed" | "failed";
  description?: string;
  time?: string;
}

export interface TimelineProps {
  steps: TimelineStep[];
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ steps, className = "" }) => {
  return (
    <div className={`relative pl-6 border-l border-border flex flex-col space-y-6 ${className}`}>
      {steps.map((step) => {
        const statusConfigs = {
          waiting: {
            icon: <Circle className="h-3.5 w-3.5 text-muted-foreground bg-background" />,
            border: "border-border",
            text: "text-muted-foreground",
          },
          active: {
            icon: <Loader2 className="h-4 w-4 text-primary bg-background animate-spin" />,
            border: "border-primary",
            text: "text-primary font-medium",
          },
          completed: {
            icon: <Check className="h-3.5 w-3.5 text-success bg-background" />,
            border: "border-success",
            text: "text-foreground",
          },
          failed: {
            icon: <AlertCircle className="h-3.5 w-3.5 text-destructive bg-background" />,
            border: "border-destructive",
            text: "text-destructive font-medium",
          },
        };

        const config = statusConfigs[step.status];

        return (
          <div key={step.id} className="relative flex flex-col items-start">
            {/* Step Icon */}
            <div className={`absolute -left-[35px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-background z-10`}>
              {config.icon}
            </div>

            {/* Content */}
            <div className="flex items-center space-x-2">
              <span className={`text-xs ${config.text}`}>{step.title}</span>
              {step.time && (
                <span className="text-[10px] text-muted-foreground font-mono">
                  ({step.time})
                </span>
              )}
            </div>
            {step.description && (
              <p className="text-[11px] text-muted-foreground mt-0.5 text-left leading-relaxed">
                {step.description}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
};
