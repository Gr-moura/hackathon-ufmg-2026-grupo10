import { useMemo, useState } from 'react';
import { navigationItems, views, type ViewKey } from './data';
import { Icon } from './modules/ui/Icon';
import { LoginScreen } from './screens/LoginScreen/LoginScreen';
import { UploadScreen } from './screens/UploadScreen/UploadScreen';
import { DashboardScreen } from './screens/DashboardScreen/DashboardScreen';
import { MonitoringScreen } from './screens/MonitoringScreen/MonitoringScreen';
import './modules/theme/theme.css';
import { getThemeClassName, themeOptions, type ThemeName } from './modules/theme/palettes';

function App() {
  const [view, setView] = useState<ViewKey>('login');
  const [theme, setTheme] = useState<ThemeName>('light');
  const activeLabel = useMemo(() => views.find((entry) => entry.key === view)?.label ?? 'Login', [view]);
  const themeClassName = getThemeClassName(theme);

  return (
    <div className={`app-shell ${themeClassName}`}>
      <div className="ambient" />

      <div className="layout">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-mark">
              <Icon name="account_balance" />
            </div>
            <div>
              <h1 className="brand-name">EnterOS</h1>
              <p className="brand-subtitle">Legal Division</p>
            </div>
          </div>

          <ul className="nav-list">
            {navigationItems.map((item) => (
              <li key={item.label}>
                <button className={`nav-button ${view === item.view ? 'active' : ''}`} type="button" onClick={() => setView(item.view)}>
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>

          <button className="sidebar-cta" type="button" onClick={() => setView('dashboard')}>
            New Analysis
          </button>
        </aside>

        <div className="content">
          <header className="topbar">
            <div>
              <h2 className="topbar-title">EnterOS | {activeLabel}</h2>
              <p className="topbar-subtitle">Decision workflow, file intake, and monitoring for the Banco UFMG challenge.</p>
            </div>

            <div className="topbar-actions">
              {views.map((entry) => (
                <button key={entry.key} type="button" className={`view-switch ${view === entry.key ? 'active' : ''}`} onClick={() => setView(entry.key)}>
                  <Icon name={entry.icon} />
                  {entry.label}
                </button>
              ))}
              <button type="button" className="view-switch" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
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
          {view === 'login' && <LoginScreen onLaunch={() => setView('upload')} />}
          {view === 'upload' && <UploadScreen onOpenDashboard={() => setView('dashboard')} />}
          {view === 'dashboard' && <DashboardScreen onOpenMonitoring={() => setView('monitoring')} />}
          {view === 'monitoring' && <MonitoringScreen onOpenDecision={() => setView('dashboard')} />}
        </div>
      </div>
    </div>
  );
}
export default App;