import { useState, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { views } from './data';
import { LoginScreen } from './screens/LoginScreen/LoginScreen';
import { UploadScreen } from './screens/UploadScreen/UploadScreen';
import { DashboardScreen } from './screens/DashboardScreen/DashboardScreen';
import { MonitoringScreen } from './screens/MonitoringScreen/MonitoringScreen';
import './modules/theme/theme.css';
import { getThemeClassName, type ThemeName } from './modules/theme/palettes';
import { SideBar } from './modules/ui/SideBar/SideBar';

function App() {
  const [theme, setTheme] = useState<ThemeName>('light');
  const navigate = useNavigate();
  const location = useLocation();
  const themeClassName = getThemeClassName(theme);
  const isLoginView = location.pathname === '/' || location.pathname === '/login';
  const activeLabel = views.find((entry) => entry.path === location.pathname)?.label ?? 'Login';

  const renderWorkspace = (content: ReactNode) => (
    <div className="layout">
      <SideBar currentPath={location.pathname} onNavigate={(path) => navigate(path)} />

      <div className="content">
        {content}
      </div>
    </div>
  );

  return (
    <div className={`app-shell ${themeClassName}`}>
      <div className="ambient" />

      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/upload" element={renderWorkspace(<UploadScreen />)} />
        <Route path="/dashboard" element={renderWorkspace(<DashboardScreen />)} />
        <Route path="/monitoring" element={renderWorkspace(<MonitoringScreen />)} />
        <Route path="*" element={<Navigate to={isLoginView ? '/login' : '/dashboard'} replace />} />
      </Routes>
    </div>
  );
}
export default App;