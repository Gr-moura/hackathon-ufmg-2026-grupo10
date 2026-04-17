import { roleTabs } from '../../data';
import { Icon } from '../../modules/ui/Icon';
import './LoginScreen.css';

export function LoginScreen({ onLaunch }: { onLaunch: () => void }) {
  return (
    <main className="login-wrap login-screen">
      <div className="login-shell login-screen__shell">
        <div className="login-screen__hero">
          <div className="pill login-screen__pill">Secure access</div>
          <h1 className="headline login-screen__headline">
            EnterOS <span className="accent">Enterprise Legal Operations</span>
          </h1>
          <p className="lede login-screen__lede">
            Access the case workspace, load autos and subsídios, then inspect the AI recommendation before making a decision.
          </p>
        </div>

        <section className="login-card login-screen__card">
          <div className="login-screen__role-block">
            <div className="field-label">Identify Your Role</div>
            <div className="tabs">
              {roleTabs.map((tab) => (
                <button key={tab.label} type="button" className={`tab ${tab.active ? 'active' : ''}`}>
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-grid login-screen__form">
            <div>
              <label className="field-label" htmlFor="identifier">
                ID or Email Address
              </label>
              <div className="input-row">
                <Icon name="person" className="icon-prefix" />
                <input id="identifier" className="text-input" type="text" placeholder="username@bankufmg.com" />
              </div>
            </div>

            <div>
              <div className="login-screen__label-row">
                <label className="field-label" htmlFor="password" style={{ marginBottom: 0 }}>
                  Secure Password
                </label>
                <a href="/" className="pill" onClick={(event) => event.preventDefault()}>
                  Forgot?
                </a>
              </div>
              <div className="input-row">
                <Icon name="lock" className="icon-prefix" />
                <input id="password" className="text-input" type="password" placeholder="••••••••••••" />
                <button type="button" className="icon-button icon-suffix" aria-label="Toggle password visibility">
                  <Icon name="visibility_off" />
                </button>
              </div>
            </div>

            <label className="checkbox-row">
              <input type="checkbox" />
              <span className="muted login-screen__remember">Keep me authenticated for 24 hours</span>
            </label>

            <button type="button" className="access-button" onClick={onLaunch}>
              Access System
            </button>
          </div>

          <div className="login-screen__footer">
            <p className="muted login-screen__footer-text">
              Internal enterprise access only. <a href="/" onClick={(event) => event.preventDefault()} style={{ color: 'var(--secondary)', fontWeight: 700 }}>Request access credentials</a>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}