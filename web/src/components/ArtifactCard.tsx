import * as React from "react";
import { Download, FileCode, HardDrive, Settings } from "lucide-react";
import { Card } from "./Card";
import { Button } from "./Button";

export interface ArtifactCardProps {
  name: string;
  type: "model" | "preprocessor" | "code" | "metrics" | string;
  path: string;
  size?: string;
  created?: string;
  onDownload?: () => void;
  onPreview?: () => void;
  className?: string;
}

export const ArtifactCard: React.FC<ArtifactCardProps> = ({
  name,
  type,
  path,
  size = "N/A",
  created = "N/A",
  onDownload,
  onPreview,
  className = "",
}) => {
  const icons = {
    model: <HardDrive className="h-4 w-4 text-primary" />,
    preprocessor: <Settings className="h-4 w-4 text-accent" />,
    code: <FileCode className="h-4 w-4 text-success" />,
    metrics: <FileCode className="h-4 w-4 text-warning" />,
  };

  const getIcon = () => {
    if (type in icons) return icons[type as keyof typeof icons];
    return <FileCode className="h-4 w-4 text-muted-foreground" />;
  };

  return (
    <Card className={`p-4 border border-border bg-card/30 hover:border-border/60 transition-all flex flex-col justify-between space-y-4 ${className}`}>
      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded bg-secondary/50 border border-border/20">
            {getIcon()}
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-xs font-semibold font-mono tracking-tight text-foreground truncate" title={name}>
              {name}
            </h4>
            <span className="text-[10px] text-muted-foreground capitalize font-mono">
              Type: {type}
            </span>
          </div>
        </div>

        {/* Path and details */}
        <div className="text-[11px] font-mono text-muted-foreground space-y-0.5 text-left truncate">
          <div className="truncate" title={path}>
            <span className="text-[10px] text-muted-foreground/60">Path:</span> {path}
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground/60">Size:</span> {size}
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground/60">Created:</span> {created}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2 pt-2 border-t border-border/10">
        {onPreview && (
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 text-[11px] h-8"
            onClick={onPreview}
          >
            Preview
          </Button>
        )}
        <Button
          variant="secondary"
          size="sm"
          className="flex-1 text-[11px] h-8"
          onClick={onDownload}
        >
          <Download className="h-3 w-3 mr-1" />
          Download
        </Button>
      </div>
    </Card>
  );
};
