import { PermissionsAndroid, Platform } from 'react-native';
import {
  AudioScenarioType,
  ChannelProfileType,
  ClientRoleType,
  createAgoraRtcEngine,
  IRtcEngine,
  IRtcEngineEventHandler,
} from 'react-native-agora';
import type { VoiceHandlers, VoiceSession } from './types';

let engine: IRtcEngine | null = null;

export async function joinVoice(s: VoiceSession, h: VoiceHandlers): Promise<() => Promise<void>> {
  if (Platform.OS === 'android') {
    const res = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO, {
      title: 'Microphone',
      message: 'Aarogya needs the microphone so you can talk to it.',
      buttonPositive: 'Allow',
    });
    if (res !== PermissionsAndroid.RESULTS.GRANTED) throw new Error('Microphone permission denied');
  }

  if (!engine) {
    engine = createAgoraRtcEngine();
    // AI dialogue scenario: Agora's echo cancellation / noise suppression tuned for Conversational AI, so the
    // agent's own voice from the phone speaker isn't treated as the user interrupting.
    engine.initialize({
      appId: s.app_id,
      channelProfile: ChannelProfileType.ChannelProfileCommunication,
      audioScenario: AudioScenarioType.AudioScenarioAiClient,
    });
  }
  const e = engine;

  // Greeting guard (see web): mic muted until the agent's greeting ends, max 9 s.
  let greeting: 'waiting' | 'speaking' | 'done' = 'waiting';
  let quietSince = 0;
  let lastAgent = 0;
  let lastMe = 0;
  let lastAgentTs = 0;
  const openMic = () => {
    if (greeting === 'done') return;
    greeting = 'done';
    e.muteLocalAudioStream(false);
    h.onMicOpen?.();
  };
  const fallback = setTimeout(openMic, 9000);

  const handler: IRtcEngineEventHandler = {
    onUserJoined: (_c, uid) => {
      if (uid === s.agent_uid) h.onAgentJoined?.();
    },
    onUserOffline: (_c, uid) => {
      if (uid === s.agent_uid) h.onAgentLeft?.();
    },
    onAudioVolumeIndication: (_c, speakers) => {
      // Android reports local (uid 0) and remote speakers in separate callbacks: update each side only when present
      const now = Date.now();
      for (const sp of speakers) {
        const v = ((sp.volume ?? 0) / 255) * 100; // native 0-255 -> web-like 0-100
        if (sp.uid === 0 || sp.uid === s.uid) lastMe = v;
        else if (sp.uid === s.agent_uid) {
          lastAgent = v;
          lastAgentTs = now;
        }
      }
      if (now - lastAgentTs > 450) lastAgent = 0;
      const agent = lastAgent;
      h.onLevels?.({ agent, me: greeting === 'done' ? lastMe : 0 });
      if (greeting === 'waiting' && agent > 6) greeting = 'speaking';
      if (greeting === 'speaking') {
        if (agent < 2) {
          quietSince = quietSince || now;
          if (now - quietSince > 900) openMic();
        } else quietSince = 0;
      }
    },
    onConnectionStateChanged: (_c, state) => h.onState?.(String(state)),
  };
  e.registerEventHandler(handler);
  e.enableAudio();
  e.setAudioScenario(AudioScenarioType.AudioScenarioAiClient);
  e.setDefaultAudioRouteToSpeakerphone(true);
  e.enableAudioVolumeIndication(200, 3, true);
  e.joinChannel(s.token ?? '', s.channel, s.uid, {
    clientRoleType: ClientRoleType.ClientRoleBroadcaster,
    publishMicrophoneTrack: true,
    autoSubscribeAudio: true,
  });
  e.muteLocalAudioStream(true);

  return async () => {
    clearTimeout(fallback);
    try {
      e.muteLocalAudioStream(false);
      e.leaveChannel();
      e.unregisterEventHandler(handler);
    } catch {}
  };
}

export async function setMuted(muted: boolean) {
  engine?.muteLocalAudioStream(muted);
}
