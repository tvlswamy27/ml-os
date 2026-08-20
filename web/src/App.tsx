import * as React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ToastProvider } from "./components/Toast";
import { MarketingShell } from "./layouts/MarketingShell";
import { AppShell } from "./layouts/AppShell";
import { AuthGuard } from "./components/AuthGuard";

// Page Views
import { Home } from "./pages/Home";
import { Features } from "./pages/Features";
import { HowItWorks } from "./pages/HowItWorks";
import { Docs } from "./pages/Docs";
import { Pricing } from "./pages/Pricing";
import { About } from "./pages/About";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { ForgotPassword } from "./pages/ForgotPassword";
import { Dashboard } from "./pages/Dashboard";
import { Analyze } from "./pages/Analyze";
import { Run } from "./pages/Run";
import { Experiments } from "./pages/Experiments";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
        <Routes>
          {/* Public / Marketing Routes */}
          <Route
            path="/"
            element={
              <MarketingShell>
                <Home />
              </MarketingShell>
            }
          />
          <Route
            path="/features"
            element={
              <MarketingShell>
                <Features />
              </MarketingShell>
            }
          />
          <Route
            path="/how-it-works"
            element={
              <MarketingShell>
                <HowItWorks />
              </MarketingShell>
            }
          />
          <Route
            path="/docs"
            element={
              <MarketingShell>
                <Docs />
              </MarketingShell>
            }
          />
          <Route
            path="/pricing"
            element={
              <MarketingShell>
                <Pricing />
              </MarketingShell>
            }
          />
          <Route
            path="/about"
            element={
              <MarketingShell>
                <About />
              </MarketingShell>
            }
          />

          {/* Auth Routes */}
          <Route
            path="/login"
            element={
              <MarketingShell>
                <Login />
              </MarketingShell>
            }
          />
          <Route
            path="/signup"
            element={
              <MarketingShell>
                <Signup />
              </MarketingShell>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <MarketingShell>
                <ForgotPassword />
              </MarketingShell>
            }
          />

          {/* Authenticated Workspace App Layouts */}
          <Route
            path="/workspace"
            element={
              <AuthGuard>
                <AppShell>
                  <Dashboard />
                </AppShell>
              </AuthGuard>
            }
          />
          <Route
            path="/workspace/analyze"
            element={
              <AuthGuard>
                <AppShell>
                  <Analyze />
                </AppShell>
              </AuthGuard>
            }
          />
          <Route
            path="/workspace/run"
            element={
              <AuthGuard>
                <AppShell>
                  <Run />
                </AppShell>
              </AuthGuard>
            }
          />
          <Route
            path="/workspace/experiments"
            element={
              <AuthGuard>
                <AppShell>
                  <Experiments />
                </AppShell>
              </AuthGuard>
            }
          />

          {/* Fallback redirects */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
    </QueryClientProvider>
  );
};
export default App;
