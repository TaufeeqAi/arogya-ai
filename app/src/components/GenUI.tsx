/** Generative UI registry: the agent selects a component by name + typed props; no model-generated code runs. */
import React, { useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line, Rect, Text as SvgText } from 'react-native-svg';
import { post, url } from '../api';
import { C, font } from '../theme';
import { Btn, Card, Pill, SourceChip, TrustBadge } from './ui';

export type UIItem = { id: string; component: string; version: number; props: any };
export type GenCtx = {
  say: (text: string) => void;
  decide: (approvalId: string, decision: 'approve' | 'reject') => Promise<void>;
  approvals: Record<string, string>;
};

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

function RangeBar({ v, lo, hi }: { v: number; lo: number | null; hi: number | null }) {
  const L = lo ?? (hi ? hi * 0.4 : 0);
  const H = hi ?? (lo ? lo * 2 : 1);
  const min = Math.min(L - (H - L) * 0.5, v);
  const max = Math.max(H + (H - L) * 0.5, v);
  const x = (n: number) => ((n - min) / (max - min)) * 100;
  const out = (lo != null && v < lo) || (hi != null && v > hi);
  return (
    <Svg width="100%" height={14} viewBox="0 0 100 14" preserveAspectRatio="none">
      <Rect x={0} y={5} width={100} height={4} rx={2} fill={C.line} />
      <Rect x={x(L)} y={5} width={Math.max(2, x(H) - x(L))} height={4} rx={2} fill={C.primarySoft} />
      <Circle cx={Math.min(98, Math.max(2, x(v)))} cy={7} r={4.5} fill={out ? C.saffron : C.primary} />
    </Svg>
  );
}

function LabSummary({ p }: { p: any }) {
  const [all, setAll] = useState(false);
  const obs: any[] = p.observations || [];
  const flagged = obs.filter((o) => o.lab_flag !== 'within lab range');
  const shown = all ? obs : flagged.length ? flagged : obs.slice(0, 4);
  return (
    <Card tone="info">
      <Text style={font.tiny}>REPORT SUMMARY</Text>
      <Text style={[font.h3, { marginTop: 2 }]}>{p.document.title}</Text>
      <View style={st.row}>
        <Text style={font.small}>{p.document.source_name}</Text>
        <TrustBadge label={p.document.trust_label} />
      </View>
      <View style={[st.banner, { backgroundColor: flagged.length ? C.saffronSoft : C.okSoft }]}>
        <Text style={{ fontWeight: '700', color: flagged.length ? '#9A5A16' : C.ok }}>
          {flagged.length} of {obs.length} values outside the lab's printed range
        </Text>
      </View>
      {shown.map((o) => (
        <View key={o.observation_id} style={st.obs}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={[font.body, { flex: 1, fontWeight: '600' }]}>{o.test_name}</Text>
            <Text style={[font.body, { fontWeight: '800' }]}>
              {o.value} <Text style={font.small}>{o.unit}</Text>
            </Text>
          </View>
          <RangeBar v={o.value} lo={o.ref_low} hi={o.ref_high} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={font.tiny}>Lab range {o.reference_range}</Text>
            {o.lab_flag !== 'within lab range' && <Pill text={o.lab_flag} tone="warn" />}
          </View>
        </View>
      ))}
      <View style={[st.row, { marginTop: 8 }]}>
        <SourceChip documentId={p.document.id} title={`Source: ${p.document.title}, p.1`} />
        {obs.length > shown.length || all ? (
          <Pressable onPress={() => setAll(!all)}>
            <Text style={st.link}>{all ? 'Show less' : `All ${obs.length} values`}</Text>
          </Pressable>
        ) : null}
      </View>
      <Text style={[font.tiny, { marginTop: 8 }]}>Explains what the report states. Not a diagnosis.</Text>
    </Card>
  );
}

