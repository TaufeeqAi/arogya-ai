import { Platform } from 'react-native';

// Same-origin when the backend serves the web build (ngrok); explicit base during local dev.
const envBase = process.env.EXPO_PUBLIC_API_BASE;
export const API_BASE: string =
  envBase !== undefined
    ? envBase
    : Platform.OS === 'web' && typeof window !== 'undefined' && window.location.port === '8081'
      ? `http://${window.location.hostname}:8000`
      : Platform.OS === 'web'
        ? ''
        : 'http://10.0.2.2:8000';

export const url = (p: string) => `${API_BASE}${p}`;

const HEADERS = { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' };

export async function get<T = any>(path: string): Promise<T> {
  const r = await fetch(url(path), { headers: HEADERS });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export async function post<T = any>(path: string, body?: any): Promise<T> {
  const r = await fetch(url(path), { method: 'POST', headers: HEADERS, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json().catch(() => ({}));
  if (!r.ok && r.status !== 409) throw new Error(data?.detail || `HTTP ${r.status}`);
  return data;
}

export type AgentEvent = {
  type: 'activity' | 'ui' | 'transcript' | 'approval_resolved' | 'reminder' | 'document_updated';
  session_id: string;
  payload: any;
  ts: string;
};

/** Subscribe to the live agent event stream (SSE). Returns an unsubscribe fn. */
export function subscribe(onEvent: (e: AgentEvent) => void, onStatus?: (s: 'open' | 'error') => void): () => void {
  if (typeof EventSource === 'undefined') {
    // Native fallback: poll recent activity (native SSE added with the Android build)
    return () => {};
  }
  let es: EventSource | null = null;
  let closed = false;
  const connect = () => {
    es = new EventSource(url('/api/events'));
    es.onopen = () => onStatus?.('open');
    es.onmessage = (m) => {
      try {
        onEvent(JSON.parse(m.data));
      } catch {}
    };
    es.onerror = () => {
      onStatus?.('error');
      es?.close();
      if (!closed) setTimeout(connect, 1500);
    };
  };
  connect();
  return () => {
    closed = true;
    es?.close();
  };
}
