'use client';

export default function LogoutButton() {
  function logout() {
    localStorage.removeItem('ati_token');
    localStorage.removeItem('ati_user');
    window.location.href = '/login';
  }

  return <button className="text-slate-500 hover:text-slate-200" onClick={logout}>Sair</button>;
}