function Spark({ c }: { c: any }) {
  const pts = c.points as any[];
  const vals = pts.map((p) => p.value).concat([c.ref_low, c.ref_high].filter((x: any) => x != null));
  const min = Math.min(...vals) * 0.9;
  const max = Math.max(...vals) * 1.08;
  const W = 120, H = 46;
  const y = (v: number) => H - 6 - ((v - min) / (max - min)) * (H - 12);
  const x = (i: number) => 10 + (i * (W - 20)) / Math.max(1, pts.length - 1);
  const lo = c.ref_low ?? min, hi = c.ref_high ?? max;
  return (
    <Svg width={W} height={H}>
      <Rect x={0} y={y(Math.min(hi, max))} width={W} height={Math.max(0, y(Math.max(lo, min)) - y(Math.min(hi, max)))} fill={C.primarySoft} opacity={0.7} />
      {pts.slice(1).map((p, i) => (
        <Line key={i} x1={x(i)} y1={y(pts[i].value)} x2={x(i + 1)} y2={y(p.value)} stroke={C.ink} strokeWidth={2} />
      ))}
      {pts.map((p, i) => (
        <Circle key={i} cx={x(i)} cy={y(p.value)} r={4} fill={i === pts.length - 1 ? C.saffron : C.ink} />
      ))}
      <SvgText x={x(pts.length - 1)} y={Math.max(10, y(pts[pts.length - 1].value) - 7)} fontSize={9} fill={C.ink} textAnchor="end">
        {String(pts[pts.length - 1].value)}
      </SvgText>
    </Svg>
  );
}

function Comparison({ p }: { p: any }) {
  const comps: any[] = p.comparisons || [];
  const first = comps[0]?.points || [];
  return (
    <Card tone="info">
      <Text style={font.tiny}>HISTORICAL COMPARISON</Text>
      <Text style={[font.h3, { marginTop: 2 }]}>
        {first.length ? `${fmtDate(first[0].observed_on)} → ${fmtDate(first[first.length - 1].observed_on)}` : 'Your reports'}
      </Text>
      {comps.map((c) => {
        const up = c.direction === 'up', down = c.direction === 'down';
        return (
          <View key={c.test_code} style={st.cmp}>
            <View style={{ flex: 1 }}>
              <Text style={[font.body, { fontWeight: '600' }]}>{c.test_name}</Text>
              <Text style={font.small}>
                {c.previous} → <Text style={{ fontWeight: '800', color: C.ink }}>{c.latest}</Text> {c.unit}{' '}
                <Text style={{ color: up ? C.danger : down ? C.info : C.muted, fontWeight: '700' }}>
                  {up ? '▲' : down ? '▼' : '='} {c.change_pct != null ? `${Math.abs(c.change_pct)}%` : ''}
                </Text>
              </Text>
              <Text style={font.tiny}>Lab range {c.reference_range}</Text>
            </View>
            <Spark c={c} />
          </View>
        );
      })}
      {p.not_comparable?.length ? (
        <View style={[st.banner, { backgroundColor: C.surfaceAlt }]}>
          <Text style={font.small}>
            Not compared: {p.not_comparable.map((n: any) => `${n.test_name} (${n.reason})`).join('; ')}
          </Text>
        </View>
      ) : null}
      <View style={[st.row, { marginTop: 6, flexWrap: 'wrap', gap: 6 }]}>
        {first.map((pt: any) => (
          <SourceChip key={pt.source.document_id} documentId={pt.source.document_id} title={pt.source.title} />
        ))}
      </View>
      <Text style={[font.tiny, { marginTop: 8 }]}>{p.method}</Text>
    </Card>
  );
}

function DoctorSlots({ p, ctx }: { p: any; ctx: GenCtx }) {
  const d = p.doctor;
  return (
    <Card>
      <Text style={font.tiny}>AVAILABLE APPOINTMENTS{p.note ? ` · ${p.note.toUpperCase()}` : ''}</Text>
      <View style={[st.row, { marginTop: 6, alignItems: 'center' }]}>
        <View style={st.avatar}>
          <Text style={{ color: '#fff', fontWeight: '800' }}>{d.name.replace('Dr. ', '').split(' ').map((w: string) => w[0]).join('')}</Text>
        </View>
        <View style={{ flex: 1, marginLeft: 10 }}>
          <Text style={font.h3}>{d.name}</Text>
          <Text style={font.small}>{d.specialty ? `${d.specialty} · ` : ''}{d.clinic}, {d.area} · ₹{d.fee}</Text>
        </View>
      </View>
      <View style={st.slots}>
        {p.slots.map((s: any) => (
          <Pressable key={s.slot_id} onPress={() => ctx.say(`${s.label} wala slot book karna hai`)} style={({ pressed }) => [st.slot, pressed && { backgroundColor: C.primarySoft }]}>
            <Text style={{ fontWeight: '700', color: C.primaryDark }}>{s.label.split(', ')[1]}</Text>
            <Text style={font.tiny}>{s.label.split(', ')[0]}</Text>
          </Pressable>
        ))}
      </View>
      <Text style={font.tiny}>Live availability from clinic system · tap a slot or just say it</Text>
    </Card>
  );
}

