import { Icon } from '../Icon';
import { useMemo } from 'react';
import type { UserRole } from '../LoginRoleSelector/LoginRoleSelector';
import './SideBar.css';
import type { ThemeName } from '../../theme/palettes';


export function SideBar({
  currentPath,
  theme,
  onNavigate,
  onToggleTheme,
}: {
  currentPath: string;
  theme: ThemeName;
  onNavigate: (nextPath: string) => void;
  onToggleTheme: () => void;
}) {


  const userRole = useMemo<UserRole>(() => {
      const savedRole = window.localStorage.getItem('enteros-role');
      return savedRole === 'Bank Administrator' ? 'Bank Administrator' : 'Lawyer';
  }, []);

  const navigationItems = [
    { label: 'Home', icon: 'home', path: '/home' },
    userRole === 'Lawyer' && { label: 'Process Autos', icon: 'description', path: '/upload' },
    userRole === 'Lawyer' && { label: 'Decision Outcome', icon: 'gavel', path: '/dashboard' },
    userRole === 'Bank Administrator' && { label: 'Monitoring', icon: 'analytics', path: '/monitoring' },
  ];


  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Icon name="account_balance" />
        </div>
        <div>
          <h1 className="brand-name">EnterOS</h1>
          <p className="brand-subtitle">Legal Division</p>
        </div>
        <button type="button" className="sidebar-theme-button" onClick={onToggleTheme} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
          <Icon name={theme === 'light' ? 'dark_mode' : 'light_mode'} />
        </button>
      </div>

      <ul className="nav-list">
        {navigationItems.map((item) => (
            item && (
              <li key={item.label}>
                <button className={`nav-button ${currentPath === item.path || currentPath.startsWith(item.path + '/') ? 'active' : ''}`} type="button" onClick={() => onNavigate(item.path)}>
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                </button>
              </li>
            )
        ))}
      </ul>

      <button className="sidebar-cta" type="button" onClick={() => onNavigate('/dashboard')}>
        {userRole === 'Lawyer' ? 'New Analysis' : 'View Performance'}
      </button>
    </aside>
  );
}