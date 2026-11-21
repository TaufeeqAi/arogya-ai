import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { get } from '../api';
import { Card, Pill, SourceChip } from '../components/ui';
import { useStore } from '../store';
import { C, font } from '../theme';

const FILTERS: [string, string][] = [
  ['all', 'All'],
  ['document', 'Reports & documents'],
  ['appointment', 'Visits'],
  ['medication', 'Medicines'],
  ['follow_up', 'Follow-ups'],
  ['sharing', 'Sharing'],
  ['action', 'Actions'],
];

const tone = (s: string) =>
  ['done', 'confirmed', 'processed', 'taken', 'active', 'reminders_active', 'booked'].includes(s) ? 'ok'
    : ['overdue', 'failed', 'skipped', 'cancelled', 'revoked'].includes(s) ? 'danger'
      : ['open', 'needs_review', 'needs_clarification', 'pending'].includes(s) ? 'warn' : 'neutral';

export default function Timeline() {
  const { dataVersion } = useStore();
  const [items, setItems] = useState<any[] | null>(null);
  const [filter, setFilter] = useState('all');
  const [err, setErr] = useState('');
  useEffect(() => {
    get('/api/timeline').then((x) => { setItems(x); setErr(''); }).catch((e) => setErr(e.message));
  }, [dataVersion]);

  const groups = useMemo(() => {
    const out: [string, any[]][] = [];
    for (const e of (items || []).filter((x) => filter === 'all' || x.type === filter)) {
      const month = new Date(e.ts).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
      const g = out.find((x) => x[0] === month);
      g ? g[1].push(e) : out.push([month, [e]]);
    }
    return out;
  }, [items, filter]);

  return (
    <ScrollView contentContainerStyle={s.page}>
      <Text style={font.h1}>Care timeline</Text>
      <Text style={[font.small, { marginBottom: 12 }]}>Everything that happened in your care — each entry links to its source.</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingBottom: 12 }}>
        {FILTERS.map(([k, label]) => (
          <Pressable key={k} onPress={() => setFilter(k)} style={[s.chip, filter === k && s.chipOn]}>
            <Text style={[s.chipText, filter === k && { color: '#fff' }]}>{label}</Text>
          </Pressable>
        ))}
      </ScrollView>
      {err ? <Card><Text style={font.small}>Could not load the timeline: {err}</Text></Card> : null}
      {!err && items === null && <Card><Text style={font.small}>Loading your history…</Text></Card>}
      {!err && items !== null && groups.length === 0 && <Card><Text style={font.small}>Nothing here yet.</Text></Card>}
      {groups.map(([month, evs]) => (
        <View key={month} style={{ marginBottom: 8 }}>
          <Text style={[font.tiny, { marginVertical: 8 }]}>{month.toUpperCase()}</Text>
          {evs.map((e: any, i: number) => (
            <View key={`${e.ts}-${i}`} style={s.row}>
              <View style={s.rail}>
                <View style={[s.dot, e.future && { backgroundColor: C.surface, borderWidth: 2, borderColor: C.primary }]}>
                  <Text style={{ fontSize: 13 }}>{e.icon}</Text>
                </View>
                {i < evs.length - 1 && <View style={s.line} />}
              </View>
              <Card style={{ flex: 1, paddingVertical: 12 }}>
                <View style={s.head}>
                  <Text style={[font.h3, { flex: 1 }]}>{e.title}</Text>
                  {e.future ? <Pill text="upcoming" tone="info" /> : null}
                  {e.status ? <Pill text={String(e.status).replace(/_/g, ' ')} tone={tone(e.status) as any} /> : null}
                </View>
                <Text style={font.small}>{e.detail}</Text>
                <View style={[s.head, { marginTop: 6 }]}>
                  <Text style={font.tiny}>{e.label}</Text>
                  {e.document_id ? <SourceChip documentId={e.document_id} title="Source" /> : null}
                </View>
              </Card>
            </View>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 820, width: '100%', alignSelf: 'center' },
  chip: { borderWidth: 1.5, borderColor: C.line, borderRadius: 99, paddingHorizontal: 12, paddingVertical: 7, backgroundColor: C.surface },
  chipOn: { backgroundColor: C.primary, borderColor: C.primary },
  chipText: { fontWeight: '700', color: C.inkSoft, fontSize: 13 },
  row: { flexDirection: 'row', gap: 10 },
  rail: { width: 30, alignItems: 'center' },
  dot: { width: 30, height: 30, borderRadius: 15, backgroundColor: C.primarySoft, alignItems: 'center', justifyContent: 'center', marginTop: 10 },
  line: { flex: 1, width: 2, backgroundColor: C.line, marginTop: 2 },
  head: { flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'space-between' },
});