function Approval({ p, ctx }: { p: any; ctx: GenCtx }) {
  const status = ctx.approvals[p.approval_id] || 'pending';
  const [busy, setBusy] = useState(false);
  const act = async (d: 'approve' | 'reject') => {
    setBusy(true);
    try {
      await ctx.decide(p.approval_id, d);
    } finally {
      setBusy(false);
    }
  };
  const tone = status === 'executed' ? 'ok' : status === 'failed' || status === 'rejected' ? 'danger' : 'warn';
  return (
    <Card tone={tone as any} style={{ backgroundColor: status === 'pending' ? '#FFFBF5' : C.surface }}>
      <View style={st.row}>
        <Text style={font.tiny}>NEEDS YOUR APPROVAL</Text>
        <Pill
          text={{ pending: 'Waiting for you', executed: 'Done ✓', failed: 'Could not complete', rejected: 'Cancelled', expired: 'Expired', approved: 'Approved' }[status] || status}
          tone={status === 'executed' ? 'ok' : status === 'pending' ? 'warn' : 'danger'}
        />
      </View>
      <Text style={[font.h3, { marginTop: 4 }]}>{p.summary.title}</Text>
      {p.summary.lines.map((l: string, i: number) => (
        <Text key={i} style={[font.body, { color: C.inkSoft }]}>• {l}</Text>
      ))}
      {status === 'pending' && (
        <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
          <View style={{ flex: 1 }}>
            <Btn title="Approve" onPress={() => act('approve')} disabled={busy} />
          </View>
          <View style={{ flex: 1 }}>
            <Btn title="Cancel" kind="ghost" onPress={() => act('reject')} disabled={busy} />
          </View>
        </View>
      )}
      {status === 'pending' && <Text style={[font.tiny, { marginTop: 8 }]}>Or say "haan, kar do". Bound to these exact details · expires in 10 min</Text>}
    </Card>
  );
}

function BookingConfirmation({ p }: { p: any }) {
  return (
    <Card tone="ok">
      <View style={st.row}>
        <Text style={font.tiny}>APPOINTMENT CONFIRMED</Text>
        <Pill text="Verified with clinic" tone="ok" />
      </View>
      <Text style={[font.h2, { marginTop: 4 }]}>{p.doctor_name}</Text>
      <Text style={font.body}>{p.label}</Text>
      <Text style={font.small}>{p.clinic}, {p.area}{p.fee ? ` · ₹${p.fee}` : ''}</Text>
      <View style={[st.banner, { backgroundColor: C.okSoft, flexDirection: 'row', justifyContent: 'space-between' }]}>
        <Text style={{ color: C.ok, fontWeight: '700' }}>Booking ref</Text>
        <Text style={{ color: C.ok, fontWeight: '800', letterSpacing: 1 }}>{p.booking_ref}</Text>
      </View>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <View style={{ flex: 1 }}>
          <Btn small kind="soft" title="📅 Google Calendar" onPress={() => Linking.openURL(p.calendar_url)} />
        </View>
        <View style={{ flex: 1 }}>
          <Btn small kind="soft" title="⬇ .ics file" onPress={() => Linking.openURL(url(p.ics_url))} />
        </View>
      </View>
      <Text style={[font.tiny, { marginTop: 8 }]}>Reminders scheduled: 1 day before and 2 hours before</Text>
    </Card>
  );
}

