import React, { createContext, useContext } from 'react';
import { Platform, useWindowDimensions } from 'react-native';

export type Route = 'home' | 'talk' | 'records' | 'care' | 'timeline' | 'notifications' | 'profile';

export const ROUTES: { key: Route; label: string; icon: string; mobile: boolean }[] = [
  { key: 'home', label: 'Home', icon: '🏠', mobile: true },
  { key: 'talk', label: 'Aarogya', icon: '🎙', mobile: true },
  { key: 'records', label: 'Records', icon: '📂', mobile: true },
  { key: 'care', label: 'Care', icon: '💊', mobile: true },
  { key: 'timeline', label: 'Timeline', icon: '🕒', mobile: false },
  { key: 'notifications', label: 'Notifications', icon: '🔔', mobile: false },
  { key: 'profile', label: 'Profile', icon: '👤', mobile: true },
];

export const SIDEBAR_W = 232;

/** Side navigation on wide web screens; bottom tab bar on phones and narrow browser windows. */
export function useLayout() {
  const { width } = useWindowDimensions();
  const sidebar = Platform.OS === 'web' && width >= 820;
  return { sidebar, contentWidth: sidebar ? width - SIDEBAR_W : width };
}

const NavCtx = createContext<{ route: Route; go: (r: Route) => void }>({ route: 'home', go: () => {} });
export const NavProvider = NavCtx.Provider;
export const useNav = () => useContext(NavCtx);
