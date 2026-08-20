import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '../services/projectService';
import type { Workspace } from '../types';

export function useWorkspaces() {
  const queryClient = useQueryClient();

  const workspacesQuery = useQuery<Workspace[], Error>({
    queryKey: ['workspaces'],
    queryFn: projectService.listWorkspaces,
    staleTime: 30000,
  });

  const createWorkspaceMutation = useMutation({
    mutationFn: (name: string) => projectService.createWorkspace(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  return {
    workspaces: workspacesQuery.data || [],
    isLoading: workspacesQuery.isLoading,
    isError: workspacesQuery.isError,
    error: workspacesQuery.error,
    workspacesQuery,
    createWorkspaceMutation,
  };
}
