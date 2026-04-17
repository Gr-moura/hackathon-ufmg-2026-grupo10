import { navigationItems } from '../../../data';
import { Icon } from '../Icon';

export function SideBar({
  currentPath,
  onNavigate,
}: {
  currentPath: string;
  onNavigate: (nextPath: string) => void;
}) {
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
      </div>

      <ul className="nav-list">
        {navigationItems.map((item) => (
          <li key={item.label}>
            <button className={`nav-button ${currentPath === item.path ? 'active' : ''}`} type="button" onClick={() => onNavigate(item.path)}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </button>
          </li>
        ))}
      </ul>

      <button className="sidebar-cta" type="button" onClick={() => onNavigate('/dashboard')}>
        New Analysis
      </button>
    </aside>
  );
}