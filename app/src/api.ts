import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Permanent backend URL (ngrok static domain). Overridable at build time or from the Profile screen.
export const DEFAULT_REMOTE = process.env.EXPO_PUBLIC_API_BASE || 'https://reverence-haziness-apprehend.ngrok-free.dev';
const KEY = 'aarogya.apiBase';

function initialBase(): string {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    // dev server on :8081 talks to local backend; otherwise the backend serves the app (same origin)
    return window.location.port === '8081' ? `http://${window.location.hostname}:8000` : '';
  }
  return DEFAULT_REMOTE;
}

let base = initialBase();

export const getApiBase = () => base;

export async function loadApiBase(): Promise<void> {
  if (Platform.OS === 'web') return;
  try {
    const v = await AsyncStorage.getItem(KEY);
    if (v) base = v;
  } catch {}
}

export async function setApiBase(v: string): Promise<void> {
  base = v.trim().replace(/\/+$/, '');
  try {
    await AsyncStorage.setItem(KEY, base);
  } catch {}
}

export const url = (p: string) => `${base}${p}`;

export const HEADERS = { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' };

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
  let closed = false;
  let es: any = null;
  const handle = (data: string | null | undefined) => {
    if (!data) return;
    try {
      onEvent(JSON.parse(data));
    } catch {}
  };
  const connect = () => {
    if (closed) return;
    if (Platform.OS === 'web') {
      es = new EventSource(url('/api/events'));
      es.onopen = () => onStatus?.('open');
      es.onmessage = (m: MessageEvent) => handle(m.data);
      es.onerror = () => {
        onStatus?.('error');
        es?.close();
        setTimeout(connect, 1500);
      };
    } else {
      // React Native: XHR-based SSE (supports custom headers, e.g. ngrok)
      const RNEventSource = require('react-native-sse').default;
      es = new RNEventSource(url('/api/events'), { headers: { 'ngrok-skip-browser-warning': '1' }, pollingInterval: 0 });
      es.addEventListener('open', () => onStatus?.('open'));
      es.addEventListener('message', (m: any) => handle(m.data));
      es.addEventListener('error', () => {
        onStatus?.('error');
        es?.close();
        setTimeout(connect, 1500);
      });
    }
  };
  connect();
  return () => {
    closed = true;
    es?.close();
  };
}
