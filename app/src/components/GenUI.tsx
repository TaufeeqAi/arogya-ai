/** Generative UI registry: the agent selects a component by name + typed props; no model-generated code runs. */
import React, { useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line, Rect, Text as SvgText } from 'react-native-svg';
import { post, url } from '../api';
import { C, font } from '../theme';
import { useNav } from '../nav';
import { Btn, Card, Pill, SourceChip, TrustBadge } from './ui';

export type UIItem = { id: string; component: string; version: number; props: any };
export type GenCtx = {
  say: (text: string) => void;
  decide: (approvalId: string, decision: 'approve' | 'reject', hash?: string) => Promise<void>;
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
                <Text style={{ color: C.inkSoft, fontWeight: '700' }}>
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
      <Text style={font.tiny}>Demo clinic network (simulated) · times in IST · tap a slot or just say it</Text>
    </Card>
  );
}

function Approval({ p, ctx }: { p: any; ctx: GenCtx }) {
  const status = ctx.approvals[p.approval_id] || 'pending';
  const [busy, setBusy] = useState(false);
  const act = async (d: 'approve' | 'reject') => {
    setBusy(true);
    try {
      await ctx.decide(p.approval_id, d, p.payload_hash);
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
          text={{ pending: 'Waiting for you', executed: 'Done ✓', failed: 'Could not complete', rejected: 'Cancelled', expired: 'Expired', approved: 'Approved', unknown: 'Outcome unknown' }[status] || status}
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
      {status === 'pending' && (
        <Text style={[font.tiny, { marginTop: 8 }]}>
          Or say "haan, kar do". Bound to these exact details{p.payload_hash ? ` · ref #${p.payload_hash}` : ''} · expires in 10 min
        </Text>
      )}
    </Card>
  );
}

function BookingConfirmation({ p }: { p: any }) {
  return (
    <Card tone="ok">
      <View style={st.row}>
        <Text style={font.tiny}>APPOINTMENT CONFIRMED</Text>
        <Pill text="Verified with booking service (demo)" tone="ok" />
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
      <Text style={[font.tiny, { marginTop: 8 }]}>
        {p.reminders ? `${p.reminders} reminder${p.reminders > 1 ? 's' : ''} scheduled before the visit` : 'Visit is too soon for advance reminders'}
      </Text>
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
      {p.purpose ? <Text style={font.small}>Purpose: {p.purpose}</Text> : null}
      <Text style={[font.tiny, { marginTop: 6 }]}>Access expires {fmtDate(p.expires_at)} · revoke anytime in Profile</Text>
    </Card>
  );
}

const MED_GROUPS: [string, string][] = [
  ['reminders_active', 'Reminders on'],
  ['verified', 'No reminders yet'],
  ['needs_clarification', 'Needs clarification'],
  ['stopped', 'Stopped by your doctor'],
];

function Medication({ p, ctx }: { p: any; ctx?: GenCtx }) {
  const meds: any[] = p.medications || [];
  const say = (q: string) => ctx?.say(q);
  return (
    <Card tone="info">
      <Text style={font.tiny}>MEDICINES ON RECORD · {meds.filter((m) => m.status !== 'stopped').length} ACTIVE</Text>
      {MED_GROUPS.map(([status, title]) => {
        const group = meds.filter((m) => m.status === status);
        if (!group.length) return null;
        return (
          <View key={status} style={{ marginTop: 10 }}>
            <Text style={[font.small, { fontWeight: '800', color: status === 'needs_clarification' ? C.danger : status === 'stopped' ? C.muted : C.primaryDark }]}>
              {title.toUpperCase()}
            </Text>
            {group.map((m: any) => {
              const unclear = m.status === 'needs_clarification';
              const stopped = m.status === 'stopped';
              const low = !unclear && !stopped && m.supply_left_days <= 5 && !m.refill_order;
              const label = stopped ? 'Stopped' : unclear ? 'Needs clarification' : m.status === 'reminders_active' ? 'Reminders on'
                : m.source?.trust_label === 'provider_verified' ? 'Doctor verified' : 'From your prescription';
              return (
                <View key={m.medication_id} style={[st.obs, p.highlight === m.medication_id && { backgroundColor: C.okSoft, borderRadius: 10, padding: 8 }, stopped && { opacity: 0.7 }]}>
                  <View style={st.row}>
                    <Text style={[font.h3, stopped && { textDecorationLine: 'line-through' }]}>💊 {m.name} {m.strength}</Text>
                    <Pill text={label} tone={unclear ? 'danger' : stopped ? 'neutral' : m.status === 'reminders_active' ? 'ok' : 'primary'} />
                  </View>
                  <Text style={font.small}>{m.frequency || 'Frequency not on source'} · {m.instructions}</Text>
                  {m.times?.length && !stopped ? (
                    <View style={{ flexDirection: 'row', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                      {m.times.map((t: string) => <Pill key={t} text={`⏰ ${t}`} tone="neutral" />)}
                      {m.next_dose ? <Pill text={`Next: ${m.next_dose}`} tone="info" /> : null}
                    </View>
                  ) : null}
                  {m.adherence_7d ? (
                    <Text style={[font.small, { marginTop: 4 }]}>
                      Last 7 days: {m.adherence_7d.taken} taken · {m.adherence_7d.skipped} skipped <Text style={font.tiny}>(self-reported)</Text>
                    </Text>
                  ) : null}
                  {low ? <Text style={[font.small, { color: C.danger, marginTop: 4, fontWeight: '700' }]}>Only ~{m.supply_left_days} days of supply left</Text> : null}
                  {m.refill_order ? <Text style={[font.small, { color: C.ok, marginTop: 4, fontWeight: '700' }]}>📦 Refill on the way · {m.refill_order}</Text> : null}
                  <View style={{ flexDirection: 'row', gap: 6, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    <SourceChip documentId={m.source.document_id} title={m.source.title} />
                    {ctx && m.status === 'verified' ? <Btn small kind="soft" title="⏰ Set reminder" onPress={() => say(`${m.name} ka reminder laga do`)} /> : null}
                    {ctx && !unclear && !stopped && !m.refill_order && (low || m.status === 'reminders_active') ? <Btn small kind="soft" title="📦 Refill" onPress={() => say(`${m.name} ka refill order kar do`)} /> : null}
                    {ctx && unclear ? <Btn small kind="soft" title="Ask doctor" onPress={() => say(`${m.name} ki dose doctor se confirm karni hai, appointment chahiye`)} /> : null}
                  </View>
                </View>
              );
            })}
          </View>
        );
      })}
      <Text style={[font.tiny, { marginTop: 8 }]}>Aarogya never changes doses or restarts stopped medicines. Unclear instructions must be confirmed by your doctor or pharmacist.</Text>
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
    try {
      const r: any = await post(`/api/documents/${p.document_id}/confirm`, {});
      setState(r?.ok ? 'confirmed' : 'review');
    } catch {
      setState('review');
    }
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

function ProviderRecord({ p }: { p: any }) {
  return (
    <Card tone="ok">
      <View style={st.row}>
        <Text style={font.tiny}>NEW RECORD FROM YOUR DOCTOR</Text>
        <Pill text="Provider verified" tone="ok" />
      </View>
      <Text style={[font.h3, { marginTop: 4 }]}>{p.title}</Text>
      <Text style={font.small}>{p.provider} · {fmtDate(p.date)}</Text>
      {p.changes.map((c: string) => (
        <View key={c} style={[st.banner, { backgroundColor: C.okSoft, marginVertical: 6 }]}>
          <Text style={{ color: C.ok, fontWeight: '700' }}>{c}</Text>
        </View>
      ))}
      <View style={st.row}>
        <SourceChip documentId={p.document_id} title="View signed prescription" />
        <Text style={[font.tiny, { fontFamily: 'monospace' }]}>sig {p.signature}…</Text>
      </View>
    </Card>
  );
}

function DoctorResults({ p, ctx }: { p: any; ctx: GenCtx }) {
  return (
    <Card>
      <Text style={font.tiny}>DOCTORS · DEMO NETWORK{p.note ? ` · ${p.note.toUpperCase()}` : ''}</Text>
      {p.doctors.map((d: any) => (
        <Pressable key={d.id} onPress={() => ctx.say(`${d.name} ke slots dikhao`)} style={({ pressed }) => [st.docRow, pressed && { backgroundColor: C.primarySoft }]}>
          <View style={st.avatar}>
            <Text style={{ color: '#fff', fontWeight: '800' }}>{d.name.replace('Dr. ', '').split(' ').map((w: string) => w[0]).join('')}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={font.h3}>{d.name}</Text>
            <Text style={font.small}>{d.specialty} · {d.clinic}, {d.area}</Text>
            <Text style={font.tiny}>{d.languages.join(', ')} · ₹{d.fee} · ★ {d.rating}</Text>
          </View>
          <Text style={{ color: C.muted, fontSize: 18 }}>›</Text>
        </Pressable>
      ))}
      <Text style={[font.tiny, { marginTop: 6 }]}>Tap a doctor or say their name to see open slots</Text>
    </Card>
  );
}

function CarePlan({ p }: { p: any }) {
  const tone = (s: string) => (s === 'done' ? 'ok' : s === 'booked' ? 'primary' : s === 'overdue' ? 'danger' : 'warn');
  return (
    <Card tone="info">
      <Text style={font.tiny}>DOCTOR-ADVISED FOLLOW-UPS</Text>
      {p.tasks.map((t: any) => (
        <View key={t.task_id} style={st.obs}>
          <View style={st.row}>
            <Text style={[font.h3, { flex: 1 }]}>{t.title}</Text>
            <Pill text={t.status} tone={tone(t.status) as any} />
          </View>
          <Text style={font.small}>{t.detail}</Text>
          <Text style={font.tiny}>Due {t.due}</Text>
          {t.source_document_id ? <SourceChip documentId={t.source_document_id} title="Source: consultation summary" /> : null}
        </View>
      ))}
    </Card>
  );
}

function HealthOverview({ p }: { p: any }) {
  const { go } = useNav();
  return (
    <Card tone={p.overall === 'needs_attention' ? 'warn' : 'ok'}>
      <Text style={font.tiny}>HEALTH OVERVIEW · BY BODY SYSTEM</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        {p.systems.map((x: any) => (
          <View key={x.key} style={[st.hchip, x.status === 'needs_attention' ? { backgroundColor: '#FFF1DC', borderColor: C.saffron } : { backgroundColor: '#E2F6EC', borderColor: '#9AD8B6' }]}>
            <Text>{x.icon}</Text>
            <Text style={{ fontWeight: '700', color: C.ink, fontSize: 13 }}>{x.label}</Text>
            {x.status === 'needs_attention' ? <Text style={{ color: '#9A5A16', fontWeight: '800', fontSize: 12 }}>{x.attention_count}</Text> : <Text style={{ color: C.ok }}>✓</Text>}
          </View>
        ))}
      </View>
      <View style={{ marginTop: 10 }}><Btn small kind="soft" title="Open Health tab" onPress={() => go('health')} /></View>
      <Text style={[font.tiny, { marginTop: 6 }]}>Numbers = values outside the lab's printed range. Not a diagnosis.</Text>
    </Card>
  );
}

function HealthSystem({ p }: { p: any }) {
  const { go } = useNav();
  const out = p.tests.filter((t: any) => t.status !== 'within');
  return (
    <Card tone={p.status === 'needs_attention' ? 'warn' : 'ok'}>
      <View style={st.row}>
        <Text style={font.tiny}>{p.icon} {p.label.toUpperCase()}</Text>
        <Pill text={p.status === 'needs_attention' ? `${p.attention_count} outside range` : 'Within lab range'} tone={p.status === 'needs_attention' ? 'warn' : 'ok'} />
      </View>
      {(out.length ? out : p.tests.slice(0, 3)).map((t: any) => (
        <View key={t.code} style={st.obs}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={[font.body, { flex: 1, fontWeight: '600' }]}>{t.name}</Text>
            <Text style={[font.body, { fontWeight: '800' }]}>{t.value} <Text style={font.small}>{t.unit}</Text></Text>
          </View>
          <Text style={font.small}>Lab range {t.reference_range} · {t.history.map((h: any) => h.value).join(' → ')}</Text>
          <Text style={font.tiny}>{t.about}</Text>
        </View>
      ))}
      <View style={{ marginTop: 8 }}><Btn small kind="soft" title={`See all ${p.test_count} ${p.label.toLowerCase()} tests`} onPress={() => go('health')} /></View>
    </Card>
  );
}

class CardBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <Card>
          <Text style={font.small}>This card could not be displayed. The details are in the conversation above.</Text>
        </Card>
      );
    return this.props.children;
  }
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
  return (
    <CardBoundary>
      <GenUIInner item={item} ctx={ctx} />
    </CardBoundary>
  );
}

function GenUIInner({ item, ctx }: { item: UIItem; ctx: GenCtx }) {
  const p = item.props;
  try {
    switch (item.component) {
      case 'lab_summary': return <LabSummary p={p} />;
      case 'comparison_chart': return <Comparison p={p} />;
      case 'doctor_slots': return <DoctorSlots p={p} ctx={ctx} />;
      case 'approval_card': return <Approval p={p} ctx={ctx} />;
      case 'booking_confirmation': return <BookingConfirmation p={p} />;
      case 'share_confirmation': return <ShareConfirmation p={p} />;
      case 'medication_schedule': return <Medication p={p} ctx={ctx} />;
      case 'doctor_brief': return <DoctorBrief p={p} />;
      case 'order_confirmation': return <Order p={p} />;
      case 'emergency': return <Emergency />;
      case 'extraction_review': return <ExtractionReview p={p} />;
      case 'provider_record': return <ProviderRecord p={p} />;
      case 'doctor_results': return <DoctorResults p={p} ctx={ctx} />;
      case 'care_plan': return <CarePlan p={p} />;
      case 'health_overview': return <HealthOverview p={p} />;
      case 'health_system': return <HealthSystem p={p} />;
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
  hchip: { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1.5, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6 },
  docRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
  slot: { borderWidth: 1.5, borderColor: C.primary, borderRadius: 12, paddingVertical: 8, paddingHorizontal: 12, alignItems: 'center', minWidth: 92 },
});
