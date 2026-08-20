import * as React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", size = "md", children, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium rounded transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]";
    
    const variants = {
      primary: "bg-primary text-primary-foreground hover:bg-primary/95 shadow-sm shadow-primary/20",
      secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
      destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/95 shadow-sm",
      ghost: "hover:bg-secondary text-foreground hover:text-foreground",
      outline: "border border-border bg-transparent hover:bg-secondary text-foreground",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs",
      md: "h-9 px-4 text-sm",
      lg: "h-10 px-6 text-sm",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
