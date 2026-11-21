import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { post } from './src/api';
import { Btn, Card } from './src/components/ui';
import { NavProvider, Route, ROUTES, SIDEBAR_W, useLayout } from './src/nav';
import Care from './src/screens/Care';
import Companion from './src/screens/Companion';
import Home from './src/screens/Home';
import Notifications from './src/screens/Notifications';
import Profile from './src/screens/Profile';
import Records from './src/screens/Records';
import Timeline from './src/screens/Timeline';
import { StoreProvider, useStore } from './src/store';
import { C, font } from './src/theme';

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

function Logo({ size = 38 }: { size?: number }) {
  return (
    <View style={[s.logo, { width: size, height: size, borderRadius: size * 0.32 }]}>
      <Text style={{ color: '#fff', fontWeight: '900', fontSize: size * 0.45 }}>आ</Text>
    </View>
  );
}

function StatusChip() {
  const { connected, voice } = useStore();
  return (
    <View style={s.chip}>
      <View style={[s.live, { backgroundColor: voice === 'live' ? C.saffron : connected ? C.ok : C.muted }]} />
      <Text style={[font.tiny, { color: C.inkSoft, fontWeight: '700' }]}>{voice === 'live' ? 'ON CALL' : connected ? 'LIVE' : 'OFFLINE'}</Text>
    </View>
  );
}

function Sidebar({ route, go }: { route: Route; go: (r: Route) => void }) {
  const { pendingApproval } = useStore();
  return (
    <View style={s.sidebar}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 8, marginBottom: 22 }}>
        <Logo />
        <View>
          <Text style={s.brand}>Aarogya</Text>
          <Text style={font.tiny}>Your care, connected</Text>
        </View>
      </View>
      {ROUTES.map((r) => {
        const on = route === r.key;
        return (
          <Pressable key={r.key} onPress={() => go(r.key)} accessibilityRole="link" accessibilityState={{ selected: on }}
            style={({ hovered, pressed }: any) => [s.navItem, on && s.navOn, !on && (hovered || pressed) && { backgroundColor: C.surfaceAlt }]}>
            <Text style={{ fontSize: 17, width: 24, textAlign: 'center' }}>{r.icon}</Text>
            <Text style={[s.navLabel, on && { color: C.primaryDark }]}>{r.label}</Text>
            {r.key === 'talk' && pendingApproval ? <View style={s.badge} /> : null}
          </Pressable>
        );
      })}
      <View style={{ flex: 1 }} />
      <Card style={{ padding: 12, marginBottom: 0 }}>
        <Text style={font.h3}>Sunita Sharma</Text>
        <Text style={font.tiny}>56 · Whitefield, Bengaluru</Text>
        <View style={{ marginTop: 8 }}><StatusChip /></View>
      </Card>
      <Text style={[font.tiny, { marginTop: 8, paddingHorizontal: 4 }]}>Synthetic demo data · not medical advice</Text>
    </View>
  );
}

function Shell() {
  const initial = (Platform.OS === 'web' && typeof window !== 'undefined' ? window.location.hash.replace('#', '') : '') as Route;
  const [route, setRouteState] = useState<Route>(ROUTES.some((r) => r.key === initial) ? initial : 'home');
  const setRoute = (r: Route) => {
    setRouteState(r);
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location.hash !== `#${r}`) window.history.pushState(null, '', `#${r}`);
  };
  React.useEffect(() => {
    if (Platform.OS !== 'web' || typeof window === 'undefined') return;
    const onPop = () => {
      const h = window.location.hash.replace('#', '') as Route;
      if (ROUTES.some((r) => r.key === h)) setRouteState(h);
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const { sidebar } = useLayout();
  const { pendingApproval } = useStore();
  const screen = {
    home: <Home />, talk: <Companion />, records: <Records />, care: <Care />,
    timeline: <Timeline />, notifications: <Notifications />, profile: <Profile />,
  }[route];

  return (
    <NavProvider value={{ route, go: setRoute }}>
      <SafeAreaView style={s.root} edges={['top', 'bottom']}>
        {sidebar ? (
          <View style={{ flex: 1, flexDirection: 'row' }}>
            <Sidebar route={route} go={setRoute} />
            <View style={{ flex: 1 }}>{screen}</View>
          </View>
        ) : (
          <>
            <View style={s.header}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1, marginRight: 10 }}>
                <Logo />
                <View style={{ flex: 1 }}>
                  <Text style={s.brand}>Aarogya</Text>
                  <Text style={font.tiny} numberOfLines={1}>Your health history · your language · your care, connected</Text>
                </View>
              </View>
              <StatusChip />
            </View>
            <View style={{ flex: 1 }}>{screen}</View>
            <View style={s.tabs}>
              {ROUTES.filter((r) => r.mobile).map((t) => {
                const on = route === t.key || (t.key === 'profile' && route === 'notifications') || (t.key === 'care' && route === 'timeline');
                return (
                  <Pressable key={t.key} onPress={() => setRoute(t.key)} style={s.tab} accessibilityRole="tab" accessibilityState={{ selected: on }}>
                    <View>
                      <Text style={{ fontSize: 20, opacity: on ? 1 : 0.55 }}>{t.icon}</Text>
                      {t.key === 'talk' && pendingApproval ? <View style={[s.badge, { position: 'absolute', right: -4, top: -2 }]} /> : null}
                    </View>
                    <Text style={[s.tabLabel, on && { color: C.primary }]}>{t.label}</Text>
                  </Pressable>
                );
              })}
            </View>
          </>
        )}
        <ReminderSheet />
      </SafeAreaView>
    </NavProvider>
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
  logo: { backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  brand: { fontSize: 19, fontWeight: '800', color: C.ink, letterSpacing: -0.3 },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: C.surface, borderRadius: 99, paddingHorizontal: 10, paddingVertical: 5, borderWidth: 1, borderColor: C.line, alignSelf: 'flex-start' },
  live: { width: 8, height: 8, borderRadius: 4 },
  tabs: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: C.line, backgroundColor: C.surface, paddingTop: 6, paddingBottom: 8 },
  tab: { flex: 1, alignItems: 'center', gap: 2 },
  tabLabel: { fontSize: 11.5, fontWeight: '700', color: C.muted },
  sidebar: { width: SIDEBAR_W, backgroundColor: C.surface, borderRightWidth: 1, borderRightColor: C.line, paddingVertical: 18, paddingHorizontal: 12 },
  navItem: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 10, paddingHorizontal: 10, borderRadius: 12, marginBottom: 2 },
  navOn: { backgroundColor: C.primarySoft },
  navLabel: { fontSize: 15, fontWeight: '700', color: C.inkSoft, flex: 1 },
  badge: { width: 9, height: 9, borderRadius: 5, backgroundColor: C.saffron },
  overlay: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, backgroundColor: 'rgba(22,48,43,0.45)', alignItems: 'center', justifyContent: 'center', padding: 16 },
});
