import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { getGamification, getWallet, claimDailyBonus } from '../../lib/api';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const { user } = useAuth();
  
  const { data: gamification, isLoading: gamificationLoading, refetch: refetchGamification } = useQuery({
    queryKey: ['gamification'],
    queryFn: getGamification,
  });

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['wallet'],
    queryFn: getWallet,
  });

  const handleClaimBonus = async () => {
    try {
      await claimDailyBonus();
      refetchGamification();
    } catch (error: any) {
      console.error('Claim error:', error);
    }
  };

  if (gamificationLoading || walletLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.greeting}>Hello, {user?.first_name}!</Text>
          <Text style={styles.subGreeting}>Welcome to InboxQuest</Text>
        </View>

        {gamification?.daily_bonus_available && (
          <TouchableOpacity style={styles.bonusCard} onPress={handleClaimBonus}>
            <View style={styles.bonusContent}>
              <Text style={styles.bonusIcon}>🎁</Text>
              <View style={styles.bonusText}>
                <Text style={styles.bonusTitle}>Daily Bonus Available!</Text>
                <Text style={styles.bonusSubtitle}>Day {gamification.daily_bonus_streak_day} of 7</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#4CAF50" />
          </TouchableOpacity>
        )}

        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>${wallet?.available_balance.toFixed(2) || '0.00'}</Text>
            <Text style={styles.statLabel}>Balance</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{gamification?.tasks_completed || 0}</Text>
            <Text style={styles.statLabel}>Tasks Done</Text>
          </View>
        </View>

        <View style={styles.levelCard}>
          <View style={styles.levelHeader}>
            <Text style={styles.levelTitle}>Level {gamification?.level || 1}</Text>
            <Text style={styles.levelName}>{gamification?.level_name || 'Newcomer'}</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${gamification?.xp_progress || 0}%` }]} />
          </View>
          <Text style={styles.progressText}>
            {gamification?.xp || 0} XP • {gamification?.xp_to_next_level || 100} XP to next level
          </Text>
        </View>

        <View style={styles.streakCard}>
          <Text style={styles.streakIcon}>🔥</Text>
          <View style={styles.streakContent}>
            <Text style={styles.streakValue}>{gamification?.current_streak || 0} days</Text>
            <Text style={styles.streakLabel}>Current Streak</Text>
          </View>
        </View>
      </ScrollView>
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
  header: {
    marginBottom: 24,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subGreeting: {
    fontSize: 16,
    color: '#aaa',
    marginTop: 4,
  },
  bonusCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  bonusContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  bonusIcon: {
    fontSize: 40,
    marginRight: 16,
  },
  bonusText: {
    flex: 1,
  },
  bonusTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  bonusSubtitle: {
    fontSize: 14,
    color: '#aaa',
    marginTop: 2,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#aaa',
  },
  levelCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  levelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  levelTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  levelName: {
    fontSize: 16,
    color: '#4CAF50',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  progressText: {
    fontSize: 14,
    color: '#aaa',
  },
  streakCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  streakIcon: {
    fontSize: 40,
    marginRight: 16,
  },
  streakContent: {
    flex: 1,
  },
  streakValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  streakLabel: {
    fontSize: 14,
    color: '#aaa',
    marginTop: 2,
  },
});
