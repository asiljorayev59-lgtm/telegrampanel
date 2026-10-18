import { useState } from 'react';
import { api } from '../api';

export default function AuthPage({ onAuth }) {
  const [step, setStep] = useState('phone');
  const [phone, setPhone] = useState('+998');
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [hint, setHint] = useState('');
  const [err, setErr] = useState('');

  const requestCode = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      const r = await api('/auth/request-code', { method: 'POST', body: { phone } });
      if (r.devCode) setHint(`Dev kod: ${r.devCode}`);
      setStep('code');
    } catch (e) { setErr(e.message); }
  };

  const verify = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      const r = await api('/auth/verify', { method: 'POST', body: { phone, code, name } });
      localStorage.setItem('token', r.token);
      onAuth(r.user);
    } catch (e) { setErr(e.message); }
  };

  return (
    <div className="h-full grid place-items-center bg-panel px-4">
      <form onSubmit={step === 'phone' ? requestCode : verify} className="w-80 text-center space-y-4">
        <div className="mx-auto w-28 h-28 rounded-full bg-accent grid place-items-center text-5xl text-white">✈</div>
        <h1 className="text-3xl font-medium">{step === 'phone' ? 'Messenger' : phone}</h1>
        <p className="text-sub text-sm">
          {step === 'phone'
            ? 'Telefon raqamingizni kiriting.'
            : 'Tasdiqlash kodi yuborildi (dev rejimda server konsolida va quyida).'}
        </p>

        {step === 'phone' ? (
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="Telefon raqam"
            className="w-full px-4 py-3 rounded-xl border border-line bg-transparent outline-none focus:border-accent"
          />
        ) : (
          <>
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={5}
              placeholder="Kod"
              autoFocus
              className="w-full px-4 py-3 rounded-xl border border-line bg-transparent text-center tracking-[0.5em] outline-none focus:border-accent"
            />
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ismingiz (yangi foydalanuvchi uchun)"
              className="w-full px-4 py-3 rounded-xl border border-line bg-transparent outline-none focus:border-accent"
            />
            {hint && <p className="text-xs text-sub">{hint}</p>}
          </>
        )}

        {err && <p className="text-red-500 text-sm">{err}</p>}
        <button className="w-full py-3 rounded-xl bg-accent text-white font-medium uppercase tracking-wide">
          Keyingisi
        </button>
      </form>
    </div>
  );
}
