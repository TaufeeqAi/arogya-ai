import AgoraRTC, { IAgoraRTCClient, IMicrophoneAudioTrack } from 'agora-rtc-sdk-ng';
import type { VoiceHandlers, VoiceSession } from './types';

AgoraRTC.setLogLevel(3);

export async function joinVoice(s: VoiceSession, h: VoiceHandlers): Promise<() => Promise<void>> {
  const client: IAgoraRTCClient = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
  let mic: IMicrophoneAudioTrack | null = null;

  client.on('user-published', async (user, mediaType) => {
    await client.subscribe(user, mediaType);
    if (mediaType === 'audio') {
      user.audioTrack?.play();
      h.onAgentJoined?.();
    }
  });
  client.on('user-left', () => h.onAgentLeft?.());
  client.enableAudioVolumeIndicator();
  client.on('volume-indicator', (vols) => {
    let agent = 0;
    let me = 0;
    for (const v of vols) {
      if (String(v.uid) === String(s.agent_uid)) agent = v.level;
      else if (String(v.uid) === String(s.uid) || v.uid === 0) me = v.level;
    }
    h.onLevels?.({ agent, me });
  });
  client.on('connection-state-change', (cur) => h.onState?.(cur));

  await client.join(s.app_id, s.channel, s.token || null, s.uid);
  mic = await AgoraRTC.createMicrophoneAudioTrack({ AEC: true, ANS: true, AGC: true });
  await client.publish([mic]);

  return async () => {
    try {
      mic?.stop();
      mic?.close();
      await client.leave();
    } catch {}
  };
}

export async function setMuted(_muted: boolean) {
  /* handled by leaving/joining in this prototype */
}
