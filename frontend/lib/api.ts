import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

// Token management
let authToken: string | null = null;

export const setAuthToken = (token: string) => {
  authToken = token;
  AsyncStorage.setItem('auth_token', token);
};

export const getAuthToken = (): string | null => {
  return authToken;
};

export const clearAuthToken = () => {
  authToken = null;
  AsyncStorage.removeItem('auth_token');
  AsyncStorage.removeItem('user_data');
};

// Initialize token from storage
AsyncStorage.getItem('auth_token').then(token => {
  if (token) authToken = token;
});

// Create API instance
const api = axios.create({
  baseURL: API_URL + '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - SYNCHRONOUS
api.interceptors.request.use(
  (config) => {
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthToken();
    }
    return Promise.reject(error);
  }
);

// Auth
export const authWithTelegram = async (initData: string) => {
  const response = await api.post('/auth/telegram', { init_data: initData });
  if (response.data.access_token) {
    setAuthToken(response.data.access_token);
  }
  return response.data;
};

// Emails
export const getMyEmail = async () => {
  const response = await api.get('/emails/me');
  return response.data;
};

export const addEmail = async (email: string) => {
  const response = await api.post('/emails', { email });
  return response.data;
};

export const sendVerification = async (emailId: string) => {
  const response = await api.post(`/emails/${emailId}/send-verification`);
  return response.data;
};

export const verifyEmail = async (emailId: string, code: string) => {
  const response = await api.post(`/emails/${emailId}/verify`, { code });
  return response.data;
};

// Campaigns
export const getCampaigns = async (params?: any) => {
  const response = await api.get('/campaigns', { params });
  return response.data;
};

export const subscribeToCampaign = async (campaignId: string) => {
  const response = await api.post(`/campaigns/${campaignId}/subscribe`);
  return response.data;
};

export const unsubscribeFromCampaign = async (campaignId: string) => {
  const response = await api.delete(`/campaigns/${campaignId}/subscribe`);
  return response.data;
};

// Tasks
export const getTasks = async (params?: any) => {
  const response = await api.get('/tasks', { params });
  return response.data;
};

// Wallet
export const getWallet = async () => {
  const response = await api.get('/wallet');
  return response.data;
};

export const getLedger = async (params?: any) => {
  const response = await api.get('/wallet/ledger', { params });
  return response.data;
};

export const requestPayout = async (data: any) => {
  const response = await api.post('/wallet/payouts', data);
  return response.data;
};

export const getPayouts = async () => {
  const response = await api.get('/wallet/payouts');
  return response.data;
};

// Gamification
export const getGamification = async () => {
  const response = await api.get('/gamification');
  return response.data;
};

export const claimDailyBonus = async () => {
  const response = await api.post('/gamification/daily-bonus');
  return response.data;
};

// Achievements
export const getAchievements = async () => {
  const response = await api.get('/achievements');
  return response.data;
};

// Referrals
export const getReferrals = async () => {
  const response = await api.get('/referrals');
  return response.data;
};

export default api;
