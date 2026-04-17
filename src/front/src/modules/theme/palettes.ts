export type ThemeName = 'light' | 'dark';

export const themeOptions: Record<ThemeName, string> = {
  light: 'Light mode',
  dark: 'Dark mode',
};

export function getThemeClassName(theme: ThemeName): string {
  return theme === 'dark' ? 'theme-dark' : 'theme-light';
}