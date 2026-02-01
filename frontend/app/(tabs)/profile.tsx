import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { getAchievements } from '../../lib/api';
import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const { data } = useQuery({
    queryKey: ['achievements'],
    queryFn: getAchievements,
  });

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/');
          },
        },
      ]
    );
  };

  const unlockedCount = data?.achievements.filter((a: any) => a.is_unlocked).length || 0;
  const totalCount = data?.achievements.length || 0;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.first_name?.charAt(0) || 'U'}</Text>
          </View>
          <Text style={styles.name}>{user?.first_name} {user?.last_name || ''}</Text>
          <Text style={styles.username}>@{user?.username}</Text>
          {user?.email && (
            <Text style={styles.email}>{user.email}</Text>
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Achievements ({unlockedCount}/{totalCount})
          </Text>
          
          {data?.achievements.slice(0, 6).map((achievement: any) => (
            <View
              key={achievement.id}
              style={[styles.achievementCard, !achievement.is_unlocked && styles.achievementLocked]}
            >
              <View style={styles.achievementIcon}>
                <Text style={styles.achievementIconText}>
                  {achievement.is_unlocked ? '🏆' : '🔒'}
                </Text>
              </View>
              
              <View style={styles.achievementInfo}>
                <Text style={styles.achievementName}>{achievement.name}</Text>
                <Text style={styles.achievementDescription}>{achievement.description}</Text>
                
                {!achievement.is_unlocked && (
                  <View style={styles.progressBar}>
                    <View style={[styles.progressFill, { width: `${achievement.progress_percent}%` }]} />
                  </View>
                )}
                
                <View style={styles.achievementReward}>
                  <Text style={styles.rewardText}>
                    {achievement.xp_reward} XP
                  </Text>
                  {achievement.cash_reward > 0 && (
                    <Text style={styles.rewardText}>
                      • ${achievement.cash_reward.toFixed(2)}
                    </Text>
                  )}
                </View>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          
          <TouchableOpacity style={styles.settingItem}>
            <Ionicons name="notifications-outline" size={24} color="#fff" />
            <Text style={styles.settingText}>Notifications</Text>
            <Ionicons name="chevron-forward" size={24} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingItem}>
            <Ionicons name="help-circle-outline" size={24} color="#fff" />
            <Text style={styles.settingText}>Help & Support</Text>
            <Ionicons name="chevron-forward" size={24} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingItem}>
            <Ionicons name="document-text-outline" size={24} color="#fff" />
            <Text style={styles.settingText}>Terms & Privacy</Text>
            <Ionicons name="chevron-forward" size={24} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity style={[styles.settingItem, styles.logoutItem]} onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={24} color="#EF5350" />
            <Text style={[styles.settingText, styles.logoutText]}>Logout</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.version}>Version 1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  scroll: {
    flex: 1,
    padding: 16,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
    paddingVertical: 24,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#4CAF50',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  username: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    color: '#666',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  achievementCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
  },
  achievementLocked: {
    opacity: 0.6,
  },
  achievementIcon: {
    marginRight: 16,
  },
  achievementIconText: {
    fontSize: 32,
  },
  achievementInfo: {
    flex: 1,
  },
  achievementName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  achievementDescription: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 8,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#333',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  achievementReward: {
    flexDirection: 'row',
    gap: 8,
  },
  rewardText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '600',
  },
  settingItem: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingText: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
    marginLeft: 16,
  },
  logoutItem: {
    marginTop: 16,
  },
  logoutText: {
    color: '#EF5350',
  },
  version: {
    textAlign: 'center',
    color: '#666',
    fontSize: 12,
    marginVertical: 24,
  },
});
