import * as React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { meQuery, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="text-xs font-mono text-muted-foreground animate-pulse">
            Checking session verification...
          </span>
        </div>
      </div>
    );
  }

  if (meQuery.isError || !meQuery.data) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
export default AuthGuard;
