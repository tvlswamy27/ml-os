import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/authService';
import type { User } from '../types';

export function useAuth() {
  const queryClient = useQueryClient();

  const meQuery = useQuery<User, Error>({
    queryKey: ['authMe'],
    queryFn: authService.getMe,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['authMe'] });
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  const signupMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.signup(email, password),
    onSuccess: () => {
      // Signup doesn't auto-login on session cookie unless login is called,
      // but actually backend signup returns User. In our signup router:
      // it returns User, does not set session cookie. The user still needs to login.
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authService.logout,
    onSuccess: () => {
      queryClient.setQueryData(['authMe'], null);
      queryClient.clear();
    },
  });

  return {
    user: meQuery.data,
    isLoading: meQuery.isLoading,
    isError: meQuery.isError,
    error: meQuery.error,
    meQuery,
    loginMutation,
    signupMutation,
    logoutMutation,
  };
}
