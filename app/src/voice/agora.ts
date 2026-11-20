// Native implementation (react-native-agora) is added with the Android dev build.
// Metro picks agora.web.ts on web automatically.
import type { VoiceHandlers, VoiceSession } from './types';

export async function joinVoice(_s: VoiceSession, _h: VoiceHandlers): Promise<() => Promise<void>> {
  throw new Error('Native voice requires the Android dev build (react-native-agora).');
}

export async function setMuted(_muted: boolean) {}
