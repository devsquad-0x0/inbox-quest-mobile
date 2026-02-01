import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setAuthToken, clearAuthToken, getAuthToken } from '../lib/api';

interface User {
  id: string;
  telegram_id: number;
  username: string;
  first_name: string;
  last_name?: string;
  photo_url?: string;
  email?: string;
  email_verification_status: string;
  referral_code: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, userData: User) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (userData: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await getToken();
      const userStr = await AsyncStorage.getItem('user_data');
      
      if (token && userStr) {
        const userData = JSON.parse(userStr);
        setUser(userData);
      }
    } catch (error) {
      console.error('Error checking auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (token: string, userData: User) => {
    await setToken(token);
    await AsyncStorage.setItem('user_data', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = async () => {
    await clearToken();
    await AsyncStorage.removeItem('user_data');
    setUser(null);
  };

  const updateUser = (userData: User) => {
    setUser(userData);
    AsyncStorage.setItem('user_data', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
