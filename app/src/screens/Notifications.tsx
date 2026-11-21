import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { get, HEADERS, post, url } from '../api';
import { Btn, Card, Pill, SectionTitle } from '../components/ui';
import { C, font } from '../theme';

const START = ['21:00', '22:00', '23:00'];
const END = ['06:00', '07:00', '08:00'];

function Row({ title, sub, value, onChange, disabled }: { title: string; sub?: string; value: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <View style={s.row}>
      <View style={{ flex: 1, paddingRight: 12 }}>
        <Text style={[font.h3, disabled && { color: C.muted }]}>{title}</Text>
        {sub ? <Text style={font.small}>{sub}</Text> : null}
      </View>
      <Switch value={value} onValueChange={onChange} disabled={disabled}
        trackColor={{ false: C.line, true: C.primarySoft }} thumbColor={value ? C.primary : '#f4f3f4'}
        accessibilityLabel={title} />
    </View>
  );
}

function Choice({ options, value, onPick }: { options: string[]; value: string; onPick: (v: string) => void }) {
  return (
    <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
      {options.map((o) => (
        <Pressable key={o} onPress={() => onPick(o)} style={[s.chip, value === o && s.chipOn]} accessibilityRole="button" accessibilityState={{ selected: value === o }}>
          <Text style={[s.chipText, value === o && { color: '#fff' }]}>{o}</Text>
        </Pressable>
      ))}
    </View>
  );
}

export default function Notifications() {
  const [p, setP] = useState<any>(null);
  const [msg, setMsg] = useState('');
  useEffect(() => {
    get('/api/patient/notifications').then(setP).catch((e) => setMsg(e.message));
  }, []);

  const save = async (patch: any) => {
    const optimistic = { ...p, ...patch, quiet_hours: { ...p.quiet_hours, ...(patch.quiet_hours || {}) } };
    setP(optimistic);
    try {
      const r = await fetch(url('/api/patient/notifications'), { method: 'PATCH', headers: HEADERS, body: JSON.stringify(patch) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setP(await r.json());
      setMsg('Saved ✓');
    } catch (e: any) {
      setMsg(`Could not save: ${e.message}`);
    }
  };
  const lead = (k: string) => (p?.appointment_lead || []).includes(k);
  const toggleLead = (k: string) => save({ appointment_lead: lead(k) ? p.appointment_lead.filter((x: string) => x !== k) : [...p.appointment_lead, k] });

  if (!p) return <ScrollView contentContainerStyle={s.page}><Text style={font.h1}>Notifications</Text><Text style={font.small}>{msg || 'Loading…'}</Text></ScrollView>;

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.h1}>Notifications</Text>
      <Text style={[font.small, { marginBottom: 6 }]}>Choose what Aarogya reminds you about, and when it stays quiet.</Text>
      {msg ? <Text style={[font.small, { color: C.primaryDark }]}>{msg}</Text> : null}

      <SectionTitle>Reminders</SectionTitle>
      <Card>
        <Row title="Medicine reminders" sub="From verified prescriptions only" value={p.medication} onChange={(v) => save({ medication: v })} />
        <Row title="Appointment reminders" sub="Before each booked visit" value={p.appointment} onChange={(v) => save({ appointment: v })} />
        {p.appointment && (
          <View style={{ paddingVertical: 8, gap: 6 }}>
            <Text style={font.small}>Remind me</Text>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Btn small kind={lead('1d') ? 'primary' : 'ghost'} title="1 day before" onPress={() => toggleLead('1d')} />
              <Btn small kind={lead('2h') ? 'primary' : 'ghost'} title="2 hours before" onPress={() => toggleLead('2h')} />
            </View>
          </View>
        )}
        <Row title="Doctor-advised follow-ups" sub="Repeat tests, reviews from your care plan" value={p.follow_up} onChange={(v) => save({ follow_up: v })} />
        <Row title="Low medicine supply" sub="When a refill may be needed" value={p.refill} onChange={(v) => save({ refill: v })} />
      </Card>

      <SectionTitle>Quiet hours</SectionTitle>
      <Card style={{ gap: 10 }}>
        <Row title="Pause reminders at night" sub="Medicine and follow-up reminders wait until quiet hours end. Visit reminders still arrive." value={p.quiet_hours.enabled} onChange={(v) => save({ quiet_hours: { enabled: v } })} />
        {p.quiet_hours.enabled && (
          <>
            <Text style={font.small}>From</Text>
            <Choice options={START} value={p.quiet_hours.start} onPick={(v) => save({ quiet_hours: { start: v } })} />
            <Text style={font.small}>Until</Text>
            <Choice options={END} value={p.quiet_hours.end} onPick={(v) => save({ quiet_hours: { end: v } })} />
          </>
        )}
      </Card>

      <SectionTitle>Privacy & delivery</SectionTitle>
      <Card>
        <Row title="Show medicine names" sub="Turn off to show 'Time for your medicine' instead" value={p.show_medicine_names} onChange={(v) => save({ show_medicine_names: v })} />
        <Row title="Caregiver alerts" sub="Needs your explicit authorization of a caregiver (coming soon)" value={p.caregiver_alerts} onChange={() => {}} disabled />
        <View style={[s.row, { borderBottomWidth: 0 }]}>
          <View style={{ flex: 1 }}>
            <Text style={font.h3}>Delivery</Text>
            <Text style={font.small}>In-app alerts while Aarogya is open. Phone push notifications are on the roadmap.</Text>
          </View>
          <Pill text="In-app" tone="primary" />
        </View>
      </Card>

      <View style={{ marginTop: 12 }}>
        <Btn kind="soft" title="Send a test medicine reminder" onPress={async () => { await post('/api/demo/medication-reminder-now'); setMsg('Test reminder arrives in ~5 seconds'); }} />
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
  chip: { borderWidth: 1.5, borderColor: C.line, borderRadius: 99, paddingHorizontal: 14, paddingVertical: 7, backgroundColor: C.surface },
  chipOn: { backgroundColor: C.primary, borderColor: C.primary },
  chipText: { fontWeight: '700', color: C.inkSoft },
});
