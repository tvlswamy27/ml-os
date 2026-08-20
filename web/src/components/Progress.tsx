import * as React from "react";

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  indicatorClassName?: string;
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className = "", value, indicatorClassName = "", ...props }, ref) => {
    const clampedValue = Math.min(100, Math.max(0, value));
    return (
      <div
        ref={ref}
        className={`relative h-2 w-full overflow-hidden rounded bg-secondary border border-border/20 ${className}`}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
        {...props}
      >
        <div
          className={`h-full w-full flex-1 bg-primary transition-all duration-300 ${indicatorClassName}`}
          style={{ transform: `translateX(-${100 - clampedValue}%)` }}
        />
      </div>
    );
  }
);
Progress.displayName = "Progress";
