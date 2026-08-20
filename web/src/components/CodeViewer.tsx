import * as React from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "./Button";

export interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
  className?: string;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  language = "python",
  title,
  className = "",
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  };

  const lines = code.trim().split("\n");

  return (
    <div className={`rounded border border-border bg-card/60 shadow-lg flex flex-col overflow-hidden text-left ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-secondary/30 px-4 py-2">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-muted-foreground">
            {language}
          </span>
          {title && (
            <span className="text-xs font-mono font-medium text-foreground truncate max-w-[250px]">
              ({title})
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 hover:bg-secondary"
          onClick={handleCopy}
          aria-label="Copy code snippet"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
        </Button>
      </div>

      {/* Code Area */}
      <div className="flex-1 overflow-auto p-4 font-mono text-[11px] leading-relaxed text-foreground select-text max-h-[350px]">
        <pre className="code-block-pre flex">
          {/* Line Numbers */}
          <div className="text-muted-foreground/40 text-right pr-4 border-r border-border/20 select-none mr-4 min-w-[20px]">
            {lines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          {/* Code lines */}
          <code className="flex-1 whitespace-pre">{code}</code>
        </pre>
      </div>
    </div>
  );
};
export default CodeViewer;
