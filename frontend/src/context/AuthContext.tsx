import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, tenantApi } from '../services/api';
import type { User, Tenant } from '../types';

interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    church_name: string;
    city: string;
    state: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    pco_app_id?: string;
    pco_secret?: string;
  }) => Promise<void>;
  logout: () => void;
  refreshTenant: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const [userData, tenantData] = await Promise.all([
            authApi.getMe(),
            tenantApi.getTenant(),
          ]);
          setUser(userData);
          setTenant(tenantData);
        } catch {
          localStorage.removeItem('token');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const { access_token } = await authApi.login(email, password);
    localStorage.setItem('token', access_token);

    const [userData, tenantData] = await Promise.all([
      authApi.getMe(),
      tenantApi.getTenant(),
    ]);
    setUser(userData);
    setTenant(tenantData);
    navigate('/dashboard');
  };

  const signup = async (data: {
    church_name: string;
    city: string;
    state: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    pco_app_id?: string;
    pco_secret?: string;
  }) => {
    const { access_token } = await authApi.signup(data);
    localStorage.setItem('token', access_token);

    const [userData, tenantData] = await Promise.all([
      authApi.getMe(),
      tenantApi.getTenant(),
    ]);
    setUser(userData);
    setTenant(tenantData);
    navigate('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setTenant(null);
    navigate('/login');
  };

  const refreshTenant = async () => {
    const tenantData = await tenantApi.getTenant();
    setTenant(tenantData);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tenant,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        refreshTenant,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
