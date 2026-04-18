import { useState, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginScreen } from './screens/LoginScreen/LoginScreen';
import { UploadScreen } from './screens/UploadScreen/UploadScreen';
import { DashboardScreen } from './screens/DashboardScreen/DashboardScreen';
import { ProcessListScreen } from './screens/ProcessListScreen/ProcessListScreen';
import { MonitoringScreen } from './screens/MonitoringScreen/MonitoringScreen';
import './modules/theme/theme.css';
import { getThemeClassName, type ThemeName } from './modules/theme/palettes';
import { SideBar } from './modules/ui/SideBar/SideBar';
import { Home } from './screens/Home/Home';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10_000, retry: 1 } },
});

function App() {
  const [theme, setTheme] = useState<ThemeName>(() => {
    const savedTheme = window.localStorage.getItem('enteros-theme');
    return savedTheme === 'dark' ? 'dark' : 'light';
  });
  const navigate = useNavigate();
  const location = useLocation();
  const themeClassName = getThemeClassName(theme);
  const isLoginView = location.pathname === '/' || location.pathname === '/login';

  const handleToggleTheme = () => {
    setTheme((currentTheme) => {
      const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
      window.localStorage.setItem('enteros-theme', nextTheme);
      return nextTheme;
    });
  };

  const renderWorkspace = (content: ReactNode) => (
    <div className="layout">
      <SideBar currentPath={location.pathname} theme={theme} onNavigate={(path) => navigate(path)} onToggleTheme={handleToggleTheme} />

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
        <Route path="/home" element={renderWorkspace(<Home />)} />
        <Route path="/upload" element={renderWorkspace(<UploadScreen />)} />
        <Route path="/processes" element={renderWorkspace(<ProcessListScreen />)} />
        <Route path="/dashboard/:processoId" element={renderWorkspace(<DashboardScreen />)} />
        <Route path="/monitoring" element={renderWorkspace(<MonitoringScreen />)} />
        <Route path="*" element={<Navigate to={isLoginView ? '/login' : '/home'} replace />} />
      </Routes>
    </div>
  );
}

export default function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}