function ShareConfirmation({ p }: { p: any }) {
  return (
    <Card tone="ok">
      <Text style={font.tiny}>RECORDS SHARED WITH CONSENT</Text>
      <Text style={[font.h3, { marginTop: 4 }]}>{p.doctor_name}</Text>
      {p.documents.map((d: string) => (
        <Text key={d} style={font.body}>📄 {d}</Text>
      ))}
      <Text style={[font.tiny, { marginTop: 6 }]}>Access expires {fmtDate(p.expires_at)} · revocable anytime</Text>
    </Card>
  );
}

function Medication({ p }: { p: any }) {
  return (
    <Card tone="info">
      <Text style={font.tiny}>MEDICINES ON RECORD</Text>
      {p.medications.map((m: any) => {
        const unclear = m.status === 'needs_clarification';
        return (
          <View key={m.medication_id} style={[st.obs, p.highlight === m.medication_id && { backgroundColor: C.okSoft, borderRadius: 10, padding: 8 }]}>
            <View style={st.row}>
              <Text style={font.h3}>{m.name} {m.strength}</Text>
              <Pill
                text={unclear ? 'Needs clarification' : m.status === 'reminders_active' ? 'Reminders on' : 'Verified'}
                tone={unclear ? 'danger' : m.status === 'reminders_active' ? 'ok' : 'primary'}
              />
            </View>
            <Text style={font.small}>{m.frequency || 'Frequency not on source'} · {m.instructions}</Text>
            {m.times?.length ? (
              <View style={{ flexDirection: 'row', gap: 6, marginTop: 4 }}>
                {m.times.map((t: string) => (
                  <Pill key={t} text={`⏰ ${t}`} tone="neutral" />
                ))}
              </View>
            ) : null}
            {m.supply_left_days <= 5 && !unclear ? <Text style={[font.small, { color: C.danger, marginTop: 4 }]}>Only ~{m.supply_left_days} days of supply left</Text> : null}
            <View style={{ marginTop: 4 }}>
              <SourceChip documentId={m.source.document_id} title={m.source.title} />
            </View>
          </View>
        );
      })}
      <Text style={[font.tiny, { marginTop: 6 }]}>Aarogya never changes doses. Unclear instructions must be confirmed by your doctor or pharmacist.</Text>
    </Card>
  );
}

function DoctorBrief({ p }: { p: any }) {
  const Sec = ({ t, items }: { t: string; items: string[] }) => (
    <View style={{ marginTop: 8 }}>
      <Text style={[font.small, { fontWeight: '800', color: C.primaryDark }]}>{t}</Text>
      {items.map((i) => (
        <Text key={i} style={font.body}>• {i}</Text>
      ))}
    </View>
  );
  return (
    <Card tone="info">
      <Text style={font.tiny}>PRE-CONSULTATION BRIEF</Text>
      <Text style={[font.h3, { marginTop: 2 }]}>{p.patient}</Text>
      <Sec t="Conditions" items={p.conditions} />
      <Sec t="Allergies" items={p.allergies} />
      <Sec t="Medicines" items={p.medications} />
      <Sec t="Changed since last report" items={p.changes_since_last_report} />
      <Sec t="Questions to ask" items={p.questions} />
      <Text style={[font.tiny, { marginTop: 8 }]}>Sources: {p.sources.join(' · ')}</Text>
    </Card>
  );
}

function Order({ p }: { p: any }) {
  return (
    <Card tone="ok">
      <Text style={font.tiny}>REFILL ORDER PLACED (SANDBOX)</Text>
      <Text style={[font.h3, { marginTop: 4 }]}>{p.item} × {p.quantity}</Text>
      <Text style={font.body}>{p.pharmacy} · ₹{p.price_inr}</Text>
      <Text style={font.small}>{p.delivery}</Text>
      <View style={[st.banner, { backgroundColor: C.okSoft }]}>
        <Text style={{ color: C.ok, fontWeight: '700' }}>Order {p.order_ref} · pharmacist verification pending</Text>
      </View>
    </Card>
  );
}

