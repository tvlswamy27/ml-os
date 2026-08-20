import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "./Button";

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children }) => {
  // Close on Escape key press
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Modal content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15 }}
            className="relative z-10 w-full max-w-lg rounded border border-border bg-card p-6 shadow-lg shadow-black/40 focus:outline-none"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
              <h2 id="modal-title" className="text-md font-semibold tracking-tight">
                {title}
              </h2>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={onClose}
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Content */}
            <div className="text-sm">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
