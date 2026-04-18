import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLogin } from '../../api/processes';
import { saveToken } from '../../api/client';
import { Icon } from '../../modules/ui/Icon';
import { LoginRoleSelector } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './LoginScreen.css';

export function LoginScreen() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState('Lawyer');
  const [error, setError] = useState<string | null>(null);

  const login = useLogin();

  const emailForRole = role === 'Lawyer' ? 'advogado@banco.com' : 'banco@banco.com';

  async function handleAccess() {
    setError(null);
    try {
      const data = await login.mutateAsync({ email: email || emailForRole, password: password || (role === 'Lawyer' ? 'advogado123' : 'banco123') });
      saveToken(data.access_token);
      window.localStorage.setItem('enteros-role', role);
      navigate(role === 'Bank Administrator' ? '/monitoring' : '/home');
    } catch {
      setError('Email ou senha inválidos.');
    }
  }

  return (
    <main className="login-wrap login-screen">
      <div className="login-shell login-screen__shell">
        <div className="login-screen__hero">
          <h1 className="headline login-screen__headline">
            EnterOS <span className="accent">Enterprise Legal Operations</span>
          </h1>
          <p className="lede login-screen__lede">
            Access the case workspace, load autos and subsídios, then inspect the AI recommendation before making a decision.
          </p>
        </div>

        <section className="login-card login-screen__card">
          <LoginRoleSelector onSelectRole={(r) => { setRole(r); setEmail(''); setPassword(''); }} />

          <div className="form-grid login-screen__form">
            <div>
              <div className="login-screen__label-row">
                <label className="field-label">ID or Email Address</label>
              </div>
              <div className="input-row">
                <Icon name="person" className="icon-prefix" />
                <input
                  className="text-input" type="text"
                  placeholder={emailForRole}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div>
              <div className="login-screen__label-row">
                <label className="field-label">Password</label>
              </div>
              <div className="input-row">
                <Icon name="lock" className="icon-prefix" />
                <input
                  className="text-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAccess()}
                />
                <button type="button" className="icon-button icon-suffix" onClick={() => setShowPassword((v) => !v)}>
                  <Icon name={showPassword ? 'visibility' : 'visibility_off'} />
                </button>
              </div>
            </div>

            {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', margin: 0 }}>{error}</p>}

            <button
              type="button" className="access-button"
              onClick={handleAccess}
              disabled={login.isPending}
            >
              {login.isPending ? 'Authenticating…' : 'Access System'}
            </button>
          </div>

          <div className="login-screen__footer">
            <p className="muted login-screen__footer-text">
              Internal enterprise access only.{' '}
              <a href="/" onClick={(e) => e.preventDefault()} style={{ color: 'var(--secondary)', fontWeight: 700 }}>
                Request access credentials
              </a>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
