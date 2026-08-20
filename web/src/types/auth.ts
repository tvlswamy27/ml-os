export interface User {
  id: number;
  email: string;
  created_at: string;
}

export type AuthState = 'AUTH_LOADING' | 'AUTHENTICATED' | 'UNAUTHENTICATED';
