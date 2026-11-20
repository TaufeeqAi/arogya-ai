export const C = {
  bg: '#F6F3EE',
  surface: '#FFFFFF',
  surfaceAlt: '#EFF6F4',
  ink: '#16302B',
  inkSoft: '#4B5F5A',
  muted: '#8A9A95',
  line: '#E3E0D9',
  primary: '#0F766E',
  primaryDark: '#0B4F49',
  primarySoft: '#D7EFEA',
  saffron: '#E8913A',
  saffronSoft: '#FCEBD8',
  danger: '#C2410C',
  dangerSoft: '#FDE4D8',
  ok: '#15803D',
  okSoft: '#DCF3E3',
  info: '#2563EB',
  infoSoft: '#E0E9FD',
};

export const R = { sm: 10, md: 16, lg: 22, xl: 28 };

export const shadow = {
  shadowColor: '#16302B',
  shadowOpacity: 0.08,
  shadowRadius: 14,
  shadowOffset: { width: 0, height: 6 },
  elevation: 3,
};

export const font = {
  h1: { fontSize: 26, fontWeight: '800' as const, color: C.ink, letterSpacing: -0.4 },
  h2: { fontSize: 19, fontWeight: '700' as const, color: C.ink },
  h3: { fontSize: 15.5, fontWeight: '700' as const, color: C.ink },
  body: { fontSize: 14.5, color: C.ink, lineHeight: 21 },
  small: { fontSize: 12.5, color: C.inkSoft },
  tiny: { fontSize: 11, color: C.muted, letterSpacing: 0.3 },
};
