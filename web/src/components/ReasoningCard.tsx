import * as React from "react";
import { HelpCircle, Terminal, Eye } from "lucide-react";
import { Card } from "./Card";
import { Button } from "./Button";

export interface ReasoningCardProps {
  decisionTitle: string;
  simpleExplanation: string;
  technicalExplanation: string;
  evidenceLink?: string;
  onViewEvidence?: () => void;
  className?: string;
}

export const ReasoningCard: React.FC<ReasoningCardProps> = ({
  decisionTitle,
  simpleExplanation,
  technicalExplanation,
  evidenceLink,
  onViewEvidence,
  className = "",
}) => {
  const [mode, setMode] = React.useState<"simple" | "technical">("simple");

  return (
    <Card className={`p-5 border border-border bg-card/40 flex flex-col space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border pb-3">
        <div>
          <span className="text-[10px] font-mono text-primary uppercase tracking-wider">
            ML Mentor Analysis
          </span>
          <h4 className="text-sm font-semibold tracking-tight text-foreground">
            {decisionTitle}
          </h4>
        </div>

        {/* Switch mode */}
        <div className="flex bg-secondary p-0.5 rounded border border-border/40">
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 px-3 text-[11px] rounded ${mode === "simple" ? "bg-card text-foreground" : "text-muted-foreground"}`}
            onClick={() => setMode("simple")}
          >
            <HelpCircle className="h-3.5 w-3.5 mr-1" />
            Explain Simply
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 px-3 text-[11px] rounded ${mode === "technical" ? "bg-card text-foreground" : "text-muted-foreground"}`}
            onClick={() => setMode("technical")}
          >
            <Terminal className="h-3.5 w-3.5 mr-1" />
            Technical
          </Button>
        </div>
      </div>

      {/* Explanation text body */}
      <div className="flex-1 text-xs text-muted-foreground leading-relaxed text-left min-h-[70px]">
        {mode === "simple" ? (
          <p className="animate-in fade-in duration-200">{simpleExplanation}</p>
        ) : (
          <p className="font-mono text-[11px] text-foreground bg-secondary/30 p-3 rounded border border-border/20 animate-in fade-in duration-200">
            {technicalExplanation}
          </p>
        )}
      </div>

      {/* Footer CTAs */}
      {(onViewEvidence || evidenceLink) && (
        <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border/40">
          <Button
            variant="ghost"
            size="sm"
            className="text-[11px] h-8 text-primary hover:text-primary hover:bg-primary/5"
            onClick={onViewEvidence}
          >
            <Eye className="h-3.5 w-3.5 mr-1" />
            View Evidence
          </Button>
        </div>
      )}
    </Card>
  );
};
