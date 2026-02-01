import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import { addEmail, sendVerification, verifyEmail, getMyEmail } from '../lib/api';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function EmailGate() {
  const router = useRouter();
  const { user, updateUser } = useAuth();
  const [step, setStep] = useState<'add' | 'verify'>('add');
  const [email, setEmail] = useState('');
  const [emailId, setEmailId] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');

  const handleAddEmail = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');
    try {
      // Check if user is authenticated
      const token = await AsyncStorage.getItem('auth_token');
      console.log('Auth token exists:', !!token);
      
      if (!token) {
        setError('Not authenticated. Please restart the app.');
        setLoading(false);
        return;
      }
      
      const response = await addEmail(email);
      setEmailId(response.id);
      
      // Automatically send verification
      const verifyResponse = await sendVerification(response.id);
      
      // For mock mode, extract code from response if available
      if (verifyResponse.code) {
        setVerificationCode(verifyResponse.code);
      }
      
      setStep('verify');
    } catch (err: any) {
      console.error('Add email error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to add email';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) {
      setError('Please enter the 6-digit code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await verifyEmail(emailId, code);
      
      // Update user data
      const emailData = await getMyEmail();
      if (user) {
        updateUser({
          ...user,
          email: emailData.email,
          email_verification_status: 'verified'
        });
      }
      
      router.replace('/(tabs)');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.icon}>📧</Text>
          <Text style={styles.title}>Email Verification</Text>
          <Text style={styles.subtitle}>
            {step === 'add' 
              ? 'Add your email to start earning' 
              : 'Enter the verification code below'}
          </Text>
        </View>

        {step === 'add' ? (
          <View style={styles.form}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              placeholder="your@email.com"
              placeholderTextColor="#666"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
              editable={!loading}
            />
            
            {error ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}
            
            <TouchableOpacity 
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleAddEmail}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Continue</Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.form}>
            {verificationCode ? (
              <View style={styles.codeDisplay}>
                <Text style={styles.codeLabel}>Your Verification Code:</Text>
                <Text style={styles.codeText}>{verificationCode}</Text>
                <Text style={styles.codeHint}>Enter this code below</Text>
              </View>
            ) : null}
            
            <Text style={styles.label}>Verification Code</Text>
            <TextInput
              style={styles.input}
              placeholder="000000"
              placeholderTextColor="#666"
              value={code}
              onChangeText={setCode}
              keyboardType="number-pad"
              maxLength={6}
              editable={!loading}
            />
            
            {error ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}
            
            <TouchableOpacity 
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleVerifyCode}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Verify</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.linkButton}
              onPress={async () => {
                const response = await sendVerification(emailId);
                if (response.code) {
                  setVerificationCode(response.code);
                }
              }}
              disabled={loading}
            >
              <Text style={styles.linkText}>Resend Code</Text>
            </TouchableOpacity>
          </View>
        )}

        <Text style={styles.note}>
          Mock mode: Code shown above for testing
        </Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  icon: {
    fontSize: 60,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
  },
  form: {
    marginBottom: 32,
  },
  label: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#fff',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  linkText: {
    color: '#4CAF50',
    fontSize: 16,
  },
  note: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 24,
  },
  codeDisplay: {
    backgroundColor: '#1a3a1a',
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  codeLabel: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 8,
  },
  codeText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4CAF50',
    letterSpacing: 4,
    marginBottom: 8,
  },
  codeHint: {
    fontSize: 12,
    color: '#666',
  },
  errorBox: {
    backgroundColor: '#3a1a1a',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#ff4444',
  },
  errorText: {
    color: '#ff6666',
    fontSize: 14,
    textAlign: 'center',
  },
});
