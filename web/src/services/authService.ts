import { apiClient } from './apiClient';

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export const authService = {
  signup: async (email: string, password: string): Promise<User> => {
    return apiClient.post<User>('/api/auth/signup', { email, password });
  },

  login: async (email: string, password: string): Promise<{ message: string; email: string }> => {
    return apiClient.post<{ message: string; email: string }>('/api/auth/login', { email, password });
  },

  logout: async (): Promise<{ message: string }> => {
    return apiClient.post<{ message: string }>('/api/auth/logout');
  },

  getMe: async (): Promise<User> => {
    return apiClient.get<User>('/api/auth/me');
  },
};
