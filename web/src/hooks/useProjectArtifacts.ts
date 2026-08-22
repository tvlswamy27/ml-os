import { useQuery, useMutation } from '@tanstack/react-query';
import { projectService } from '../services/projectService';
import type { Artifact } from '../types';

export const useProjectArtifacts = (projectId: number | null) => {
  const query = useQuery({
    queryKey: ['projectArtifacts', projectId],
    queryFn: () => {
      if (projectId === null) throw new Error("No project ID");
      return projectService.getProjectArtifacts(projectId);
    },
    enabled: projectId !== null,
  });

  const downloadArtifactMutation = useMutation({
    mutationFn: ({ path, name }: { path: string; name: string }) => {
      if (projectId === null) throw new Error("No project ID");
      return projectService.downloadArtifact(projectId, path, name);
    },
  });

  return {
    artifacts: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error as Error | null,
    downloadArtifactMutation,
    refetch: query.refetch,
  };
};
