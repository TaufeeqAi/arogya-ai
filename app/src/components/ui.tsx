import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { url } from '../api';
import { C, R, font, shadow } from '../theme';

export function Card({ children, style, tone }: { children: React.ReactNode; style?: ViewStyle; tone?: 'ok' | 'warn' | 'danger' | 'info' }) {
  const border = tone === 'ok' ? C.ok : tone === 'warn' ? C.saffron : tone === 'danger' ? C.danger : tone === 'info' ? C.primary : 'transparent';
  return <View style={[s.card, tone && { borderLeftWidth: 4, borderLeftColor: border }, style]}>{children}</View>;
}

export function Pill({ text, tone = 'neutral' }: { text: string; tone?: 'neutral' | 'ok' | 'warn' | 'danger' | 'info' | 'primary' }) {
  const map = {
    neutral: [C.surfaceAlt, C.inkSoft],
    ok: [C.okSoft, C.ok],
    warn: [C.saffronSoft, '#9A5A16'],
    danger: [C.dangerSoft, C.danger],
    info: [C.infoSoft, C.info],
    primary: [C.primarySoft, C.primaryDark],
  } as const;
  const [bg, fg] = map[tone];
  return (
    <View style={[s.pill, { backgroundColor: bg }]}>
      <Text style={[s.pillText, { color: fg }]}>{text}</Text>
    </View>
  );
}

export function Btn({ title, onPress, kind = 'primary', disabled, small }: { title: string; onPress?: () => void; kind?: 'primary' | 'ghost' | 'danger' | 'soft'; disabled?: boolean; small?: boolean }) {
  const bg = kind === 'primary' ? C.primary : kind === 'danger' ? C.danger : kind === 'soft' ? C.primarySoft : 'transparent';
  const fg = kind === 'primary' || kind === 'danger' ? '#fff' : C.primaryDark;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        s.btn,
        small && { paddingVertical: 8, paddingHorizontal: 12 },
        { backgroundColor: bg, opacity: disabled ? 0.45 : pressed ? 0.8 : 1 },
        kind === 'ghost' && { borderWidth: 1.5, borderColor: C.line },
      ]}
    >
      <Text style={[s.btnText, { color: fg }, small && { fontSize: 13 }]}>{title}</Text>
    </Pressable>
  );
}

export function SourceChip({ documentId, title }: { documentId: string; title: string }) {
  return (
    <Pressable onPress={() => Linking.openURL(url(`/api/documents/${documentId}/file`))} style={s.source}>
      <Text style={s.sourceText} numberOfLines={1}>📄 {title}</Text>
    </Pressable>
  );
}

export function TrustBadge({ label }: { label: string }) {
  const m: Record<string, [string, any]> = {
    provider_verified: ['Provider verified', 'ok'],
    patient_uploaded: ['Patient uploaded', 'warn'],
    ai_extracted: ['AI extracted · review', 'info'],
    patient_confirmed: ['Patient confirmed', 'primary'],
  };
  const [t, tone] = m[label] || [label, 'neutral'];
  return <Pill text={t} tone={tone} />;
}

export function SectionTitle({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <View style={s.section}>
      <Text style={font.h2}>{children}</Text>
      {right}
    </View>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.surface, borderRadius: R.lg, padding: 16, ...shadow, marginBottom: 12 },
  pill: { paddingHorizontal: 9, paddingVertical: 3.5, borderRadius: 99, alignSelf: 'flex-start' },
  pillText: { fontSize: 11.5, fontWeight: '700' },
  btn: { paddingVertical: 12, paddingHorizontal: 18, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  btnText: { fontWeight: '700', fontSize: 15 },
  source: { backgroundColor: C.surfaceAlt, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, alignSelf: 'flex-start', maxWidth: '100%' },
  sourceText: { fontSize: 12, color: C.primaryDark, fontWeight: '600' },
  section: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, marginBottom: 10 },
});
