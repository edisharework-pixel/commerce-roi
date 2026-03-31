import { useState, useCallback } from 'react';
import api from '../api/client';

export function useAuth() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  const login = useCallback(async (username: string, password: string) => {
    const resp = await api.post('/auth/login', { username, password });
    const { access_token } = resp.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    return access_token;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
  }, []);

  const register = useCallback(async (username: string, password: string, role: string = 'user') => {
    await api.post('/auth/register', { username, password, role });
  }, []);

  return { token, isAuthenticated: !!token, login, logout, register };
}
