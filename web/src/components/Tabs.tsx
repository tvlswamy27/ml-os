import * as React from "react";

export interface TabItem {
  id: string;
  label: string;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ items, activeId, onChange, className = "" }) => {
  return (
    <div className={`flex border-b border-border space-x-1 ${className}`} role="tablist">
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-all border-b-2 -mb-[2px] disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:text-primary ${
              isActive
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
};
