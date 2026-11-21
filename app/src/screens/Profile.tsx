import React, { useEffect, useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { get, getApiBase, HEADERS, post, setApiBase, url } from '../api';
import { Btn, Card, Pill, SectionTitle } from '../components/ui';
import { useNav } from '../nav';
import { useStore } from '../store';
import { C, font } from '../theme';

export default function Profile() {
  const { clearFeed, reconnectServer, sessionId } = useStore();
  const { go } = useNav();
  const [server, setServer] = useState(getApiBase());
  const [p, setP] = useState<any>(null);
  const [h, setH] = useState<any>(null);
  const [msg, setMsg] = useState('');
  const [shares, setShares] = useState<any[]>([]);
  const [lang, setLang] = useState('auto');
  const { dataVersion, sessionId: sid } = useStore();
  useEffect(() => {
    get('/api/patient').then((x) => { setP(x); setLang(x?.preferences?.reply_language || 'auto'); }).catch(() => {});
    get('/api/health').then(setH).catch(() => {});
  }, []);
  useEffect(() => {
    get('/api/shares').then(setShares).catch(() => {});
  }, [dataVersion]);
  const setLanguage = async (v: string) => {
    setLang(v);
    await fetch(url('/api/patient/preferences'), { method: 'PATCH', headers: HEADERS, body: JSON.stringify({ reply_language: v }) }).catch(() => {});
  };
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

      <Btn kind="soft" title="🔔  Notification preferences" onPress={() => go('notifications')} />

      <SectionTitle>Reply language</SectionTitle>
      <Card style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {[['auto', 'Auto (match me)'], ['hindi', 'हिंदी'], ['hinglish', 'Hinglish'], ['english', 'English']].map(([k, label]) => (
          <Btn key={k} small kind={lang === k ? 'primary' : 'ghost'} title={label} onPress={() => setLanguage(k)} />
        ))}
      </Card>

      <SectionTitle>Shared records</SectionTitle>
      <Card>
        {shares.length === 0 && <Text style={font.small}>You have not shared any records.</Text>}
        {shares.map((x) => (
          <View key={x.share_id} style={{ paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.line, gap: 4 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text style={font.h3}>{x.doctor_name}</Text>
              <Pill text={x.status} tone={x.status === 'active' ? 'ok' : 'neutral'} />
            </View>
            <Text style={font.small}>{x.documents.join(', ')}</Text>
            <Text style={font.tiny}>{x.purpose ? `Purpose: ${x.purpose} · ` : ''}{x.status === 'active' ? `expires ${x.label}` : ''}</Text>
            {x.status === 'active' && (
              <Btn small kind="ghost" title="Revoke access" onPress={() => run('Access revoked', async () => {
                await post(`/api/shares/${x.share_id}/revoke`, { session_id: sid });
                setShares(await get('/api/shares'));
              })} />
            )}
          </View>
        ))}
      </Card>

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
        <Btn kind="soft" title="Simulate: Dr. Meera's clinic sends clarified prescription" onPress={() => run('Provider record pushed — see Aarogya tab', () => post(`/api/demo/provider-sync?session_id=${sessionId}`))} />
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
