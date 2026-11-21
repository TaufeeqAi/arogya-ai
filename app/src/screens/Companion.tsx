import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Animated, Easing, Pressable, ScrollView, StyleSheet, Text, TextInput, useWindowDimensions, View } from 'react-native';
import { GenUI } from '../components/GenUI';
import { useStore } from '../store';
import { C, R, font, shadow } from '../theme';

const SUGGESTIONS = [
  'Meri latest blood report samjhao',
  'Pichhli report se compare karo',
  'Saturday morning doctor ka appointment chahiye',
  'Meri dawaiyon ka reminder laga do',
];

function Orb() {
  const { voice, levels, startVoice, stopVoice, thinking, micOpen, pendingApproval } = useStore();
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1100, easing: Easing.inOut(Easing.quad), useNativeDriver: false }),
        Animated.timing(pulse, { toValue: 0, duration: 1100, easing: Easing.inOut(Easing.quad), useNativeDriver: false }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const speaking = levels.agent > 4;
  const listening = voice === 'live' && levels.me > 4;
  const live = voice === 'live';
  const label =
    voice === 'connecting' ? 'Connecting…' : voice === 'error' ? 'Tap to retry' : voice === 'ended' ? 'Call ended · tap to talk again' : !live ? 'Tap to talk' : speaking ? (micOpen ? 'Aarogya is speaking' : 'Aarogya is greeting you… mic opens next') : !micOpen ? 'Connecting voice…' : thinking ? 'Thinking…' : pendingApproval ? 'Waiting for your approval — say "haan" or tap Approve' : listening ? 'Listening…' : 'Listening — speak naturally';
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, live ? 1.12 + Math.min(levels.agent, 60) / 200 : 1.04] });
  return (
    <View style={{ alignItems: 'center' }}>
      <Pressable onPress={live ? stopVoice : startVoice} accessibilityRole="button" accessibilityLabel={live ? 'End voice call' : 'Start voice call'}>
        <Animated.View style={[s.halo, { transform: [{ scale }], backgroundColor: speaking ? C.saffronSoft : live ? C.primarySoft : '#E7E3DA' }]}>
          <View style={[s.orb, { backgroundColor: live ? (speaking ? C.saffron : C.primary) : C.primaryDark }]}>
            {voice === 'connecting' ? <ActivityIndicator color="#fff" /> : <Text style={s.orbIcon}>{live ? '■' : '🎙'}</Text>}
          </View>
        </Animated.View>
      </Pressable>
      <Text style={[font.small, { marginTop: 6, fontWeight: '600' }]}>{label}</Text>
    </View>
  );
}

export function ActivityPanel({ compact }: { compact?: boolean }) {
  const { activity } = useStore();
  const items = compact ? activity.slice(0, 6) : activity;
  return (
    <View>
      {items.length === 0 && <Text style={font.small}>Actions the agent performs will appear here, live.</Text>}
      {items.map((a) => (
        <View key={a.id} style={s.act}>
          <View style={[s.dot, { backgroundColor: { done: C.ok, failed: C.danger, blocked: C.danger, waiting: C.saffron, unknown: C.saffron, cancelled: C.muted }[a.status] || C.info }]} />
          <View style={{ flex: 1 }}>
            <Text style={[font.small, { color: C.ink, fontWeight: '700' }]}>{a.label}</Text>
            {a.detail ? <Text style={font.tiny} numberOfLines={2}>{a.detail}</Text> : null}
          </View>
          <Text style={[font.tiny, { fontFamily: 'monospace' }]}>{a.tool}</Text>
        </View>
      ))}
    </View>
  );
}

