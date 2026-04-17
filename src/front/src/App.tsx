import { useMemo, useState } from 'react';
import { views, type ViewKey } from './data';
import { LoginScreen } from './screens/LoginScreen/LoginScreen';
import { UploadScreen } from './screens/UploadScreen/UploadScreen';
import { DashboardScreen } from './screens/DashboardScreen/DashboardScreen';
import { MonitoringScreen } from './screens/MonitoringScreen/MonitoringScreen';
import './modules/theme/theme.css';
import { getThemeClassName, type ThemeName } from './modules/theme/palettes';
import { SideBar } from './modules/ui/SideBar/SideBar';
import { TopBar } from './modules/ui/TopBar/TopBar';

function App() {
  const [view, setView] = useState<ViewKey>('login');
  const [theme, setTheme] = useState<ThemeName>('light');
  const activeLabel = useMemo(() => views.find((entry) => entry.key === view)?.label ?? 'Login', [view]);
  const themeClassName = getThemeClassName(theme);
  const isLoginView = view === 'login';

  return (
    <div className={`app-shell ${themeClassName}`}>
      <div className="ambient" />

      {isLoginView ? (
        <LoginScreen onLaunch={() => setView('upload')} />
      ) : (
        <div className="layout">
          <SideBar view={view} onNavigate={setView} />

          <div className="content">
            <TopBar
              activeLabel={activeLabel}
              currentView={view}
              theme={theme}
              onNavigate={setView}
              onToggleTheme={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            />
            {view === 'upload' && <UploadScreen onOpenDashboard={() => setView('dashboard')} />}
            {view === 'dashboard' && <DashboardScreen onOpenMonitoring={() => setView('monitoring')} />}
            {view === 'monitoring' && <MonitoringScreen onOpenDecision={() => setView('dashboard')} />}
          </div>
        </div>
      )}
    </div>
  );
}
export default App;