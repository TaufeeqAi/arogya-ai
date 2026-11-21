import AgoraRTC, { IAgoraRTCClient, IMicrophoneAudioTrack, IRemoteAudioTrack } from 'agora-rtc-sdk-ng';
import type { VoiceHandlers, VoiceSession } from './types';

AgoraRTC.setLogLevel(3);

export async function joinVoice(s: VoiceSession, h: VoiceHandlers): Promise<() => Promise<void>> {
  const client: IAgoraRTCClient = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
  let mic: IMicrophoneAudioTrack | null = null;
  let remote: IRemoteAudioTrack | null = null;

  // Greeting guard: keep the mic muted until the agent's greeting finishes, so a noise burst when the mic
  // opens can't interrupt it. Opens after the agent's first speech ends, or after 9 s at the latest.
  let greeting: 'waiting' | 'speaking' | 'done' = 'waiting';
  let quietSince = 0;
  const openMic = () => {
    if (greeting === 'done') return;
    greeting = 'done';
    mic?.setMuted(false).catch(() => {});
    h.onMicOpen?.();
  };
  const fallback = setTimeout(openMic, 9000);

  client.on('user-published', async (user, mediaType) => {
    await client.subscribe(user, mediaType);
    if (mediaType === 'audio') {
      remote = user.audioTrack ?? null;
      remote?.play();
      h.onAgentJoined?.();
    }
  });
  client.on('user-left', () => h.onAgentLeft?.());
  client.on('connection-state-change', (cur) => h.onState?.(cur));

  await client.join(s.app_id, s.channel, s.token || null, s.uid);
  mic = await AgoraRTC.createMicrophoneAudioTrack({ AEC: true, ANS: true, AGC: true });
  await mic.setMuted(true);
  await client.publish([mic]);

  // 150 ms level polling (smooth orb + greeting detection)
  const poll = setInterval(() => {
    const agent = (remote?.getVolumeLevel?.() ?? 0) * 100;
    const me = greeting === 'done' ? (mic?.getVolumeLevel?.() ?? 0) * 100 : 0;
    h.onLevels?.({ agent, me });
    const now = Date.now();
    if (greeting === 'waiting' && agent > 6) greeting = 'speaking';
    if (greeting === 'speaking') {
      if (agent < 2) {
        quietSince = quietSince || now;
        if (now - quietSince > 900) openMic();
      } else quietSince = 0;
    }
  }, 150);

  return async () => {
    clearInterval(poll);
    clearTimeout(fallback);
    try {
      mic?.stop();
      mic?.close();
      await client.leave();
    } catch {}
  };
}

export async function setMuted(_muted: boolean) {}
