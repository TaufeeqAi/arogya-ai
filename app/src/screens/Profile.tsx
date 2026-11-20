import React, { useEffect, useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { get, getApiBase, post, setApiBase } from '../api';
import { Btn, Card, Pill, SectionTitle } from '../components/ui';
import { useStore } from '../store';
import { C, font } from '../theme';

export default function Profile() {
  const { clearFeed, reconnectServer } = useStore();
  const [server, setServer] = useState(getApiBase());
  const [p, setP] = useState<any>(null);
  const [h, setH] = useState<any>(null);
  const [msg, setMsg] = useState('');
  useEffect(() => {
    get('/api/patient').then(setP).catch(() => {});
    get('/api/health').then(setH).catch(() => {});
  }, []);
  const run = async (label: string, fn: () => Promise<any>) => {
    setMsg('…');
    try {
      await fn();
      setMsg(`✓ ${label}`);
    } catch (e: any) {
      setMsg(`⚠️ ${e.message}`);
    }
  };

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.h1}>Profile & Privacy</Text>
      {p && (
        <Card style={{ marginTop: 12 }}>
          <Text style={font.h2}>{p.name}</Text>
          <Text style={font.small}>{p.age} yrs · {p.sex === 'F' ? 'Female' : 'Male'} · {p.area}, {p.city}</Text>
          <View style={s.wrap}>{p.conditions.map((c: string) => <Pill key={c} text={c} tone="primary" />)}</View>
          <Text style={[font.small, { marginTop: 8 }]}>Allergies: {p.allergies.join(', ')}</Text>
          <Text style={font.small}>Prefers: {p.preferences.preferred_language} · {p.preferences.preferred_time} slots · {p.preferences.preferred_doctor}</Text>
        </Card>
      )}

      <SectionTitle>Your data, your control</SectionTitle>
      <Card>
        {[
          'Aarogya explains documents — it never diagnoses or changes medicines.',
          'Every booking, share or order needs your explicit approval, bound to exact details.',
          'Records are shared only with the doctor you choose, for 7 days, and can be revoked.',
          'Every action is logged in your audit trail.',
          'Demo uses synthetic data only.',
        ].map((t) => (
          <Text key={t} style={[font.body, { marginBottom: 6 }]}>✓ {t}</Text>
        ))}
      </Card>

      <SectionTitle>System status</SectionTitle>
      <Card>
        {h ? (
          <View style={s.wrap}>
            <Pill text={`LLM ${h.llm ? '✓' : '✗'}`} tone={h.llm ? 'ok' : 'danger'} />
            <Pill text={`Agora ${h.agora ? '✓' : '✗'}`} tone={h.agora ? 'ok' : 'danger'} />
            <Pill text={`Murf ${h.murf ? '✓' : '✗'}`} tone={h.murf ? 'ok' : 'danger'} />
          </View>
        ) : (
          <Text style={font.small}>Checking…</Text>
        )}
      </Card>

      {Platform.OS !== 'web' && (
        <>
          <SectionTitle>Server</SectionTitle>
          <Card style={{ gap: 8 }}>
            <TextInput value={server} onChangeText={setServer} autoCapitalize="none" autoCorrect={false}
              style={{ backgroundColor: C.bg, borderRadius: 12, padding: 12, color: C.ink }} />
            <Btn kind="soft" title="Save & reconnect" onPress={() => run('Server saved', async () => {
              await setApiBase(server);
              reconnectServer();
              setH(await get('/api/health'));
            })} />
          </Card>
        </>
      )}

      <SectionTitle>Demo controls</SectionTitle>
      <Card style={{ gap: 10 }}>
        <Btn kind="soft" title="Simulate: next approved slot gets taken" onPress={() => run('Next booking will hit a slot conflict', () => post('/api/demo/conflict?on=true'))} />
        <Btn kind="soft" title="Trigger a medicine reminder now" onPress={() => run('Reminder fires in ~5s', () => post('/api/demo/medication-reminder-now'))} />
        <Btn kind="ghost" title="Reset demo data" onPress={() => run('Demo data reset', async () => { await post('/api/demo/reset'); clearFeed(); })} />
        {msg ? <Text style={[font.small, { color: C.primaryDark }]}>{msg}</Text> : null}
      </Card>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
});
