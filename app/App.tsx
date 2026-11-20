import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { post } from './src/api';
import { Btn, Card } from './src/components/ui';
import Care from './src/screens/Care';
import Companion from './src/screens/Companion';
import Profile from './src/screens/Profile';
import Records from './src/screens/Records';
import { StoreProvider, useStore } from './src/store';
import { C, font } from './src/theme';

const TABS = [
  { key: 'talk', label: 'Aarogya', icon: '🎙' },
  { key: 'records', label: 'Records', icon: '📂' },
  { key: 'care', label: 'Care', icon: '💊' },
  { key: 'me', label: 'Profile', icon: '👤' },
] as const;

function ReminderSheet() {
  const { reminder, dismissReminder } = useStore();
  if (!reminder) return null;
  const act = async (a: string) => {
    await post(`/api/reminders/${reminder.reminder_id}/action`, { action: a }).catch(() => {});
    dismissReminder();
  };
  return (
    <View style={s.overlay}>
      <Card tone="warn" style={{ width: '100%', maxWidth: 420 }}>
        <Text style={font.tiny}>{reminder.kind === 'medication' ? 'MEDICINE REMINDER' : 'REMINDER'}</Text>
        <Text style={[font.h2, { marginTop: 4 }]}>{reminder.title}</Text>
        <Text style={font.body}>{reminder.body}</Text>
        {reminder.kind === 'medication' ? (
          <>
            <Text style={[font.body, { marginTop: 8 }]}>आपकी दवा का समय हो गया है। क्या आपने दवा ले ली?</Text>
            <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
              <View style={{ flex: 1 }}><Btn title="Taken" onPress={() => act('taken')} /></View>
              <View style={{ flex: 1 }}><Btn kind="soft" title="Snooze 10m" onPress={() => act('snoozed')} /></View>
              <View style={{ flex: 1 }}><Btn kind="ghost" title="Skipped" onPress={() => act('skipped')} /></View>
            </View>
          </>
        ) : (
          <View style={{ marginTop: 12 }}><Btn title="OK" onPress={() => act('done')} /></View>
        )}
      </Card>
    </View>
  );
}

function Shell() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('talk');
  const { connected, voice } = useStore();
  return (
    <SafeAreaView style={s.root} edges={['top', 'bottom']}>
      <View style={s.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <View style={s.logo}><Text style={{ color: '#fff', fontWeight: '900', fontSize: 17 }}>आ</Text></View>
          <View>
            <Text style={s.brand}>Aarogya</Text>
            <Text style={font.tiny}>Your health history · your language · your care, connected</Text>
          </View>
        </View>
        <View style={s.chip}>
          <View style={[s.live, { backgroundColor: voice === 'live' ? C.saffron : connected ? C.ok : C.muted }]} />
          <Text style={[font.tiny, { color: C.inkSoft, fontWeight: '700' }]}>{voice === 'live' ? 'ON CALL' : 'हिंदी · EN'}</Text>
        </View>
      </View>
      <View style={{ flex: 1 }}>
        {tab === 'talk' && <Companion />}
        {tab === 'records' && <Records />}
        {tab === 'care' && <Care />}
        {tab === 'me' && <Profile />}
      </View>
      <View style={s.tabs}>
        {TABS.map((t) => (
          <Pressable key={t.key} onPress={() => setTab(t.key)} style={s.tab} accessibilityRole="tab" accessibilityState={{ selected: tab === t.key }}>
            <Text style={{ fontSize: 20, opacity: tab === t.key ? 1 : 0.55 }}>{t.icon}</Text>
            <Text style={[s.tabLabel, tab === t.key && { color: C.primary }]}>{t.label}</Text>
          </Pressable>
        ))}
      </View>
      <ReminderSheet />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <StoreProvider>
        <StatusBar style="dark" />
        <Shell />
      </StoreProvider>
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg, ...(Platform.OS === 'web' ? { height: '100dvh' as any } : {}) },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: C.line, backgroundColor: C.bg },
  logo: { width: 38, height: 38, borderRadius: 12, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  brand: { fontSize: 19, fontWeight: '800', color: C.ink, letterSpacing: -0.3 },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: C.surface, borderRadius: 99, paddingHorizontal: 10, paddingVertical: 5, borderWidth: 1, borderColor: C.line },
  live: { width: 8, height: 8, borderRadius: 4 },
  tabs: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: C.line, backgroundColor: C.surface, paddingTop: 6, paddingBottom: 8 },
  tab: { flex: 1, alignItems: 'center', gap: 2 },
  tabLabel: { fontSize: 11.5, fontWeight: '700', color: C.muted },
  overlay: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, backgroundColor: 'rgba(22,48,43,0.45)', alignItems: 'center', justifyContent: 'center', padding: 16 },
});
