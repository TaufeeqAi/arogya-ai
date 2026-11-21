import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { get } from '../api';
import { Btn, Card, Pill, SourceChip } from '../components/ui';
import { useLayout, useNav } from '../nav';
import { useStore } from '../store';
import { C, R, font, shadow } from '../theme';

const short = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
const long = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

export function SystemIcon({ k, emoji, size = 22 }: { k: string; emoji: string; size?: number }) {
  if (k === 'liver')
    return (
      <Svg width={size} height={size} viewBox="0 0 64 64">
        <Path d="M5 30 C5 15 22 9 39 11 C52 12 61 18 59 27 C57 35 45 36 37 44 C31 50 20 55 12 49 C7 45 5 38 5 30 Z" fill="#B5523B" />
        <Path d="M30 13 C28 24 31 34 37 43" stroke="#8E3B28" strokeWidth={2} fill="none" />
        <Circle cx={33} cy={46} r={4.5} fill="#7BAF4E" />
      </Svg>
    );
  if (k === 'kidney')
    return (
      <Svg width={size} height={size} viewBox="0 0 64 64">
        <Path d="M20 8 C8 8 3 22 5 34 C7 47 17 56 25 51 C31 47 27 39 23 33 C20 27 29 23 29 16 C29 11 25 8 20 8 Z" fill="#B8504F" />
        <Path d="M44 8 C56 8 61 22 59 34 C57 47 47 56 39 51 C33 47 37 39 41 33 C44 27 35 23 35 16 C35 11 39 8 44 8 Z" fill="#B8504F" />
      </Svg>
    );
  return <Text style={{ fontSize: size * 0.78 }}>{emoji}</Text>;
}

export function statusText(s: string) {
  return s === 'needs_attention' ? 'Needs attention' : s === 'within_range' ? 'Within lab range' : 'No data yet';
}

function Figure({ height }: { height: number }) {
  // Neutral, stylised human silhouette (illustrative only)
  return (
    <Svg width={height * 0.48} height={height} viewBox="0 0 200 420">
      <Circle cx={100} cy={46} r={30} fill="#F4E2BE" stroke="#E2C792" strokeWidth={2} />
      <Rect x={88} y={72} width={24} height={18} rx={6} fill="#F4E2BE" />
      <Path d="M58 92 Q100 80 142 92 L168 108 Q178 114 176 126 L168 214 Q166 224 157 222 L150 220 L154 130 L146 124 L146 232 L54 232 L54 124 L46 130 L50 220 L43 222 Q34 224 32 214 L24 126 Q22 114 32 108 Z"
        fill="#F4E2BE" stroke="#E2C792" strokeWidth={2} />
      <Path d="M56 230 L144 230 L140 398 Q139 410 127 410 L113 410 L104 262 L96 262 L87 410 L73 410 Q61 410 60 398 Z"
        fill="#F1DCB2" stroke="#E2C792" strokeWidth={2} />
      <Path d="M70 150 Q100 162 130 150" stroke="#E2C792" strokeWidth={1.5} fill="none" strokeDasharray="4 4" />
      <Path d="M100 100 L100 228" stroke="#E2C792" strokeWidth={1.5} fill="none" strokeDasharray="4 4" />
    </Svg>
  );
}

function SystemChip({ x, onPress }: { x: any; onPress: () => void }) {
  const att = x.status === 'needs_attention';
  const none = x.status === 'no_data';
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={`${x.label}: ${statusText(x.status)}`}
      style={({ pressed }) => [s.chip, att ? s.chipAtt : none ? s.chipNone : s.chipOk, pressed && { opacity: 0.85 }]}>
      <SystemIcon k={x.key} emoji={x.icon} />
      <View style={{ flex: 1 }}>
        <Text style={s.chipLabel} numberOfLines={1}>{x.label}</Text>
        <Text style={[s.chipSub, att && { color: '#9A5A16' }]}>{att ? `${x.attention_count} outside range` : none ? 'No data' : 'Within range'}</Text>
      </View>
      <View style={[s.arrow, { backgroundColor: att ? C.saffron : none ? C.muted : C.ok }]}><Text style={{ color: '#fff', fontWeight: '900' }}>›</Text></View>
    </Pressable>
  );
}

