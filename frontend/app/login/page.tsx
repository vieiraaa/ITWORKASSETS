'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000/api/v1';

export default function LoginPage() {
  const router = useRouter();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('ati_token')) router.replace('/');
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${api}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: login.trim(), password }),
      });

      if (!response.ok) {
        let message = 'Usuário ou senha inválidos.';
        try {
          const details = await response.json();
          if (typeof details.detail === 'string' && response.status !== 401) message = details.detail;
        } catch {}
        throw new Error(message);
      }

      const data = await response.json();
      if (!data.access_token || !data.user) throw new Error('Resposta inválida do servidor.');
      localStorage.setItem('ati_token', data.access_token);
      localStorage.setItem('ati_user', JSON.stringify(data.user));
      router.replace('/');
    } catch (requestError) {
      setError(requestError instanceof TypeError ? 'Não foi possível conectar à API.' : requestError instanceof Error ? requestError.message : 'Não foi possível entrar.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="login-brand">
          <span className="brand-mark">A</span>
          <div>
            <p className="eyebrow">ATI Work Analytics</p>
            <h1>Bem-vindo de volta</h1>
          </div>
        </div>
        <p className="login-intro">Acesse os indicadores objetivos de atividade da sua operação.</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="login">Usuário</label>
          <input id="login" name="login" value={login} onChange={(event) => setLogin(event.target.value)} autoComplete="username" required autoFocus />
          <label htmlFor="password">Senha</label>
          <div className="password-field">
            <input id="password" name="password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
            <button type="button" className="password-toggle" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}>
              {showPassword ? 'Ocultar' : 'Mostrar'}
            </button>
          </div>
          {error && <p className="login-error" role="alert">{error}</p>}
          <button type="submit" disabled={loading || !login.trim() || !password}>{loading ? 'Entrando...' : 'Entrar'}</button>
        </form>
        <p className="login-footer">Ambiente protegido para usuários autorizados.</p>
      </section>
    </main>
  );
}