function ExtractionReview({ p }: { p: any }) {
  const [state, setState] = useState<'review' | 'saving' | 'confirmed'>('review');
  const confirm = async () => {
    setState('saving');
    await post(`/api/documents/${p.document_id}/confirm`, {}).catch(() => {});
    setState('confirmed');
  };
  return (
    <Card tone={state === 'confirmed' ? 'ok' : 'warn'}>
      <View style={st.row}>
        <Text style={font.tiny}>AI EXTRACTED · PLEASE REVIEW</Text>
        <Pill text={state === 'confirmed' ? 'Confirmed ✓' : 'Needs your review'} tone={state === 'confirmed' ? 'ok' : 'warn'} />
      </View>
      <Text style={[font.h3, { marginTop: 4 }]}>{p.title}</Text>
      <Text style={font.small}>{p.source_name} · {fmtDate(p.issued_on)}</Text>
      <Text style={[font.body, { marginTop: 6, color: C.inkSoft }]}>{p.summary}</Text>
      {p.observations.map((o: any, i: number) => (
        <View key={i} style={[st.row, { paddingVertical: 5, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line }]}>
          <Text style={[font.small, { flex: 1, color: C.ink }]}>{o.test_name}</Text>
          <Text style={[font.small, { fontWeight: '800', color: C.ink }]}>{o.value} {o.unit}</Text>
          <Text style={[font.tiny, { width: 78, textAlign: 'right' }]}>{o.ref_text}</Text>
        </View>
      ))}
      {p.medications?.length ? <Text style={[font.small, { marginTop: 6 }]}>Medicines found: {p.medications.map((m: any) => m.name).join(', ')} (need verification)</Text> : null}
      <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
        <View style={{ flex: 1 }}>
          <Btn title={state === 'confirmed' ? 'Added to health memory' : state === 'saving' ? 'Saving…' : 'Values match — confirm'} onPress={confirm} disabled={state !== 'review'} />
        </View>
        <Btn kind="ghost" title="View PDF" onPress={() => Linking.openURL(url(`/api/documents/${p.document_id}/file`))} />
      </View>
      <Text style={[font.tiny, { marginTop: 8 }]}>Unconfirmed values are never used in comparisons or answers.</Text>
    </Card>
  );
}

function Emergency() {
  return (
    <Card tone="danger" style={{ backgroundColor: C.dangerSoft }}>
      <Text style={[font.h2, { color: C.danger }]}>Possible emergency</Text>
      <Text style={font.body}>Call emergency services now. Aarogya does not give medical advice in emergencies.</Text>
      <View style={{ marginTop: 10 }}>
        <Btn kind="danger" title="📞 Call 112" onPress={() => Linking.openURL('tel:112')} />
      </View>
    </Card>
  );
}

export function GenUI({ item, ctx }: { item: UIItem; ctx: GenCtx }) {
  const p = item.props;
  try {
    switch (item.component) {
      case 'lab_summary': return <LabSummary p={p} />;
      case 'comparison_chart': return <Comparison p={p} />;
      case 'doctor_slots': return <DoctorSlots p={p} ctx={ctx} />;
      case 'approval_card': return <Approval p={p} ctx={ctx} />;
      case 'booking_confirmation': return <BookingConfirmation p={p} />;
      case 'share_confirmation': return <ShareConfirmation p={p} />;
      case 'medication_schedule': return <Medication p={p} />;
      case 'doctor_brief': return <DoctorBrief p={p} />;
      case 'order_confirmation': return <Order p={p} />;
      case 'emergency': return <Emergency />;
      case 'extraction_review': return <ExtractionReview p={p} />;
      default: return null; // unknown component: ignored safely
    }
  } catch {
    return null;
  }
}

const st = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  banner: { borderRadius: 10, padding: 10, marginVertical: 10 },
  obs: { paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line, gap: 3 },
  cmp: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
  link: { color: C.primary, fontWeight: '700', fontSize: 13 },
  avatar: { width: 42, height: 42, borderRadius: 21, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  slots: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginVertical: 12 },
  slot: { borderWidth: 1.5, borderColor: C.primary, borderRadius: 12, paddingVertical: 8, paddingHorizontal: 12, alignItems: 'center', minWidth: 92 },
});