function AttentionCard({ title, body, onBook, onAsk, askLabel }: { title: string; body: string; onBook: () => void; onAsk: () => void; askLabel: string }) {
  return (
    <View style={s.att}>
      <Text style={s.attTitle}>{title}</Text>
      <Text style={s.attBody}>{body}</Text>
      <View style={{ gap: 8, marginTop: 12 }}>
        <Pressable onPress={onBook} style={({ pressed }) => [s.attBtn, pressed && { opacity: 0.85 }]}>
          <Text style={{ color: '#fff', fontWeight: '800', fontSize: 15 }}>Book consultation</Text>
        </Pressable>
        <Pressable onPress={onAsk} style={({ pressed }) => [s.attGhost, pressed && { opacity: 0.85 }]}>
          <Text style={{ color: '#fff', fontWeight: '700' }}>{askLabel}</Text>
        </Pressable>
      </View>
      <Text style={s.attNote}>Based on the lab's printed reference ranges — not a diagnosis.</Text>
    </View>
  );
}

function TestRow({ t }: { t: any }) {
  const [open, setOpen] = useState(false);
  const out = t.status !== 'within';
  return (
    <View style={s.test}>
      <View style={s.testHead}>
        <Pressable onPress={() => setOpen(!open)} style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 }} accessibilityRole="button" accessibilityLabel={`About ${t.name}`}>
          <Text style={[font.body, { fontWeight: '600', flexShrink: 1 }]}>{t.name}</Text>
          <View style={s.info}><Text style={{ fontSize: 11, color: C.inkSoft, fontWeight: '800' }}>i</Text></View>
        </Pressable>
        <Text style={[font.body, { fontWeight: '800' }]}>{t.value} <Text style={font.small}>{t.unit}</Text></Text>
      </View>
      <View style={s.testHead}>
        <Text style={font.small}>Lab range: {t.reference_range} {t.unit}</Text>
        <Text style={{ fontWeight: '700', fontSize: 13, color: out ? '#B8741A' : C.ok }}>
          {t.status === 'above' ? 'Above lab range' : t.status === 'below' ? 'Below lab range' : 'Within lab range'}
        </Text>
      </View>
      {open && <Text style={[font.small, s.about]}>{t.about}</Text>}
      {t.history.length > 1 && (
        <Text style={[font.tiny, { marginTop: 4 }]}>
          {t.history.map((h: any) => `${short(h.date)}: ${h.value}`).join('  ·  ')}
          {t.direction ? `   ${t.direction === 'up' ? '▲' : t.direction === 'down' ? '▼' : '='}` : ''}
        </Text>
      )}
    </View>
  );
}

