import * as React from "react";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./Card";

export interface ChartContainerProps {
  title: string;
  description?: string;
  isLoading?: boolean;
  isEmpty?: boolean;
  emptyText?: string;
  children: React.ReactNode;
  className?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  description,
  isLoading = false,
  isEmpty = false,
  emptyText = "No data available to plot.",
  children,
  className = "",
}) => {
  return (
    <Card className={`flex flex-col border border-border bg-card/40 ${className}`}>
      <CardHeader className="pb-3 border-b border-border/10">
        <CardTitle className="text-sm font-semibold tracking-tight text-foreground">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col justify-center items-center min-h-[220px] p-6 relative">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center space-y-2 text-muted-foreground animate-in fade-in">
            <Loader2 className="h-6 w-6 text-primary animate-spin" />
            <span className="text-xs font-mono">Computing dataset telemetry...</span>
          </div>
        ) : isEmpty ? (
          <div className="text-xs text-muted-foreground font-mono flex items-center justify-center h-full">
            {emptyText}
          </div>
        ) : (
          <div className="w-full h-full min-h-[180px] text-xs text-foreground animate-in fade-in duration-200">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
export default ChartContainer;
