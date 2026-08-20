import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Card } from "./Card";
import { Badge } from "./Badge";
import { Button } from "./Button";

export interface DecisionCardProps {
  title: string;
  strategy: string;
  confidence: number;
  reason: string;
  evidence?: string;
  className?: string;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({
  title,
  strategy,
  confidence,
  reason,
  evidence,
  className = "",
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <Card className={`p-4 border border-border bg-card/50 hover:bg-card hover:border-border/60 transition-all ${className}`}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold tracking-tight text-foreground">{title}</h4>
          <div className="flex items-center space-x-2">
            <Badge variant="secondary">{strategy}</Badge>
            <span className="text-xs text-muted-foreground font-mono">
              Confidence: {Math.round(confidence * 100)}%
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-2 flex items-center space-x-1"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="text-xs">Why?</span>
          {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </Button>
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-border/40 text-xs text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-top-1 duration-150">
          <p className="mb-2">
            <strong className="text-foreground">Rationalization:</strong> {reason}
          </p>
          {evidence && (
            <p>
              <strong className="text-foreground">Evidence:</strong> {evidence}
            </p>
          )}
        </div>
      )}
    </Card>
  );
};