export function SystemDetail({ x, onBack }: { x: any; onBack?: () => void }) {
  const { go } = useNav();
  const { send } = useStore();
  const ask = (q: string) => { go('talk'); send(q); };
  const att = x.status === 'needs_attention';
  const docs: any[] = Object.values(Object.fromEntries(x.tests.map((t: any) => [t.source.document_id, t.source])));
  return (
    <ScrollView contentContainerStyle={s.page}>
      {onBack && (
        <Pressable onPress={onBack} style={s.back} accessibilityRole="button" accessibilityLabel="Back to health overview">
          <Text style={{ color: C.primary, fontSize: 22, fontWeight: '700' }}>‹</Text>
        </Pressable>
      )}
      <View style={s.hero}>
        <View style={s.heroIcon}><SystemIcon k={x.key} emoji={x.icon} size={78} /></View>
        <Text style={s.heroTitle}>{x.label.toUpperCase()}</Text>
        <Text style={font.small}>{x.subtitle} · last tested {x.last_tested ? long(x.last_tested) : '—'}</Text>
        <View style={[s.badge, att ? s.badgeAtt : s.badgeOk]}>
          <Text style={{ fontWeight: '800', color: att ? '#9A5A16' : C.ok, letterSpacing: 0.5 }}>{statusText(x.status).toUpperCase()}</Text>
        </View>
      </View>
      {att && (
        <AttentionCard
          title="Your test result needs attention"
          body={`${x.attention_count} of ${x.test_count} ${x.label.toLowerCase()} values are outside the lab's printed range. A doctor can explain what this means for you and the next steps.`}
          onBook={() => ask(`Mujhe ${x.label} ke results doctor ko dikhane hain, consultation book karni hai`)}
          onAsk={() => ask(`Meri ${x.label} report samjhao, kya attention chahiye aur doctor se kya poochun?`)}
          askLabel={`Ask Aarogya to explain my ${x.label.toLowerCase()} results`}
        />
      )}
      <Card style={{ marginTop: 14 }}>
        {x.tests.map((t: any) => <TestRow key={t.code} t={t} />)}
        {x.tests.length === 0 && <Text style={font.small}>No results yet. Upload a report to see this area.</Text>}
      </Card>
      {!att && x.tests.length > 0 && (
        <Btn kind="soft" title={`Ask Aarogya about my ${x.label.toLowerCase()} results`} onPress={() => ask(`Meri ${x.label} report samjhao`)} />
      )}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
        {docs.map((d: any) => <SourceChip key={d.document_id} documentId={d.document_id} title={d.title} />)}
      </View>
      <Text style={[font.tiny, { marginTop: 10 }]}>Tap ⓘ to see what a test measures. Aarogya explains reports; it does not diagnose.</Text>
    </ScrollView>
  );
}

