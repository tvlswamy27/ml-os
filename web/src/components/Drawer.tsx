import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "./Button";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Drawer: React.FC<DrawerProps> = ({ isOpen, onClose, title, children }) => {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Drawer Content */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="relative z-10 h-full w-full max-w-md border-l border-border bg-card p-6 shadow-lg shadow-black/40 flex flex-col focus:outline-none"
            role="dialog"
            aria-modal="true"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
              <h2 className="text-md font-semibold tracking-tight">{title}</h2>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={onClose}
                aria-label="Close panel"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto text-sm pr-1">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
