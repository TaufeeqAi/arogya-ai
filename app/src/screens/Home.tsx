import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { get } from '../api';
import { Btn, Card, Pill, SectionTitle, TrustBadge } from '../components/ui';
import { useLayout, useNav } from '../nav';
import { useStore } from '../store';
import { C, R, font, shadow } from '../theme';

const ACTION_LABEL: Record<string, string> = {
  book_appointment: 'Appointment booking',
  share_records: 'Record sharing',
  medication_reminders: 'Medicine reminders',
  refill_order: 'Refill order',
};

export default function Home() {
  const { go } = useNav();
  const { dataVersion, send, startVoice, voice } = useStore();
  const { contentWidth } = useLayout();
  const two = contentWidth >= 900;
  const [h, setH] = useState<any>(null);
  const [err, setErr] = useState('');
  useEffect(() => {
    get('/api/home').then((x) => { setH(x); setErr(''); }).catch((e) => setErr(e.message));
  }, [dataVersion]);

  const ask = (q: string) => {
    go('talk');
    send(q);
  };
  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });
  const attention = h ? h.pending_approvals.length + h.open_follow_ups.length + h.low_supply.length : 0;

  const Col = ({ children }: { children: React.ReactNode }) => <View style={[{ gap: 12 }, two && { flex: 1 }]}>{children}</View>;

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.tiny}>{today.toUpperCase()}</Text>
      <Text style={[font.h1, { marginTop: 2 }]}>नमस्ते, {h?.patient.first_name || 'Sunita'} जी</Text>
      <Text style={[font.small, { marginBottom: 14 }]}>Here is your health today.</Text>
      {err ? <Card><Text style={font.small}>Could not load your summary: {err}</Text></Card> : null}

      <Pressable onPress={() => { go('talk'); if (voice !== 'live') startVoice(); }} style={({ pressed }) => [s.hero, pressed && { opacity: 0.9 }]}>
        <View style={s.heroMic}><Text style={{ fontSize: 26 }}>🎙</Text></View>
        <View style={{ flex: 1 }}>
          <Text style={s.heroTitle}>Talk to Aarogya</Text>
          <Text style={s.heroSub}>Hindi, Hinglish or English — reports, doctors, medicines</Text>
        </View>
        <Text style={{ color: '#fff', fontSize: 22 }}>›</Text>
      </Pressable>

      <View style={[{ gap: 12, marginTop: 12 }, two && { flexDirection: 'row', alignItems: 'flex-start' }]}>
        <Col>
          <Card tone={h?.next_appointment ? 'ok' : undefined}>
            <Text style={font.tiny}>NEXT APPOINTMENT</Text>
            {h?.next_appointment ? (
              <>
                <Text style={[font.h2, { marginTop: 4 }]}>{h.next_appointment.doctor_name}</Text>
                <Text style={font.body}>{h.next_appointment.label}</Text>
                <Text style={font.small}>{h.next_appointment.clinic}, {h.next_appointment.area} · ref {h.next_appointment.booking_ref}</Text>
              </>
            ) : (
              <>
                <Text style={[font.body, { marginTop: 4 }]}>No upcoming visit.</Text>
                <View style={{ marginTop: 8 }}>
                  <Btn small kind="soft" title="Book a doctor" onPress={() => ask('Doctor ka appointment chahiye')} />
                </View>
              </>
            )}
          </Card>

          <Card>
            <View style={s.row}>
              <Text style={font.tiny}>TODAY'S REMINDERS</Text>
              <Pressable onPress={() => go('notifications')}><Text style={s.link}>Settings</Text></Pressable>
            </View>
            {h && h.today_reminders.length === 0 && (
              <>
                <Text style={[font.small, { marginTop: 6 }]}>No reminders today.</Text>
                <View style={{ marginTop: 8 }}>
                  <Btn small kind="soft" title="Set medicine reminders" onPress={() => ask('Meri dawaiyon ka reminder laga do')} />
                </View>
              </>
            )}
            {h?.today_reminders.map((r: any) => (
              <View key={r.id} style={s.item}>
                <Text style={{ fontSize: 18 }}>{r.kind === 'medication' ? '💊' : '🩺'}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={font.h3}>{r.title}</Text>
                  <Text style={font.small}>{r.time}</Text>
                </View>
                <Pill text={r.status} tone={r.status === 'taken' ? 'ok' : r.status === 'skipped' ? 'danger' : 'neutral'} />
              </View>
            ))}
          </Card>

          <Card tone={attention ? 'warn' : undefined}>
            <Text style={font.tiny}>NEEDS YOUR ATTENTION{attention ? ` · ${attention}` : ''}</Text>
            {h && attention === 0 && <Text style={[font.small, { marginTop: 6 }]}>All caught up. ✓</Text>}
            {h?.pending_approvals.map((a: any) => (
              <Pressable key={a.approval_id} onPress={() => go('talk')} style={s.item}>
                <Text style={{ fontSize: 18 }}>⏳</Text>
                <View style={{ flex: 1 }}>
                  <Text style={font.h3}>{ACTION_LABEL[a.action] || a.action} awaits approval</Text>
                  <Text style={font.small}>{a.label}</Text>
                </View>
              </Pressable>
            ))}
            {h?.open_follow_ups.map((t: any) => (
              <Pressable key={t.task_id} onPress={() => ask('Mere pending follow-ups kya hain?')} style={s.item}>
                <Text style={{ fontSize: 18 }}>📌</Text>
                <View style={{ flex: 1 }}>
                  <Text style={font.h3}>{t.title}</Text>
                  <Text style={font.small}>Doctor-advised · due {t.due}</Text>
                </View>
                <Pill text={t.status} tone={t.status === 'overdue' ? 'danger' : 'warn'} />
              </Pressable>
            ))}
            {h?.low_supply.map((m: any) => (
              <Pressable key={m.name} onPress={() => ask(`${m.name} khatam hone wali hai, refill order kar do`)} style={s.item}>
                <Text style={{ fontSize: 18 }}>📦</Text>
                <View style={{ flex: 1 }}>
                  <Text style={font.h3}>{m.name} {m.strength}: ~{m.days} days left</Text>
                  <Text style={font.small}>Tap to request a refill (needs your approval)</Text>
                </View>
              </Pressable>
            ))}
          </Card>
        </Col>

        <Col>
          <Card tone="info">
            <View style={s.row}>
              <Text style={font.tiny}>KEY RESULTS · LATEST VS PREVIOUS</Text>
              <Pressable onPress={() => go('records')}><Text style={s.link}>Records</Text></Pressable>
            </View>
            {h?.key_results.map((k: any) => (
              <View key={k.test_name} style={s.item}>
                <View style={{ flex: 1 }}>
                  <Text style={font.h3}>{k.test_name}</Text>
                  <Text style={font.tiny}>{k.flag}</Text>
                </View>
                <Text style={font.body}>
                  {k.previous} → <Text style={{ fontWeight: '800' }}>{k.latest}</Text> <Text style={font.small}>{k.unit}</Text>
                </Text>
              </View>
            ))}
            {h && h.key_results.length === 0 && <Text style={font.small}>Upload two reports to see changes over time.</Text>}
            <View style={{ marginTop: 8 }}>
              <Btn small kind="soft" title="Explain my latest report" onPress={() => ask('Meri latest blood report samjhao')} />
            </View>
          </Card>

          <Card>
            <View style={s.row}>
              <Text style={font.tiny}>RECENT DOCUMENTS</Text>
              <Pressable onPress={() => go('records')}><Text style={s.link}>Health Locker</Text></Pressable>
            </View>
            {h?.recent_documents.map((d: any) => (
              <Pressable key={d.id} onPress={() => go('records')} style={s.item}>
                <Text style={{ fontSize: 18 }}>{d.doc_type === 'lab_report' ? '🧪' : d.doc_type === 'prescription' ? '💊' : '📄'}</Text>
                <View style={{ flex: 1, gap: 3 }}>
                  <Text style={font.h3} numberOfLines={1}>{d.title}</Text>
                  <TrustBadge label={d.trust_label} />
                </View>
              </Pressable>
            ))}
          </Card>

          <Pressable onPress={() => go('timeline')}>
            <Card style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <Text style={{ fontSize: 22 }}>🕒</Text>
              <View style={{ flex: 1 }}>
                <Text style={font.h3}>Care timeline</Text>
                <Text style={font.small}>Reports, visits, medicines, follow-ups and sharing — in one history</Text>
              </View>
              <Text style={{ color: C.muted, fontSize: 20 }}>›</Text>
            </Card>
          </Pressable>
        </Col>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 1100, width: '100%', alignSelf: 'center' },
  hero: { flexDirection: 'row', alignItems: 'center', gap: 14, backgroundColor: C.primary, borderRadius: R.lg, padding: 18, ...shadow },
  heroMic: { width: 52, height: 52, borderRadius: 26, backgroundColor: C.primaryDark, alignItems: 'center', justifyContent: 'center' },
  heroTitle: { color: '#fff', fontSize: 19, fontWeight: '800' },
  heroSub: { color: '#CDE9E4', fontSize: 13, marginTop: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  link: { color: C.primary, fontWeight: '700', fontSize: 13 },
  item: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 9, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
});