export default function Health() {
  const { dataVersion, send } = useStore();
  const { go } = useNav();
  const { contentWidth } = useLayout();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState('');
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => {
    get('/api/health-status').then((d) => { setData(d); setErr(''); }).catch((e) => setErr(e.message));
  }, [dataVersion]);
  const ask = (q: string) => { go('talk'); send(q); };

  if (sel && data) {
    const x = data.systems.find((y: any) => y.key === sel);
    if (x) return <SystemDetail x={x} onBack={() => setSel(null)} />;
  }
  const sys: any[] = data?.systems || [];
  const left = sys.filter((_, i) => i % 2 === 0);
  const right = sys.filter((_, i) => i % 2 === 1);
  const wide = contentWidth >= 760;
  const att = data?.attention_systems || [];

  return (
    <ScrollView contentContainerStyle={[s.page, { maxWidth: 980 }]}>
      <View style={s.headRow}>
        <View style={s.avatar}><Text style={{ color: '#fff', fontWeight: '800', fontSize: 18 }}>SS</Text></View>
        <View style={{ flex: 1 }}>
          <Text style={font.h2}>{data ? `${data.patient.name} · ${data.patient.age} ${data.patient.sex === 'F' ? 'Female' : 'Male'}` : 'Health status'}</Text>
          {data && (
            <Text style={{ fontWeight: '800', color: data.overall === 'needs_attention' ? '#B8741A' : C.ok, letterSpacing: 0.4 }}>
              {data.overall === 'needs_attention' ? `NEEDS ATTENTION · ${att.length} AREAS` : 'ALL WITHIN LAB RANGE'}
            </Text>
          )}
        </View>
      </View>
      {err ? <Card><Text style={font.small}>Could not load health status: {err}</Text></Card> : null}
      {!data && !err && <Card><Text style={font.small}>Loading your health overview…</Text></Card>}

      {data && (
        <View style={[s.bodyArea, { minHeight: wide ? 470 : 430 }]}>
          <View style={s.figure} pointerEvents="none"><Figure height={wide ? 450 : 410} /></View>
          <View style={[s.col, { width: wide ? 250 : '48%' }]}>{left.map((x) => <SystemChip key={x.key} x={x} onPress={() => setSel(x.key)} />)}</View>
          <View style={[s.col, { width: wide ? 250 : '48%' }]}>{right.map((x) => <SystemChip key={x.key} x={x} onPress={() => setSel(x.key)} />)}</View>
        </View>
      )}

      {data && att.length > 0 && (
        <AttentionCard
          title="Your test results need attention"
          body={`Some recent values in ${att.join(', ')} are outside the lab's printed range. Talk to a doctor for advice and next steps.`}
          onBook={() => ask('Meri reports mein kuch values range se bahar hain, doctor ka consultation book karna hai')}
          onAsk={() => ask('Meri reports mein kya attention chahiye aur doctor se kya poochna chahiye?')}
          askLabel="What should I ask my doctor?"
        />
      )}
      {data && (
        <Text style={[font.tiny, { marginTop: 12, textAlign: 'center' }]}>
          Built from {data.report_count} lab reports in your Health Locker · tap an area for details
        </Text>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40, maxWidth: 760, width: '100%', alignSelf: 'center' },
  headRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 6 },
  avatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  bodyArea: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 10, backgroundColor: '#FFF6E6', borderRadius: R.xl, padding: 12 },
  figure: { position: 'absolute', left: 0, right: 0, top: 10, alignItems: 'center', opacity: 0.95 },
  col: { gap: 14, justifyContent: 'center' },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 16, paddingVertical: 10, paddingHorizontal: 10, borderWidth: 1.5, ...shadow },
  chipOk: { backgroundColor: '#E2F6EC', borderColor: '#9AD8B6' },
  chipAtt: { backgroundColor: '#FFF1DC', borderColor: C.saffron, borderBottomWidth: 4 },
  chipNone: { backgroundColor: C.surface, borderColor: C.line },
  chipLabel: { fontWeight: '800', color: C.ink, fontSize: 14.5 },
  chipSub: { fontSize: 11.5, color: C.ok, fontWeight: '600' },
  arrow: { width: 24, height: 24, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  att: { backgroundColor: '#14234A', borderRadius: R.lg, padding: 18, marginTop: 8, ...shadow },
  attTitle: { color: '#F7B5C8', fontWeight: '800', fontSize: 16, textAlign: 'center', letterSpacing: 0.3 },
  attBody: { color: '#fff', fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 8 },
  attBtn: { backgroundColor: '#1F5BFF', borderRadius: 99, paddingVertical: 13, alignItems: 'center' },
  attGhost: { borderWidth: 1.5, borderColor: '#5A6B9A', borderRadius: 99, paddingVertical: 11, alignItems: 'center' },
  attNote: { color: '#A9B4D6', fontSize: 11, textAlign: 'center', marginTop: 10 },
  back: { width: 44, height: 44, borderRadius: 22, borderWidth: 1.5, borderColor: C.primary, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  hero: { alignItems: 'center', backgroundColor: '#FFF6E6', borderRadius: R.xl, paddingVertical: 20, paddingHorizontal: 16, gap: 6 },
  heroIcon: { width: 120, height: 120, borderRadius: 24, backgroundColor: C.surface, alignItems: 'center', justifyContent: 'center', ...shadow },
  heroTitle: { fontSize: 26, fontWeight: '900', letterSpacing: 3, color: C.ink, marginTop: 8 },
  badge: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 10, borderWidth: 1.5, marginTop: 6, borderBottomWidth: 3 },
  badgeAtt: { backgroundColor: '#FFF1DC', borderColor: C.saffron },
  badgeOk: { backgroundColor: '#E2F6EC', borderColor: '#9AD8B6' },
  test: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: C.line, borderStyle: 'dashed', gap: 4 },
  testHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
  info: { width: 18, height: 18, borderRadius: 9, borderWidth: 1.2, borderColor: C.muted, alignItems: 'center', justifyContent: 'center' },
  about: { backgroundColor: C.surfaceAlt, borderRadius: 8, padding: 8, marginTop: 4 },
});
