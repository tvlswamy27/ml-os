import * as React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "primary" | "secondary" | "destructive" | "success" | "warning" | "outline";
}

export const Badge = ({ className = "", variant = "primary", ...props }: BadgeProps) => {
  const baseStyles = "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium font-mono select-none transition-colors";
  
  const variants = {
    primary: "border-transparent bg-primary text-primary-foreground",
    secondary: "border-transparent bg-secondary text-secondary-foreground",
    destructive: "border-transparent bg-destructive text-destructive-foreground",
    success: "border-transparent bg-success/15 border-success/30 text-success",
    warning: "border-transparent bg-warning/15 border-warning/30 text-warning",
    outline: "text-foreground border-border",
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${className}`} {...props} />
  );
};
