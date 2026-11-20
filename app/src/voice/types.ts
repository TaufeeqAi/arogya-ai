export type VoiceSession = {
  app_id: string;
  channel: string;
  token: string | null;
  uid: number;
  agent_uid: number;
  agent_id?: string;
};

export type VoiceHandlers = {
  onAgentJoined?: () => void;
  onAgentLeft?: () => void;
  onLevels?: (l: { agent: number; me: number }) => void;
  onState?: (s: string) => void;
};
