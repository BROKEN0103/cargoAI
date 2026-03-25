import { useState } from 'react';
import { useRouter } from 'next/router';
import { Lock, User, ShieldCheck } from 'lucide-react';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/api/login', { email, password });
      if (res.data.success) {
        localStorage.setItem('user', JSON.stringify(res.data.user));
        router.push('/dashboard');
      }
    } catch (err) {
      setError('Invalid credentials. Use admin@cargo.ai / password123');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4 font-sans text-gray-100">
      <div className="max-w-md w-full bg-gray-900 rounded-2xl border border-gray-800 shadow-2xl p-8">
        <div className="text-center mb-10">
          <div className="inline-flex p-4 bg-blue-600/10 rounded-full text-blue-500 mb-4">
            <ShieldCheck size={40} />
          </div>
          <h1 className="text-2xl font-black uppercase tracking-widest">
            Cargo<span className="text-blue-500">AI</span> Terminal
          </h1>
          <p className="text-gray-500 text-sm mt-2">Authorized Access Only</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Identity</label>
            <div className="relative">
              <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@cargo.ai" 
                className="w-full bg-gray-950 border border-gray-800 rounded-xl py-3 pl-12 pr-4 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Clearance Code</label>
            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                className="w-full bg-gray-950 border border-gray-800 rounded-xl py-3 pl-12 pr-4 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                required
              />
            </div>
          </div>

          {error && (
            <p className="text-red-500 text-xs text-center font-medium bg-red-500/10 py-2 rounded-lg border border-red-500/20">{error}</p>
          )}

          <button 
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 py-4 rounded-xl font-bold uppercase tracking-widest transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Enter Terminal'}
          </button>

          <div className="text-center pt-4 border-t border-gray-800/50">
            <p className="text-[10px] text-gray-600 uppercase tracking-widest">
              Secured by CargoAI Intelligence Node v1.0
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
