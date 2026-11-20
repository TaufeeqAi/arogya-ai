import { PermissionsAndroid, Platform } from 'react-native';
import {
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
    engine.initialize({ appId: s.app_id, channelProfile: ChannelProfileType.ChannelProfileCommunication });
  }
  const e = engine;

  const handler: IRtcEngineEventHandler = {
    onUserJoined: (_c, uid) => {
      if (uid === s.agent_uid) h.onAgentJoined?.();
    },
    onUserOffline: (_c, uid) => {
      if (uid === s.agent_uid) h.onAgentLeft?.();
    },
    onAudioVolumeIndication: (_c, speakers) => {
      let agent = 0;
      let me = 0;
      for (const sp of speakers) {
        const v = ((sp.volume ?? 0) / 255) * 100; // native 0-255 -> web-like 0-100
        if (sp.uid === 0 || sp.uid === s.uid) me = v;
        else if (sp.uid === s.agent_uid) agent = v;
      }
      h.onLevels?.({ agent, me });
    },
    onConnectionStateChanged: (_c, state) => h.onState?.(String(state)),
  };
  e.registerEventHandler(handler);
  e.enableAudio();
  e.setDefaultAudioRouteToSpeakerphone(true);
  e.enableAudioVolumeIndication(200, 3, true);
  e.joinChannel(s.token ?? '', s.channel, s.uid, {
    clientRoleType: ClientRoleType.ClientRoleBroadcaster,
    publishMicrophoneTrack: true,
    autoSubscribeAudio: true,
  });

  return async () => {
    try {
      e.leaveChannel();
      e.unregisterEventHandler(handler);
    } catch {}
  };
}

export async function setMuted(muted: boolean) {
  engine?.muteLocalAudioStream(muted);
}
