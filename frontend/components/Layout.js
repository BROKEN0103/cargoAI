import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { LayoutDashboard, History, UploadCloud } from 'lucide-react';

export default function Layout({ children }) {
  const router = useRouter();
  const [isAuth, setIsAuth] = useState(false);

  useEffect(() => {
    if (router.pathname === '/login') {
      setIsAuth(true);
      return;
    }
    const user = localStorage.getItem('user');
    if (!user) {
      router.push('/login');
    } else {
      setIsAuth(true);
    }
  }, [router.pathname]);

  if (!isAuth) return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-500 uppercase tracking-widest text-xs animate-pulse">Initializing Terminal...</div>;
  if (router.pathname === '/login') return children;

  const handleLogout = () => {
    localStorage.removeItem('user');
    router.push('/login');
  };

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'Upload Scan', icon: UploadCloud, path: '/' },
    { label: 'Scan History', icon: History, path: '/history' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-black text-white tracking-widest uppercase flex items-center gap-2">
            Cargo<span className="text-blue-500">AI</span>
          </h1>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest">Intelligence Node</p>
        </div>
        <nav className="flex-1 p-4 flex flex-col gap-2">
          {navItems.map((item) => {
            const active = router.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link key={item.path} href={item.path} className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${active ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'}`}>
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-800 space-y-4">
          <button 
            onClick={handleLogout}
            className="w-full py-2 bg-red-900/10 hover:bg-red-900/20 text-red-500 text-[10px] font-bold uppercase tracking-widest rounded-lg transition-colors border border-red-900/20 text-center block"
          >
            Logout session
          </button>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-xs text-gray-400 uppercase tracking-widest">System Online</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm flex items-center px-8 z-10 sticky top-0">
          <h2 className="text-sm font-medium text-gray-300">
            {navItems.find(i => i.path === router.pathname)?.label || 'Application'}
          </h2>
        </header>
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
