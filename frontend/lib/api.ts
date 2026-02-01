import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL + '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests - FIXED VERSION
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      console.log('Interceptor - Token exists:', !!token);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('Interceptor - Authorization header set');
      } else {
        console.log('Interceptor - No token found in storage');
      }
    } catch (error) {
      console.error('Interceptor error:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to log errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Auth
export const authWithTelegram = async (initData: string) => {
  const response = await api.post('/auth/telegram', { init_data: initData });
  if (response.data.access_token) {
    console.log('Saving token to storage...');
    await AsyncStorage.setItem('auth_token', response.data.access_token);
    console.log('Token saved successfully');
  }
  return response.data;
};

// Emails - WITH TOKEN RETRY
export const getMyEmail = async () => {
  const response = await api.get('/emails/me');
  return response.data;
};

export const addEmail = async (email: string) => {
  // Get token directly before making request
  const token = await AsyncStorage.getItem('auth_token');
  console.log('addEmail - Token check:', !!token);
  
  const response = await api.post('/emails', { email });
  return response.data;
};

export const sendVerification = async (emailId: string) => {
  const token = await AsyncStorage.getItem('auth_token');
  console.log('sendVerification - Token check:', !!token);
  
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
