import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLogin } from '../../api/processes';
import { saveToken } from '../../api/client';
import { Icon } from '../../modules/ui/Icon';
import { LoginRoleSelector } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './LoginScreen.css';
import { LoginInputs } from '../../modules/ui/LoginInputs/LoginInputs';

export function LoginScreen() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Lawyer');
  const [error, setError] = useState<string | null>(null);
  const login = useLogin();

  async function handleAccess() {
    setError(null);
    try {
      const data = await login.mutateAsync({ email: email, password: password });
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
            <LoginInputs inputType="Login" setValueFunction={setEmail} />
            <LoginInputs inputType="Password" placeholder="password" setValueFunction={setPassword} />

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
