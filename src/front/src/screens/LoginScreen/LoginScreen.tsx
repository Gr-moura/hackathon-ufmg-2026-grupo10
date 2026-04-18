import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLogin } from '../../api/processes';
import { saveToken } from '../../api/client';
import { Icon } from '../../modules/ui/Icon';
import { LoginRoleSelector, type UserRole } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './LoginScreen.css';
import { LoginInputs } from '../../modules/ui/LoginInputs/LoginInputs';

function resolveUserRole(apiRole: string | undefined, fallbackRole: UserRole): UserRole {
  const normalizedRole = (apiRole ?? '').trim().toLowerCase();

  if (normalizedRole === 'banco' || normalizedRole === 'bank administrator') {
    return 'Bank Administrator';
  }

  if (normalizedRole === 'advogado' || normalizedRole === 'lawyer') {
    return 'Lawyer';
  }

  return fallbackRole;
}

export function LoginScreen() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('Lawyer');
  const [error, setError] = useState<string | null>(null);
  const login = useLogin();

  async function handleAccess() {
    setError(null);

    const normalizedEmail = email.trim();
    if (!normalizedEmail || !password) {
      setError('Informe email e senha.');
      return;
    }

    try {
      const data = await login.mutateAsync({ email: normalizedEmail, password });
      const resolvedRole = resolveUserRole(data.role, role);

      saveToken(data.access_token);
      window.localStorage.setItem('enteros-role', resolvedRole);
      navigate(resolvedRole === 'Bank Administrator' ? '/monitoring' : '/home');
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
            <br />
            <small style={{ opacity: 0.7 }}>Demo: advogado@banco.com / advogado123 | banco@banco.com / banco123</small>
          </p>
        </div>

        <section className="login-card login-screen__card">
          <LoginRoleSelector onSelectRole={(r) => { setRole(r); setEmail(''); setPassword(''); }} />

          <div className="form-grid login-screen__form">
            <LoginInputs inputType="Login" value={email} onChange={setEmail} />
            <LoginInputs inputType="Password" placeholder="password" value={password} onChange={setPassword} />

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
