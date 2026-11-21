import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AgentEvent, loadApiBase, post, subscribe, url } from './api';
import type { UIItem } from './components/GenUI';
import { joinVoice } from './voice/agora';

export type FeedItem =
  | { kind: 'msg'; id: string; role: 'user' | 'assistant'; text: string; channel?: string }
  | { kind: 'ui'; id: string; item: UIItem };
export type Activity = { id: string; label: string; status: string; detail: string; tool: string; ts: string };
export type VoiceState = 'idle' | 'connecting' | 'live' | 'error' | 'ended';

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
  micOpen: boolean;
  reminder: any | null;
  dismissReminder: () => void;
  send: (text: string) => Promise<void>;
  decide: (approvalId: string, d: 'approve' | 'reject', hash?: string) => Promise<void>;
  startVoice: () => Promise<void>;
  stopVoice: () => Promise<void>;
  clearFeed: () => void;
  dataVersion: number;
  lastExtraction: UIItem | null;
  uploadError: string;
  pendingApproval: boolean;
  upload: (file: any, name: string) => Promise<void>;
  reconnectServer: () => void;
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
  const [micOpen, setMicOpen] = useState(false);
  const [reminder, setReminder] = useState<any | null>(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [lastExtraction, setLastExtraction] = useState<UIItem | null>(null);
  const [uploadError, setUploadError] = useState('');
  const leaveRef = useRef<null | (() => Promise<void>)>(null);
  const sidRef = useRef('');

  const [ready, setReady] = useState(false);
  const [reconnect, setReconnect] = useState(0);

  useEffect(() => {
    loadApiBase().finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready) return;
    post('/api/session')
      .then((r) => {
        setSessionId(r.session_id);
        sidRef.current = r.session_id;
      })
      .catch(() => setTimeout(() => setReconnect((n) => n + 1), 2000));
  }, [ready, reconnect]);

  useEffect(() => {
    if (!ready) return;
    return subscribe(
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
            if (e.payload?.status === 'failed') setUploadError('The document could not be read. Please try again or upload a clearer copy.');
          } else if (e.type === 'reminder') {
            setReminder(e.payload);
            setDataVersion((v) => v + 1);
          }
        },
        (s) => setConnected(s === 'open'),
      );
  }, [ready, reconnect]);

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

  const decide = useCallback(async (approvalId: string, d: 'approve' | 'reject', hash?: string) => {
    const r = await post(`/api/approvals/${approvalId}/decide`, { session_id: sidRef.current, decision: d, expected_payload_hash: hash || '' });
    setApprovals((a) => ({ ...a, [approvalId]: r.status }));
  }, []);

  const startVoice = useCallback(async () => {
    setVoice('connecting');
    setVoiceError('');
    try {
      const s = await post('/api/voice/start', { session_id: sidRef.current });
      setMicOpen(false);
      leaveRef.current = await joinVoice(s, {
        onLevels: setLevels,
        onAgentLeft: () => {
          setLevels({ agent: 0, me: 0 });
          setVoice('ended');
          leaveRef.current?.().catch(() => {});
          leaveRef.current = null;
        },
        onState: (st) => {
          if (/DISCONNECTED/i.test(st) || st === '5') setVoice((v) => (v === 'live' ? 'ended' : v));
        },
        onMicOpen: () => setMicOpen(true),
      });
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
        sessionId, feed, activity, approvals, thinking, connected, voice, voiceError, levels, micOpen, reminder,
        dismissReminder: () => setReminder(null), send, decide, startVoice, stopVoice,
        clearFeed: () => setFeed([]), dataVersion, lastExtraction, uploadError,
        pendingApproval: Object.values(approvals).includes('pending'),
        reconnectServer: () => setReconnect((n) => n + 1),
        upload: async (file: any, name: string) => {
          const fd = new FormData();
          if (file && typeof file === 'object' && 'uri' in file) fd.append('file', file as any); // native {uri,name,type}
          else fd.append('file', file, name);
          fd.append('session_id', sidRef.current);
          const r = await fetch(url('/api/documents/upload'), { method: 'POST', body: fd, headers: { 'ngrok-skip-browser-warning': '1' } });
          if (!r.ok) throw new Error(await r.text());
          setUploadError('');
          const j = await r.json().catch(() => ({}));
          if (j?.duplicate) setUploadError('This document is already in your Health Locker.');
          setDataVersion((v) => v + 1);
        },
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
