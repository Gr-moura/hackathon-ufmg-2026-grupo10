import { views, type ViewKey } from '../../../data';
import { Icon } from '../Icon';
import { themeOptions, type ThemeName } from '../../theme/palettes';

export function TopBar({
  activeLabel,
  currentView,
  theme,
  onNavigate,
  onToggleTheme,
}: {
  activeLabel: string;
  currentView: ViewKey;
  theme: ThemeName;
  onNavigate: (nextView: ViewKey) => void;
  onToggleTheme: () => void;
}) {
  return (
    <header className="topbar">
      <div>
        <h2 className="topbar-title">EnterOS | {activeLabel}</h2>
        <p className="topbar-subtitle">Decision workflow, file intake, and monitoring for the Banco UFMG challenge.</p>
      </div>

      <div className="topbar-actions">
        {views.map((entry) => (
          <button key={entry.key} type="button" className={`view-switch ${currentView === entry.key ? 'active' : ''}`} onClick={() => onNavigate(entry.key)}>
            <Icon name={entry.icon} />
            {entry.label}
          </button>
        ))}
        <button type="button" className="view-switch" onClick={onToggleTheme}>
          <Icon name={theme === 'light' ? 'dark_mode' : 'light_mode'} />
          {themeOptions[theme]}
        </button>
        <button type="button" className="small-icon-button">
          <Icon name="notifications" />
        </button>
        <button type="button" className="small-icon-button">
          <Icon name="settings" />
        </button>
      </div>
    </header>
  );
}