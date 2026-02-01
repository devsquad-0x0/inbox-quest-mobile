import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, TextInput, Modal, Alert } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getWallet, getLedger, requestPayout, getReferrals } from '../../lib/api';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';

export default function WalletScreen() {
  const queryClient = useQueryClient();
  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutMethod, setPayoutMethod] = useState('paypal');
  const [payoutAddress, setPayoutAddress] = useState('');

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['wallet'],
    queryFn: getWallet,
  });

  const { data: ledger } = useQuery({
    queryKey: ['ledger'],
    queryFn: () => getLedger({ limit: 10 }),
  });

  const { data: referrals } = useQuery({
    queryKey: ['referrals'],
    queryFn: getReferrals,
  });

  const payout = useMutation({
    mutationFn: requestPayout,
    onSuccess: () => {
      setShowPayoutModal(false);
      setPayoutAmount('');
      setPayoutAddress('');
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      Alert.alert('Success', 'Payout requested successfully!');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || 'Payout failed');
    },
  });

  const handleRequestPayout = () => {
    if (!payoutAmount || !payoutAddress) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    payout.mutate({
      amount: parseFloat(payoutAmount),
      payout_method: payoutMethod,
      payout_address: payoutAddress,
    });
  };

  if (walletLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Available Balance</Text>
          <Text style={styles.balanceAmount}>${wallet?.available_balance.toFixed(2) || '0.00'}</Text>
          
          <TouchableOpacity
            style={[styles.payoutButton, !wallet?.can_request_payout && styles.payoutButtonDisabled]}
            onPress={() => setShowPayoutModal(true)}
            disabled={!wallet?.can_request_payout}
          >
            <Text style={styles.payoutButtonText}>Request Payout</Text>
          </TouchableOpacity>
          
          {!wallet?.can_request_payout && (
            <Text style={styles.payoutNote}>Minimum ${wallet?.minimum_payout || 10} required</Text>
          )}
        </View>

        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>${wallet?.total_earnings.toFixed(2) || '0.00'}</Text>
            <Text style={styles.statLabel}>Total Earned</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>${wallet?.pending_payouts.toFixed(2) || '0.00'}</Text>
            <Text style={styles.statLabel}>Pending</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Transactions</Text>
          {ledger?.entries.map((entry: any) => (
            <View key={entry.id} style={styles.transactionCard}>
              <View style={styles.transactionInfo}>
                <Text style={styles.transactionType}>{entry.entry_type.replace('_', ' ')}</Text>
                <Text style={styles.transactionDate}>
                  {format(new Date(entry.created_at), 'MMM d, h:mm a')}
                </Text>
              </View>
              <Text style={[
                styles.transactionAmount,
                { color: entry.amount > 0 ? '#4CAF50' : '#EF5350' }
              ]}>
                {entry.amount > 0 ? '+' : ''}${entry.amount.toFixed(2)}
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.referralCard}>
          <Text style={styles.referralTitle}>Refer & Earn</Text>
          <Text style={styles.referralCode}>{referrals?.referral_code || 'Loading...'}</Text>
          <TouchableOpacity style={styles.copyButton}>
            <Text style={styles.copyButtonText}>Copy Link</Text>
          </TouchableOpacity>
          <Text style={styles.referralStats}>
            {referrals?.total_referrals || 0} referrals • ${referrals?.total_earnings.toFixed(2) || '0.00'} earned
          </Text>
        </View>
      </ScrollView>

      <Modal visible={showPayoutModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Request Payout</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Amount"
              placeholderTextColor="#666"
              value={payoutAmount}
              onChangeText={setPayoutAmount}
              keyboardType="decimal-pad"
            />
            
            <TextInput
              style={styles.input}
              placeholder="PayPal Email"
              placeholderTextColor="#666"
              value={payoutAddress}
              onChangeText={setPayoutAddress}
              autoCapitalize="none"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButtonCancel}
                onPress={() => setShowPayoutModal(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalButtonConfirm}
                onPress={handleRequestPayout}
                disabled={payout.isPending}
              >
                {payout.isPending ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.modalButtonTextConfirm}>Confirm</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0c0c0c',
  },
  scroll: {
    flex: 1,
    padding: 16,
  },
  balanceCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    padding: 24,
    marginBottom: 16,
    alignItems: 'center',
  },
  balanceLabel: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 8,
  },
  balanceAmount: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 20,
  },
  payoutButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  payoutButtonDisabled: {
    backgroundColor: '#333',
  },
  payoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  payoutNote: {
    marginTop: 8,
    color: '#666',
    fontSize: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#aaa',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  transactionCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  transactionInfo: {
    flex: 1,
  },
  transactionType: {
    fontSize: 16,
    color: '#fff',
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  transactionDate: {
    fontSize: 12,
    color: '#666',
  },
  transactionAmount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  referralCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  referralTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  referralCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 12,
  },
  copyButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  copyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  referralStats: {
    fontSize: 14,
    color: '#aaa',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#0c0c0c',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButtonCancel: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#333',
    alignItems: 'center',
  },
  modalButtonConfirm: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#4CAF50',
    alignItems: 'center',
  },
  modalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalButtonTextConfirm: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
