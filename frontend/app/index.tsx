import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import { authWithTelegram } from '../lib/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function Index() {
  const router = useRouter();
  const { user, isLoading, login, logout } = useAuth();
  const [authenticating, setAuthenticating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        // User is authenticated, check email verification
        if (!user.email || user.email_verification_status !== 'verified') {
          router.replace('/email-gate');
        } else {
          router.replace('/(tabs)');
        }
      }
      // If no user, stay on this screen to show login button
    }
  }, [isLoading, user]);

  const handleMockLogin = async () => {
    setAuthenticating(true);
    setError(null);
    
    try {
      // Mock Telegram init data for testing
      const mockInitData = `query_id=test&user=${encodeURIComponent(JSON.stringify({
        id: Math.floor(Math.random() * 1000000),
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser'
      }))}&auth_date=${Math.floor(Date.now() / 1000)}&hash=mockhash`;
      
      console.log('Starting authentication...');
      const response = await authWithTelegram(mockInitData);
      
      console.log('Login successful, saving token...');
      await login(response.access_token, response.user);
      
      // Wait a bit to ensure token is saved
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Verify token was saved
      const savedToken = await AsyncStorage.getItem('auth_token');
      console.log('Token saved:', !!savedToken);
      
      if (!savedToken) {
        throw new Error('Token was not saved properly');
      }
      
    } catch (err: any) {
      console.error('Auth error:', err);
      setError(err.response?.data?.detail || err.message || 'Authentication failed');
    } finally {
      setAuthenticating(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  // If user exists, don't show login screen (useEffect will handle routing)
  if (user) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Redirecting...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>📧</Text>
        </View>
        
        <Text style={styles.title}>InboxQuest</Text>
        <Text style={styles.subtitle}>Earn rewards for reading emails</Text>
        
        <View style={styles.features}>
          <Text style={styles.feature}>✓ Complete email tasks</Text>
          <Text style={styles.feature}>✓ Earn cash rewards</Text>
          <Text style={styles.feature}>✓ Unlock achievements</Text>
          <Text style={styles.feature}>✓ Refer friends</Text>
        </View>

        <TouchableOpacity 
          style={[styles.loginButton, authenticating && styles.loginButtonDisabled]}
          onPress={handleMockLogin}
          disabled={authenticating}
        >
          {authenticating ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.loginButtonText}>Get Started</Text>
          )}
        </TouchableOpacity>

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <Text style={styles.note}>
          Note: Using mock authentication for testing
        </Text>
        
        <TouchableOpacity 
          style={styles.resetButton}
          onPress={async () => {
            await logout();
            setError(null);
          }}
        >
          <Text style={styles.resetText}>Reset App Data</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  iconContainer: {
    marginBottom: 24,
  },
  icon: {
    fontSize: 80,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 32,
  },
  features: {
    marginBottom: 32,
  },
  feature: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 8,
  },
  loginButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 48,
    paddingVertical: 16,
    borderRadius: 12,
    minWidth: 200,
    alignItems: 'center',
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  loadingText: {
    color: '#fff',
    marginTop: 16,
    fontSize: 16,
  },
  errorContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#ff4444',
    borderRadius: 8,
  },
  errorText: {
    color: '#fff',
    textAlign: 'center',
  },
  note: {
    marginTop: 24,
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
  },
  resetButton: {
    marginTop: 16,
    padding: 12,
  },
  resetText: {
    color: '#ff6666',
    fontSize: 14,
    textAlign: 'center',
    textDecorationLine: 'underline',
  },
});
