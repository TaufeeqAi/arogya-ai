import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AgentEvent, post, subscribe, url } from './api';
import type { UIItem } from './components/GenUI';
import { joinVoice } from './voice/agora';

export type FeedItem =
  | { kind: 'msg'; id: string; role: 'user' | 'assistant'; text: string; channel?: string }
  | { kind: 'ui'; id: string; item: UIItem };
export type Activity = { id: string; label: string; status: string; detail: string; tool: string; ts: string };
export type VoiceState = 'idle' | 'connecting' | 'live' | 'error';

type Store = {
  sessionId: string;
  feed: FeedItem[];
  activity: Activity[];
  approvals: Record<string, string>;
  thinking: boolean;
  connected: boolean;
  voice: VoiceState;
  voiceError: string;
  levels: { agent: number; me: number };
  reminder: any | null;
  dismissReminder: () => void;
  send: (text: string) => Promise<void>;
  decide: (approvalId: string, d: 'approve' | 'reject') => Promise<void>;
  startVoice: () => Promise<void>;
  stopVoice: () => Promise<void>;
  clearFeed: () => void;
  dataVersion: number;
  lastExtraction: UIItem | null;
  upload: (file: Blob, name: string) => Promise<void>;
};

const Ctx = createContext<Store>(null as any);
export const useStore = () => useContext(Ctx);
let n = 0;
const nid = () => `${Date.now()}-${n++}`;

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState('');
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [approvals, setApprovals] = useState<Record<string, string>>({});
  const [thinking, setThinking] = useState(false);
  const [connected, setConnected] = useState(false);
  const [voice, setVoice] = useState<VoiceState>('idle');
  const [voiceError, setVoiceError] = useState('');
  const [levels, setLevels] = useState({ agent: 0, me: 0 });
  const [reminder, setReminder] = useState<any | null>(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [lastExtraction, setLastExtraction] = useState<UIItem | null>(null);
  const leaveRef = useRef<null | (() => Promise<void>)>(null);
  const sidRef = useRef('');

  useEffect(() => {
    post('/api/session').then((r) => {
      setSessionId(r.session_id);
      sidRef.current = r.session_id;
    });
  }, []);

  useEffect(
    () =>
      subscribe(
        (e: AgentEvent) => {
          const mine = !e.session_id || e.session_id === sidRef.current;
          if (e.type === 'activity') {
            setActivity((a) => [{ id: nid(), ts: e.ts, ...e.payload }, ...a].slice(0, 80));
          } else if (e.type === 'ui' && mine) {
            setFeed((f) => [...f, { kind: 'ui', id: nid(), item: { id: nid(), ...e.payload } }]);
            if (e.payload.component === 'approval_card') setApprovals((a) => ({ ...a, [e.payload.props.approval_id]: 'pending' }));
            if (e.payload.component === 'extraction_review') setLastExtraction({ id: nid(), ...e.payload });
            if (['booking_confirmation', 'share_confirmation', 'medication_schedule', 'order_confirmation'].includes(e.payload.component))
              setDataVersion((v) => v + 1);
          } else if (e.type === 'transcript' && mine) {
            if (e.payload.role === 'assistant') setThinking(false);
            else if (e.payload.channel === 'voice') setThinking(true);
            setFeed((f) => [...f, { kind: 'msg', id: nid(), role: e.payload.role, text: e.payload.text, channel: e.payload.channel }]);
          } else if (e.type === 'approval_resolved') {
            setApprovals((a) => ({ ...a, [e.payload.approval_id]: e.payload.status }));
          } else if (e.type === 'document_updated') {
            setDataVersion((v) => v + 1);
          } else if (e.type === 'reminder') {
            setReminder(e.payload);
            setDataVersion((v) => v + 1);
          }
        },
        (s) => setConnected(s === 'open'),
      ),
    [],
  );

  const send = useCallback(async (text: string) => {
    if (!text.trim() || !sidRef.current) return;
    setThinking(true);
    try {
      await post('/api/chat', { session_id: sidRef.current, text });
    } catch (e: any) {
      setFeed((f) => [...f, { kind: 'msg', id: nid(), role: 'assistant', text: `⚠️ ${e.message}` }]);
    } finally {
      setThinking(false);
    }
  }, []);

  const decide = useCallback(async (approvalId: string, d: 'approve' | 'reject') => {
    const r = await post(`/api/approvals/${approvalId}/decide`, { session_id: sidRef.current, decision: d });
    setApprovals((a) => ({ ...a, [approvalId]: r.status }));
  }, []);

  const startVoice = useCallback(async () => {
    setVoice('connecting');
    setVoiceError('');
    try {
      const s = await post('/api/voice/start', { session_id: sidRef.current });
      leaveRef.current = await joinVoice(s, { onLevels: setLevels, onAgentLeft: () => setLevels({ agent: 0, me: 0 }) });
      setVoice('live');
    } catch (e: any) {
      setVoice('error');
      setVoiceError(e?.message || String(e));
      post('/api/voice/stop', { session_id: sidRef.current }).catch(() => {});
    }
  }, []);

  const stopVoice = useCallback(async () => {
    await leaveRef.current?.();
    leaveRef.current = null;
    setVoice('idle');
    setLevels({ agent: 0, me: 0 });
    post('/api/voice/stop', { session_id: sidRef.current }).catch(() => {});
  }, []);

  return (
    <Ctx.Provider
      value={{
        sessionId, feed, activity, approvals, thinking, connected, voice, voiceError, levels, reminder,
        dismissReminder: () => setReminder(null), send, decide, startVoice, stopVoice,
        clearFeed: () => setFeed([]), dataVersion, lastExtraction,
        upload: async (file: Blob, name: string) => {
          const fd = new FormData();
          fd.append('file', file, name);
          fd.append('session_id', sidRef.current);
          const r = await fetch(url('/api/documents/upload'), { method: 'POST', body: fd, headers: { 'ngrok-skip-browser-warning': '1' } });
          if (!r.ok) throw new Error(await r.text());
          setDataVersion((v) => v + 1);
        },
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
