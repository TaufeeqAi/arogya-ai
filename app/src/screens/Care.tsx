import React, { useEffect, useState } from 'react';
import { Linking, ScrollView, StyleSheet, Text, View } from 'react-native';
import { get } from '../api';
import { GenUI } from '../components/GenUI';
import { Btn, Card, Pill, SectionTitle } from '../components/ui';
import { useStore } from '../store';
import { C, font } from '../theme';

export default function Care() {
  const { dataVersion, approvals, decide, send } = useStore();
  const [meds, setMeds] = useState<any[]>([]);
  const [appts, setAppts] = useState<any[]>([]);
  const [rem, setRem] = useState<any[]>([]);
  const [plan, setPlan] = useState<any[]>([]);
  useEffect(() => {
    get('/api/medications').then(setMeds).catch(() => {});
    get('/api/appointments').then(setAppts).catch(() => {});
    get('/api/reminders').then(setRem).catch(() => {});
    get('/api/care-plan').then(setPlan).catch(() => {});
  }, [dataVersion]);
  const ctx = { say: send, decide, approvals };
  const upcoming = rem.filter((r) => r.status === 'scheduled');

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.h1}>My Care</Text>
      <Text style={[font.small, { marginBottom: 12 }]}>Appointments, medicines and follow-ups in one place.</Text>

      {plan.length > 0 && <GenUI ctx={ctx} item={{ id: 'plan', component: 'care_plan', version: 1, props: { tasks: plan } }} />}

      <SectionTitle>Appointments</SectionTitle>
      {appts.length === 0 && (
        <Card>
          <Text style={font.body}>No upcoming appointments.</Text>
          <Text style={font.small}>Say "Saturday ko doctor ka appointment chahiye".</Text>
        </Card>
      )}
      {appts.map((a) => (
        <Card key={a.id} tone="ok">
          <View style={s.row}>
            <Text style={font.h3}>{a.doctor_name}</Text>
            <Pill text={a.status} tone="ok" />
          </View>
          <Text style={font.body}>{a.label}</Text>
          <Text style={font.small}>{a.clinic}, {a.area} · Ref {a.booking_ref}</Text>
          {a.calendar_url ? (
            <View style={{ marginTop: 8 }}>
              <Btn small kind="soft" title="📅 Add to Google Calendar" onPress={() => Linking.openURL(a.calendar_url)} />
            </View>
          ) : null}
        </Card>
      ))}

      <SectionTitle>Medicines</SectionTitle>
      {meds.length > 0 && <GenUI ctx={ctx} item={{ id: 'meds', component: 'medication_schedule', version: 1, props: { medications: meds } }} />}

      <SectionTitle right={<Pill text={`${upcoming.length} scheduled`} />}>Reminders</SectionTitle>
      {upcoming.length === 0 && <Card><Text style={font.small}>No reminders yet.</Text></Card>}
      {upcoming.slice(0, 8).map((r) => (
        <Card key={r.id} style={{ paddingVertical: 12 }}>
          <View style={s.row}>
            <Text style={font.h3}>{r.kind === 'medication' ? '💊' : r.kind === 'appointment' ? '🩺' : '📌'} {r.title}</Text>
            {r.recurrence ? <Pill text="daily" tone="primary" /> : null}
          </View>
          <Text style={font.small}>{r.label} · {r.body}</Text>
        </Card>
      ))}
      <Text style={[font.tiny, { marginTop: 8, color: C.muted }]}>Taken / skipped responses are patient self-reports, not verified intake.</Text>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
});
