import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";

import { ToastContext } from "../hooks/useToast";
import type { ToastType } from "../hooks/useToast";

export interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = React.useState<ToastMessage[]>([]);

  const toast = React.useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto dismiss after 4s
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 w-full max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => {
            const icons = {
              success: <CheckCircle className="h-4 w-4 text-success" />,
              error: <AlertTriangle className="h-4 w-4 text-destructive" />,
              info: <Info className="h-4 w-4 text-primary" />,
            };

            const borderColors = {
              success: "border-success/30 bg-success/5",
              error: "border-destructive/30 bg-destructive/5",
              info: "border-primary/30 bg-primary/5",
            };

            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 50 }}
                transition={{ duration: 0.2 }}
                className={`flex items-start p-4 rounded border bg-card text-foreground shadow-lg pointer-events-auto border-border ${borderColors[t.type]}`}
                role="alert"
              >
                <div className="flex-shrink-0 mr-3 mt-0.5">{icons[t.type]}</div>
                <div className="flex-1 text-sm font-medium tracking-tight pr-4">
                  {t.message}
                </div>
                <button
                  onClick={() => removeToast(t.id)}
                  className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors ml-2"
                  aria-label="Dismiss toast"
                >
                  <X className="h-4 w-4" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};