export default function Companion() {
  const { feed, send, thinking, approvals, decide, voice, voiceError, connected, activity } = useStore();
  const [text, setText] = useState('');
  const [showAct, setShowAct] = useState(false);
  const scroll = useRef<any>(null);
  const { width } = useWindowDimensions();
  const wide = width >= 980;
  const ctx = { say: (t: string) => send(t), decide, approvals };

  useEffect(() => {
    setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 80);
  }, [feed.length, thinking]);

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    setText('');
    send(t);
  };

  return (
    <View style={{ flex: 1, flexDirection: 'row' }}>
      <View style={{ flex: 1 }}>
        <ScrollView ref={scroll} contentContainerStyle={s.feed}>
          {feed.length === 0 && (
            <View style={s.empty}>
              <Text style={[font.h1, { textAlign: 'center' }]}>नमस्ते, सुनीता जी</Text>
              <Text style={[font.body, { textAlign: 'center', color: C.inkSoft, marginTop: 6 }]}>
                Apni health history ke baare mein poochiye, report samjhiye, doctor book kijiye — apni bhasha mein.
              </Text>
              <View style={s.sugs}>
                {SUGGESTIONS.map((q) => (
                  <Pressable key={q} onPress={() => send(q)} style={({ pressed }) => [s.sug, pressed && { backgroundColor: C.primarySoft }]}>
                    <Text style={{ color: C.primaryDark, fontWeight: '600' }}>{q}</Text>
                  </Pressable>
                ))}
              </View>
            </View>
          )}
          {feed.map((f) =>
            f.kind === 'msg' ? (
              <View key={f.id} style={[s.bubble, f.role === 'user' ? s.user : s.bot]}>
                <Text style={[font.body, f.role === 'user' && { color: '#fff' }]}>{f.text}</Text>
                {f.channel === 'voice' && <Text style={[font.tiny, f.role === 'user' && { color: '#CDE9E4' }]}>🎙 voice</Text>}
              </View>
            ) : (
              <View key={f.id} style={{ maxWidth: 560, width: '100%', alignSelf: 'flex-start' }}>
                <GenUI item={f.item} ctx={ctx} />
              </View>
            ),
          )}
          {thinking && (
            <View style={[s.bubble, s.bot, { flexDirection: 'row', gap: 8, alignItems: 'center' }]}>
              <ActivityIndicator size="small" color={C.primary} />
              <Text style={font.small}>{activity[0]?.status === 'running' ? activity[0].label : 'Aarogya is working…'}</Text>
            </View>
          )}
        </ScrollView>

        {!wide && (
          <Pressable onPress={() => setShowAct(!showAct)} style={s.actBar}>
            <Text style={[font.small, { fontWeight: '700', color: C.primaryDark }]}>
              ⚡ Agent activity · {activity.length} {showAct ? '▾' : '▸'}
            </Text>
            {activity[0] && !showAct ? <Text style={font.tiny} numberOfLines={1}>{activity[0].label}</Text> : null}
          </Pressable>
        )}
        {!wide && showAct && (
          <ScrollView style={s.actSheet}>
            <ActivityPanel />
          </ScrollView>
        )}

        <View style={s.dock}>
          {voice === 'error' && <Text style={[font.tiny, { color: C.danger, marginBottom: 6 }]} numberOfLines={3}>Voice error: {voiceError}</Text>}
          <Orb />
          <View style={s.inputRow}>
            <TextInput
              value={text}
              onChangeText={setText}
              onSubmitEditing={submit}
              placeholder="Ya yahan likhiye… (type instead)"
              placeholderTextColor={C.muted}
              style={s.input}
              returnKeyType="send"
            />
            <Pressable onPress={submit} style={s.send}>
              <Text style={{ color: '#fff', fontWeight: '800' }}>➤</Text>
            </Pressable>
          </View>
          {!connected && <Text style={[font.tiny, { textAlign: 'center', marginTop: 4 }]}>Connecting to live updates…</Text>}
        </View>
      </View>
      {wide && (
        <View style={s.side}>
          <Text style={[font.h3, { marginBottom: 10 }]}>⚡ Agent activity</Text>
          <Text style={[font.tiny, { marginBottom: 12 }]}>Every tool call, approval and verification — live</Text>
          <ScrollView>
            <ActivityPanel />
          </ScrollView>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  feed: { padding: 16, paddingBottom: 24, gap: 10 },
  empty: { paddingTop: 28, paddingHorizontal: 8, alignItems: 'center' },
  sugs: { marginTop: 22, gap: 10, width: '100%', maxWidth: 420 },
  sug: { borderWidth: 1.5, borderColor: C.primarySoft, backgroundColor: C.surface, borderRadius: 16, paddingVertical: 12, paddingHorizontal: 16 },
  bubble: { maxWidth: '86%', borderRadius: 18, paddingVertical: 10, paddingHorizontal: 14 },
  user: { alignSelf: 'flex-end', backgroundColor: C.primary, borderBottomRightRadius: 6 },
  bot: { alignSelf: 'flex-start', backgroundColor: C.surface, borderBottomLeftRadius: 6, ...shadow },
  dock: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 14, backgroundColor: C.surface, borderTopLeftRadius: R.xl, borderTopRightRadius: R.xl, ...shadow },
  halo: { width: 96, height: 96, borderRadius: 48, alignItems: 'center', justifyContent: 'center' },
  orb: { width: 70, height: 70, borderRadius: 35, alignItems: 'center', justifyContent: 'center' },
  orbIcon: { fontSize: 28, color: '#fff' },
  inputRow: { flexDirection: 'row', gap: 8, marginTop: 10, alignItems: 'center' },
  input: { flex: 1, backgroundColor: C.bg, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 11, fontSize: 15, color: C.ink },
  send: { width: 44, height: 44, borderRadius: 22, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  actBar: { marginHorizontal: 16, marginBottom: 8, backgroundColor: C.surfaceAlt, borderRadius: 12, paddingVertical: 8, paddingHorizontal: 12 },
  actSheet: { maxHeight: 230, marginHorizontal: 16, marginBottom: 8, backgroundColor: C.surface, borderRadius: 14, padding: 12 },
  act: { flexDirection: 'row', gap: 10, alignItems: 'flex-start', paddingVertical: 7, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
  dot: { width: 9, height: 9, borderRadius: 5, marginTop: 5 },
  side: { width: 340, borderLeftWidth: 1, borderLeftColor: C.line, padding: 18, backgroundColor: '#FBFAF7' },
});
