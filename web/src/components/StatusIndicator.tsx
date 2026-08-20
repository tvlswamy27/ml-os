import * as React from "react";

export interface StatusIndicatorProps {
  status: "active" | "inactive" | "success" | "warning" | "error" | string;
  label?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  className = "",
}) => {
  const dotColors = {
    active: "bg-primary animate-pulse-cyan shadow-sm shadow-primary/40",
    inactive: "bg-muted-foreground/30",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-destructive",
  };

  const currentDot = dotColors[status as keyof typeof dotColors] || dotColors.inactive;

  return (
    <div className={`inline-flex items-center space-x-2 select-none ${className}`}>
      <span className={`h-2 w-2 rounded-full ${currentDot}`} />
      {label && (
        <span className="text-xs font-medium tracking-tight text-foreground">
          {label}
        </span>
      )}
    </div>
  );
};
